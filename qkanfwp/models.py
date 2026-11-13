"""Gated fast-weight programmers (re-implementation of arXiv:2605.06734) and
the extensions studied in this repository.

Paper mechanism (Sec. 3.2 / 4):

    y_t      = F(x_t; W_t)                      fast programmer
    dW_t, g_t = S(x_t)                          slow programmer
    W_{t+1}  = g_t W_t + (1 - g_t) dW_t         scalar-gated update (Eq. 3)

Because ``(dW_t, g_t)`` depend on the input only, the recursion has the closed
form of Eq. 4, ``W_T = beta_0 W_1 + sum_k beta_k dW_k`` with
``beta_k = (1 - g_k) prod_{s>k} g_s``, which is what ``gated_aggregate``
evaluates (in log space, without a Python loop over time).

Extensions (all optional, all keep ``(dW_t, g_t)`` independent of ``W_{t-1}``,
so Eq. 4, the convexity bound and the parallel-scan property still hold
per gate group):

* ``gate_groups``  - one gate per group of fast weights instead of one scalar
  (multi-timescale memory).
* ``gate_init='chrono'`` - gate biases initialised to log-spaced memory
  time-scales spanning the input window (Tallec & Ollivier, 2018).
* ``context``      - the token fed to both programmers is the causal patch
  ``(x_{t-p+1}, ..., x_t)`` instead of the scalar ``x_t`` (patch / delay
  embedding, stride ``stride``).
* ``skip``         - residual read-out ``y = anchor(x) + F(...)``.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass

import torch
import torch.nn.functional as F
from torch import nn

from .daruan import QKANLayer, fast_qkan_layer, theta_size


@dataclass
class FWPConfig:
    d_in: int = 1  # features per time step
    d_out: int = 1
    # slow programmer
    slow: str = "hqkan"  # 'hqkan' | 'mlp'
    slow_hidden: int = 6
    slow_latent: int = 3
    slow_reps: int = 1
    # fast programmer
    fast: str = "hqkan"  # 'hqkan' | 'linear'
    fast_in: int = 2
    fast_out: int = 2
    fast_reps: int = 1
    # memory rule
    gate: str = "scalar"  # 'none' (additive, Eq. 2) | 'scalar' (Eq. 3) | 'group'
    gate_groups: str = "edge"  # used when gate == 'group': 'node' | 'edge' | 'layer' | 'param'
    gate_init: str = "default"  # 'default' | 'chrono'
    max_len: int = 16  # longest memory time-scale for chrono init
    # tokenisation / read-out
    context: int = 1
    stride: int = 1
    skip: str = "none"  # 'none' | 'last' | 'mean'
    fast_measure: bool = True

    def to_dict(self):
        return asdict(self)


def gated_aggregate(
    proposals: torch.Tensor,
    gate_logits: torch.Tensor | None,
    w_init: torch.Tensor | None = None,
    group_index: torch.Tensor | None = None,
) -> torch.Tensor:
    """Closed form of the fast-weight recursion after consuming all proposals.

    Args:
        proposals: ``(B, T, P)`` proposals ``dW_1..dW_T``.
        gate_logits: ``(B, T, K)`` pre-sigmoid gates, or ``None`` for the
            ungated additive rule ``W + sum_k dW_k``.
        w_init: ``(P,)`` initial fast weights ``W_1`` (``None`` = zeros).
        group_index: ``(P,)`` long tensor mapping each fast weight to its gate
            (``None`` when ``K == 1``).

    Returns:
        ``(B, P)`` fast weights ``W_{T+1}``.
    """
    if gate_logits is None:
        out = proposals.sum(1)
        return out if w_init is None else out + w_init
    log_g = F.logsigmoid(gate_logits)
    log_w = F.logsigmoid(-gate_logits)  # log(1 - g)
    # suffix[k] = sum_{s > k} log g_s
    total = log_g.sum(1, keepdim=True)
    suffix = total - log_g.cumsum(1)
    beta = torch.exp(log_w + suffix)  # (B, T, K)
    if group_index is not None:
        beta = beta[..., group_index]  # (B, T, P)
    out = (beta * proposals).sum(1)
    if w_init is not None:
        beta0 = torch.exp(total.squeeze(1))
        if group_index is not None:
            beta0 = beta0[..., group_index]
        out = out + beta0 * w_init
    return out


def gated_recursion(proposals, gate_logits, w_init=None, group_index=None):
    """Step-by-step reference implementation of Eq. 3 (used in tests)."""
    b, t, p = proposals.shape
    w = proposals.new_zeros(b, p) if w_init is None else w_init.expand(b, p)
    for k in range(t):
        if gate_logits is None:
            w = w + proposals[:, k]
            continue
        g = torch.sigmoid(gate_logits[:, k])
        if group_index is not None:
            g = g[..., group_index]
        w = g * w + (1.0 - g) * proposals[:, k]
    return w


class SlowHQKAN(nn.Module):
    """HQKAN programmer: classical encoder -> QKAN -> classical decoder."""

    def __init__(self, d_in, hidden, latent, reps, d_out, fast_measure=True):
        super().__init__()
        self.enc = nn.Linear(d_in, hidden)
        self.qkan = QKANLayer(hidden, latent, reps, fast_measure=fast_measure)
        self.dec = nn.Linear(latent, d_out)

    def features(self, x):
        return self.qkan(self.enc(x))

    def forward(self, x):
        return self.dec(self.features(x))


class SlowMLP(nn.Module):
    """Classical slow programmer: encoder -> tanh -> linear heads."""

    def __init__(self, d_in, hidden, d_out):
        super().__init__()
        self.enc = nn.Linear(d_in, hidden)
        self.dec = nn.Linear(hidden, d_out)

    def features(self, x):
        return torch.tanh(self.enc(x))

    def forward(self, x):
        return self.dec(self.features(x))


class GatedFWP(nn.Module):
    """Fast-weight programmer with an HQKAN or classical slow/fast network."""

    def __init__(self, cfg: FWPConfig):
        super().__init__()
        self.cfg = cfg
        self.dedup_min_tokens = 4096
        d_tok = cfg.d_in * cfg.context

        # ---- fast programmer -------------------------------------------------
        if cfg.fast == "hqkan":
            self.fast_enc = nn.Linear(d_tok, cfg.fast_in)
            self.fast_dec = nn.Linear(cfg.fast_out, cfg.d_out)
            self.n_fast = theta_size(cfg.fast_in, cfg.fast_out, cfg.fast_reps)
            self.n_slow_out = self.n_fast
            shape = (cfg.fast_out, cfg.fast_in, cfg.fast_reps + 1, 2)
            idx = torch.arange(cfg.fast_out * cfg.fast_in).reshape(cfg.fast_out, cfg.fast_in)
            edge = idx[:, :, None, None].expand(shape)
            node = torch.arange(cfg.fast_out)[:, None, None, None].expand(shape)
            # one gate per (circuit, re-uploading layer)
            layer = (idx[:, :, None, None] * (cfg.fast_reps + 1) + torch.arange(cfg.fast_reps + 1)[:, None]).expand(shape)
        elif cfg.fast == "linear":
            # y = tok @ W + b, dW = L (x) D (rank one), db = B   (paper Sec. 4.2)
            self.fast_dec = nn.Linear(cfg.fast_out, cfg.d_out)
            self.n_fast = d_tok * cfg.fast_out + cfg.fast_out
            self.n_slow_out = d_tok + 2 * cfg.fast_out
            w_idx = torch.arange(d_tok * cfg.fast_out).reshape(d_tok, cfg.fast_out)
            edge = torch.cat([w_idx.reshape(-1), d_tok * cfg.fast_out + torch.arange(cfg.fast_out)])
            node = torch.cat(
                [torch.arange(cfg.fast_out).expand(d_tok, cfg.fast_out).reshape(-1), torch.arange(cfg.fast_out)]
            )
            layer = edge
        else:
            raise ValueError(cfg.fast)

        # ---- gate groups -----------------------------------------------------
        if cfg.gate == "none":
            self.n_gates = 0
            group_index = None
        elif cfg.gate == "scalar":
            self.n_gates = 1
            group_index = None
        elif cfg.gate == "group":
            if cfg.gate_groups == "param":
                group_index = torch.arange(self.n_fast)
            elif cfg.gate_groups == "edge":
                group_index = edge.reshape(-1)
            elif cfg.gate_groups == "node":
                group_index = node.reshape(-1)
            elif cfg.gate_groups == "layer":
                group_index = layer.reshape(-1)
            else:
                raise ValueError(cfg.gate_groups)
            group_index = torch.unique(group_index, return_inverse=True)[1]
            self.n_gates = int(group_index.max()) + 1
        else:
            raise ValueError(cfg.gate)
        self.register_buffer("group_index", group_index, persistent=False)

        # ---- slow programmer -------------------------------------------------
        d_slow_out = self.n_slow_out + self.n_gates
        if cfg.slow == "hqkan":
            self.slow = SlowHQKAN(
                d_tok, cfg.slow_hidden, cfg.slow_latent, cfg.slow_reps, d_slow_out, cfg.fast_measure
            )
        elif cfg.slow == "mlp":
            self.slow = SlowMLP(d_tok, cfg.slow_hidden, d_slow_out)
        else:
            raise ValueError(cfg.slow)

        if self.n_gates and cfg.gate_init == "chrono":
            # memory time-scale tau -> retention g = 1 - 1/tau -> bias logit(g)
            hi = max(float(cfg.max_len) / cfg.stride, 2.0)
            if self.n_gates == 1:
                tau = torch.tensor([math.sqrt(2.0 * hi)])
            else:
                tau = torch.exp(torch.linspace(math.log(2.0), math.log(hi), self.n_gates))
            with torch.no_grad():
                self.slow.dec.bias[self.n_slow_out :].copy_(torch.log(tau - 1.0).clamp_min(-6.0))

    # ------------------------------------------------------------------
    def tokens(self, x: torch.Tensor) -> torch.Tensor:
        """``(B, T, d_in)`` -> ``(B, T', d_in * context)`` causal patches."""
        cfg = self.cfg
        if cfg.context > 1:
            pad = x[:, :1].expand(-1, cfg.context - 1, -1)  # replicate-pad the past
            xp = torch.cat([pad, x], 1)
            x = xp.unfold(1, cfg.context, 1).reshape(x.shape[0], x.shape[1], -1)
        if cfg.stride > 1:
            # keep the most recent token, then every ``stride``-th one before it
            start = (x.shape[1] - 1) % cfg.stride
            x = x[:, start :: cfg.stride]
        return x

    def split_slow(self, out: torch.Tensor):
        """Slow-programmer output -> (proposal for all fast weights, gate logits)."""
        cfg = self.cfg
        raw, gate = out[..., : self.n_slow_out], out[..., self.n_slow_out :]
        if cfg.fast == "linear":
            d_tok = cfg.d_in * cfg.context
            lvec = raw[..., :d_tok]
            dvec = raw[..., d_tok : d_tok + cfg.fast_out]
            bvec = raw[..., d_tok + cfg.fast_out :]
            dw = (lvec.unsqueeze(-1) * dvec.unsqueeze(-2)).flatten(-2)
            raw = torch.cat([dw, bvec], -1)
        return raw, (gate if self.n_gates else None)

    def fast_weights(self, tok: torch.Tensor) -> torch.Tensor:
        """Fast weights seen by the last token: built from tokens ``1..T-1``."""
        if tok.shape[1] == 1:
            return tok.new_zeros(tok.shape[0], self.n_fast)
        if self.cfg.fast == "linear":
            proposals, gate = self.split_slow(self.slow(tok[:, :-1]))
            return gated_aggregate(proposals, gate, None, self.group_index)
        return self._fast_weights_latent(tok[:, :-1])

    def _slow_features(self, tok: torch.Tensor) -> torch.Tensor:
        """Slow-programmer features of every token.  The slow programmer is a
        pointwise function of the token, so identical tokens (overlapping
        sliding windows in a batch) are evaluated only once."""
        b, t, d = tok.shape
        if b * t < self.dedup_min_tokens:
            return self.slow.features(tok)
        uniq, inverse = torch.unique(tok.reshape(-1, d), dim=0, return_inverse=True)
        return self.slow.features(uniq)[inverse].reshape(b, t, -1)

    def _fast_weights_latent(self, tok: torch.Tensor) -> torch.Tensor:
        """Same result as ``gated_aggregate(dec(z))`` but aggregated before the
        linear decoder: ``sum_k beta_k (A z_k + c) = A (sum_k beta_k z_k) + c sum_k beta_k``.
        Costs O(B T K h) instead of O(B T P)."""
        z = self._slow_features(tok)  # (B, T, h)
        n = self.n_slow_out
        a, c = self.slow.dec.weight[:n], self.slow.dec.bias[:n]
        if self.n_gates == 0:
            return z.sum(1) @ a.T + c * z.shape[1]
        logits = z @ self.slow.dec.weight[n:].T + self.slow.dec.bias[n:]
        log_g = F.logsigmoid(logits)
        suffix = log_g.sum(1, keepdim=True) - log_g.cumsum(1)
        beta = torch.exp(F.logsigmoid(-logits) + suffix)  # (B, T, K)
        m = torch.einsum("btk,bth->bkh", beta, z)  # (B, K, h)
        mass = beta.sum(1)  # (B, K)
        if self.group_index is None:
            return m[:, 0] @ a.T + c * mass
        gi = self.group_index
        return torch.einsum("bph,ph->bp", m[:, gi], a) + c * mass[:, gi]

    def read(self, tok_last: torch.Tensor, w: torch.Tensor) -> torch.Tensor:
        cfg = self.cfg
        if cfg.fast == "hqkan":
            h = self.fast_enc(tok_last)
            h = fast_qkan_layer(h, w, cfg.fast_in, cfg.fast_out, cfg.fast_reps, cfg.fast_measure)
        else:
            d_tok = tok_last.shape[-1]
            wm = w[:, : d_tok * cfg.fast_out].reshape(-1, d_tok, cfg.fast_out)
            h = torch.einsum("bi,bio->bo", tok_last, wm) + w[:, d_tok * cfg.fast_out :]
        return self.fast_dec(h)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """``x``: ``(B, T, d_in)`` -> prediction ``(B, d_out)`` at the last step."""
        cfg = self.cfg
        tok = self.tokens(x)
        y = self.read(tok[:, -1], self.fast_weights(tok))
        if cfg.skip == "last":
            y = y + x[:, -1, : min(cfg.d_in, cfg.d_out)].mean(-1, keepdim=True)
        elif cfg.skip == "mean":
            y = y + x[:, -cfg.context :].mean((1, 2))[:, None]
        return y

    @torch.no_grad()
    def memory_kernel(self, x: torch.Tensor) -> torch.Tensor:
        """Return ``beta_{k}`` of Eq. 5 for each gate group: ``(B, T-1, K)``."""
        tok = self.tokens(x)
        _, gate = self.split_slow(self.slow(tok[:, :-1]))
        log_g = F.logsigmoid(gate)
        suffix = log_g.sum(1, keepdim=True) - log_g.cumsum(1)
        return torch.exp(F.logsigmoid(-gate) + suffix)


class ARHQKAN(nn.Module):
    """Control without fast weights: HQKAN on the last ``context`` values."""

    def __init__(self, context: int, hidden: int, latent: int, reps: int, d_out: int = 1, skip: str = "none"):
        super().__init__()
        self.context, self.skip = context, skip
        self.net = SlowHQKAN(context, hidden, latent, reps, d_out)

    def forward(self, x):
        y = self.net(x[:, -self.context :, 0])
        if self.skip == "last":
            y = y + x[:, -1, :1]
        return y


class LSTMBaseline(nn.Module):
    """Classical reference: single-layer LSTM + linear read-out."""

    def __init__(self, hidden: int, d_in: int = 1, d_out: int = 1):
        super().__init__()
        self.lstm = nn.LSTM(d_in, hidden, batch_first=True)
        self.head = nn.Linear(hidden, d_out)

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.head(out[:, -1])


def count_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)
