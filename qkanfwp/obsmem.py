"""Observable-memory QKAN fast-weight programmer ("QKAN-FWP-O").

Motivation
----------
In the gated QKAN-FWP family (scalar gate arXiv:2605.06734, self-modulation
arXiv:2606.24933 / 2607.02363, CMG arXiv:2607.27945) the fast weights are the
*rotation angles* of the fast programmer's DARUAN circuits and every write is
open loop: the proposal and the gate are functions of the current token only,
so the memory ``W_T = sum_k beta_k dW(x_k)`` is a weighted average of per-token
guesses.  Nothing ever compares what the fast programmer predicted with what
was observed next.

Here the fast weights are instead the *measurement observables* of the same
circuits.  A DARUAN activation with observable ``O = r0 I + r . sigma`` is

    phi(u) = <0| U(u)^dag O U(u) |0> = r0 + r . n(u),

where ``n(u)`` is the Bloch vector of the circuit output - the activation, and
therefore the whole QKAN layer, is *linear* in the observables.  Each context
step supplies a supervised pair for free (token ``t`` -> next value), so the
best observable given the context is a least-squares problem, and its
sufficient statistics obey exactly the scalar-gated recursion of the paper:

    C_t = g_t C_{t-1} + (1 - g_t) (Lambda_0 + k_t k_t^T)        k_t: features of token t
    b_t = g_t b_{t-1} + (1 - g_t) (Lambda_0 R_0 + k_t y_t)      y_t: what followed token t
    C_0 = Lambda_0,  b_0 = Lambda_0 R_0                         learned prior
    R_T = C_T^{-1} b_T,       y_hat = k_T . R_T                 fast observable, read-out

Every proposal carries the prior, so with ``beta_t = (1 - g_t) prod_{s>t} g_s``
(paper Eq. 5) the closed form is

    C_T = Lambda_0 + sum_t beta_t k_t k_t^T,   b_T = Lambda_0 R_0 + sum_t beta_t k_t y_t

and ``C_T >= Lambda_0`` whatever the gates do: the read-out solve is always
well posed.  (Without the prior in the proposal a single closed gate, g = 0,
erases the prior together with the old evidence and the solve becomes rank
deficient - this happened on the NARMA start-up transient.)

So the closed form (paper Eq. 4), the convex-hull bound and the associative
prefix scan all still hold - for the statistics ``(C, b)`` - while the write
is closed loop: ``R_T = R_0 + C_T^{-1} sum_t beta_t k_t (y_t - k_t . R_0)`` is
driven by the prediction errors of the prior observable.  With the gates shut
(all ``beta_t = 0``) the model is a static QKAN with trainable observable ``R_0``.

On hardware the circuits never depend on the memory: every token is run
through the same fixed circuits and measured in the X, Y and Z bases; the
fast weights only enter the classical post-processing of those expectations.

Classical relatives: ALPaCA (Harrison et al., 2018; meta-learned Bayesian last
layer), R2D2 (Bertinetto et al., 2019), the mesa-layer (von Oswald et al.,
2023) and the delta rule of linear-transformer FWPs (Schlag et al., 2021).
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, replace

import torch
import torch.nn.functional as F
from torch import nn

from . import daruan
from .daruan import daruan_bloch
from .models import Tokenizer


@dataclass
class ObsMemConfig:
    # token = last ``context`` values ...; 0 = automatic: min(8, max_len // 2), so
    # that at least half of the window yields complete in-context pairs
    context: int = 4
    context_mode: str = "diff"  # ... as (x, Dx, D^2 x, ...) or raw lags
    hidden: int = 4  # number of single-qubit feature circuits (HQKAN: Linear -> QKAN(hidden -> 1))
    reps: int = 2  # data re-uploading repetitions
    # QKAN base-activation term of every edge (qkan's ``base_activation``):
    # phi(u) = a * base(u) + r . n(u).  'none' | 'identity' | 'silu'
    base: str = "identity"
    quantum: bool = True  # False: drop the Bloch features (classical control, needs base != 'none')
    # Classical replacement of the Bloch features when ``quantum`` is False, read
    # by exactly the same memory (same prior, gate and solve):
    #   'none'     only the base (linear) term
    #   'fourier1' cos(u), sin(u) per hidden unit: the function space of a
    #              reps = 1 circuit, whose Bloch components are a + b cos u + c sin u
    #   'fourier'  three features cos(w u + b) per unit, w and b trainable
    #   'tanh'     three features tanh(w u + b) per unit, w and b trainable
    #   'poly2'    all products u_i u_j (i <= j) of the hidden units
    #   'mlp'      ``mlp_units`` features tanh(W u + c): a two-layer network
    classical: str = "none"
    mlp_units: int = 8
    precision: str = "float64"  # 'float32': features, statistics and the solve in single precision
    # Tangent features u * d n / d u (reps = 1 only): the first-order effect of
    # changing the frequency w of the data-encoding gate RZ(w u) around w = 1, so
    # the context can also adapt the frequency of each circuit, still by a
    # linear solve.  On hardware d n / d u is the parameter-shift difference
    # [n(u + pi/2) - n(u - pi/2)] / 2 of the same circuit.
    tangent: bool = False
    # 'ls'   : gated least squares (closed form, see module docstring)
    # 'rls'  : the same statistics with the prior only in the initial condition
    #          (C_0 = Lambda_0, then C_t = g C_{t-1} + (1 - g) k k^T): exponentially
    #          weighted recursive least squares, whose inverse can be updated in
    #          O(F^2) per step by Sherman-Morrison; the prior decays with the gates
    # 'delta': normalised delta rule (no matrix), ``delta_passes`` sweeps over the context
    # 'none' : static observable R_0 (no fast weights)
    memory: str = "ls"
    delta_passes: int = 1
    # Finite shots only: how the query circuit is read.  'xyz' estimates <X>, <Y>,
    # <Z> with a third of the budget each; 'axis' measures the single observable
    # R_T . sigma that the context has just programmed (one basis, all shots).
    query_readout: str = "xyz"
    # Finite shots only (diagnostics): which circuit runs are sampled.  'all' |
    # 'query' (context features exact) | 'context' (query features exact)
    shot_scope: str = "all"
    # 'feature': g_t read from the same circuits (one more observable)
    # 'const'  : one learned scalar g
    # 'none'   : additive statistics (ungated rule, plain Bayesian linear regression)
    gate: str = "feature"
    prior: str = "diag"  # 'diag' (one precision per feature) | 'scalar'
    prior_init: float = 0.1
    prior_floor: float = 1e-10  # lower bound of the prior precision (keeps the solve well conditioned)
    # Tokens whose patch reaches before the window: with ``token_pad='replicate'``
    # the patch is filled with the first value; with 'truncate' the unknown
    # difference orders are zero.  ``mask_padded`` writes only tokens that know
    # at least ``min_context`` values (0 = all ``context`` values).
    mask_padded: bool = True
    token_pad: str = "replicate"
    min_context: int = 0
    max_len: int = 16  # chrono init of the gate bias
    skip: str = "last"  # 'last': predict the increment x_{T+1} - x_T | 'none'
    # ---- direct multi-step forecasting (d_out > 1) -----------------------------
    # The pair written for token t is (features of token t, the d_out values that
    # followed it minus an anchor built from values up to t), for every t whose
    # d_out successors lie inside the window.
    d_out: int = 1
    pool: int = 1  # > 1: token = means of the last ``context`` blocks of ``pool`` steps
    anchor: str = "last"  # 'last' (value at t) | 'cycle' (the previous d_out values, smoothed)
    anchor_smooth: int = 13  # centred moving-average width of the 'cycle' anchor
    out_basis: int = 0  # > 0: regress that many smooth cosine modes of the horizon
    pair_stride: int = 1  # write every ``pair_stride``-th complete pair (neighbouring pairs are redundant)

    def to_dict(self):
        return asdict(self)


class PooledTokenizer(nn.Module):
    """token_t = (m_t, m_{t-pool}, ..., m_{t-pool (context-1)}) with ``m_t`` the
    mean of the last ``pool`` values up to ``t`` (causal block means)."""

    def __init__(self, pool: int, context: int):
        super().__init__()
        self.pool, self.context = pool, context

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        s = x[..., 0].double()
        t = s.shape[1]
        cs = F.pad(s.cumsum(1), (1, 0))
        idx = torch.arange(t, device=x.device)
        lo = (idx - self.pool + 1).clamp_min(0)
        mean = (cs[:, idx + 1] - cs[:, lo]) / (idx + 1 - lo)
        lag = (idx[:, None] - self.pool * torch.arange(self.context, device=x.device)[None, :]).clamp_min(0)
        return mean[:, lag]

    def fit_scale(self, x_train: torch.Tensor) -> None:  # block means need no rescaling
        return None


class ObservableMemoryFWP(nn.Module):
    """Scalar series ``(B, T, 1)`` -> prediction of the next ``d_out`` values.

    Tokens and in-context targets are always formed in float64 (as in the other
    models of this repository); features, statistics and the solve use
    ``cfg.precision``."""

    def __init__(self, cfg: ObsMemConfig):
        super().__init__()
        if cfg.context == 0:
            cfg = replace(cfg, context=max(1, min(8, cfg.max_len // 2)))
        self.cfg = cfg
        if cfg.pool > 1:
            self.tokenizer = PooledTokenizer(cfg.pool, cfg.context)
        else:
            self.tokenizer = Tokenizer(1, cfg.context, cfg.context_mode, dtype="float64", keep_dtype=True,
                                       pad=cfg.token_pad)
        h = cfg.hidden
        self.dtype = {"float64": torch.float64, "float32": torch.float32}[cfg.precision]
        self.enc = nn.Linear(cfg.context, h)
        nonlinear = cfg.quantum
        if cfg.quantum:
            if cfg.classical != "none":
                raise ValueError("classical features replace the Bloch features: set quantum=False")
            self.theta = nn.Parameter(torch.empty(1, h, cfg.reps + 1, 2))
            nn.init.xavier_normal_(self.theta)
        elif cfg.classical in ("tanh", "fourier"):
            nonlinear = True
            self.cl_w = nn.Parameter(torch.empty(h, 3).normal_(1.0, 0.5))
            self.cl_b = nn.Parameter(torch.empty(h, 3).uniform_(-math.pi, math.pi))
        elif cfg.classical == "mlp":
            self.mlp = nn.Linear(h, cfg.mlp_units)
        elif cfg.classical not in ("none", "fourier1", "poly2"):
            raise ValueError(cfg.classical)
        elif cfg.classical == "none" and cfg.base == "none":
            raise ValueError("a model without nonlinear features needs a base activation")
        if cfg.tangent and not (cfg.quantum and cfg.reps == 1):
            raise ValueError("tangent features need Bloch features and reps == 1")
        n_nonlinear = {"none": 0, "tanh": 3 * h, "fourier": 3 * h, "fourier1": 2 * h, "poly2": h * (h + 1) // 2,
                       "mlp": cfg.mlp_units}[cfg.classical]
        if cfg.quantum:
            n_nonlinear = 3 * h
        if cfg.classical == "poly2":
            iu = torch.triu_indices(h, h)
            self.register_buffer("poly_i", iu[0], persistent=False)
            self.register_buffer("poly_j", iu[1], persistent=False)
        self.n_feat = 1 + (h if cfg.base != "none" else 0) + n_nonlinear + (3 * h if cfg.tangent else 0)
        f = self.n_feat
        self.n_out = cfg.out_basis or cfg.d_out  # regression outputs per pair
        # prior / static observable: one coefficient per feature (and per output)
        self.r0 = nn.Parameter(torch.zeros(f) if self.n_out == 1 else torch.zeros(f, self.n_out))
        if cfg.out_basis:
            n = torch.arange(cfg.d_out, dtype=torch.float64) + 0.5
            j = torch.arange(cfg.out_basis, dtype=torch.float64)
            basis = torch.cos(math.pi * n[:, None] * j[None, :] / cfg.d_out)  # DCT-II modes, (d_out, K)
            self.register_buffer("basis", basis)
            self.register_buffer("basis_pinv", torch.linalg.pinv(basis))  # (K, d_out)
        self.register_buffer("y_scale", torch.ones(()))
        if cfg.memory == "history":
            # The targets are not part of the window (e.g. a drive u is read and an
            # output y is predicted), so there is nothing to write from the context.
            # The observable is then solved from a labelled history - the training
            # windows - with the same closed form, and kept fixed afterwards.
            if cfg.gate != "none" or cfg.skip != "none" or cfg.d_out != 1:
                raise ValueError("memory='history' needs gate='none', skip='none' and d_out=1")
            self.register_buffer("r_hist", torch.zeros(f))
            self.register_buffer("has_history", torch.zeros((), dtype=torch.bool))
        if cfg.memory != "none":
            n_prior = f if cfg.prior == "diag" else 1
            self.log_prior = nn.Parameter(torch.full((n_prior,), math.log(cfg.prior_init)))
            tau = max(float(cfg.max_len), 2.0)
            if cfg.gate == "feature":
                self.gate_w = nn.Parameter(torch.zeros(f))
                self.gate_b = nn.Parameter(torch.tensor(math.log(tau - 1.0)))
            elif cfg.gate == "const":
                self.gate_b = nn.Parameter(torch.tensor(math.log(tau - 1.0)))
            elif cfg.gate != "none":
                raise ValueError(cfg.gate)
        self.to(self.dtype)

    # ------------------------------------------------------------------
    @torch.no_grad()
    def fit_token_scale(self, x_train: torch.Tensor) -> None:
        self.tokenizer.fit_scale(x_train)
        s = x_train[..., 0].double()
        if self.cfg.d_out > 1:
            sub = x_train[:: max(1, len(x_train) // 256)]
            _, _, z, valid = self.context_pairs(sub)
            self.y_scale.copy_(z[valid].std().clamp_min(1e-8))
        elif self.cfg.skip == "last":
            self.y_scale.copy_((s[:, 1:] - s[:, :-1]).std().clamp_min(1e-8))
        else:
            self.y_scale.copy_(s.std().clamp_min(1e-8))

    @torch.no_grad()
    def fit_target_scale(self, y_train: torch.Tensor) -> None:
        """Scale of targets that are not the input series (``memory='history'``, or a static model with ``skip='none'``)."""
        self.y_scale.copy_(y_train.double().std().clamp_min(1e-8))

    def query_features(self, x: torch.Tensor) -> torch.Tensor:
        """Features ``(B, F)`` of the last token of every window."""
        return self.features(self.tokenizer(x)[:, -1].to(self.dtype))

    def history_observable(self, k: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        """Observable ``R = R0 + (Lambda0 + sum_i k_i k_i^T)^{-1} sum_i k_i (y_i - k_i . R0)``
        solved from labelled windows: ``k`` (n, F) their query features, ``y`` (n,) their targets."""
        err0 = y.to(self.dtype) / self.y_scale - k @ self.r0
        c = k.T @ k + torch.diag(self._prior_precision())
        return self.r0 + torch.linalg.solve(c, k.T @ err0)

    @torch.no_grad()
    def fit_history(self, x: torch.Tensor, y: torch.Tensor) -> None:
        """Store the observable solved from the labelled windows ``(x, y)``; it is used by ``forward`` from then on."""
        self.r_hist.copy_(self.history_observable(self.query_features(x), y.reshape(-1)))
        self.has_history.fill_(True)

    def features(self, tok: torch.Tensor) -> torch.Tensor:
        """``(..., context)`` tokens -> ``(..., F)`` features
        ``[1, base(u_1..h), <X>,<Y>,<Z> of circuit 1..h]`` with ``u = enc(tok)``."""
        cfg = self.cfg
        u = self.enc(tok)
        parts = [torch.ones_like(u[..., :1])]
        if cfg.base == "identity":
            parts.append(u)
        elif cfg.base == "silu":
            parts.append(F.silu(u))
        elif cfg.base != "none":
            raise ValueError(cfg.base)
        # with finite shots a circuit shares its budget with its parameter-shifted copies
        copies = 3 if cfg.tangent else 1
        if cfg.quantum:
            parts.append(daruan_bloch(u, self.theta, circuit_copies=copies).flatten(-3))
        elif cfg.classical == "tanh":
            parts.append(torch.tanh(u[..., None] * self.cl_w + self.cl_b).flatten(-2))
        elif cfg.classical == "fourier":
            parts.append(torch.cos(u[..., None] * self.cl_w + self.cl_b).flatten(-2))
        elif cfg.classical == "fourier1":
            parts += [torch.cos(u), torch.sin(u)]
        elif cfg.classical == "poly2":
            parts.append(u[..., self.poly_i] * u[..., self.poly_j])
        elif cfg.classical == "mlp":
            parts.append(torch.tanh(self.mlp(u)))
        if cfg.tangent:
            shift = 0.5 * math.pi
            dn = 0.5 * (daruan_bloch(u + shift, self.theta, circuit_copies=copies)
                        - daruan_bloch(u - shift, self.theta, circuit_copies=copies))  # d n / d u
            parts.append((u[..., None, :, None] * dn).flatten(-3))
        return torch.cat(parts, -1)

    def _prior_precision(self) -> torch.Tensor:
        return (torch.exp(self.log_prior) + self.cfg.prior_floor).expand(self.n_feat)

    def _log_gates(self, k_ctx: torch.Tensor, valid: torch.Tensor):
        """log g_t and log(1 - g_t) for the context tokens; masked tokens get
        g = 1 (no decay, no write)."""
        cfg = self.cfg
        if cfg.gate == "feature":
            logit = k_ctx @ self.gate_w + self.gate_b
        else:
            logit = self.gate_b.expand(k_ctx.shape[:-1])
        log_g = F.logsigmoid(logit)
        log_w = F.logsigmoid(-logit)
        log_g = torch.where(valid, log_g, torch.zeros_like(log_g))
        log_w = torch.where(valid, log_w, torch.full_like(log_w, -torch.inf))
        return log_g, log_w

    def _anchor(self, s: torch.Tensor, ends: torch.Tensor) -> torch.Tensor:
        """Anchor of the ``d_out``-step forecast issued after each index in
        ``ends``, built from values up to that index only: ``(B, len(ends), d_out)``."""
        cfg = self.cfg
        if cfg.anchor == "last":
            return s[:, ends, None].expand(-1, -1, cfg.d_out)
        if cfg.anchor != "cycle":
            raise ValueError(cfg.anchor)
        # the previous d_out values after a centred moving average that is
        # truncated at the forecast origin (and at the start of the window)
        half = cfg.anchor_smooth // 2
        width = cfg.d_out + half
        idx = (ends[:, None] - width + 1 + torch.arange(width, device=s.device)[None, :]).clamp_min(0)
        seg = s[:, idx]  # (B, E, width)
        if cfg.anchor_smooth > 1:
            flat = seg.reshape(-1, 1, width)
            flat = F.avg_pool1d(flat, cfg.anchor_smooth, stride=1, padding=half, count_include_pad=False)
            seg = flat.reshape(seg.shape)
        return seg[..., -cfg.d_out:]

    def _to_outputs(self, y: torch.Tensor) -> torch.Tensor:
        return y @ self.basis_pinv.T.to(y.dtype) if self.cfg.out_basis else y

    def _context_pairs_multistep(self, x: torch.Tensor):
        cfg = self.cfg
        s = x[..., 0].double()
        t_len, h = s.shape[1], cfg.d_out
        # tokens 0 .. T-h-1 have all h successors inside the window; keep every
        # ``pair_stride``-th of them, counted back from the most recent one
        t = torch.arange(t_len - h - 1, -1, -cfg.pair_stride, device=x.device).flip(0)
        need = max(cfg.pool * cfg.context if cfg.pool > 1 else (cfg.min_context or cfg.context),
                   h if cfg.anchor == "cycle" else 1)
        if cfg.mask_padded:
            t = t[t >= need - 1]
        tok = self.tokenizer(x)
        last = torch.tensor([t_len - 1], device=x.device)
        k = self.features(tok[:, torch.cat([t, last])].to(self.dtype))  # features of the written tokens, then the query
        if len(t):
            future = s[:, t[:, None] + 1 + torch.arange(h, device=x.device)[None, :]]  # what followed token t
            z = (self._to_outputs(future - self._anchor(s, t)) / self.y_scale.double()).to(self.dtype)
        else:
            z = s.new_zeros(s.shape[0], 0, self.n_out, dtype=self.dtype)
        return s, k, z, torch.ones(s.shape[0], len(t), dtype=torch.bool, device=x.device)

    def context_pairs(self, x: torch.Tensor):
        """Features of every token, in-context targets and the write mask."""
        cfg = self.cfg
        if cfg.d_out > 1:
            return self._context_pairs_multistep(x)
        s = x[..., 0].double()
        k = self.features(self.tokenizer(x).to(self.dtype))  # (B, T, F)
        if cfg.skip == "last":
            y_ctx = (s[:, 1:] - s[:, :-1]) / self.y_scale.double()  # what followed token t
        else:
            y_ctx = s[:, 1:] / self.y_scale.double()
        y_ctx = y_ctx.to(self.dtype)
        t = torch.arange(s.shape[1] - 1, device=x.device)
        need = cfg.min_context or cfg.context
        valid = (t >= need - 1) if cfg.mask_padded else torch.ones_like(t, dtype=torch.bool)
        return s, k, y_ctx, valid.expand(s.shape[0], -1)

    def memory_weights(self, k_ctx: torch.Tensor, valid: torch.Tensor) -> torch.Tensor:
        """Closed-form weights ``beta_t`` of the gated recursion (paper Eq. 5)
        for every context pair; ``gate='none'`` is the additive rule (all 1)."""
        if self.cfg.gate == "none":
            return valid.to(k_ctx.dtype)
        log_g, log_w = self._log_gates(k_ctx, valid)
        return torch.exp(log_w + log_g.sum(1, keepdim=True) - log_g.cumsum(1))

    def fast_observable(self, k_ctx, y_ctx, valid) -> torch.Tensor:
        """``R_T`` (B, F): the observable programmed by the context."""
        cfg = self.cfg
        b = k_ctx.shape[0]
        r0 = self.r0.expand(b, *self.r0.shape)
        if cfg.memory == "none" or k_ctx.shape[1] == 0 or not bool(valid.any()):
            return r0
        lam = self._prior_precision()
        err0 = y_ctx - k_ctx @ self.r0  # prediction errors of the prior observable
        if cfg.memory in ("ls", "rls"):
            beta = self.memory_weights(k_ctx, valid)
            if cfg.memory == "rls" and cfg.gate != "none":
                # the prior is only the initial condition, so it keeps the weight beta_0 = prod_t g_t
                beta0 = torch.exp(self._log_gates(k_ctx, valid)[0].sum(1))
                prior = beta0[:, None] * lam + 1e-12
            else:
                prior = lam.expand(b, -1)
            c = torch.einsum("bt,btf,btg->bfg", beta, k_ctx, k_ctx) + torch.diag_embed(prior)
            if err0.dim() == 2:
                rhs = torch.einsum("bt,btf,bt->bf", beta, k_ctx, err0)
                return r0 + torch.linalg.solve(c, rhs[..., None])[..., 0]
            rhs = torch.einsum("bt,btf,btk->bfk", beta, k_ctx, err0)
            return r0 + torch.linalg.solve(c, rhs)
        if cfg.memory == "delta":
            assert err0.dim() == 2, "the delta rule is implemented for one-step prediction"
            # R_t = R_{t-1} + (1 - g_t) e_t P k_t / (k_t . P k_t), P = Lambda_0^{-1}
            if cfg.gate == "none":
                eta = valid.to(k_ctx.dtype)
            else:
                eta = torch.exp(self._log_gates(k_ctx, valid)[1])
            p = 1.0 / lam
            r = r0
            for _ in range(cfg.delta_passes):
                for t in range(k_ctx.shape[1]):
                    kt = k_ctx[:, t]
                    pk = p * kt
                    e = y_ctx[:, t] - (kt * r).sum(-1)
                    r = r + (eta[:, t] * e / (kt * pk).sum(-1))[:, None] * pk
            return r
        raise ValueError(cfg.memory)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if self.cfg.memory == "history":
            r = self.r_hist if bool(self.has_history) else self.r0
            return ((self.query_features(x) * r).sum(-1) * self.y_scale)[:, None]
        shots = daruan.get_shots()
        scope = self.cfg.shot_scope if (shots is not None and self.cfg.d_out == 1) else "all"
        if scope == "all":
            s, k, y_ctx, valid = self.context_pairs(x)
        else:
            # sample only part of the circuit runs: the query token is the last one
            daruan.set_shots(None)
            try:
                s, k, y_ctx, valid = self.context_pairs(x)  # exact everywhere
                if scope == "context":
                    daruan.set_shots(shots)
                    k = torch.cat([self.context_pairs(x)[1][:, :-1], k[:, -1:]], 1)
                elif scope == "query":
                    daruan.set_shots(shots)
                    k = torch.cat([k[:, :-1], self.features(self.tokenizer(x)[:, -1:].to(self.dtype))], 1)
                else:
                    raise ValueError(scope)
            finally:
                daruan.set_shots(shots)
        if self.cfg.d_out > 1:
            r = self.fast_observable(k[:, : y_ctx.shape[1]], y_ctx, valid)  # (B, F, K)
            out = torch.einsum("bf,bfk->bk", k[:, -1], r) * self.y_scale
            if self.cfg.out_basis:
                out = out @ self.basis.T
            last = torch.tensor([s.shape[1] - 1], device=x.device)
            return out + self._anchor(s, last)[:, 0].to(self.dtype)
        r = self.fast_observable(k[:, :-1], y_ctx, valid)
        if (shots is not None and scope != "context" and self.cfg.query_readout == "axis" and self.cfg.quantum
                and not self.cfg.tangent):
            y = self._read_query_along_axis(x, r, shots) * self.y_scale
        else:
            y = (k[:, -1] * r).sum(-1) * self.y_scale
        if self.cfg.skip == "last":
            y = y + s[:, -1].to(self.dtype)
        return y[:, None]

    def _read_query_along_axis(self, x: torch.Tensor, r: torch.Tensor, shots: float) -> torch.Tensor:
        """Finite-shot read-out of the query with the measurement basis programmed
        by the context.  For circuit i the fast observable is ``R_i . sigma`` with
        ``R_i`` the three Bloch coefficients of ``R_T``; rotating the measurement
        axis to ``R_i / |R_i|`` estimates ``R_i . n_i`` from one setting with all
        ``shots`` (instead of three settings with a third each).  The classical
        terms (constant and base activation) carry no shot noise."""
        cfg, h = self.cfg, self.cfg.hidden
        daruan.set_shots(None)
        try:
            k_q = self.features(self.tokenizer(x)[:, -1].to(self.dtype))  # exact expectations of the query
        finally:
            daruan.set_shots(shots)
        n_cl = self.n_feat - 3 * h
        classical = (k_q[:, :n_cl] * r[:, :n_cl]).sum(-1)
        rv = r[:, n_cl:].reshape(-1, h, 3)
        nv = k_q[:, n_cl:].reshape(-1, h, 3)
        amp = rv.norm(dim=-1).clamp_min(1e-30)
        cos = ((rv * nv).sum(-1) / amp).clamp(-1.0, 1.0)  # expectation of the unit observable
        n = max(int(shots), 1)
        contraction, offset, _ = daruan.get_device()  # static errors of the measured expectation
        cos = (contraction * cos + offset).clamp(-1.0, 1.0)
        counts = torch.binomial(torch.full_like(cos, float(n)), ((1.0 + cos.detach()) * 0.5).clamp(0.0, 1.0))
        est = cos + (2.0 * counts / n - 1.0 - cos.detach())
        return classical + (amp * est).sum(-1)

    @torch.no_grad()
    def query_shot_variance(self, x: torch.Tensor, shots: float, readout: str = "axis") -> torch.Tensor:
        """Closed-form variance of the prediction caused by the finite shots of
        the *query* circuits alone (exact context), in units of the target:
        ``y_scale^2 * sum_i |R_i|^2 (1 - cos_i^2) / S`` when each circuit is read
        along its programmed axis, and ``y_scale^2 * sum_i sum_a R_ia^2 (1 - n_ia^2) / floor(S/3)``
        for the X/Y/Z read-out.  The fast observable ``R_T`` is known before the
        query is measured, so this number is available in advance."""
        h = self.cfg.hidden
        old = daruan.get_shots()
        daruan.set_shots(None)
        try:
            _, k, y_ctx, valid = self.context_pairs(x)
        finally:
            daruan.set_shots(old)
        r = self.fast_observable(k[:, :-1], y_ctx, valid)
        n_cl = self.n_feat - 3 * h
        rv = r[:, n_cl:].reshape(-1, h, 3)
        nv = k[:, -1, n_cl:].reshape(-1, h, 3)
        if readout == "axis":
            amp2 = (rv**2).sum(-1)
            cos2 = (rv * nv).sum(-1) ** 2 / amp2.clamp_min(1e-300)
            var = (amp2 * (1.0 - cos2)).sum(-1) / max(int(shots), 1)
        else:
            var = (rv**2 * (1.0 - nv**2)).sum((-1, -2)) / max(int(shots // 3), 1)
        return var * self.y_scale**2

    @torch.no_grad()
    def gram_matrix(self, x: torch.Tensor) -> torch.Tensor:
        """``C_T = Lambda_0 + sum_t beta_t k_t k_t^T`` of every window, ``(B, F, F)``
        (diagnostics: its condition number bounds the error amplification of
        the read-out solve)."""
        _, k, y_ctx, valid = self.context_pairs(x)
        k_ctx = k[:, : y_ctx.shape[1]]
        beta = self.memory_weights(k_ctx, valid)
        return torch.einsum("bt,btf,btg->bfg", beta, k_ctx, k_ctx) + torch.diag_embed(self._prior_precision())

    # ------------------------------------------------------------------
    def statistics_recursion(self, x: torch.Tensor):
        """Step-by-step reference of the gated statistics (used in tests):
        returns ``(C_T, b_T)`` built with ``C_t = g C_{t-1} + (1 - g) (Lambda_0 + k k^T)``."""
        assert self.cfg.d_out == 1
        _, k, y_ctx, valid = self.context_pairs(x)
        k_ctx = k[:, :-1]
        lam = self._prior_precision()
        c0 = torch.diag_embed(lam.expand(k.shape[0], -1))
        b0 = (lam * self.r0).expand(k.shape[0], -1)
        c, b = c0.clone(), b0.clone()
        log_g, log_w = self._log_gates(k_ctx, valid)
        for t in range(k_ctx.shape[1]):
            g, w = torch.exp(log_g[:, t]), torch.exp(log_w[:, t])
            kt = k_ctx[:, t]
            c = g[:, None, None] * c + w[:, None, None] * (c0 + kt[:, :, None] * kt[:, None, :])
            b = g[:, None] * b + w[:, None] * (b0 + y_ctx[:, t, None] * kt)
        return c, b
