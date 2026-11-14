"""Cost of the read-out of QKAN-FWP-O: closed-form least squares against the
sequential delta rule and the static model.

Per window of T complete context pairs and F features:

  least squares  O(T F^2) to accumulate the gated statistics + one O(F^3) solve
                 (O(T F^3) if a prediction is wanted after every step: the prior
                 that is re-injected at every write is a full-rank update, so
                 the O(F^2) Sherman-Morrison recursion of exponentially weighted
                 RLS does not apply)
  delta rule     O(T F), no matrix
  static         O(F)

The script times the forward pass (features included) on one CPU thread and
writes results/cost.json.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from qkanfwp.obsmem import ObservableMemoryFWP, ObsMemConfig  # noqa: E402


def main():
    torch.set_num_threads(1)
    torch.manual_seed(0)
    out = []
    for window in (16, 64, 256):
        x = (0.1 * torch.randn(256, window, 1, dtype=torch.float64)).cumsum(1)
        for memory in ("none", "delta", "ls"):
            model = ObservableMemoryFWP(ObsMemConfig(context=8, hidden=6, reps=1, memory=memory, max_len=window))
            model.fit_token_scale(x)
            with torch.no_grad():
                model(x)
                times = []
                for _ in range(7):
                    t0 = time.perf_counter()
                    model(x)
                    times.append(time.perf_counter() - t0)
                # the part that depends on the memory rule: everything after the features
                _, k, y_ctx, valid = model.context_pairs(x)
                mem = []
                for _ in range(7):
                    t0 = time.perf_counter()
                    model.fast_observable(k[:, :-1], y_ctx, valid)
                    mem.append(time.perf_counter() - t0)
            row = dict(window=window, pairs=window - 8, features=model.n_feat, memory=memory,
                       ms_per_1000_windows=1e3 * sorted(times)[3] / len(x) * 1e3,
                       memory_ms_per_1000_windows=1e3 * sorted(mem)[3] / len(x) * 1e3)
            out.append(row)
            print(row, flush=True)
    Path("results/cost.json").write_text(json.dumps(out))


if __name__ == "__main__":
    main()
