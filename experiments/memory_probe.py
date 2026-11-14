"""What the memory of QKAN-FWP-O uses: the learned weights ``beta_t`` of the
context pairs (paper Eq. 5), averaged over the test windows.

For every benchmark the model is trained with the paper split at window
N = 32 (24 complete context pairs) and the script records the mean weight of
each pair as a function of its age, the total weight ``sum_t beta_t``, the
effective number of pairs ``(sum beta)^2 / sum beta^2`` and the condition
number of the Gram matrix ``C_T`` of the read-out solve.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from qkanfwp import data  # noqa: E402
from qkanfwp.train import fit  # noqa: E402
from run_timeseries import build_model, resolve  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", nargs="+", default=["bessel", "shm", "narma5", "narma10", "dqc", "jc"])
    ap.add_argument("--variant", default="om_c0h6r1_p5@cos30")
    ap.add_argument("--window", type=int, default=32)
    ap.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    ap.add_argument("--out", default="results/memory_probe.json")
    args = ap.parse_args()
    torch.set_num_threads(1)
    out_path = Path(args.out)
    out = json.loads(out_path.read_text()) if out_path.exists() else {}
    spec = resolve(args.variant)
    for ds in args.datasets:
        if ds in out:
            continue
        series = data.load_series(ds, dtype=np.float64)
        x, y = data.make_windows(series, args.window)
        x, y = torch.tensor(x), torch.tensor(y, dtype=torch.float32)
        tr, te = data.chrono_split(len(x), (0.8, 0.2))
        runs = []
        for seed in args.seeds:
            torch.manual_seed(seed)
            np.random.seed(seed)
            model = build_model(spec, args.window, x[tr])
            kw = dict(epochs=50, batch_size=4, lr=1e-3, seed=seed, eval_every=50)
            kw.update(spec.get("train", {}))
            res = fit(model, (x[tr], y[tr]), {"test": (x[te], y[te])}, **kw)
            with torch.no_grad():
                _, k, _, valid = model.context_pairs(x[te])
                beta = model.memory_weights(k[:, :-1], valid)[:, valid[0]]  # complete pairs only, oldest first
                cond = torch.linalg.cond(model.gram_matrix(x[te]).double())
                prior = torch.exp(model.log_prior)
            runs.append(dict(
                seed=seed, test=res["final"]["test"],
                beta_by_age=beta.mean(0).flip(0).tolist(),  # index 0 = the most recent pair
                total_weight=beta.sum(1).mean().item(),
                effective_pairs=(beta.sum(1) ** 2 / (beta**2).sum(1)).mean().item(),
                n_pairs=beta.shape[1],
                cond_median=cond.median().item(), cond_max=cond.max().item(),
                prior_precision_median=prior.median().item(),
            ))
            print(ds, seed, f"test {runs[-1]['test']:.1e} effective pairs {runs[-1]['effective_pairs']:.1f} of {beta.shape[1]}", flush=True)
        out[ds] = runs
        out_path.write_text(json.dumps(out))


if __name__ == "__main__":
    main()
