"""Solar-cycle direct multi-step forecasting (paper Sec. 6.2).

Protocol (from the paper): SILSO monthly mean total sunspot number, 3,326
records (1749-01 .. 2026-02) min-max scaled to [0, 1]; 528-month input ->
132-month forecast; chronological 80/10/10 split of the sliding windows;
peak-aware loss  L = (1/B) sum (y - yhat)^2 (1 + alpha y), alpha = 1;
batch 32, 100 epochs, Adam; the checkpoint with the lowest validation loss is
evaluated on the test split.  Metrics: scaled MSE, peak amplitude error (PAE,
in sunspot-number units) and peak timing error (PTE, months).

Splitting the *windows* by index lets the 132-month targets of neighbouring
splits overlap by 131 months: the last validation targets lie after the first
test forecast origin, so choosing the checkpoint on validation looks ahead,
and the last training targets lie inside the validation period.  ``--purge``
removes the last 131 windows of the training and of the validation split, so
that every target of a split precedes the first forecast origin of the next
one (a split by target time).  Without the flag the split is the window-index
split described in the paper.

The authors' released code (https://github.com/MatthewPeng57/Gated-QKAN-FWP)
differs from the text of the paper in two respects that this runner can
reproduce: it trains on a file with 3,265 records that ends in 2021-01
(``--records 3265``; 2,606 windows, split 2084 / 260 / 262), and its model
(variant ``authors``, qkanfwp/authors.py) has a rank-one proposal, a
write-then-read order and a BatchNorm / Dropout read-out.
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
    # ---- parameter-matched variants (<= the 12,423-parameter baseline) -------
    # (a) pay for the gates by narrowing the slow latent 10 -> 9
    "mtg_pm": dict(model={**BASE, **MTG, "slow_latent": 9}),
    "mtg_y_pm": dict(model={**BASE, **MTG, "context": 12, "stride": 12, "slow_latent": 9}),
    # (b) smooth read-out: 132 free outputs -> K cosine modes over the horizon
    "base_b16": dict(model={**BASE, "out_basis": 16}),
    "base_b24": dict(model={**BASE, "out_basis": 24}),
    "mtg_b16": dict(model={**BASE, **MTG, "out_basis": 16}),
    "mtg_b24": dict(model={**BASE, **MTG, "out_basis": 24}),
    "mtg_b40": dict(model={**BASE, **MTG, "out_basis": 40}),
    "mtg_y_b16": dict(model={**BASE, **MTG, "context": 12, "stride": 12, "out_basis": 16}),
    "mtg_y_b24": dict(model={**BASE, **MTG, "context": 12, "stride": 12, "out_basis": 24}),
    "mtg_y_b40": dict(model={**BASE, **MTG, "context": 12, "stride": 12, "out_basis": 40}),
    # (c) seasonal residual read-out: forecast = smoothed last cycle + learned correction
    "base_cyc": dict(model={**BASE, "skip": "cycle"}),
    "base_cyc_b24": dict(model={**BASE, "skip": "cycle", "out_basis": 24}),
    "mtg_cyc_pm": dict(model={**BASE, **MTG, "slow_latent": 9, "skip": "cycle"}),
    "mtg_cyc_b24": dict(model={**BASE, **MTG, "skip": "cycle", "out_basis": 24}),
    # LSTM-S of the paper: LSTM(64) -> BatchNorm -> Dropout(0.3) -> Linear, 25,860 parameters
    "lstm_s": dict(kind="lstm", model=dict(hidden=64)),
    # GQKAN-QKANFWP as built and trained in the authors' released code (12,474 parameters): mean-reduced
    # peak-aware loss and the per-batch decay lr / (1 + 1e-6 step) of that code
    "authors": dict(kind="authors", model={}, train=dict(schedule="keras", loss="mean")),
}

# Observable-memory FWP (qkanfwp/obsmem.py) for direct multi-step forecasting:
# token = the last 11 yearly means; the pair written for month t is (token_t,
# the 132 months that followed t minus the smoothed previous cycle), for every
# third month t whose 132 successors lie inside the 528-month window (89 pairs).
OM = dict(context=11, pool=12, hidden=6, reps=1, d_out=HORIZON, anchor="cycle", out_basis=16,
          pair_stride=3, max_len=89, prior_init=1e-2)
OM_TRAIN = dict(grad_clip=1.0)
VARIANTS.update({
    "om": dict(kind="om", model=OM, train=OM_TRAIN),
    "om_static": dict(kind="om", model={**OM, "memory": "none"}, train=OM_TRAIN),  # no fast weights
    "om_gnone": dict(kind="om", model={**OM, "gate": "none"}, train=OM_TRAIN),  # ungated statistics
    "om_classical": dict(kind="om", model={**OM, "quantum": False}, train=OM_TRAIN),  # no Bloch features
    "om_last": dict(kind="om", model={**OM, "anchor": "last"}, train=OM_TRAIN),  # anchor = last value
    "om_b8": dict(kind="om", model={**OM, "out_basis": 8}, train=OM_TRAIN),
    "om_b24": dict(kind="om", model={**OM, "out_basis": 24}, train=OM_TRAIN),
    "om_h4": dict(kind="om", model={**OM, "hidden": 4}, train=OM_TRAIN),
    "om_h10": dict(kind="om", model={**OM, "hidden": 10}, train=OM_TRAIN),
    "om_c6": dict(kind="om", model={**OM, "context": 6}, train=OM_TRAIN),
    "om_c22p6": dict(kind="om", model={**OM, "context": 22, "pool": 6}, train=OM_TRAIN),
    "om_p1": dict(kind="om", model={**OM, "prior_init": 1e-1}, train=OM_TRAIN),
    "om_p4": dict(kind="om", model={**OM, "prior_init": 1e-4}, train=OM_TRAIN),
    "om_s1": dict(kind="om", model={**OM, "pair_stride": 1, "max_len": 265}, train=OM_TRAIN),
})


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
    from qkanfwp.obsmem import ObservableMemoryFWP, ObsMemConfig

    if spec.get("kind", "fwp") == "fwp":
        return GatedFWP(FWPConfig(**spec["model"]))
    if spec["kind"] == "om":
        return ObservableMemoryFWP(ObsMemConfig(**spec["model"]))
    if spec["kind"] == "authors":
        from qkanfwp.authors import AuthorsSolarFWP

        return AuthorsSolarFWP(**spec["model"])

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
    raw, scaled, (lo, hi) = data.load_sunspots(job.get("records") or 3326)
    x, y = data.make_windows(scaled, WINDOW, HORIZON)
    x, y = torch.tensor(x), torch.tensor(y)
    tr, va, te = data.chrono_split(len(x), tuple(job.get("split") or (0.8, 0.1, 0.1)))
    if (job.get("records") or 3326) == 3265 and tuple(job.get("split") or (0.8, 0.1, 0.1)) == (0.8, 0.1, 0.1):
        # the authors' code truncates: int(0.8 N), int(0.1 N), remainder -> 2084 / 260 / 262
        a, b = int(0.8 * len(x)), int(0.8 * len(x)) + int(0.1 * len(x))
        tr, va, te = np.arange(a), np.arange(a, b), np.arange(b, len(x))
    if job.get("purge"):
        tr, va = tr[: -(HORIZON - 1)], va[: -(HORIZON - 1)]

    torch.manual_seed(job["seed"])
    np.random.seed(job["seed"])
    model = build(spec)
    if spec.get("kind") == "om":
        model.fit_token_scale(x[tr])  # scale of the in-context regression targets (training windows only)
    tkw = dict(lr=job["lr"], schedule="constant")
    tkw.update(spec.get("train", {}))
    alpha = 1.0

    def peak_loss(pred, target):
        weighted = ((pred - target) ** 2) * (1.0 + alpha * target)
        return weighted.mean() if tkw.get("loss") == "mean" else weighted.sum() / len(pred)

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
    sched = None
    if tkw["schedule"] == "cosine":
        sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, steps)
    elif tkw["schedule"] == "keras":
        sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda step: 1.0 / (1.0 + 1e-6 * step))
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
            if tkw.get("grad_clip"):
                torch.nn.utils.clip_grad_norm_(model.parameters(), tkw["grad_clip"])
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
    return (job["variant"], job["seed"], job["lr"], job["epochs"], tuple(job.get("split") or (0.8, 0.1, 0.1)),
            bool(job.get("purge")), job.get("records") or 3326)


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
    ap.add_argument("--split", nargs=3, type=float, default=[0.8, 0.1, 0.1],
                    help="chronological train/val/test fractions (paper: 0.8 0.1 0.1)")
    ap.add_argument("--purge", action="store_true",
                    help="drop the last 131 windows of train and validation (no target overlap between splits)")
    ap.add_argument("--records", type=int, default=3326,
                    help="monthly records used (paper: 3326, to 2026-02; the authors' code: 3265, to 2021-01)")
    args = ap.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    done = {key(json.loads(line)) for line in out.read_text().splitlines()} if out.exists() else set()
    jobs = [
        dict(variant=v, seed=s, lr=args.lr, epochs=args.epochs, threads=args.threads, save_dir=args.save_dir,
             split=list(args.split), purge=args.purge, records=args.records)
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
