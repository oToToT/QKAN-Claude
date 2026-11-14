"""Finite-shot sensitivity of the observable-memory FWP and of the earlier models.

On hardware every expectation value is estimated from a finite number of
shots.  The observable-memory read-out solves a linear system built from
measured features, so measurement noise can be amplified when the learned
prior precision is small.  This script trains each model twice - with exact
expectations, and "noise-aware" with ``--train-shots`` shots per expectation
during training - and evaluates the test MSE as a function of the shot count.

Only physical read-outs are compared: the baselines use <Z> ("+z" variants).
"""

from __future__ import annotations

import argparse
import itertools
import json
import os
import sys
from multiprocessing import get_context
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

EVAL_SHOTS = [1e2, 1e3, 1e4, 1e5, 1e6, None]


def run_job(job: dict) -> dict:
    import numpy as np
    import torch

    torch.set_num_threads(1)
    from qkanfwp import daruan, data
    from qkanfwp.models import count_parameters
    from qkanfwp.train import fit, mse
    from run_family import load_family
    from run_timeseries import build_model, resolve

    spec = resolve(job["variant"])
    if job["task"].startswith("family:"):
        _, fam, noise = job["task"].split(":")
        sp = load_family(fam, job["window"], float(noise))
        tr, te = ((torch.tensor(sp[k][0]), torch.tensor(sp[k][1], dtype=torch.float32)) for k in ("train", "test"))
        tkw = dict(epochs=40, batch_size=32, lr=1e-2, schedule="cosine")
    else:
        series = data.load_series(job["task"], dtype=np.float64)
        x, y = data.make_windows(series, job["window"])
        x, y = torch.tensor(x), torch.tensor(y, dtype=torch.float32)
        a, b = data.chrono_split(len(x), (0.8, 0.2))
        tr, te = (x[a], y[a]), (x[b], y[b])
        tkw = dict(epochs=50, batch_size=4, lr=1e-3)
    tkw.update(spec.get("train", {}))
    torch.manual_seed(job["seed"])
    np.random.seed(job["seed"])
    model = build_model(spec, job["window"], tr[0])
    daruan.set_shots(job["train_shots"])
    fit(model, tr, {}, seed=job["seed"], eval_every=10**9, **tkw)
    out = {}
    for shots in EVAL_SHOTS:
        daruan.set_shots(shots)
        torch.manual_seed(1000 + job["seed"])
        reps = 1 if shots is None else 5
        out["inf" if shots is None else f"{shots:g}"] = float(np.mean([mse(model, *te) for _ in range(reps)]))
    daruan.set_shots(None)
    return dict(job, params=count_parameters(model), test=out)


def key(job):
    return (job["task"], job["window"], job["variant"], job["seed"], job["train_shots"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", nargs="+", default=["bessel", "narma10", "dqc", "family:shm:0.02", "family:henon:0"])
    ap.add_argument("--window", type=int, default=16)
    ap.add_argument("--variants", nargs="+", required=True)
    ap.add_argument("--train-shots", nargs="+", type=float, default=[0, 1e4], help="0 = exact expectations")
    ap.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    args = ap.parse_args()
    out = Path(args.out)
    done = {key(json.loads(line)) for line in out.read_text().splitlines()} if out.exists() else set()
    jobs = [dict(task=t, window=args.window, variant=v, seed=s, train_shots=ts or None)
            for t, v, ts, s in itertools.product(args.tasks, args.variants, args.train_shots, args.seeds)]
    jobs = [j for j in jobs if key(j) not in done]
    print(f"{len(jobs)} jobs to run ({len(done)} already done)", flush=True)
    with get_context("spawn").Pool(args.workers) as pool, out.open("a") as fh:
        for i, res in enumerate(pool.imap_unordered(run_job, jobs), 1):
            fh.write(json.dumps(res) + "\n")
            fh.flush()
            print(f"[{i}/{len(jobs)}] {res['task']} {res['variant']} train_shots={res['train_shots']} seed={res['seed']} "
                  + " ".join(f"{k}:{v:.1e}" for k, v in res["test"].items()), flush=True)


if __name__ == "__main__":
    main()
