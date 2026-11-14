import math

import pytest
import torch

from qkanfwp.daruan import daruan_bloch, daruan_pz
from qkanfwp.models import FWPConfig, GatedFWP, count_parameters, gated_recursion
from qkanfwp.obsmem import ObservableMemoryFWP, ObsMemConfig


def _series(b=6, t=16, seed=0):
    g = torch.Generator().manual_seed(seed)
    return torch.randn(b, t, 1, generator=g, dtype=torch.float64).cumsum(1) * 0.1


def _randomise(m, seed=1):
    g = torch.Generator().manual_seed(seed)
    with torch.no_grad():
        for name in ("r0", "gate_w", "log_prior"):
            if hasattr(m, name):
                getattr(m, name).copy_(torch.randn(getattr(m, name).shape, generator=g, dtype=torch.float64))


def test_bloch_vector_is_unit_and_matches_z():
    torch.manual_seed(0)
    x = torch.randn(9, 3)
    theta = torch.randn(2, 3, 4, 2)
    bloch = daruan_bloch(x, theta)
    assert bloch.shape == (9, 2, 3, 3)
    assert torch.allclose(bloch.norm(dim=-1), torch.ones(9, 2, 3), atol=1e-5)
    assert torch.allclose(bloch[..., 2], daruan_pz(x, theta, fast_measure=False), atol=1e-6)


def test_activation_is_linear_in_the_observable():
    """<O> for O = r . sigma equals r . bloch: rotate the observable by the
    final RZ-RY gate and compare with the plain <Z> of the extended circuit."""
    torch.manual_seed(0)
    x = torch.randn(5, 2, dtype=torch.float64)
    theta = torch.randn(1, 2, 3, 2, dtype=torch.float64)
    extra = torch.randn(1, 2, 1, 2, dtype=torch.float64)  # one more RZ-RY layer before <Z>
    # appending the gates RZ(a) RY(b) and measuring Z == measuring the rotated observable
    a, b = extra[..., 0, 0], extra[..., 0, 1]
    r = torch.stack([-torch.sin(b) * torch.cos(a), torch.sin(b) * torch.sin(a), torch.cos(b)], -1)
    theta_ext = torch.cat([theta, extra], -2)
    # the extended circuit has one more data upload; switch it off with preact weight 0
    w = torch.ones(1, 2, 3, dtype=torch.float64)
    w[..., -1] = 0.0
    z_ext = daruan_pz(x, theta_ext, w, torch.zeros_like(w), fast_measure=False)
    lin = (daruan_bloch(x, theta) * r).sum(-1)
    assert torch.allclose(z_ext, lin, atol=1e-10)


@pytest.mark.parametrize("kw", [dict(), dict(gate="const"), dict(prior="scalar"), dict(mask_padded=False),
                                dict(base="none"), dict(context=8, hidden=3, reps=1)])
def test_gated_statistics_closed_form_matches_recursion(kw):
    torch.manual_seed(0)
    m = ObservableMemoryFWP(ObsMemConfig(**kw))
    _randomise(m)
    x = _series()
    m.fit_token_scale(x)
    _, k, y_ctx, valid = m.context_pairs(x)
    c, b = m.statistics_recursion(x)
    ref = torch.linalg.solve(c, b)
    out = m.fast_observable(k[:, :-1], y_ctx, valid)
    assert torch.allclose(out, ref, atol=1e-8)


def test_statistics_stay_in_the_convex_hull_and_keep_the_prior():
    """C_T is a convex combination of the proposals Lambda_0 + k k^T (and
    Lambda_0 itself), so C_T - Lambda_0 is PSD even when a gate closes fully."""
    torch.manual_seed(0)
    m = ObservableMemoryFWP(ObsMemConfig(mask_padded=False))
    _randomise(m)
    with torch.no_grad():
        m.gate_w.mul_(30.0)  # saturate the gates: some g_t are numerically 0 or 1
    x = _series()
    _, k, _, valid = m.context_pairs(x)
    beta = m.memory_weights(k[:, :-1], valid)
    assert torch.all(beta >= 0) and torch.all(beta.sum(1) <= 1 + 1e-10)
    c, _ = m.statistics_recursion(x)
    lam = torch.diag_embed(m._prior_precision())
    assert torch.linalg.eigvalsh(c - lam).min() > -1e-9
    assert torch.linalg.eigvalsh(c).min() >= m._prior_precision().min() - 1e-9


def test_closed_gate_or_no_memory_gives_the_static_model():
    torch.manual_seed(0)
    x = _series()
    m = ObservableMemoryFWP(ObsMemConfig())
    _randomise(m)
    static = ObservableMemoryFWP(ObsMemConfig(memory="none"))
    static.load_state_dict(m.state_dict(), strict=False)
    with torch.no_grad():
        m.gate_w.zero_()
        m.gate_b.fill_(60.0)  # g = 1: nothing is written
    assert torch.allclose(m(x), static(x), atol=1e-9)


def test_padded_tokens_are_not_written():
    """With context 8 and a window of 8 no token is complete, so the fast
    observable equals the prior."""
    torch.manual_seed(0)
    m = ObservableMemoryFWP(ObsMemConfig(context=8))
    _randomise(m)
    x = _series(t=8)
    _, k, y_ctx, valid = m.context_pairs(x)
    assert not valid.any()
    assert torch.allclose(m.fast_observable(k[:, :-1], y_ctx, valid), m.r0.expand(len(x), -1))


def test_in_context_identification_of_a_linear_recurrence():
    """Sequences with different AR(2) coefficients are predicted from the
    window alone (untrained features, weak prior)."""
    t = torch.arange(40, dtype=torch.float64)
    om = torch.tensor([0.3, 0.7, 1.1])[:, None]
    x = (torch.exp(-0.02 * t) * torch.cos(om * t + 0.4))[..., None]
    torch.manual_seed(0)
    m = ObservableMemoryFWP(ObsMemConfig(context=2, context_mode="lags", hidden=2, quantum=False,
                                         gate="none", prior_init=1e-12))
    m.fit_token_scale(x[:, :-1])
    err = (m(x[:, :-1])[:, 0] - x[:, -1, 0]).abs().max()
    assert err < 1e-4
    static = ObservableMemoryFWP(ObsMemConfig(context=2, context_mode="lags", hidden=2, quantum=False, memory="none"))
    static.fit_token_scale(x[:, :-1])
    assert (static(x[:, :-1])[:, 0] - x[:, -1, 0]).abs().max() > 100 * err


def test_delta_rule_moves_towards_least_squares():
    torch.manual_seed(0)
    x = _series(t=32)
    ls = ObservableMemoryFWP(ObsMemConfig(gate="none"))
    _randomise(ls)
    dl = ObservableMemoryFWP(ObsMemConfig(gate="none", memory="delta"))
    dl.load_state_dict(ls.state_dict())
    _, k, y_ctx, valid = ls.context_pairs(x)
    k_ctx = k[:, :-1]

    def sse(r):
        return (((k_ctx * r[:, None]).sum(-1) - y_ctx) ** 2 * valid).sum()

    r0 = ls.r0.expand(len(x), -1)
    assert sse(ls.fast_observable(k_ctx, y_ctx, valid)) < sse(dl.fast_observable(k_ctx, y_ctx, valid)) < sse(r0)


def test_parameter_budget():
    assert count_parameters(ObservableMemoryFWP(ObsMemConfig())) == 96
    assert count_parameters(ObservableMemoryFWP(ObsMemConfig(memory="none"))) == 61


def test_cmg_gate_matches_recursion_and_is_per_weight():
    torch.manual_seed(0)
    cfg = FWPConfig(slow_hidden=3, slow_latent=3, slow_reps=3, fast_in=2, fast_out=1, fast_reps=3, gate="cmg")
    m = GatedFWP(cfg)
    x = torch.randn(5, 12, 1)
    tok = m.tokens(x)
    proposals, gate = m.split_slow(m.slow(tok[:, :-1]))
    assert gate.shape[-1] == m.n_fast == 16
    # rank-one logits: P x Q matrix of every step has rank 1
    assert torch.linalg.matrix_rank(gate[0, 0].reshape(m.cmg_shape), tol=1e-5) == 1
    assert torch.allclose(m.fast_weights(tok), gated_recursion(proposals, gate), atol=1e-6)


# ---------------------------------------------------------------------------
# token-length rule, truncated tokens, direct multi-step forecasting
# ---------------------------------------------------------------------------
from qkanfwp.models import Tokenizer  # noqa: E402
from qkanfwp.obsmem import PooledTokenizer  # noqa: E402


def test_automatic_token_length():
    for window, expect in ((8, 4), (16, 8), (64, 8), (2, 1)):
        assert ObservableMemoryFWP(ObsMemConfig(context=0, max_len=window)).cfg.context == expect
    for window in (8, 16, 32, 64):  # never above the paper's 159 parameters
        assert count_parameters(ObservableMemoryFWP(ObsMemConfig(context=0, hidden=6, reps=1, max_len=window))) <= 159


def test_truncated_difference_tokens():
    tok = Tokenizer(1, 4, "diff", dtype="float64", keep_dtype=True, pad="truncate")
    x = (torch.arange(7, dtype=torch.float64) ** 2)[None, :, None]
    out = tok(x)[0]
    # order k of token t is known iff k <= t; x = t^2 has differences (2t - 1, 2, 0)
    assert torch.equal(out[0], torch.tensor([0.0, 0.0, 0.0, 0.0], dtype=torch.float64))
    assert torch.equal(out[1], torch.tensor([1.0, 1.0, 0.0, 0.0], dtype=torch.float64))
    assert torch.equal(out[5], torch.tensor([25.0, 9.0, 2.0, 0.0], dtype=torch.float64))


def test_pooled_tokens_are_causal_block_means():
    tok = PooledTokenizer(pool=3, context=2)
    x = torch.arange(10, dtype=torch.float64)[None, :, None]
    out = tok(x)[0]
    assert torch.allclose(out[8], torch.tensor([7.0, 4.0], dtype=torch.float64))  # mean(6,7,8), mean(3,4,5)
    x2 = x.clone()
    x2[:, 6:] += 5.0
    assert torch.equal(tok(x2)[0, :6], out[:6])


def _multistep(**kw):
    cfg = dict(context=3, pool=4, hidden=3, reps=1, d_out=10, anchor="cycle", anchor_smooth=5, out_basis=4,
               pair_stride=2, max_len=20)
    cfg.update(kw)
    return ObservableMemoryFWP(ObsMemConfig(**cfg))


def test_multistep_pairs_use_only_the_past_of_their_target():
    torch.manual_seed(0)
    m = _multistep()
    x = _series(b=3, t=60)
    _, k, z, valid = m.context_pairs(x)
    assert valid.all() and z.shape == (3, k.shape[1] - 1, 4)
    # pair of token t depends on x[: t + d_out + 1] only; changing the last 5 values
    # touches only pairs whose targets reach into them
    t = torch.arange(60 - 10 - 1, -1, -2).flip(0)
    t = t[t >= max(4 * 3, 10) - 1]
    x2 = x.clone()
    x2[:, 55:] += 1.0
    _, k2, z2, _ = m.context_pairs(x2)
    untouched = t + 10 < 55
    assert untouched.any() and (~untouched).any()
    assert torch.equal(z[:, untouched], z2[:, untouched])
    assert torch.equal(k[:, :-1][:, untouched], k2[:, :-1][:, untouched])
    assert not torch.equal(z[:, ~untouched], z2[:, ~untouched])


def test_multistep_query_anchor_is_the_smoothed_last_cycle():
    torch.manual_seed(0)
    m = _multistep(anchor_smooth=13, d_out=20)
    x = _series(b=4, t=80)
    old = GatedFWP(FWPConfig(d_out=20, skip="cycle", skip_smooth=13))
    new = m._anchor(x[..., 0], torch.tensor([79]))[:, 0]
    assert torch.allclose(new, old.cycle_anchor(x).double(), atol=1e-6)
    # zero prior and no memory: the forecast is exactly the anchor
    static = _multistep(anchor_smooth=13, d_out=20, memory="none")
    assert torch.allclose(static(x), new, atol=1e-12)


def test_multistep_solve_is_column_wise_ridge_regression():
    torch.manual_seed(0)
    m = _multistep(gate="none", out_basis=0, d_out=6, anchor="last")
    _randomise(m)
    x = _series(b=2, t=50)
    _, k, z, valid = m.context_pairs(x)
    r = m.fast_observable(k[:, :-1], z, valid)
    lam = torch.diag(m._prior_precision())
    for col in range(z.shape[-1]):
        a = k[0, :-1]
        ref = torch.linalg.solve(a.T @ a + lam, a.T @ z[0, :, col] + lam @ m.r0[:, col])
        assert torch.allclose(r[0, :, col], ref, atol=1e-8)


def test_tangent_features_are_the_parameter_shift_derivative():
    """For reps = 1 the input enters one RZ gate, so d n / d u is the exact
    parameter-shift difference of the same circuit."""
    torch.manual_seed(0)
    u = torch.randn(5, 4, dtype=torch.float64, requires_grad=True)
    theta = torch.randn(1, 4, 2, 2, dtype=torch.float64)
    n = daruan_bloch(u, theta)
    shift = 0.5 * math.pi
    ps = 0.5 * (daruan_bloch(u + shift, theta) - daruan_bloch(u - shift, theta))[:, 0]
    ad = torch.stack([torch.autograd.grad(n[..., i].sum(), u, retain_graph=True)[0] for i in range(3)], -1)
    assert torch.allclose(ps, ad, atol=1e-10)
    m = ObservableMemoryFWP(ObsMemConfig(hidden=4, reps=1, tangent=True))
    assert m.n_feat == 1 + 4 + 12 + 12
    with pytest.raises(ValueError):
        ObservableMemoryFWP(ObsMemConfig(hidden=4, reps=2, tangent=True))


# ---------------------------------------------------------------------------
# finite shots, precision, classical feature controls
# ---------------------------------------------------------------------------
from qkanfwp import daruan  # noqa: E402


def test_shot_budget_is_split_over_the_three_bases():
    """A circuit budget of S shots gives floor(S / 3) shots to each of the
    non-commuting X, Y, Z bases; estimates are binomial counts mapped to [-1, 1]."""
    torch.manual_seed(0)
    x = torch.zeros(20000, 1)
    theta = torch.zeros(1, 1, 2, 2)
    theta[..., 1] = 0.7
    exact = daruan_bloch(x[:1], theta)[0, 0, 0]
    try:
        daruan.set_shots(100)
        assert daruan.shots_per_setting(3) == 33 and daruan.shots_per_setting(1) == 100
        est = daruan_bloch(x, theta)[:, 0, 0]
        counts = (est + 1.0) * 33 / 2.0
        assert torch.allclose(counts, counts.round(), atol=1e-4)  # values lie on the 33-shot grid
        assert torch.allclose(est.mean(0), exact, atol=0.01)
        assert torch.allclose(est.std(0), ((1 - exact**2) / 33).sqrt(), rtol=0.05, atol=2e-3)
        z = daruan_pz(x, theta, fast_measure=False)[:, 0, 0]  # Z only: all 100 shots in one basis
        assert torch.allclose(z.std(), ((1 - exact[2] ** 2) / 100).sqrt(), rtol=0.1)
        # parameter-shifted copies share the same budget
        est9 = daruan_bloch(x, theta, circuit_copies=3)[:, 0, 0]
        assert torch.allclose(est9.std(0)[:2], ((1 - exact[:2] ** 2) / 11).sqrt(), rtol=0.05)
    finally:
        daruan.set_shots(None)
    assert torch.equal(daruan_bloch(x[:1], theta)[0, 0, 0], exact)


def test_shot_noise_keeps_the_gradient_of_the_exact_expectation():
    x = torch.linspace(-1, 1, 7)[:, None].requires_grad_(True)
    theta = torch.randn(1, 1, 2, 2, generator=torch.Generator().manual_seed(0))
    g_exact = torch.autograd.grad(daruan_bloch(x, theta).sum(), x)[0]
    try:
        daruan.set_shots(50)
        g_shots = torch.autograd.grad(daruan_bloch(x, theta).sum(), x)[0]
    finally:
        daruan.set_shots(None)
    assert torch.allclose(g_exact, g_shots)


def test_single_precision_model_matches_double_precision_weights():
    torch.manual_seed(0)
    x = _series()
    m64 = ObservableMemoryFWP(ObsMemConfig(hidden=6, reps=1, prior_init=1e-1))
    _randomise(m64)
    m32 = ObservableMemoryFWP(ObsMemConfig(hidden=6, reps=1, prior_init=1e-1, precision="float32"))
    m32.load_state_dict({k: v.float() for k, v in m64.state_dict().items()})
    y32 = m32(x)
    assert y32.dtype == torch.float32
    assert torch.allclose(m64(x), y32.double(), atol=1e-4)


@pytest.mark.parametrize("kind", ["tanh", "fourier"])
def test_classical_feature_controls_use_the_same_memory(kind):
    torch.manual_seed(0)
    x = _series()
    m = ObservableMemoryFWP(ObsMemConfig(hidden=6, reps=1, quantum=False, classical=kind))
    q = ObservableMemoryFWP(ObsMemConfig(hidden=6, reps=1))
    assert m.n_feat == q.n_feat == 25 and not hasattr(m, "theta")
    _randomise(m)
    _, k, y_ctx, valid = m.context_pairs(x)
    c, b = m.statistics_recursion(x)
    assert torch.allclose(m.fast_observable(k[:, :-1], y_ctx, valid), torch.linalg.solve(c, b), atol=1e-8)
    with pytest.raises(ValueError):
        ObservableMemoryFWP(ObsMemConfig(classical=kind))  # needs quantum=False


def test_gram_matrix_is_bounded_below_by_the_prior():
    torch.manual_seed(0)
    m = ObservableMemoryFWP(ObsMemConfig(hidden=6, reps=1))
    _randomise(m)
    x = _series()
    c = m.gram_matrix(x)
    assert torch.allclose(c, m.statistics_recursion(x)[0], atol=1e-10)
    lam = m._prior_precision()
    assert torch.linalg.eigvalsh(c).min() >= lam.min() - 1e-12
