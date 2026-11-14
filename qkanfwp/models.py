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
  embedding, stride ``stride``); with ``context_mode='diff'`` the patch is
  expressed as ``(x_t, Dx_t, D^2x_t, ...)`` with unit-variance differences.
* ``skip``         - residual read-out ``y = anchor(x) + F(...)``; the anchor is
  the last value (one-step tasks) or the smoothed last cycle (``'cycle'``,
  multi-step seasonal forecasts).
* ``out_basis``    - multi-step read-out through a fixed smooth cosine basis.
* ``write_first``  - apply the update of the current step before reading, so
  the newest token also reaches the slow programmer.
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
    # 'none' (additive, Eq. 2) | 'scalar' (Eq. 3) | 'group' | 'cmg' (complementary
    # matrix gate of arXiv:2607.27945: one gate per fast weight, logits = rank-one
    # outer product of two slow-programmer heads)
    gate: str = "scalar"
    gate_groups: str = "edge"  # used when gate == 'group': 'node' | 'edge' | 'layer' | 'param'
    gate_init: str = "default"  # 'default' | 'chrono'
    max_len: int = 16  # longest memory time-scale for chrono init
    # tokenisation / read-out
    context: int = 1
    context_mode: str = "lags"  # 'lags' (raw patch) | 'diff' (value + backward differences)
    token_dtype: str = "float32"  # 'float64': form the differences in double precision
    stride: int = 1
    skip: str = "none"  # 'none' | 'last' | 'mean' | 'cycle'
    skip_smooth: int = 13  # moving-average width of the 'cycle' anchor
    out_basis: int = 0  # > 0: decode the output as that many smooth cosine modes
    # False: y_T = F(x_T; W_T), the paper's read-before-write order.
    # True : y_T = F(x_T; W_{T+1}); the newest token also programs the fast weights
    #        (the order used by linear-transformer fast weight programmers).
    write_first: bool = False
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


class Tokenizer(nn.Module):
    """``(B, T, d_in)`` series -> ``(B, T', d_in * context)`` causal tokens.

    ``mode='lags'``: token_t = (x_{t-p+1}, ..., x_t)  (stride-1 patch).
    ``mode='diff'``: token_t = (x_t, Dx_t, D^2x_t, ...) / scale, i.e. the same
    patch in backward-difference (discrete phase-space) coordinates, with
    every difference order rescaled to unit variance on the training set.
    ``stride > 1`` keeps the most recent token and every ``stride``-th before it.
    """

    def __init__(self, d_in: int = 1, context: int = 1, mode: str = "lags", stride: int = 1,
                 dtype: str = "float32", keep_dtype: bool = False, pad: str = "replicate"):
        super().__init__()
        self.d_in, self.context, self.mode, self.stride = d_in, context, mode, stride
        self.keep_dtype = keep_dtype  # return tokens in the working precision instead of float32
        # 'replicate': the patch of an early step is filled with the first value.
        # 'truncate' : (diff mode) differences that would reach before the window
        #              are set to zero, i.e. token_t holds orders 0..t only.
        self.pad = pad
        # High-order differences of a smooth series cancel many leading digits
        # (in float32 the 6th difference of the Bessel series is ~90 % rounding
        # noise), so they can be formed in float64 when the input is float64.
        self.work_dtype = torch.float64 if dtype == "float64" else torch.float32
        self.d_tok = d_in * context
        if mode == "diff":
            assert d_in == 1, "difference tokens are implemented for scalar series"
            # row k = k-th backward-difference stencil over (x_{t-p+1}, ..., x_t)
            mat = torch.zeros(context, context)
            for k in range(context):
                for j in range(k + 1):
                    mat[k, context - 1 - j] = (-1) ** j * math.comb(k, j)
            self.register_buffer("diff_matrix", mat)
            self.register_buffer("scale", torch.ones(context))
        elif mode != "lags":
            raise ValueError(mode)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x.to(self.work_dtype)
        if self.context > 1:
            pad = x[:, :1].expand(-1, self.context - 1, -1)  # replicate-pad the past
            xp = torch.cat([pad, x], 1)
            x = xp.unfold(1, self.context, 1).reshape(x.shape[0], x.shape[1], -1)
            if self.mode == "diff":
                x = (x @ self.diff_matrix.T.to(x.dtype)) / self.scale.to(x.dtype)
                if self.pad == "truncate":
                    x = x * self._known(x.shape[1], x.device).to(x.dtype)
        if self.stride > 1:
            start = (x.shape[1] - 1) % self.stride
            x = x[:, start :: self.stride]
        return x if self.keep_dtype else x.float()

    def _known(self, length: int, device) -> torch.Tensor:
        """(T, context) mask: difference order k of token t is known iff k <= t."""
        t = torch.arange(length, device=device)[:, None]
        return torch.arange(self.context, device=device)[None, :] <= t

    @torch.no_grad()
    def fit_scale(self, x_train: torch.Tensor) -> None:
        """Rescale each difference order to unit training-set std (the value
        coordinate itself is left untouched)."""
        if self.mode != "diff" or self.context == 1:
            return
        self.scale.fill_(1.0)
        tok = self(x_train)
        if self.pad == "truncate" and self.stride == 1:
            # statistics over the known entries only
            known = self._known(tok.shape[1], tok.device).to(tok.dtype)
            n = (known.sum(0) * tok.shape[0]).clamp_min(1.0)
            mean = (tok * known).sum((0, 1)) / n
            var = (((tok - mean) ** 2) * known).sum((0, 1)) / (n - 1).clamp_min(1.0)
            std = var.sqrt().clamp_min(1e-8)
        else:
            std = tok.reshape(-1, self.context).std(0).clamp_min(1e-8)
        std[0] = 1.0
        self.scale.copy_(std)


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
        self.tokenizer = Tokenizer(cfg.d_in, cfg.context, cfg.context_mode, cfg.stride, cfg.token_dtype)
        d_tok = self.tokenizer.d_tok

        # ---- fast programmer -------------------------------------------------
        # Optional smooth read-out for multi-step forecasts: the decoder emits
        # ``out_basis`` coefficients of a fixed DCT-II basis over the horizon
        # instead of one free value per step (fewer parameters, no step-to-step
        # jitter in the forecast).
        dec_out = cfg.d_out
        if cfg.out_basis:
            n = torch.arange(cfg.d_out, dtype=torch.float32) + 0.5
            k = torch.arange(cfg.out_basis, dtype=torch.float32)
            basis = torch.cos(math.pi * n[:, None] * k[None, :] / cfg.d_out)
            basis[:, 1:] *= math.sqrt(2.0)  # unit RMS per mode
            self.register_buffer("basis", basis / math.sqrt(cfg.out_basis))
            dec_out = cfg.out_basis
        if cfg.fast == "hqkan":
            self.fast_enc = nn.Linear(d_tok, cfg.fast_in)
            self.fast_dec = nn.Linear(cfg.fast_out, dec_out)
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
            self.fast_dec = nn.Linear(cfg.fast_out, dec_out)
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

        if cfg.skip == "cycle":
            # Seasonal residual read-out: the forecast starts as the (smoothed)
            # last ``d_out`` inputs, so the decoder starts at zero and the
            # programmers only have to learn the correction to "repeat the
            # previous cycle".
            assert cfg.d_in == 1, "the cycle anchor is implemented for scalar series"
            nn.init.zeros_(self.fast_dec.weight)
            nn.init.zeros_(self.fast_dec.bias)

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
        elif cfg.gate == "cmg":
            # Fast state reshaped to P x Q = (circuits) x (angles per circuit);
            # the slow programmer emits m^P (P values) and m^Q (Q values) and
            # the gate of weight (p, q) is sigmoid(m^P_p m^Q_q).
            assert cfg.fast == "hqkan", "CMG is implemented for the HQKAN fast programmer"
            self.cmg_shape = (cfg.fast_out * cfg.fast_in, (cfg.fast_reps + 1) * 2)
            self.n_gates = sum(self.cmg_shape)
            group_index = None
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

        if self.n_gates and cfg.gate_init == "chrono" and cfg.gate != "cmg":
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
        return self.tokenizer(x)

    def fit_token_scale(self, x_train: torch.Tensor) -> None:
        self.tokenizer.fit_scale(x_train)

    def split_slow(self, out: torch.Tensor):
        """Slow-programmer output -> (proposal for all fast weights, gate logits)."""
        cfg = self.cfg
        raw, gate = out[..., : self.n_slow_out], out[..., self.n_slow_out :]
        if cfg.gate == "cmg":
            p = self.cmg_shape[0]
            gate = (gate[..., :p, None] * gate[..., None, p:]).flatten(-2)  # one logit per fast weight
        if cfg.fast == "linear":
            d_tok = cfg.d_in * cfg.context
            lvec = raw[..., :d_tok]
            dvec = raw[..., d_tok : d_tok + cfg.fast_out]
            bvec = raw[..., d_tok + cfg.fast_out :]
            dw = (lvec.unsqueeze(-1) * dvec.unsqueeze(-2)).flatten(-2)
            raw = torch.cat([dw, bvec], -1)
        return raw, (gate if self.n_gates else None)

    def fast_weights(self, tok: torch.Tensor) -> torch.Tensor:
        """Fast weights seen by the last token: built from tokens ``1..T-1``
        (paper), or from ``1..T`` when ``write_first`` is set."""
        hist = tok if self.cfg.write_first else tok[:, :-1]
        if hist.shape[1] == 0:
            return tok.new_zeros(tok.shape[0], self.n_fast)
        if self.cfg.fast == "linear":
            proposals, gate = self.split_slow(self.slow(hist))
            return gated_aggregate(proposals, gate, None, self.group_index)
        return self._fast_weights_latent(hist)

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
        if self.cfg.gate == "cmg":  # per-weight gates: no latent-space shortcut
            proposals, gate = self.split_slow(self.slow.dec(z))
            return gated_aggregate(proposals, gate)
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
        y = self.fast_dec(h)
        return y @ self.basis.T if cfg.out_basis else y

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """``x``: ``(B, T, d_in)`` -> prediction ``(B, d_out)`` at the last step."""
        cfg = self.cfg
        tok = self.tokens(x)
        y = self.read(tok[:, -1], self.fast_weights(tok))
        if cfg.skip == "last":
            # parameter-free skip: add the last observed value (for a scalar
            # series the mean over the feature axis is a no-op)
            y = y + x[:, -1, : min(cfg.d_in, cfg.d_out)].float().mean(-1, keepdim=True)
        elif cfg.skip == "mean":
            y = y + x[:, -cfg.context :].float().mean((1, 2))[:, None]
        elif cfg.skip == "cycle":
            y = y + self.cycle_anchor(x)
        return y

    def cycle_anchor(self, x: torch.Tensor) -> torch.Tensor:
        """The last ``d_out`` inputs after a centred moving average (windows are
        truncated at the ends of the input, so only observed values are used)."""
        cfg = self.cfg
        s = x[..., 0].float()
        if cfg.skip_smooth > 1:
            k = cfg.skip_smooth
            s = F.avg_pool1d(s[:, None], k, stride=1, padding=k // 2, count_include_pad=False)[:, 0]
        return s[:, -cfg.d_out :]

    @torch.no_grad()
    def memory_kernel(self, x: torch.Tensor) -> torch.Tensor:
        """Return ``beta_{k}`` of Eq. 5 for each gate group: ``(B, T-1, K)``."""
        tok = self.tokens(x)
        hist = tok if self.cfg.write_first else tok[:, :-1]
        _, gate = self.split_slow(self.slow(hist))
        log_g = F.logsigmoid(gate)
        suffix = log_g.sum(1, keepdim=True) - log_g.cumsum(1)
        return torch.exp(F.logsigmoid(-gate) + suffix)


class ARHQKAN(nn.Module):
    """Control without any fast-weight memory: a static HQKAN applied to the
    last token only (same tokenisation and residual read-out as ``GatedFWP``)."""

    def __init__(self, context: int, hidden: int, latent: int, reps: int, d_out: int = 1,
                 skip: str = "none", context_mode: str = "lags", token_dtype: str = "float32",
                 fast_measure: bool = True):
        super().__init__()
        self.skip = skip
        self.tokenizer = Tokenizer(1, context, context_mode, dtype=token_dtype)
        self.net = SlowHQKAN(context, hidden, latent, reps, d_out, fast_measure)

    def fit_token_scale(self, x_train):
        self.tokenizer.fit_scale(x_train)

    def forward(self, x):
        # only the last ``context`` values matter
        y = self.net(self.tokenizer(x[:, -self.tokenizer.context :])[:, -1])
        if self.skip == "last":
            y = y + x[:, -1, :1].float()
        return y


class LSTMBaseline(nn.Module):
    """Classical reference: single-layer LSTM + linear read-out.  ``context`` /
    ``context_mode`` / ``skip`` give it the same tokens and residual read-out
    as the extended FWP."""

    def __init__(self, hidden: int, d_in: int = 1, d_out: int = 1, context: int = 1,
                 context_mode: str = "lags", skip: str = "none", token_dtype: str = "float32"):
        super().__init__()
        self.skip = skip
        self.tokenizer = Tokenizer(d_in, context, context_mode, dtype=token_dtype)
        self.lstm = nn.LSTM(self.tokenizer.d_tok, hidden, batch_first=True)
        self.head = nn.Linear(hidden, d_out)

    def fit_token_scale(self, x_train):
        self.tokenizer.fit_scale(x_train)

    def forward(self, x):
        out, _ = self.lstm(self.tokenizer(x))
        y = self.head(out[:, -1])
        if self.skip == "last":
            y = y + x[:, -1, :1].float()
        return y


def count_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)
