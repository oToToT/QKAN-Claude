import pytest
import torch

from qkanfwp.models import (
    FWPConfig,
    GatedFWP,
    count_parameters,
    gated_aggregate,
    gated_recursion,
)


@pytest.mark.parametrize("groups", [1, 4])
@pytest.mark.parametrize("with_init", [False, True])
def test_closed_form_equals_recursion(groups, with_init):
    torch.manual_seed(0)
    b, t, p = 3, 11, 8
    proposals = torch.randn(b, t, p)
    logits = 2.0 * torch.randn(b, t, groups)
    index = torch.arange(p) % groups if groups > 1 else None
    w0 = torch.randn(p) if with_init else None
    ref = gated_recursion(proposals, logits, w0, index)
    out = gated_aggregate(proposals, logits, w0, index)
    assert torch.allclose(out, ref, atol=1e-5)


def test_ungated_is_plain_sum():
    torch.manual_seed(0)
    proposals = torch.randn(2, 5, 4)
    assert torch.allclose(gated_aggregate(proposals, None), gated_recursion(proposals, None), atol=1e-6)


def test_baseline_parameter_count_matches_paper():
    # Table 2 of the paper lists 159 trainable parameters for GQKAN-QKANFWP.
    assert count_parameters(GatedFWP(FWPConfig())) == 159


def test_convex_hull_bound():
    """Eq. 11: gated fast weights never leave the hull of the proposals."""
    torch.manual_seed(0)
    proposals = torch.randn(4, 20, 6)
    logits = 3.0 * torch.randn(4, 20, 1)
    w = gated_aggregate(proposals, logits)
    # W_1 = 0 is part of the hull, so the bound is max(0, max_k |dW_k|).
    assert (w.norm(dim=-1) <= proposals.norm(dim=-1).max(1).values + 1e-5).all()


@pytest.mark.parametrize(
    "kw",
    [
        dict(),
        dict(gate="none"),
        dict(gate="group", gate_groups="edge", gate_init="chrono"),
        dict(gate="group", gate_groups="node"),
        dict(context=3, skip="last"),
        dict(context=4, stride=2, skip="mean"),
        dict(slow="mlp", slow_hidden=8),
        dict(fast="linear", fast_out=3),
        dict(fast="linear", fast_out=3, gate="group", gate_groups="node", context=2),
    ],
)
def test_forward_backward_and_causality(kw):
    torch.manual_seed(0)
    model = GatedFWP(FWPConfig(**kw))
    x = torch.randn(5, 16, 1)
    y = model(x)
    assert y.shape == (5, 1)
    y.sum().backward()
    assert all(p.grad is not None for p in model.parameters())


def test_fast_weights_ignore_last_step():
    """y_T = F(x_T; W_T): W_T must not depend on x_T (read before write)."""
    torch.manual_seed(0)
    model = GatedFWP(FWPConfig())
    x = torch.randn(2, 9, 1)
    x2 = x.clone()
    x2[:, -1] += 1.0
    assert torch.allclose(model.fast_weights(model.tokens(x)), model.fast_weights(model.tokens(x2)))


def test_chrono_init_spans_window():
    model = GatedFWP(FWPConfig(gate="group", gate_groups="edge", gate_init="chrono", max_len=64))
    g = torch.sigmoid(model.slow.dec.bias[model.n_slow_out :])
    tau = 1.0 / (1.0 - g)
    assert torch.allclose(tau[0], torch.tensor(2.0), atol=1e-4)
    assert torch.allclose(tau[-1], torch.tensor(64.0), atol=1e-2)


@pytest.mark.parametrize(
    "kw",
    [
        dict(),
        dict(gate="none"),
        dict(gate="group", gate_groups="edge", gate_init="chrono"),
        dict(gate="group", gate_groups="node", context=3),
        dict(slow="mlp", slow_hidden=8, gate="group", gate_groups="param"),
    ],
)
def test_latent_aggregation_equals_explicit_recursion(kw):
    """The latent-space shortcut must reproduce Eq. 3 applied step by step."""
    torch.manual_seed(0)
    model = GatedFWP(FWPConfig(**kw))
    tok = model.tokens(torch.randn(4, 13, 1))
    proposals, gate = model.split_slow(model.slow(tok[:, :-1]))
    ref = gated_recursion(proposals, gate, None, model.group_index)
    assert torch.allclose(model.fast_weights(tok), ref, atol=1e-5)


@pytest.mark.parametrize("kw", [dict(), dict(context=3, gate="group", gate_groups="node")])
def test_token_deduplication_is_exact(kw):
    """Evaluating the slow programmer once per unique token changes nothing."""
    torch.manual_seed(0)
    model = GatedFWP(FWPConfig(**kw))
    series = torch.randn(60)
    x = torch.stack([series[i : i + 24] for i in range(0, 30, 3)])[..., None]  # overlapping windows
    model.dedup_min_tokens = 10**9
    ref = model(x)
    model.dedup_min_tokens = 1
    out = model(x)
    assert torch.allclose(out, ref, atol=1e-6)
    g_ref = torch.autograd.grad(ref.sum(), model.slow.enc.weight, retain_graph=True)[0]
    g_out = torch.autograd.grad(out.sum(), model.slow.enc.weight)[0]
    assert torch.allclose(g_out, g_ref, atol=1e-5)


def test_difference_tokens():
    torch.manual_seed(0)
    model = GatedFWP(FWPConfig(context=3, context_mode="diff"))
    x = torch.randn(4, 10, 1)
    tok = model.tokens(x)
    s = x[..., 0]
    assert torch.allclose(tok[:, 2:, 0], s[:, 2:])
    assert torch.allclose(tok[:, 2:, 1], s[:, 2:] - s[:, 1:-1], atol=1e-6)
    assert torch.allclose(tok[:, 2:, 2], s[:, 2:] - 2 * s[:, 1:-1] + s[:, :-2], atol=1e-6)
    assert torch.allclose(tok[:, 0, 1:], torch.zeros(4, 2))  # replicate padding -> zero differences
    model.fit_token_scale(x)
    std = model.tokens(x).reshape(-1, 3).std(0)
    assert torch.allclose(std[1:], torch.ones(2), atol=1e-5)
    model(x).sum().backward()


def test_smooth_output_basis():
    torch.manual_seed(0)
    cfg = FWPConfig(d_out=132, fast_in=4, fast_out=5, fast_reps=1, out_basis=12)
    model = GatedFWP(cfg)
    assert model.fast_dec.out_features == 12
    assert model.basis.shape == (132, 12)
    # modes are orthogonal with equal norm, so the decoder is well conditioned
    gram = model.basis.T @ model.basis
    assert torch.allclose(gram, torch.eye(12) * gram[0, 0], atol=1e-3)
    y = model(torch.randn(3, 20, 1))
    assert y.shape == (3, 132)
    # 12 modes cannot produce month-to-month jitter: the forecast is band-limited
    spectrum = torch.fft.rfft(y - y.mean(1, keepdim=True), dim=1).abs()
    assert spectrum[:, 40:].max() < 0.05 * spectrum.max()
    y.sum().backward()


def test_float64_tokens_remove_rounding_noise():
    """6th-order differences of a smooth series are mostly rounding noise in
    float32; forming them in float64 recovers the true signal."""
    import numpy as np
    from qkanfwp import data
    from qkanfwp.models import Tokenizer

    s64 = data.load_series("bessel", dtype=np.float64)
    x64 = torch.tensor(s64)[None, :, None]
    exact = np.diff(s64, 6)
    for dtype, tol in (("float32", None), ("float64", 1e-4)):
        tok = Tokenizer(1, 7, "diff", dtype=dtype)
        d6 = tok(x64 if dtype == "float64" else x64.float())[0, 6:, 6].double().numpy()
        err = np.std(d6 - exact) / np.std(exact)
        if tol is None:
            assert err > 0.3  # float32: noise dominated
        else:
            assert err < tol
    assert tok(x64).dtype == torch.float32


def test_cycle_anchor_read_out():
    torch.manual_seed(0)
    cfg = FWPConfig(d_out=24, fast_in=3, fast_out=4, fast_reps=1, skip="cycle", skip_smooth=5)
    model = GatedFWP(cfg)
    x = torch.randn(2, 60, 1)
    y = model(x)
    # zero-initialised decoder: the untrained model is exactly the seasonal-naive forecast
    anchor = model.cycle_anchor(x)
    assert torch.allclose(y, anchor)
    # interior points are a centred 5-point average of the last 24 inputs
    s = x[..., 0]
    k = 60 - 24 + 10
    assert torch.allclose(anchor[:, 10], s[:, k - 2 : k + 3].mean(1), atol=1e-6)
    # the last point only averages observed values (no look-ahead)
    assert torch.allclose(anchor[:, -1], s[:, -3:].mean(1), atol=1e-6)
    y.sum().backward()
    assert model.fast_dec.weight.grad.abs().sum() > 0


def test_write_first_uses_the_newest_token():
    torch.manual_seed(0)
    x = torch.randn(2, 9, 1)
    x2 = x.clone()
    x2[:, -1] += 1.0
    model = GatedFWP(FWPConfig(write_first=True, gate="group", gate_groups="edge"))
    w, w2 = model.fast_weights(model.tokens(x)), model.fast_weights(model.tokens(x2))
    assert not torch.allclose(w, w2)  # the last step now writes before the read
    # and it is still Eq. 3 applied step by step, over all T tokens
    tok = model.tokens(x)
    proposals, gate = model.split_slow(model.slow(tok))
    assert torch.allclose(w, gated_recursion(proposals, gate, None, model.group_index), atol=1e-5)
    assert model.memory_kernel(x).shape[1] == 9
    assert GatedFWP(FWPConfig(write_first=True))(x[:, :1]).shape == (2, 1)  # a single token still works


def test_authors_model_has_the_structure_of_the_released_code():
    """159 trainable parameters as in the paper; the slow QKAN (SiLU base term
    with trainable weights) equals the layer of the qkan package; the closed
    form equals the write-then-read recursion theta_t = (1-g) A_t (x) B_t + g theta_{t-1}."""
    import qkan
    import torch.nn.functional as F

    from qkanfwp.authors import AuthorsFWP
    from qkanfwp.daruan import daruan_pz

    torch.manual_seed(0)
    m = AuthorsFWP(hidden_size=8)
    assert count_parameters(m) == 159
    ref = qkan.QKAN(width=[3, 3], reps=1, ba_trainable=True)
    with torch.no_grad():
        m.slow.theta.copy_(ref.layers[0].theta)
        m.slow_base.copy_(ref.layers[0].base_weight)
        h = torch.randn(7, 3)
        mine = daruan_pz(h, m.slow.theta).sum(-1) + F.silu(h) @ m.slow_base.T
        assert torch.allclose(mine, ref(h), atol=1e-5)
        x = torch.randn(4, 12, 1)
        a, b, g = m.slow_programmer(x)
        theta = torch.zeros(4, 3, 3, 2, 2)
        for t in range(12):
            gg = g[:, t].view(-1, 1, 1, 1, 1)
            theta = (1 - gg) * torch.einsum("bld,bqe->blqde", a[:, t], b[:, t]) + gg * theta
        assert torch.allclose(theta, m.fast_angles(x), atol=1e-6)
        # write-then-read: the last token changes the angles it is read with
        x2 = x.clone()
        x2[:, -1] += 0.5
        assert not torch.allclose(m.fast_angles(x2), m.fast_angles(x), atol=1e-4)
        assert abs(float(torch.sigmoid(m.gate.bias)) - 0.8808) < 1e-3


def test_authors_datasets_follow_the_released_generators():
    import numpy as np

    from qkanfwp import data

    lengths = {"c_bessel": 256, "c_shm": 240, "c_dqc": 2200, "c_jc": 3000, "c_narma5": 300, "c_narma10": 300}
    for name, n in lengths.items():
        inp, tgt = data.code_series(name)
        assert len(inp) == len(tgt) == n
        x, y = data.code_windows(name, 16)
        assert x.shape == (n - 17, 16, 1) and y.shape == (n - 17, 1)  # the authors' loop drops the last window
        assert np.allclose(x[5, :, 0], inp[5:21], atol=1e-6) and np.allclose(y[5, 0], tgt[21], atol=1e-6)
        tr, te = data.code_split(len(x))
        assert len(tr) == int(0.8 * len(x)) and tr[-1] + 1 == te[0]
    # NARMA: the window holds the drive u, the target is y, neither is rescaled
    u, y = data.code_series("c_narma10")
    assert not np.allclose(u, y) and u.max() < 0.2 and abs(y[0] - 0.196) < 1e-12
    k = 50
    assert abs(y[k + 1] - (0.3 * y[k] + 0.05 * y[k] * y[k - 9 : k + 1].sum() + 1.5 * u[k - 9] * u[k] + 0.1)) < 1e-12
    for name in ("c_bessel", "c_shm", "c_dqc", "c_jc"):
        s, _ = data.code_series(name)
        assert abs(s.min() + 1) < 1e-12 and abs(s.max() - 1) < 1e-12
