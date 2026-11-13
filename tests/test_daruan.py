"""Check the functional DARUAN against the official ``qkan`` package."""

import pytest
import torch

from qkanfwp.daruan import QKANLayer, daruan_pz, fast_qkan_layer

qkan = pytest.importorskip("qkan")
from qkan.solver.exact import torch_exact_solver  # noqa: E402


@pytest.mark.parametrize("reps", [1, 2, 3, 5])
@pytest.mark.parametrize("fast_measure", [True, False])
def test_matches_official_solver(reps, fast_measure):
    torch.manual_seed(0)
    batch, in_dim, out_dim = 7, 3, 4
    x = torch.randn(batch, in_dim)
    theta = torch.randn(out_dim, in_dim, reps + 1, 2)
    w = torch.ones(out_dim, in_dim, reps)
    b = torch.zeros(out_dim, in_dim, reps)
    ref = torch_exact_solver(
        x, theta, w, b, reps, ansatz="pz_encoding", out_dim=out_dim,
        preacts_trainable=False, fast_measure=fast_measure,
    )
    out = daruan_pz(x, theta, fast_measure=fast_measure)
    assert torch.allclose(out, ref, atol=1e-5), (out - ref).abs().max()


def test_matches_official_solver_trainable_preacts():
    torch.manual_seed(1)
    batch, in_dim, out_dim, reps = 5, 2, 3, 3
    x = torch.randn(batch, in_dim)
    theta = torch.randn(out_dim, in_dim, reps + 1, 2)
    w = torch.randn(out_dim, in_dim, reps)
    b = torch.randn(out_dim, in_dim, reps)
    ref = torch_exact_solver(
        x, theta, w, b, reps, ansatz="pz_encoding", out_dim=out_dim,
        preacts_trainable=True,
    )
    out = daruan_pz(x, theta, w, b)
    assert torch.allclose(out, ref, atol=1e-5)


def test_matches_official_layer():
    torch.manual_seed(2)
    layer = qkan.QKANLayer(3, 4, reps=3, ba_trainable=False)
    mine = QKANLayer(3, 4, reps=3)
    with torch.no_grad():
        mine.theta.copy_(layer.theta)
    x = torch.randn(6, 3)
    assert torch.allclose(mine(x), layer(x), atol=1e-5)


def test_per_sample_theta_equals_shared_theta():
    torch.manual_seed(3)
    batch, in_dim, out_dim, reps = 5, 2, 3, 2
    x = torch.randn(batch, in_dim)
    theta = torch.randn(batch, out_dim, in_dim, reps + 1, 2)
    out = fast_qkan_layer(x, theta.reshape(batch, -1), in_dim, out_dim, reps)
    for i in range(batch):
        ref = daruan_pz(x[i : i + 1], theta[i]).sum(-1)
        assert torch.allclose(out[i : i + 1], ref, atol=1e-6)
