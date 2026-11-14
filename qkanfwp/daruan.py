"""Functional DARUAN / QKAN layer.

DARUAN (DatA Re-Uploading ActivatioN) is the single-qubit data re-uploading
circuit used as the learnable edge activation in QKAN (Jiang et al.,
arXiv:2509.14026).  The official implementation (``pip install qkan``) stores
the circuit angles as ``nn.Parameter`` shared over the batch.  A fast-weight
programmer needs the angles to be *per-sample tensors* produced by another
network, so this module re-implements the default ``pz_encoding`` ansatz as a
pure function of ``(x, theta)``.  ``tests/test_daruan.py`` checks numerical
equivalence with the official solver.

Circuit (``pz_encoding``), per edge (o, i)::

    |0> - H - [ RZ(th[l,0]) - RY(th[l,1]) - RZ(w[l] * x_i + b[l]) ] * reps
             - RZ(th[reps,0]) - RY(th[reps,1]) - <Z>

Layer output: ``y_o = sum_i phi_{o,i}(x_i)`` (the ``QKAN`` class defaults:
post-activation weights fixed to 1 and no base activation).
"""

from __future__ import annotations

import math

import torch
from torch import nn

INV_SQRT2 = 1.0 / math.sqrt(2.0)

# Finite-shot simulation (experiments/shot_noise.py).  ``None`` = exact
# expectation values.  Otherwise ``_SHOTS`` is the shot budget of ONE circuit
# for ONE input (one edge, one token).  Non-commuting Pauli observables cannot
# be read from the same shot, so a read-out that needs ``m`` measurement
# settings (m = 1 for <Z>; m = 3 for the Bloch vector <X>, <Y>, <Z>; more with
# parameter-shifted copies of the circuit) gets ``floor(_SHOTS / m)`` shots per
# setting.  Every expectation ``v`` is then estimated from that many +-1
# outcomes drawn from the exact binomial distribution.  Only physical
# read-outs are affected; qkan's ``fast_measure`` quantity |a| - |b| is not an
# expectation value.
_SHOTS: float | None = None


def set_shots(shots: float | None) -> None:
    """Shot budget per circuit and input (``None`` = exact expectations)."""
    global _SHOTS
    _SHOTS = shots


def get_shots() -> float | None:
    return _SHOTS


def shots_per_setting(settings: int) -> int | None:
    """Shots available to each of ``settings`` measurement settings of one circuit."""
    if _SHOTS is None:
        return None
    return max(int(_SHOTS // settings), 1)


# Static device errors (experiments/device_noise.py), applied to every circuit
# of every model.  ``_DEVICE = (contraction, offset, over_rotation)``:
#   * every measured Pauli expectation v becomes ``contraction * v + offset``.
#     Depolarising noise of strength p gives contraction 1 - p; read-out errors
#     P(read 1 | 0) = e01 and P(read 0 | 1) = e10 give contraction
#     1 - e01 - e10 and offset e10 - e01;
#   * every rotation angle (trainable and data-encoding) is executed as
#     ``(1 + over_rotation) * angle`` (a calibration error of the pulse area).
_DEVICE: tuple[float, float, float] = (1.0, 0.0, 0.0)


def set_device(depolarizing: float = 0.0, e01: float = 0.0, e10: float = 0.0, over_rotation: float = 0.0) -> None:
    """Static device errors; the defaults restore the ideal device."""
    global _DEVICE
    _DEVICE = ((1.0 - depolarizing) * (1.0 - e01 - e10), e10 - e01, over_rotation)


def get_device() -> tuple[float, float, float]:
    return _DEVICE


def _measure(v: torch.Tensor, settings: int = 1) -> torch.Tensor:
    """Measured value of the Pauli expectations ``v`` (each from its own
    measurement setting): static device errors first, then the finite-shot
    estimate.  The sampling error is treated as a constant in the backward
    pass, so training with shots is possible."""
    contraction, offset, _ = _DEVICE
    if contraction != 1.0 or offset != 0.0:
        v = contraction * v + offset
    n = shots_per_setting(settings)
    if n is None:
        return v
    p = ((1.0 + v.detach()) * 0.5).clamp(0.0, 1.0)
    k = torch.binomial(torch.full_like(p, float(n)), p)  # number of +1 outcomes
    return v + (2.0 * k / n - 1.0 - v.detach())


def _pz_amplitudes(x, theta, preact_w=None, preact_b=None):
    """Final amplitudes ``(a, b)`` of every ``pz_encoding`` circuit, each of
    shape ``(*batch, out, in)`` (complex)."""
    reps = theta.shape[-2] - 1
    xe = x.unsqueeze(-2)  # (*batch, 1, in)
    over = 1.0 + _DEVICE[2]
    if over != 1.0:
        theta = theta * over

    # State after the Hadamard, kept as two complex amplitudes.
    half = 0.5 * theta
    cos_y = torch.cos(half[..., 1])
    sin_y = torch.sin(half[..., 1])
    # RZ(t) = diag(e^{-it/2}, e^{+it/2})
    ph = torch.polar(torch.ones_like(half[..., 0]), -half[..., 0])

    a = None
    b = None
    for layer in range(reps + 1):
        p = ph[..., layer]
        c = cos_y[..., layer]
        s = sin_y[..., layer]
        if a is None:
            # RZ then RY applied to (1, 1)/sqrt(2)
            a0 = p * INV_SQRT2
            b0 = torch.conj(p) * INV_SQRT2
        else:
            a0 = a * p
            b0 = b * torch.conj(p)
        a = c * a0 - s * b0
        b = s * a0 + c * b0
        if layer < reps:
            if preact_w is None:
                enc = xe
            else:
                enc = preact_w[..., layer] * xe + preact_b[..., layer]
            d = torch.polar(torch.ones_like(enc), -0.5 * over * enc)
            a = a * d
            b = b * torch.conj(d)
    return a, b


def daruan_pz(
    x: torch.Tensor,
    theta: torch.Tensor,
    preact_w: torch.Tensor | None = None,
    preact_b: torch.Tensor | None = None,
    fast_measure: bool = True,
) -> torch.Tensor:
    """Evaluate all edge activations of one QKAN layer.

    Args:
        x: ``(*batch, in_dim)`` real inputs.
        theta: ``(out, in, reps + 1, 2)`` shared angles, or
            ``(*batch, out, in, reps + 1, 2)`` per-sample ("fast") angles.
        preact_w, preact_b: optional ``(out, in, reps)`` trainable frequency /
            phase of the data-encoding gate.  ``None`` means ``RZ(x)``.
        fast_measure: ``True`` -> ``|a| - |b|`` (qkan default, "quantum
            inspired"); ``False`` -> ``|a|^2 - |b|^2`` (physical <Z>).

    Returns:
        ``(*batch, out, in)`` activations.
    """
    a, b = _pz_amplitudes(x, theta, preact_w, preact_b)
    if fast_measure:
        return a.abs() - b.abs()
    return _measure(a.real**2 + a.imag**2 - b.real**2 - b.imag**2)


def daruan_bloch(
    x: torch.Tensor,
    theta: torch.Tensor,
    preact_w: torch.Tensor | None = None,
    preact_b: torch.Tensor | None = None,
    circuit_copies: int = 1,
) -> torch.Tensor:
    """Bloch vector ``(<X>, <Y>, <Z>)`` of the output state of every DARUAN
    circuit: ``(*batch, out, in, 3)``.

    The expectation of any single-qubit observable ``O = r0 I + r . sigma`` on
    the same circuit is ``r0 + r . bloch``, i.e. *linear* in the observable.
    ``bloch[..., 2]`` equals ``daruan_pz(..., fast_measure=False)``.

    With finite shots the budget of the circuit is split over the three bases;
    ``circuit_copies`` > 1 says that the same budget is also shared with that
    many evaluations of the circuit (e.g. parameter-shifted copies).
    """
    a, b = _pz_amplitudes(x, theta, preact_w, preact_b)
    ab = torch.conj(a) * b
    z = a.real**2 + a.imag**2 - b.real**2 - b.imag**2
    return _measure(torch.stack([2.0 * ab.real, 2.0 * ab.imag, z], -1), settings=3 * circuit_copies)


def theta_size(in_dim: int, out_dim: int, reps: int) -> int:
    return out_dim * in_dim * (reps + 1) * 2


class QKANLayer(nn.Module):
    """Static QKAN layer: ``y_o = sum_i DARUAN_{o,i}(x_i)``."""

    def __init__(
        self,
        in_dim: int,
        out_dim: int,
        reps: int = 3,
        preact_trainable: bool = False,
        fast_measure: bool = True,
    ):
        super().__init__()
        self.in_dim, self.out_dim, self.reps = in_dim, out_dim, reps
        self.fast_measure = fast_measure
        self.theta = nn.Parameter(torch.empty(out_dim, in_dim, reps + 1, 2))
        nn.init.xavier_normal_(self.theta)  # same default as the qkan package
        if preact_trainable:
            self.preact_w = nn.Parameter(torch.ones(out_dim, in_dim, reps))
            self.preact_b = nn.Parameter(torch.zeros(out_dim, in_dim, reps))
        else:
            self.preact_w = None
            self.preact_b = None

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        act = daruan_pz(x, self.theta, self.preact_w, self.preact_b, self.fast_measure)
        return act.sum(-1)


def fast_qkan_layer(
    x: torch.Tensor,
    theta_flat: torch.Tensor,
    in_dim: int,
    out_dim: int,
    reps: int,
    fast_measure: bool = True,
) -> torch.Tensor:
    """QKAN layer whose angles are per-sample fast weights.

    Args:
        x: ``(*batch, in_dim)``.
        theta_flat: ``(*batch, out_dim * in_dim * (reps + 1) * 2)``.
    """
    theta = theta_flat.reshape(*theta_flat.shape[:-1], out_dim, in_dim, reps + 1, 2)
    return daruan_pz(x, theta, fast_measure=fast_measure).sum(-1)
