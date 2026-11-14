"""Finite-shot sensitivity of the observable-memory FWP, the gated FWP and the static HQKAN.

On hardware every expectation value is estimated from a finite number of
shots.  The observable-memory read-out solves a linear system built from
measured features, so measurement noise can be amplified when the learned
prior precision is small.  This script trains each model twice - with exact
expectations, and "noise-aware" with ``--train-shots`` during training - and
evaluates the test MSE as a function of the shot budget.

Shot accounting (qkanfwp/daruan.py): the budget ``S`` is per circuit and per
input (one edge, one token).  A circuit read out in the Z basis spends all S
shots there; QKAN-FWP-O needs <X>, <Y> and <Z> of every circuit, which do not
commute, so each basis gets floor(S / 3) shots.  Outcomes are drawn from the
exact binomial distribution.  Because the models run different numbers of
circuits per prediction, every record also stores ``circuit_runs`` (circuit
evaluations per prediction); total shots per prediction = circuit_runs * S.

For QKAN-FWP-O the record also holds the condition number of the Gram matrix
``C_T`` of the read-out solve (median over the test windows) at every budget.

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


def circuit_runs(model, window: int) -> int:
    """Single-qubit circuit evaluations needed for one prediction."""
    from qkanfwp.models import ARHQKAN, GatedFWP
    from qkanfwp.obsmem import ObservableMemoryFWP

    if isinstance(model, ObservableMemoryFWP):
        c = model.cfg
        tokens = max(window - c.context, 0) + 1  # complete context tokens + the query
        return c.hidden * tokens * (3 if c.tangent else 1) if c.quantum else 0
    if isinstance(model, ARHQKAN):
        q = model.net.qkan
        return q.in_dim * q.out_dim  # one token
    if isinstance(model, GatedFWP):
        c = model.cfg
        slow = model.slow.qkan.in_dim * model.slow.qkan.out_dim if c.slow == "hqkan" else 0
        fast = c.fast_in * c.fast_out if c.fast == "hqkan" else 0
        return slow * (window if c.write_first else window - 1) + fast
    raise TypeError(type(model))


def run_job(job: dict) -> dict:
    import numpy as np
    import torch

    torch.set_num_threads(1)
    from qkanfwp import daruan, data
    from qkanfwp.models import count_parameters
    from qkanfwp.obsmem import ObservableMemoryFWP
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
    out, cond = {}, {}
    for shots in EVAL_SHOTS:
        daruan.set_shots(shots)
        torch.manual_seed(1000 + job["seed"])
        key_ = "inf" if shots is None else f"{shots:g}"
        reps = 1 if shots is None else 5
        out[key_] = float(np.mean([mse(model, *te) for _ in range(reps)]))
        if isinstance(model, ObservableMemoryFWP):
            c = model.gram_matrix(te[0][:512]).double()
            cond[key_] = float(torch.linalg.cond(c).median())
    daruan.set_shots(None)
    return dict(job, params=count_parameters(model), circuit_runs=circuit_runs(model, job["window"]), test=out, cond=cond)


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
