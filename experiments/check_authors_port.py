"""Direct numerical comparison of qkanfwp.authors.AuthorsFWP with the authors' own module.

Needs a checkout of https://github.com/MatthewPeng57/Gated-QKAN-FWP and its
dependencies (``qkan``); the weights of a freshly initialised model of that
repository are copied into the port and the outputs are compared.

    python experiments/check_authors_port.py /path/to/Gated-QKAN-FWP/times_series_benchmark

This script runs the authors' code, so it is not part of the test suite; the
tests check the port against the ``qkan`` package and the recursion instead
(tests/test_models.py).
"""

import sys
import types
from pathlib import Path

import numpy
import torch

if len(sys.argv) != 2:
    sys.exit(__doc__)
# the authors' model file imports pennylane.numpy only for ceil / log2
sys.modules.setdefault("pennylane", types.SimpleNamespace(numpy=numpy))
sys.modules.setdefault("pennylane.numpy", numpy)
sys.path.insert(0, sys.argv[1])
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.models.gqkan_qkanfwp import FWP, FWPCell  # noqa: E402

from qkanfwp.authors import AuthorsFWP  # noqa: E402

torch.manual_seed(0)
cell = FWPCell(1, 8, 1, 2).float()
ref = FWP(cell, "cpu").float()
mine = AuthorsFWP(hidden_size=8)
enc = cell.slow_program_encoder
with torch.no_grad():
    mine.enc_in.load_state_dict(enc[0].state_dict())
    mine.slow.theta.copy_(enc[1].layers[0].theta)
    mine.slow_base.copy_(enc[1].layers[0].base_weight)
    mine.enc_out.load_state_dict(enc[2].state_dict())
    mine.head_a.load_state_dict(cell.theta_head_A.state_dict())
    mine.head_b.load_state_dict(cell.theta_head_B.state_dict())
    mine.prelinear.load_state_dict(cell.prelinear.state_dict())
    mine.post.load_state_dict(cell.post_processing.state_dict())
    mine.gate.load_state_dict(cell.fast_gate.state_dict())
    for t in (4, 16, 64):
        x = torch.rand(6, t, 1) * 2 - 1
        a, b = ref(x)[-1], mine(x)
        print(f"T = {t}: max |authors - port| = {(a - b).abs().max().item():.2e} (mean |output| {a.abs().mean().item():.2e})")
