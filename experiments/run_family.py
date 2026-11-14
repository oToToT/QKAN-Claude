"""In-context forecasting on families of dynamical systems (qkanfwp/families.py).

Every sequence has its own physical parameters and the train / validation /
test splits contain different sequences, so a model must identify the system
from the window.  All neural models share one protocol: Adam, batch 32, cosine
schedule, the checkpoint with the lowest *validation* MSE is evaluated on test.

Closed-form references (no training):
  persist      y_hat = x_T
  lin_global   one linear AR(p) for all sequences (least squares on the training
               windows; p chosen on validation)
  lin_ctx      a separate ridge AR(q) fitted inside every window (q, the ridge
               strength and the use of an intercept chosen on validation) -
               the "in-context linear" oracle
  poly_ctx     the same with the quadratic features of two lags,
               [1, x_t, x_{t-1}, x_t^2, x_t x_{t-1}, x_{t-1}^2] (ridge strength
               chosen on validation) - exact for the Henon map without noise
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

CACHE = Path(__file__).resolve().parent.parent / "results" / "cache"


def load_family(name: str, window: int, noise: float):
    import numpy as np
    from qkanfwp.families import family_splits

    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"family_{name}_N{window}_noise{noise:g}.npz"
    if f.exists():
        z = np.load(f)
        return {k: (z[k + "_x"], z[k + "_y"]) for k in ("train", "val", "test")}
    sp = family_splits(name, window, noise)
    tmp = f.with_suffix(f".{os.getpid()}.tmp.npz")
    np.savez(tmp, **{k + "_x": v[0] for k, v in sp.items()}, **{k + "_y": v[1] for k, v in sp.items()})
    os.replace(tmp, f)
    return sp


# ---------------------------------------------------------------------------
def references(sp: dict) -> dict:
    import numpy as np

    out = {}
    # inputs in float64, targets rounded to float32: exactly what the neural models get
    (xtr, ytr), (xva, yva), (xte, yte) = ((sp[k][0].astype(np.float64), sp[k][1].astype(np.float32).astype(np.float64))
                                          for k in ("train", "val", "test"))
    xtr, xva, xte = xtr[..., 0], xva[..., 0], xte[..., 0]
    mse = lambda p, y: float(np.mean((p - y[:, 0]) ** 2))  # noqa: E731
    out["persist"] = dict(test=mse(xte[:, -1], yte), val=mse(xva[:, -1], yva), params=0)

    # one linear AR(p) for every sequence
    best = None
    for p in range(1, xtr.shape[1] + 1):
        a = np.c_[xtr[:, -p:], np.ones(len(xtr))]
        coef = np.linalg.lstsq(a, ytr[:, 0], rcond=None)[0]
        pred = lambda x: np.c_[x[:, -p:], np.ones(len(x))] @ coef  # noqa: E731
        v = mse(pred(xva), yva)
        if best is None or v < best["val"]:
            best = dict(val=v, test=mse(pred(xte), yte), params=p + 1, order=p)
    out["lin_global"] = best

    # a ridge AR(q) fitted inside every window, with or without an intercept
    def ctx_pred(x, q, lam, intercept):
        n, t = x.shape
        m = t - q  # in-window training pairs
        idx = np.arange(q)[None, :] + np.arange(m)[:, None]
        a = x[:, idx]  # (n, m, q): lags
        last = x[:, -q:]
        if intercept:
            a = np.concatenate([a, np.ones((n, m, 1))], -1)
            last = np.concatenate([last, np.ones((n, 1))], -1)
        b = x[:, q:]  # (n, m): next values
        g = np.einsum("nmi,nmj->nij", a, a) + lam * np.eye(a.shape[-1])
        coef = np.linalg.solve(g, np.einsum("nmi,nm->ni", a, b)[..., None])[..., 0]
        return np.einsum("ni,ni->n", last, coef)

    best = None
    for q in range(1, xtr.shape[1] // 2 + 1):
        for lam in 10.0 ** np.arange(-12, 1.0):
            for intercept in (False, True):
                v = mse(ctx_pred(xva, q, lam, intercept), yva)
                if best is None or v < best["val"]:
                    best = dict(val=v, test=mse(ctx_pred(xte, q, lam, intercept), yte), params=0, order=q,
                                ridge=float(lam), intercept=intercept)
    out["lin_ctx"] = best

    # quadratic features of two lags, ridge fitted inside every window
    def quad(a, b):  # a = x_t, b = x_{t-1}
        return np.stack([np.ones_like(a), a, b, a * a, a * b, b * b], -1)

    def poly_pred(x, lam):
        feats = quad(x[:, 1:-1], x[:, :-2])  # pairs (x_t, x_{t-1}) -> x_{t+1}, t = 1 .. T-2
        target = x[:, 2:]
        g = np.einsum("nmi,nmj->nij", feats, feats) + lam * np.eye(6)
        coef = np.linalg.solve(g, np.einsum("nmi,nm->ni", feats, target)[..., None])[..., 0]
        return np.einsum("ni,ni->n", quad(x[:, -1], x[:, -2]), coef)

    best = None
    for lam in 10.0 ** np.arange(-14, 1.0):
        v = mse(poly_pred(xva, lam), yva)
        if best is None or v < best["val"]:
            best = dict(val=v, test=mse(poly_pred(xte, lam), yte), params=0, ridge=float(lam))
    out["poly_ctx"] = best
    return out


def run_job(job: dict) -> dict:
    import numpy as np
    import torch

    torch.set_num_threads(1)
    from qkanfwp.models import count_parameters
    from qkanfwp.train import fit
    from run_timeseries import build_model, resolve

    sp = load_family(job["family"], job["window"], job["noise"])
    if job["variant"] == "refs":
        return dict(job, refs=references(sp))
    spec = resolve(job["variant"])
    data = {k: (torch.tensor(v[0]), torch.tensor(v[1], dtype=torch.float32)) for k, v in sp.items()}
    torch.manual_seed(job["seed"])
    np.random.seed(job["seed"])
    model = build_model(spec, job["window"], data["train"][0])
    train_kw = dict(epochs=job["epochs"], batch_size=32, lr=1e-2, schedule="cosine", seed=job["seed"],
                    eval_every=1, select_on="val")
    train_kw.update(spec.get("train", {}))
    res = fit(model, data["train"], data, **train_kw)
    return dict(job, params=count_parameters(model), final=res["final"], best=res["best"],
                seconds=round(res["seconds"], 2))


def best_lr(path: str) -> dict:
    """{cell: [variant@tag with the lowest mean validation MSE, one per model]}."""
    import numpy as np

    val = {}
    for line in Path(path).read_text().splitlines():
        r = json.loads(line)
        if "best" in r:
            val.setdefault((r["family"], r["window"], r["noise"]), {}).setdefault(
                r["variant"].partition("@")[0], {}).setdefault(r["variant"], []).append(r["best"]["val"])
    return {cell: [min(tags, key=lambda t: np.mean(tags[t])) for tags in models.values()]
            for cell, models in val.items()}


def key(job: dict) -> tuple:
    return tuple(job[k] for k in ("family", "window", "noise", "variant", "seed", "epochs"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--families", nargs="+", default=["shm", "tones", "jc", "henon", "duffing"])
    ap.add_argument("--windows", nargs="+", type=int, default=[16])
    ap.add_argument("--noise", nargs="+", type=float, default=[0.0])
    ap.add_argument("--variants", nargs="+", default=[])
    ap.add_argument("--best-lr-from", help="results file of a learning-rate sweep: run, for every cell and "
                    "model in it, only the '@' tag with the lowest validation MSE (averaged over its seeds)")
    ap.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    args = ap.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out.exists():
        for line in out.read_text().splitlines():
            done.add(key(json.loads(line)))
    jobs = []
    for f, w, nz, v in itertools.product(args.families, args.windows, args.noise, args.variants):
        for s in ([0] if v == "refs" else args.seeds):
            jobs.append(dict(family=f, window=w, noise=nz, variant=v, seed=s, epochs=0 if v == "refs" else args.epochs))
    if args.best_lr_from:
        for (f, w, nz), v in best_lr(args.best_lr_from).items():
            if f in args.families and w in args.windows and nz in args.noise:
                jobs += [dict(family=f, window=w, noise=nz, variant=name, seed=s, epochs=args.epochs)
                         for name in v for s in args.seeds]
    jobs = [j for j in jobs if key(j) not in done]
    print(f"{len(jobs)} jobs to run ({len(done)} already done)", flush=True)
    # build the data caches before the pool starts (JC / Duffing take a while)
    for f, w, nz in {(j["family"], j["window"], j["noise"]) for j in jobs}:
        load_family(f, w, nz)
    with get_context("spawn").Pool(args.workers) as pool, out.open("a") as fh:
        for i, res in enumerate(pool.imap_unordered(run_job, jobs), 1):
            fh.write(json.dumps(res) + "\n")
            fh.flush()
            if "refs" in res:
                print(f"[{i}/{len(jobs)}] {res['family']} N={res['window']} noise={res['noise']} refs: "
                      + ", ".join(f"{k}={v['test']:.2e}" for k, v in res["refs"].items()), flush=True)
            else:
                print(f"[{i}/{len(jobs)}] {res['family']} N={res['window']} noise={res['noise']} {res['variant']} "
                      f"seed={res['seed']} p={res['params']} val={res['best']['val']:.2e} test={res['best']['test']:.2e} "
                      f"({res['seconds']}s)", flush=True)


if __name__ == "__main__":
    main()
