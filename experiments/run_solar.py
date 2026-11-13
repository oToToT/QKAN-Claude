"""Solar-cycle direct multi-step forecasting (paper Sec. 6.2).

Protocol (from the paper): SILSO monthly mean total sunspot number, 3,326
records (1749-01 .. 2026-02) min-max scaled to [0, 1]; 528-month input ->
132-month forecast; chronological 80/10/10 split of the sliding windows;
peak-aware loss  L = (1/B) sum (y - yhat)^2 (1 + alpha y), alpha = 1;
batch 32, 100 epochs, Adam; the checkpoint with the lowest validation loss is
evaluated on the test split.  Metrics: scaled MSE, peak amplitude error (PAE,
in sunspot-number units) and peak timing error (PTE, months).
"""

from __future__ import annotations

import argparse
import copy
import itertools
import json
import math
import os
import sys
import time
from multiprocessing import get_context
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

WINDOW, HORIZON = 528, 132

# GQKAN-QKANFWP at the paper's scale: 200 single-qubit DARUAN circuits in the
# fast programmer (10 -> 20, reps 1 => 800 fast angles), 12,423 parameters
# (paper: 12,474).
BASE = dict(
    d_out=HORIZON, slow_hidden=10, slow_latent=10, slow_reps=3,
    fast_in=10, fast_out=20, fast_reps=1, max_len=WINDOW,
)
MTG = dict(gate="group", gate_groups="node", gate_init="chrono")

VARIANTS = {
    "base": dict(model=BASE),
    "ungated": dict(model={**BASE, "gate": "none"}),
    "chrono": dict(model={**BASE, "gate_init": "chrono"}),
    "mtg": dict(model={**BASE, **MTG}),
    "ctx12": dict(model={**BASE, "context": 12}),
    "ctx12s12": dict(model={**BASE, "context": 12, "stride": 12}),
    "skip": dict(model={**BASE, "skip": "mean"}),
    "cos": dict(model=BASE, train=dict(schedule="cosine")),
    "mtg_ctx12": dict(model={**BASE, **MTG, "context": 12}),
    "mtg_ctx12s12": dict(model={**BASE, **MTG, "context": 12, "stride": 12}),
    "full": dict(model={**BASE, **MTG, "context": 12, "skip": "mean"}, train=dict(schedule="cosine")),
    "full_s12": dict(model={**BASE, **MTG, "context": 12, "stride": 12, "skip": "mean"}, train=dict(schedule="cosine")),
    # LSTM-S of the paper: LSTM(64) -> BatchNorm -> Dropout(0.3) -> Linear, 25,860 parameters
    "lstm_s": dict(kind="lstm", model=dict(hidden=64)),
}


def resolve(name: str) -> dict:
    """``"<variant>@cos5"`` / ``"<variant>@lr5"``: cosine schedule from (or a
    constant) learning rate of 5e-3 instead of the ``--lr`` default."""
    if "@" not in name:
        return VARIANTS[name]
    base, tag = name.split("@")
    spec = dict(VARIANTS[base])
    kind, value = (tag[:3], tag[3:]) if tag.startswith("cos") else (tag[:2], tag[2:])
    train = dict(spec.get("train") or {})
    train.update(lr=float(value) * 1e-3, schedule="cosine" if kind == "cos" else "constant")
    spec["train"] = train
    return spec


def build(spec):
    import torch
    from torch import nn

    from qkanfwp.models import FWPConfig, GatedFWP

    if spec.get("kind", "fwp") == "fwp":
        return GatedFWP(FWPConfig(**spec["model"]))

    class LSTMForecaster(nn.Module):
        def __init__(self, hidden):
            super().__init__()
            self.lstm = nn.LSTM(1, hidden, batch_first=True)
            self.bn = nn.BatchNorm1d(hidden)
            self.drop = nn.Dropout(0.3)
            self.head = nn.Linear(hidden, HORIZON)

        def forward(self, x):
            out, _ = self.lstm(x)
            return self.head(self.drop(self.bn(out[:, -1])))

    return LSTMForecaster(**spec["model"])


def run_job(job: dict) -> dict:
    import numpy as np
    import torch

    torch.set_num_threads(job.get("threads", 1))
    from qkanfwp import data
    from qkanfwp.models import count_parameters

    spec = resolve(job["variant"])
    raw, scaled, (lo, hi) = data.load_sunspots()
    x, y = data.make_windows(scaled, WINDOW, HORIZON)
    x, y = torch.tensor(x), torch.tensor(y)
    tr, va, te = data.chrono_split(len(x), (0.8, 0.1, 0.1))

    torch.manual_seed(job["seed"])
    np.random.seed(job["seed"])
    model = build(spec)
    tkw = dict(lr=job["lr"], schedule="constant")
    tkw.update(spec.get("train", {}))
    alpha = 1.0

    def peak_loss(pred, target):
        return (((pred - target) ** 2) * (1.0 + alpha * target)).sum() / len(pred)

    @torch.no_grad()
    def evaluate(idx):
        model.eval()
        preds = torch.cat([model(x[idx[i : i + 256]]) for i in range(0, len(idx), 256)])
        tgt = y[idx]
        scale = hi - lo
        return dict(
            loss=peak_loss(preds, tgt).item(),
            mse=((preds - tgt) ** 2).mean().item(),
            pae=((tgt.max(1).values - preds.max(1).values).abs() * scale).mean().item(),
            pte=(tgt.argmax(1) - preds.argmax(1)).abs().float().mean().item(),
        )

    opt = torch.optim.Adam(model.parameters(), lr=tkw["lr"])
    steps = job["epochs"] * math.ceil(len(tr) / 32)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, steps) if tkw["schedule"] == "cosine" else None
    gen = torch.Generator().manual_seed(job["seed"])
    tr_t = torch.tensor(tr)
    best, best_state, val_curve = None, None, []
    t0 = time.time()
    for epoch in range(job["epochs"]):
        model.train()
        perm = tr_t[torch.randperm(len(tr_t), generator=gen)]
        for i in range(0, len(perm), 32):
            idx = perm[i : i + 32]
            if len(idx) < 2:
                continue  # BatchNorm needs more than one sample
            loss = peak_loss(model(x[idx]), y[idx])
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            if sched is not None:
                sched.step()
        val = evaluate(va)
        val_curve.append(val["loss"])
        if best is None or val["loss"] < best["loss"]:
            best = dict(val, epoch=epoch + 1)
            best_state = copy.deepcopy(model.state_dict())
    final_test = evaluate(te)
    model.load_state_dict(best_state)
    if job.get("save_dir"):
        # keep the test forecasts (and the learned memory kernel of the last
        # test window) of the selected checkpoint for the report figures
        model.eval()
        with torch.no_grad():
            preds = torch.cat([model(x[te[i : i + 256]]) for i in range(0, len(te), 256)]).numpy()
            extra = {}
            if hasattr(model, "memory_kernel") and model.n_gates:
                extra["kernel"] = model.memory_kernel(x[te[-1:]])[0].numpy().astype(np.float32)
                extra["stride"] = np.array(model.cfg.stride)
        save_dir = Path(job["save_dir"])
        save_dir.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(save_dir / f"{job['variant']}_seed{job['seed']}.npz",
                            preds=preds.astype(np.float16), test_index=te, **extra)
    return dict(
        job,
        params=count_parameters(model),
        val=best,
        test=evaluate(te),  # at the best-validation checkpoint (paper protocol)
        test_final=final_test,  # at the last epoch
        val_curve=val_curve,
        seconds=round(time.time() - t0, 1),
    )


def key(job):
    return (job["variant"], job["seed"], job["lr"], job["epochs"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants", nargs="+", required=True)
    ap.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2, 3, 4])
    ap.add_argument("--lr", type=float, default=2.5e-3)
    ap.add_argument("--epochs", type=int, default=100)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--save-dir", default=None, help="directory for test forecasts (.npz)")
    args = ap.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    done = {key(json.loads(line)) for line in out.read_text().splitlines()} if out.exists() else set()
    jobs = [
        dict(variant=v, seed=s, lr=args.lr, epochs=args.epochs, threads=args.threads, save_dir=args.save_dir)
        for v, s in itertools.product(args.variants, args.seeds)
    ]
    jobs = [j for j in jobs if key(j) not in done]
    print(f"{len(jobs)} jobs to run ({len(done)} already done)", flush=True)
    with get_context("spawn").Pool(args.workers) as pool, out.open("a") as fh:
        for res in pool.imap_unordered(run_job, jobs):
            fh.write(json.dumps(res) + "\n")
            fh.flush()
            print(f"{res['variant']} seed={res['seed']} params={res['params']} best_ep={res['val']['epoch']} "
                  f"val={res['val']['mse']:.4f} test_mse={res['test']['mse']:.4f} pae={res['test']['pae']:.1f} "
                  f"pte={res['test']['pte']:.1f} ({res['seconds']}s)", flush=True)


if __name__ == "__main__":
    main()
