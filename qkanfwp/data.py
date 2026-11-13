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


def narma(order: int, n: int = 300) -> np.ndarray:
    alpha, beta, gamma, delta = 0.3, 0.05, 1.5, 0.1
    a_bar, b_bar, g_bar, period = 2.11, 3.73, 4.11, 100.0
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
    return y


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
    "dqc": dqc,
    "jc": jaynes_cummings,
}


def load_series(name: str, dtype=np.float32) -> np.ndarray:
    """Return the series min-max normalised to [-1, 1] as in the paper."""
    s = np.asarray(GENERATORS[name](), dtype=np.float64)
    lo, hi = s.min(), s.max()
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
