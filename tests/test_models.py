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
