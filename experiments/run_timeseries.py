"""One-step time-series benchmarks (paper Sec. 6.1).

Protocols
---------
paper : 80 % train / 20 % test (chronological), 50 epochs, batch 4, Adam 1e-3,
        report the final-epoch test MSE.  This is the paper's protocol.
dev   : 70 % train / 10 % validation / 20 % test.  Used only for design
        decisions (model selection on the validation split).

Results are appended to a JSON-lines file; finished jobs are skipped on rerun.
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

# ---------------------------------------------------------------------------
# Model variants.  ``model`` entries override FWPConfig fields; ``train``
# entries override fit() arguments.  ``kind`` selects a non-FWP control model.
# ---------------------------------------------------------------------------
# Baseline architecture.  The paper does not list layer sizes, so five
# ~160-parameter GQKAN-QKANFWP layouts were compared on the validation split
# (results/dev_baseline_arch.jsonl); this one was the strongest and is used as
# the baseline for everything else.
ARCH = dict(slow_hidden=3, slow_latent=3, slow_reps=3, fast_in=2, fast_out=1, fast_reps=3)


def fwp(*mods, train=None, **kw):
    cfg = dict(ARCH)
    for m in mods:
        cfg.update(m)
    cfg.update(kw)
    return dict(model=cfg, train=train or {})


MTG = dict(gate="group", gate_groups="layer", gate_init="chrono")
CTX = dict(context=3)
SKIP = dict(skip="last")
COS = dict(schedule="cosine")

VARIANTS = {
    # ---- baseline layout candidates (all scalar-gated GQKAN-QKANFWP) --------
    "arch_h6l3r1": dict(model={}),  # 159 parameters, as counted in the paper's Table 2
    "arch_r3": dict(model=ARCH),
    "arch_h4l4r1": dict(model=dict(slow_hidden=4, slow_latent=4)),
    "arch_f2": dict(model=dict(slow_hidden=4, slow_latent=3, fast_reps=2)),
    "arch_exactz": dict(model=dict(fast_measure=False)),
    # ---- paper models -------------------------------------------------------
    "base": fwp(),  # GQKAN-QKANFWP with the paper's scalar gate
    "ungated": fwp(gate="none"),
    # ---- single extensions --------------------------------------------------
    "chrono": fwp(gate_init="chrono"),  # scalar gate + chrono bias
    "mtg_edge": fwp(MTG, gate_groups="edge"),
    "mtg_layer_plain": fwp(gate="group", gate_groups="layer"),  # group gates, default init
    "mtg": fwp(MTG),  # group gates per (circuit, re-upload layer) + chrono init
    "mtg_param": fwp(MTG, gate_groups="param"),
    "ctx2": fwp(context=2),
    "ctx3": fwp(CTX),
    "ctx4": fwp(context=4),
    "skip": fwp(SKIP),
    "cos": fwp(train=COS),
    # ---- combinations -------------------------------------------------------
    "full": fwp(MTG, CTX, SKIP, train=COS),
    "full-mtg": fwp(CTX, SKIP, train=COS),
    "full-ctx": fwp(MTG, SKIP, train=COS),
    "full-skip": fwp(MTG, CTX, train=COS),
    "full-cos": fwp(MTG, CTX, SKIP),
    # parameter-budget controls: a smaller full model and a larger baseline
    "full_pm": fwp(MTG, CTX, SKIP, slow_latent=2, train=COS),
    "base_big": fwp(slow_latent=4),
    # ---- controls -----------------------------------------------------------
    "ar_hqkan": dict(kind="ar", model=dict(context=3, hidden=4, latent=4, reps=3, skip="last"), train=COS),
    "lstm": dict(kind="lstm", model=dict(hidden=5)),
    "lstm_cos": dict(kind="lstm", model=dict(hidden=5), train=COS),
    # ---- other paper variants (Table 1) and their extended versions ----------
    "gqkan_fwp": fwp(fast="linear", fast_out=3),
    "gqkan_fwp_full": fwp(MTG, CTX, SKIP, fast="linear", fast_out=3, gate_groups="node", train=COS),
    "g_qkanfwp": fwp(slow="mlp", slow_hidden=8),
    "g_qkanfwp_full": fwp(MTG, CTX, SKIP, slow="mlp", slow_hidden=8, train=COS),
}


def run_job(job: dict) -> dict:
    import numpy as np
    import torch

    torch.set_num_threads(1)
    from qkanfwp import data
    from qkanfwp.models import ARHQKAN, FWPConfig, GatedFWP, LSTMBaseline, count_parameters
    from qkanfwp.train import fit

    spec = VARIANTS[job["variant"]]
    series = data.load_series(job["dataset"])
    x, y = data.make_windows(series, job["window"])
    x, y = torch.tensor(x), torch.tensor(y)
    if job["protocol"] == "paper":
        tr, te = data.chrono_split(len(x), (0.8, 0.2))
        evals = {"train": (x[tr], y[tr]), "test": (x[te], y[te])}
    else:
        tr, va, te = data.chrono_split(len(x), (0.7, 0.1, 0.2))
        evals = {"train": (x[tr], y[tr]), "val": (x[va], y[va]), "test": (x[te], y[te])}

    torch.manual_seed(job["seed"])
    np.random.seed(job["seed"])
    kind = spec.get("kind", "fwp")
    if kind == "fwp":
        model = GatedFWP(FWPConfig(max_len=job["window"], **spec["model"]))
    elif kind == "ar":
        model = ARHQKAN(**spec["model"])
    elif kind == "lstm":
        model = LSTMBaseline(**spec["model"])
    else:
        raise ValueError(kind)

    train_kw = dict(epochs=job["epochs"], batch_size=4, lr=1e-3, seed=job["seed"], eval_every=5)
    train_kw.update(spec.get("train", {}))
    res = fit(model, (x[tr], y[tr]), evals, **train_kw)
    return dict(
        job,
        params=count_parameters(model),
        final=res["final"],
        history={k: v for k, v in res["history"].items() if k != "train_loss"},
        seconds=round(res["seconds"], 2),
    )


def key(job: dict) -> tuple:
    return tuple(job[k] for k in ("dataset", "window", "variant", "seed", "protocol", "epochs"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", nargs="+", default=["bessel", "shm", "narma5", "narma10", "dqc", "jc"])
    ap.add_argument("--windows", nargs="+", type=int, default=[8, 16, 32, 64])
    ap.add_argument("--variants", nargs="+", required=True)
    ap.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2, 3, 4])
    ap.add_argument("--protocol", choices=["paper", "dev"], default="paper")
    ap.add_argument("--epochs", type=int, default=50)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    args = ap.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out.exists():
        for line in out.read_text().splitlines():
            done.add(key(json.loads(line)))
    jobs = [
        dict(dataset=d, window=w, variant=v, seed=s, protocol=args.protocol, epochs=args.epochs)
        for d, w, v, s in itertools.product(args.datasets, args.windows, args.variants, args.seeds)
    ]
    jobs = [j for j in jobs if key(j) not in done]
    # long jobs (jc, large windows) first so the pool stays balanced
    jobs.sort(key=lambda j: -(3000 if j["dataset"] == "jc" else 300) * (8 + j["window"]))
    print(f"{len(jobs)} jobs to run ({len(done)} already done)", flush=True)
    with get_context("spawn").Pool(args.workers) as pool, out.open("a") as fh:
        for i, res in enumerate(pool.imap_unordered(run_job, jobs), 1):
            fh.write(json.dumps(res) + "\n")
            fh.flush()
            if i % 20 == 0 or i == len(jobs):
                print(f"[{i}/{len(jobs)}] last: {res['dataset']} N={res['window']} {res['variant']} "
                      f"seed={res['seed']} test={res['final']['test']:.2e} ({res['seconds']}s)", flush=True)


if __name__ == "__main__":
    main()
