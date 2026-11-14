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
DIF2 = dict(context=2, context_mode="diff")
DIF3 = dict(context=3, context_mode="diff")
COS3 = dict(lr=3e-3, schedule="cosine")
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
    "dif2": fwp(DIF2),  # token (x_t, dx_t)
    "dif3": fwp(DIF3),  # token (x_t, dx_t, d2x_t)
    "skip": fwp(SKIP),
    "cos": fwp(train=COS),  # cosine decay from the paper's 1e-3
    "lr3": fwp(train=dict(lr=3e-3)),
    "cos3": fwp(train=dict(lr=3e-3, schedule="cosine")),
    "cos10": fwp(train=dict(lr=1e-2, schedule="cosine")),
    # ---- screening combinations ---------------------------------------------
    "skip_mtg": fwp(SKIP, MTG),
    "skip_dif2": fwp(SKIP, DIF2),
    "skip_dif3": fwp(SKIP, DIF3),
    "skip_mtg_dif2": fwp(SKIP, MTG, DIF2),
    "skip_mtg_dif3": fwp(SKIP, MTG, DIF3),
    "skip_cos3": fwp(SKIP, train=COS3),
    "skip_mtg_dif2_cos3": fwp(SKIP, MTG, DIF2, train=COS3),
    # parameter-budget control: a larger scalar-gated baseline
    "base_big": fwp(slow_latent=4),
    # ---- controls -----------------------------------------------------------
    # no fast-weight memory at all: static HQKAN on the last (x, dx, d2x) token
    "ar_hqkan": dict(kind="ar", model=dict(context=3, hidden=4, latent=4, reps=3, skip="last", context_mode="diff")),
    "lstm": dict(kind="lstm", model=dict(hidden=5)),
    # LSTM given the same difference tokens and residual read-out as the extended FWP
    "lstm_ext": dict(kind="lstm", model=dict(hidden=4, context=3, context_mode="diff", skip="last")),
    # HQKAN-Δ and the LSTM control: the same exact 8-dim difference tokens and residual read-out as QKAN-FWP+
    "ar_hqkan8": dict(kind="ar", model=dict(context=8, hidden=4, latent=3, reps=3, skip="last",
                                             context_mode="diff", token_dtype="float64")),
    "lstm_ext8": dict(kind="lstm", model=dict(hidden=3, context=8, context_mode="diff", skip="last",
                                               token_dtype="float64")),
    # ---- other paper variants (Table 1) and their extended versions ----------
    "gqkan_fwp": fwp(fast="linear", fast_out=3),  # HQKAN slow, linear fast
    "gqkan_fwp_ext": fwp(SKIP, DIF3, fast="linear", fast_out=3),
    "g_qkanfwp": fwp(slow="mlp", slow_hidden=8),  # classical slow, HQKAN fast
    "g_qkanfwp_ext": fwp(SKIP, DIF3, slow="mlp", slow_hidden=8),
    # ---- complementary matrix gate (CMG, arXiv:2607.27945) --------------------
    # paper-style: scalar tokens, write-then-read, rank-one per-weight gate
    "cmg": fwp(gate="cmg", write_first=True),
    # CMG given this repository's tokens and residual read-out (strongest version)
    "cmg_plus": fwp(SKIP, gate="cmg", write_first=True, context=8, context_mode="diff",
                    token_dtype="float64", slow_latent=2),
}


def om_variant(name: str) -> dict:
    """Observable-memory FWP, e.g. ``om_c4h4r2`` (context 4, 4 feature circuits,
    2 re-uploading repetitions) plus optional ``_``-separated switches:
    ``static`` (no fast weights), ``delta`` (sequential delta rule), ``gconst`` /
    ``gnone`` (constant gate / additive statistics), ``nobase`` / ``silu`` (QKAN
    base activation), ``classical`` (no Bloch features), ``nomask``, ``pscalar``
    (one prior precision), ``tan`` (tangent features), ``single`` (float32),
    ``tanh`` / ``fourier`` (classical nonlinear features instead of the Bloch features), ``lags`` (raw lag tokens), ``p<x>`` (prior_init 10^-x),
    ``noclip`` (no gradient-norm clipping; the default clips the norm at 1)."""
    parts = name.split("_")
    core = parts[1]
    c, h, r = core.index("c"), core.index("h"), core.index("r")
    cfg = dict(context=int(core[c + 1 : h]), hidden=int(core[h + 1 : r]), reps=int(core[r + 1 :]))
    train = dict(grad_clip=1.0)
    switches = {
        "static": dict(memory="none"), "delta": dict(memory="delta"),
        "gconst": dict(gate="const"), "gnone": dict(gate="none"),
        "nobase": dict(base="none"), "silu": dict(base="silu"),
        "classical": dict(quantum=False), "nomask": dict(mask_padded=False),
        "pscalar": dict(prior="scalar"), "lags": dict(context_mode="lags"), "tan": dict(tangent=True),
        "single": dict(precision="float32"),
        "tanh": dict(quantum=False, classical="tanh"), "fourier": dict(quantum=False, classical="fourier"),
    }
    for extra in parts[2:]:
        if extra in switches:
            cfg.update(switches[extra])
        elif extra.startswith("p") and extra[1:].isdigit():
            cfg.update(prior_init=10.0 ** -int(extra[1:]))
        elif extra.startswith("m") and extra[1:].isdigit():
            # write every token that knows >= m values; unknown difference orders are zero
            cfg.update(min_context=int(extra[1:]), token_pad="truncate")
        elif extra.startswith("f") and extra[1:].isdigit():
            cfg.update(prior_floor=10.0 ** -int(extra[1:]))
        elif extra == "noclip":
            train = {}
        else:
            raise ValueError(name)
    return dict(kind="om", model=cfg, train=train)


def pm_variant(name: str) -> dict:
    """Parameter-matched candidates, e.g. ``pm_diff5_layer_h3l2``:
    residual read-out + ``diff``/``lags`` tokens of length 5 + gate grouping
    (``scalar`` | ``edge`` | ``layer``, chrono-initialised) with a slow HQKAN
    of hidden width 3 and latent width 2.  Optional ``_f2`` suffix: fast
    programmer with 2 instead of 3 re-uploading repetitions."""
    parts = name.split("_")
    exact = parts[0] == "pmx"  # pmx_...: differences formed in float64
    mode = "diff" if parts[1].startswith("diff") else "lags"
    context = int(parts[1][4:])
    gate = parts[2]
    hidden, latent = int(parts[3][1 : parts[3].index("l")]), int(parts[3][parts[3].index("l") + 1 :])
    cfg = dict(skip="last", context=context, context_mode=mode, slow_hidden=hidden, slow_latent=latent,
               gate_init="chrono")
    if gate != "scalar":
        cfg.update(gate="group", gate_groups=gate)
    for extra in parts[4:]:
        if extra.startswith("f"):
            cfg.update(fast_reps=int(extra[1:]))
        elif extra == "noskip":  # ablation: no residual read-out
            cfg.update(skip="none")
        elif extra == "wf":  # write-then-read: the newest token also programs the fast weights
            cfg.update(write_first=True)
        else:
            raise ValueError(name)
    if exact:
        cfg.update(token_dtype="float64")
    return fwp(cfg)


def resolve(name: str) -> dict:
    """``"<variant>@cos10"`` / ``"<variant>@lr3"``: variant trained with a cosine
    schedule from (or a constant) learning rate of 10e-3 / 3e-3."""
    base, _, tag = name.partition("@")
    base, *mods = base.split("+")
    if base.startswith("om_"):
        spec = om_variant(base)
    else:
        spec = dict(pm_variant(base) if base.startswith(("pm_", "pmx_")) else VARIANTS[base])
    # "+z": physical <Z> = |a|^2 - |b|^2 read-out instead of qkan's default |a| - |b|
    # "+wf": write-then-read (predict with the updated fast weights)
    if mods:
        model = dict(spec["model"])
        for m in mods:
            if m == "z":
                model["fast_measure"] = False
            elif m == "wf":
                model["write_first"] = True
            else:
                raise ValueError(name)
        spec["model"] = model
    if not tag:
        return spec
    kind, value = (tag[:3], tag[3:]) if tag.startswith("cos") else (tag[:2], tag[2:])
    train = dict(spec.get("train") or {})
    train.update(lr=float(value) * 1e-3, schedule="cosine" if kind == "cos" else "constant")
    spec["train"] = train
    return spec


def build_model(spec: dict, window: int, x_train):
    """Instantiate the model of a resolved variant and fit its token scales."""
    from qkanfwp.models import ARHQKAN, FWPConfig, GatedFWP, LSTMBaseline
    from qkanfwp.obsmem import ObservableMemoryFWP, ObsMemConfig

    kind = spec.get("kind", "fwp")
    if kind == "fwp":
        model = GatedFWP(FWPConfig(max_len=window, **spec["model"]))
    elif kind == "ar":
        model = ARHQKAN(**spec["model"])
    elif kind == "lstm":
        model = LSTMBaseline(**spec["model"])
    elif kind == "om":
        model = ObservableMemoryFWP(ObsMemConfig(max_len=window, **spec["model"]))
    else:
        raise ValueError(kind)
    model.fit_token_scale(x_train)
    return model


def run_job(job: dict) -> dict:
    import numpy as np
    import torch

    torch.set_num_threads(1)
    from qkanfwp import data
    from qkanfwp.models import count_parameters
    from qkanfwp.train import fit

    spec = resolve(job["variant"])
    # Inputs are kept in float64 so that models with ``token_dtype='float64'``
    # can difference them exactly; every model casts to float32 internally.
    norm = job.get("norm", "global")
    n_raw = len(data.GENERATORS[job["dataset"]]()) if norm == "train" else 0
    # for norm='train' the scaling only sees the samples the training windows touch
    fit_len = int(round((n_raw - job["window"]) * (0.8 if job["protocol"] == "paper" else 0.7))) + job["window"]
    series = data.load_series(job["dataset"], dtype=np.float64, norm=norm, fit_len=fit_len)
    x, y = data.make_windows(series, job["window"])
    x, y = torch.tensor(x), torch.tensor(y, dtype=torch.float32)
    if job["protocol"] == "paper":
        tr, te = data.chrono_split(len(x), (0.8, 0.2))
        evals = {"train": (x[tr], y[tr]), "test": (x[te], y[te])}
    else:
        tr, va, te = data.chrono_split(len(x), (0.7, 0.1, 0.2))
        evals = {"train": (x[tr], y[tr]), "val": (x[va], y[va]), "test": (x[te], y[te])}

    torch.manual_seed(job["seed"])
    np.random.seed(job["seed"])
    model = build_model(spec, job["window"], x[tr])

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
    return tuple(job[k] for k in ("dataset", "window", "variant", "seed", "protocol", "epochs")) + (job.get("norm", "global"),)


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
    ap.add_argument("--norm", choices=["global", "train", "none"], default="global",
                    help="min-max scaling from the whole series (paper), the training part only, or none")
    args = ap.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out.exists():
        for line in out.read_text().splitlines():
            done.add(key(json.loads(line)))
    jobs = [
        dict(dataset=d, window=w, variant=v, seed=s, protocol=args.protocol, epochs=args.epochs, norm=args.norm)
        for d, w, v, s in itertools.product(args.datasets, args.windows, args.variants, args.seeds)
    ]
    jobs = [j for j in jobs if key(j) not in done]
    # long jobs (jc, large windows) first so the pool stays balanced
    jobs.sort(key=lambda j: -(3000 if j["dataset"] == "jc" else 300) * (8 + j["window"]))
    if args.norm == "global":
        for j in jobs:
            j.pop("norm")  # records without a "norm" field use the default (global) scaling
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
