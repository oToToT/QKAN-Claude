"""GQKAN-QKANFWP as it is built in the authors' released code.

Port of ``times_series_benchmark/src/models/gqkan_qkanfwp.py`` of
https://github.com/MatthewPeng57/Gated-QKAN-FWP (commit 2cf0457) onto the
functional DARUAN layer of this repository.  With ``hidden_size = 8`` (the
setting of the paper's time-series benchmark) the model has the 159 trainable
parameters that the paper reports.

Structure (s = ceil(log2(hidden_size)) = 3, latent = s + 2 = 5)::

    slow programmer   Linear(1, s) -> QKAN[s, s] (reps 1, SiLU base term with
                      trainable weights) -> Linear(s, latent)
    proposal          theta_t = A_t (x) B_t, a rank-one outer product of two
                      linear heads: A_t in R^{s x (reps+1)}, B_t in R^{s x 2}
    gate              g_t = sigmoid(Linear(latent, 1)), bias initialised to 2
    recursion         theta_t = (1 - g_t) theta_new_t + g_t theta_{t-1}, theta_0 = 0
    fast programmer   Linear(1, s) -> QKAN[s, s] with the angles theta_T
                      (no base term) -> Linear(s, 1), applied to x_T

Three points differ from the equations of the paper: the fast angles are a
rank-one product rather than the output of one linear decoder; the fast
programmer reads x_T with angles that already contain the write of x_T
(write-then-read); and the gate bias starts at 2 (g = 0.88).

The authors' training loop uses only the output of the last step, so the
recursion is evaluated in closed form here.
"""

from __future__ import annotations

import math

import torch
import torch.nn.functional as F
from torch import nn

from .daruan import QKANLayer, daruan_pz


class AuthorsFWP(nn.Module):
    def __init__(self, hidden_size: int = 8, input_size: int = 1, output_size: int = 1, reps: int = 1):
        super().__init__()
        s = int(math.ceil(math.log2(hidden_size)))
        latent = s + 2
        self.s, self.reps = s, reps
        self.enc_in = nn.Linear(input_size, s)
        self.slow = QKANLayer(s, s, reps)  # |a| - |b| read-out, RZ(x) encoding (qkan defaults)
        self.slow_base = nn.Parameter(0.5 * torch.ones(s, s))  # qkan: ba_trainable=True, SiLU
        self.enc_out = nn.Linear(s, latent)
        self.head_a = nn.Linear(latent, s * (reps + 1))
        self.head_b = nn.Linear(latent, s * 2)
        self.prelinear = nn.Linear(input_size, s)
        self.post = nn.Linear(s, output_size)
        self.gate = nn.Linear(latent, output_size)
        self.gate.bias.data.fill_(2.0)

    def fit_token_scale(self, x_train: torch.Tensor) -> None:
        """The model reads the raw scalar inputs; nothing to fit."""

    def slow_programmer(self, x: torch.Tensor):
        """Proposals ``A_t (B, T, s, reps+1)``, ``B_t (B, T, s, 2)`` and gates ``g_t (B, T)``."""
        b, t, _ = x.shape
        h = self.enc_in(x)
        z = daruan_pz(h, self.slow.theta).sum(-1) + F.silu(h) @ self.slow_base.T
        res = self.enc_out(z)
        a = self.head_a(res).view(b, t, self.s, self.reps + 1)
        bb = self.head_b(res).view(b, t, self.s, 2)
        return a, bb, torch.sigmoid(self.gate(res))[..., 0]

    def fast_angles(self, x: torch.Tensor) -> torch.Tensor:
        """``theta_T`` of shape ``(B, s, s, reps+1, 2)`` after all T writes."""
        a, bb, g = self.slow_programmer(x)
        logg = torch.log(g + 1e-12)
        after = torch.flip(torch.cumsum(torch.flip(logg, [1]), 1), [1]) - logg  # log prod_{s>t} g_s
        w = (1.0 - g) * torch.exp(after)
        return torch.einsum("bt,btld,btqe->blqde", w, a, bb)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x.to(torch.float32)
        theta = self.fast_angles(x)
        out = daruan_pz(self.prelinear(x[:, -1]), theta).sum(-1)
        return self.post(out)


class AuthorsSolarFWP(nn.Module):
    """GQKAN-QKANFWP of the authors' solar-cycle code
    (``Solar_cycle_forecasting/src/models/gqkan_qkanfwp.py`` with the flags of
    its ``run.sh``): 12,474 trainable parameters, the number in the paper.

    ::

        slow programmer   Linear(1, 25) -> QKAN[25, 25] (reps 1, trainable
                          encoding weights and SiLU base term) -> Linear(25, 48)
        proposal / gate   rank-one theta_t = A_t (x) B_t, scalar gate (bias 2)
        fast programmer   Linear(1, 10) -> QKAN[10, 20] (reps 2) with theta_L
        read-out          BatchNorm1d(20) -> Dropout(0.3) -> Linear(20, 132)

    As in the time-series model the fast programmer reads the last input with
    angles that already contain its own write.
    """

    def __init__(self, horizon: int = 132, s1: int = 25, s2: int = 25, hidden: int = 48, fast_in: int = 10,
                 fast_out: int = 20, fast_reps: int = 2, dropout: float = 0.3):
        super().__init__()
        self.fast_in, self.fast_out, self.fast_reps = fast_in, fast_out, fast_reps
        self.enc_in = nn.Linear(1, s1)
        self.slow = QKANLayer(s1, s2, reps=1, preact_trainable=True)
        self.slow_base = nn.Parameter(0.5 * torch.ones(s2, s1))
        self.enc_out = nn.Linear(s2, hidden)
        self.head_a = nn.Linear(hidden, fast_out * (fast_reps + 1))
        self.head_b = nn.Linear(hidden, fast_in * 2)
        self.prelinear = nn.Linear(1, fast_in)
        self.gate = nn.Linear(hidden, 1)
        self.gate.bias.data.fill_(2.0)
        self.bn = nn.BatchNorm1d(fast_out)
        self.drop = nn.Dropout(dropout)
        self.out = nn.Linear(fast_out, horizon)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x.to(torch.float32)
        b, t, _ = x.shape
        # The slow programmer sees one scalar per step, so it is evaluated once
        # per distinct value of the batch and gathered (same result, far fewer
        # circuit evaluations: overlapping windows share almost all values).
        values, inverse = torch.unique(x.reshape(-1), return_inverse=True)
        h = self.enc_in(values[:, None])
        z = daruan_pz(h, self.slow.theta, self.slow.preact_w, self.slow.preact_b).sum(-1) + F.silu(h) @ self.slow_base.T
        res = self.enc_out(z)
        a = self.head_a(res)[inverse].view(b, t, self.fast_out, self.fast_reps + 1)
        bb = self.head_b(res)[inverse].view(b, t, self.fast_in, 2)
        g = torch.sigmoid(self.gate(res))[inverse, 0].view(b, t)
        logg = torch.log(g + 1e-12)
        after = torch.flip(torch.cumsum(torch.flip(logg, [1]), 1), [1]) - logg
        theta = torch.einsum("bt,btld,btqe->blqde", (1.0 - g) * torch.exp(after), a, bb)
        hid = daruan_pz(self.prelinear(x[:, -1]), theta).sum(-1)
        return self.out(self.drop(self.bn(hid)))
