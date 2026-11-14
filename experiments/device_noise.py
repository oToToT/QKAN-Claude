"""Static device errors at test time: does the in-context write calibrate them away?

Every model is trained once with ideal circuits and exact expectation values.
At test time a static error is switched on in every circuit (qkanfwp/daruan.py):

* ``readout``  read-out assignment errors P(read 1 | 0) = e and P(read 0 | 1) = 2e:
               every measured expectation v becomes (1 - 3e) v + e;
* ``depol``    depolarising noise of strength p: v becomes (1 - p) v;
* ``overrot``  every rotation angle (trainable and data-encoding) is executed
               as (1 + eps) * angle.

No retraining and no error mitigation.  A model with fixed read-out weights
sees features it was not trained on.  QKAN-FWP-O refits its measurement
operator inside every window from features measured on the same device, so an
error that maps the features affinely (read-out errors, depolarising noise) is
absorbed by the least-squares solve up to the influence of the prior; the
script measures how much of that survives with a short context.

The record of QKAN-FWP-O also stores the test MSE with the error present only
in the query circuits or only in the context circuits (``scope``), which
separates "the features changed" from "context and query changed together".

Only physical read-outs are compared: the baselines use <Z> ("+z" variants).
Expectation values are exact (no shot noise).
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

LEVELS = [0.0025, 0.005, 0.01, 0.02, 0.05]
KINDS = {
    "readout": lambda e: dict(e01=e, e10=2 * e),
    "depol": lambda e: dict(depolarizing=e),
    "overrot": lambda e: dict(over_rotation=e),
}


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
    fit(model, tr, {}, seed=job["seed"], eval_every=10**9, **tkw)

    is_om = isinstance(model, ObservableMemoryFWP)

    def scoped(scope: str, kw: dict) -> float:
        """Test MSE with the error in all circuits, or only in the query / context circuits."""
        if scope == "all":
            daruan.set_device(**kw)
            try:
                return mse(model, *te)
            finally:
                daruan.set_device()
        with torch.no_grad():
            s, k, y_ctx, valid = model.context_pairs(te[0])
            daruan.set_device(**kw)
            try:
                k_err = model.context_pairs(te[0])[1]
            finally:
                daruan.set_device()
            k = torch.cat([k_err[:, :-1], k[:, -1:]], 1) if scope == "context" else torch.cat([k[:, :-1], k_err[:, -1:]], 1)
            r = model.fast_observable(k[:, :-1], y_ctx, valid)
            pred = (k[:, -1] * r).sum(-1) * model.y_scale + s[:, -1].to(model.dtype)
            return float(((pred - te[1][:, 0]) ** 2).mean())

    out = {"ideal": mse(model, *te)}
    scopes = {}
    for kind, make in KINDS.items():
        out[kind] = {f"{e:g}": scoped("all", make(e)) for e in LEVELS}
        if is_om and model.cfg.memory != "none" and model.cfg.d_out == 1 and model.cfg.skip == "last":
            scopes[kind] = {sc: {f"{e:g}": scoped(sc, make(e)) for e in LEVELS} for sc in ("query", "context")}
    return dict(job, params=count_parameters(model), test=out, scope=scopes)


def key(job):
    return (job["task"], job["window"], job["variant"], job["seed"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", nargs="+", default=["bessel", "narma10", "dqc", "family:shm:0.02", "family:henon:0"])
    ap.add_argument("--window", type=int, default=16)
    ap.add_argument("--variants", nargs="+", required=True)
    ap.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    args = ap.parse_args()
    out = Path(args.out)
    done = {key(json.loads(line)) for line in out.read_text().splitlines()} if out.exists() else set()
    jobs = [dict(task=t, window=args.window, variant=v, seed=s)
            for t, v, s in itertools.product(args.tasks, args.variants, args.seeds)]
    jobs = [j for j in jobs if key(j) not in done]
    print(f"{len(jobs)} jobs to run ({len(done)} already done)", flush=True)
    with get_context("spawn").Pool(args.workers) as pool, out.open("a") as fh:
        for i, res in enumerate(pool.imap_unordered(run_job, jobs), 1):
            fh.write(json.dumps(res) + "\n")
            fh.flush()
            t = res["test"]
            print(f"[{i}/{len(jobs)}] {res['task']} {res['variant']} seed={res['seed']} ideal:{t['ideal']:.1e} "
                  + " ".join(f"{k}@0.01:{t[k]['0.01']:.1e}" for k in KINDS), flush=True)


if __name__ == "__main__":
    main()
