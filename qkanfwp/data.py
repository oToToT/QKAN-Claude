"""Benchmark series used in the Gated QKAN-FWP paper (arXiv:2605.06734, Sec. 6).

The paper fixes the generating equations but not every sampling choice.  Where
it is silent (number of samples / time span of damped SHM, Bessel and DQC) we
use 300 samples, the length the paper states for NARMA; these choices are
recorded in ``SERIES_INFO``.  Absolute MSEs on those three series are therefore
not directly comparable with the paper's tables; relative comparisons between
models trained here are.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp
from scipy.linalg import expm
from scipy.special import jv

SUNSPOT_CSV = Path(__file__).resolve().parent.parent / "data" / "SN_m_tot_V2.0.csv"

SERIES_INFO = {
    "bessel": "J_2(x), x in [0, 30], 300 samples (span/length not given in the paper)",
    "shm": "damped pendulum angular velocity, t in [0, 20], 300 samples (span/length not given)",
    "narma5": "NARMA5, M = 300 (paper), zero-initialised so the start-up transient is included",
    "narma10": "NARMA10, M = 300 (paper), zero-initialised so the start-up transient is included",
    "dqc": "delayed quantum control pulse train, t in [-2, 20], 300 samples (length not given)",
    "jc": "open Jaynes-Cummings <sigma+ sigma->, t in [0, 50], 3000 samples (paper)",
}


def bessel(n: int = 300, x_max: float = 30.0) -> np.ndarray:
    return jv(2, np.linspace(0.0, x_max, n))


def damped_shm(n: int = 300, t_max: float = 20.0) -> np.ndarray:
    g, b, length, m = 9.81, 0.15, 1.0, 1.0

    def rhs(_, s):
        theta, omega = s
        return [omega, -(b / m) * omega - (g / length) * np.sin(theta)]

    t = np.linspace(0.0, t_max, n)
    sol = solve_ivp(rhs, (0.0, t_max), [0.0, 3.0], t_eval=t, rtol=1e-10, atol=1e-12)
    return sol.y[1]


def narma(order: int, n: int = 300, burn_in: int = 0) -> np.ndarray:
    """NARMA series of length ``n``.  ``burn_in`` extra steps are simulated
    first and discarded, which removes the start-up transient from zero."""
    alpha, beta, gamma, delta = 0.3, 0.05, 1.5, 0.1
    a_bar, b_bar, g_bar, period = 2.11, 3.73, 4.11, 100.0
    n_out, n = n, n + burn_in
    t = np.arange(n)
    u = 0.1 * (
        np.sin(2 * np.pi * a_bar * t / period)
        * np.sin(2 * np.pi * b_bar * t / period)
        * np.sin(2 * np.pi * g_bar * t / period)
        + 1.0
    )
    # Standard zero-initialised recurrence: the first ``order`` outputs are 0
    # and the start-up transient is part of the M = 300 series.
    y = np.zeros(n)
    for k in range(order - 1, n - 1):
        y[k + 1] = (
            alpha * y[k]
            + beta * y[k] * y[k - order + 1 : k + 1].sum()
            + gamma * u[k - order + 1] * u[k]
            + delta
        )
    return y[-n_out:]


def dqc(n: int = 300) -> np.ndarray:
    t = np.linspace(-2.0, 20.0, n)
    pulses = sum(np.exp(-10.0 * (t - 2.0 * k) ** 2) for k in range(11))
    return pulses * np.exp(-t / 16.0)


def jaynes_cummings(n: int = 3000, t_max: float = 50.0, n_fock: int = 3) -> np.ndarray:
    """Qubit excitation of a lossy resonant Jaynes-Cummings model.

    H = wc a'a + wq s+s- + g (s- a' + s+ a), collapse sqrt(kappa) a,
    wc = wq = 2 pi, g = pi, kappa = 0.05, rho(0) = |g, 1><g, 1|.
    Solved exactly by exponentiating the Lindblad super-operator (the dynamics
    never leave the <= 1 excitation sector, so 3 Fock levels are plenty).
    """
    wc = wq = 2 * np.pi
    g, kappa = np.pi, 0.05
    a = np.diag(np.sqrt(np.arange(1, n_fock)), 1)
    sm = np.array([[0.0, 1.0], [0.0, 0.0]])  # |g><e| with basis (g, e)
    eye_f, eye_q = np.eye(n_fock), np.eye(2)
    a_full = np.kron(eye_q, a)
    sm_full = np.kron(sm, eye_f)
    ham = (
        wc * a_full.T @ a_full
        + wq * sm_full.T @ sm_full
        + g * (sm_full @ a_full.T + sm_full.T @ a_full)
    )
    c = np.sqrt(kappa) * a_full
    dim = 2 * n_fock
    eye = np.eye(dim)
    cdc = c.T @ c
    # column-stacking vec: vec(A rho B) = (B^T kron A) vec(rho)
    liouv = (
        -1j * (np.kron(eye, ham) - np.kron(ham.T, eye))
        + np.kron(c.conj(), c)
        - 0.5 * np.kron(eye, cdc)
        - 0.5 * np.kron(cdc.T, eye)
    )
    psi0 = np.kron(np.array([1.0, 0.0]), np.eye(n_fock)[1])  # |g, 1>
    rho = np.outer(psi0, psi0).astype(complex).reshape(-1, order="F")
    step = expm(liouv * (t_max / (n - 1)))
    proj = (sm_full.T @ sm_full).reshape(-1, order="F")  # vec of s+ s-
    out = np.empty(n)
    for k in range(n):
        out[k] = np.real(proj.conj() @ rho)
        rho = step @ rho
    return out


GENERATORS = {
    "bessel": bessel,
    "shm": damped_shm,
    "narma5": lambda: narma(5),
    "narma10": lambda: narma(10),
    # robustness variants: 200 burn-in steps discarded, so no start-up transient
    "narma5b": lambda: narma(5, burn_in=200),
    "narma10b": lambda: narma(10, burn_in=200),
    "dqc": dqc,
    "jc": jaynes_cummings,
}


def load_series(name: str, dtype=np.float32, norm: str = "global", fit_len: int | None = None) -> np.ndarray:
    """Return the series min-max normalised to [-1, 1].

    ``norm='global'`` uses the min / max of the whole series (the paper's
    protocol: normalise, then split - the test range leaks into the scaling).
    ``norm='train'`` takes them from the first ``fit_len`` samples only, and
    ``norm='none'`` returns the raw series.
    """
    s = np.asarray(GENERATORS[name](), dtype=np.float64)
    if norm == "none":
        return s.astype(dtype)
    ref = s if norm == "global" else s[:fit_len]
    lo, hi = ref.min(), ref.max()
    return (2.0 * (s - lo) / (hi - lo) - 1.0).astype(dtype)


def make_windows(series: np.ndarray, window: int, horizon: int = 1):
    """Sliding windows: x[i] = s[i : i+window], y[i] = s[i+window : i+window+horizon]."""
    n = len(series) - window - horizon + 1
    idx = np.arange(window)[None, :] + np.arange(n)[:, None]
    x = series[idx]
    idy = np.arange(horizon)[None, :] + np.arange(n)[:, None] + window
    y = series[idy]
    return x[..., None], y


def chrono_split(n: int, fractions: tuple[float, ...]):
    """Chronological split of ``n`` samples into consecutive index ranges."""
    edges = [0]
    acc = 0.0
    for f in fractions[:-1]:
        acc += f
        edges.append(int(round(n * acc)))
    edges.append(n)
    return [np.arange(edges[i], edges[i + 1]) for i in range(len(fractions))]


def load_sunspots(n_records: int = 3326):
    """SILSO monthly mean total sunspot number (V2.0).

    The paper uses 3,326 monthly records, i.e. 1749-01 .. 2026-02.  Returns the
    raw series and the [0, 1] min-max scaled series.
    """
    raw = np.loadtxt(SUNSPOT_CSV, delimiter=";", usecols=3)[:n_records]
    lo, hi = raw.min(), raw.max()
    return raw.astype(np.float32), ((raw - lo) / (hi - lo)).astype(np.float32), (lo, hi)


# ---------------------------------------------------------------------------
# The same benchmarks as the authors' released code generates them
# (https://github.com/MatthewPeng57/Gated-QKAN-FWP, commit 2cf0457,
# ``times_series_benchmark/src/datasets``).  The code differs from the text of
# the paper in several places; ``CODE_INFO`` lists the settings.  The most
# important one: for NARMA the input window is the *drive* u and the target is
# y, and neither is rescaled.
# ---------------------------------------------------------------------------
AUTHORS_JC_CSV = Path(__file__).resolve().parent.parent / "data" / "authors" / "jaynes_cummings.csv"

CODE_INFO = {
    "c_bessel": "J_2(x), x = linspace(2, 100, 256); min-max scaled to [-1, 1]",
    "c_shm": "damped pendulum angular velocity, t = linspace(0, 20, 240), scipy odeint; scaled to [-1, 1]",
    "c_narma5": "NARMA5, 300 steps, drive period 300, y_0 = 0.196; input window = u, target = y, no scaling",
    "c_narma10": "NARMA10, 300 steps, drive period 300, y_0 = 0.196; input window = u, target = y, no scaling",
    "c_dqc": "pulse train on x = arange(-2, 20, 0.01) (2200 samples); scaled to [-1, 1]",
    "c_jc": "open Jaynes-Cummings qubit excitation, the authors' CUDA-Q trace (3000 samples); scaled to [-1, 1]",
}
CODE_INPUT_IS_TARGET = {"c_bessel": True, "c_shm": True, "c_dqc": True, "c_jc": True, "c_narma5": False, "c_narma10": False}


def _minmax(s: np.ndarray) -> np.ndarray:
    return 2.0 * (s - s.min()) / (s.max() - s.min()) - 1.0


def narma_code(order: int, n: int = 300) -> tuple[np.ndarray, np.ndarray]:
    """Drive ``u`` and output ``y`` of the authors' NARMA generator: the three
    sine factors of u have period ``n`` (not 100), the history before t = 0 is
    zero and y_0 = 0.196."""
    t = np.arange(n)
    u = 0.1 * (np.sin(2 * np.pi * 2.11 * t / n) * np.sin(2 * np.pi * 3.73 * t / n) * np.sin(2 * np.pi * 4.11 * t / n) + 1.0)
    y = [0.196]
    for k in range(n):
        hist = sum(y[k - j] for j in range(order) if k - j >= 0)
        u_lag = u[k - order + 1] if k - order + 1 >= 0 else 0.0
        y.append(0.3 * y[k] + 0.05 * y[k] * hist + 1.5 * u_lag * u[k] + 0.1)
    return u, np.array(y[:-1])


def code_series(name: str) -> tuple[np.ndarray, np.ndarray]:
    """``(inputs, targets)`` of one benchmark of the authors' code (float64)."""
    if name == "c_bessel":
        s = _minmax(jv(2, np.linspace(2.0, 100.0, 256)))
    elif name == "c_shm":
        from scipy.integrate import odeint

        def rhs(state, _t):
            return [state[1], -0.15 * state[1] - 9.81 * np.sin(state[0])]

        s = _minmax(odeint(rhs, [0.0, 3.0], np.linspace(0.0, 20.0, 240))[:, 1])
    elif name == "c_dqc":
        x = np.arange(-2, 20, 0.01)
        s = _minmax(sum(np.exp(-10.0 * (x - 2 * k) ** 2) * np.exp(-x / 16.0) for k in range(11)))
    elif name == "c_jc":
        s = _minmax(np.loadtxt(AUTHORS_JC_CSV))
    elif name in ("c_narma5", "c_narma10"):
        return narma_code(int(name[len("c_narma"):]))
    else:
        raise KeyError(name)
    return s, s


def code_windows(name: str, window: int):
    """Windows as the authors' datasets slice them: ``x[i] = inputs[i : i+window]``,
    ``y[i] = targets[i+window]`` for ``i < len - window - 1``, both stored in
    float32 (returned here as float64 arrays holding the float32 values)."""
    inp, tgt = code_series(name)
    inp, tgt = inp.astype(np.float32).astype(np.float64), tgt.astype(np.float32)
    n = len(inp) - window - 1
    idx = np.arange(window)[None, :] + np.arange(n)[:, None]
    return inp[idx][..., None], tgt[np.arange(n) + window][:, None]


def code_split(n: int, protocol: str = "paper"):
    """Chronological split by window index with the truncation of the authors'
    code (``int(0.8 * n)``); ``'dev'`` cuts a validation part out of the
    training windows (70 / 10 / 20)."""
    cut = int(0.8 * n)
    if protocol == "paper":
        return np.arange(cut), np.arange(cut, n)
    val = int(0.7 * n)
    return np.arange(val), np.arange(val, cut), np.arange(cut, n)
