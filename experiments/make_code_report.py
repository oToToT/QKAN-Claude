"""Tables and figure for the comparison under the settings of the authors' released code.

The authors' repository (https://github.com/MatthewPeng57/Gated-QKAN-FWP)
generates the benchmarks and builds the model differently from the text of the
paper (qkanfwp/data.py ``CODE_INFO``, qkanfwp/authors.py).  This script reads

* results/code_protocol.jsonl        one-step benchmarks ``c_*``, paper split, seeds 0-4
* results/reference_linear_ar.json   closed-form references on the same windows
* results/solar_code_protocol.jsonl  solar cycle on the authors' 3,265-record file

and writes results/tables_code.md and figures/code_protocol.png.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from experiments.make_figures import BLUE, FIG, INK2, ORANGE, PAPER, PAPER_CMG, PAPER_SOLAR, RES, WINDOWS  # noqa: E402

VIOLET, MAGENTA, GREEN = "#6250d6", "#e87ba4", "#008300"
FLOOR = 1e-15  # rounding of the float32 targets
DATASETS = ["c_bessel", "c_shm", "c_narma5", "c_narma10", "c_dqc", "c_jc"]
TITLES = {"c_bessel": "Bessel J2 (256 samples)", "c_shm": "Damped SHM (240 samples)",
          "c_narma5": "NARMA5, u → y (300 samples)", "c_narma10": "NARMA10, u → y (300 samples)",
          "c_dqc": "Delayed quantum control (2200 samples)", "c_jc": "Jaynes–Cummings (3000 samples)"}
NARMA = ("c_narma5", "c_narma10")
OM = "om_c0h6r1_p5"
FWP = "pmx_diff8_edge_h3l2"


def variant(model: str, d: str) -> str:
    """Variant of a model on dataset ``d``: the learning rate is the one with the lowest
    validation MSE (results/dev_code_protocol.jsonl); on NARMA the target is not the input
    series, so the residual read-out is dropped and QKAN-FWP-O solves its observable from
    the labelled training windows."""
    narma = d in NARMA
    return {
        "authors": "authors",
        "authors_tuned": "authors@cos10" if d == "c_jc" else "authors@cos30",
        "fwp": f"{FWP}_noskip@cos30" if narma else f"{FWP}@cos30" if d == "c_dqc" else f"{FWP}@cos10",
        "hqkan": "ar_hqkan8_noskip@cos30" if narma else "ar_hqkan8@cos30",
        "static": "om_c0h9r1_p5_static_noskip@cos30" if narma else "om_c0h9r1_p5_static@cos30",
        "om": f"{OM}_hist@cos30" if narma else f"{OM}@cos30",
    }[model]


NAMES = {"authors": "GQKAN-QKANFWP, authors' code, lr 1e-3", "authors_tuned": "GQKAN-QKANFWP, authors' code, tuned lr",
         "fwp": "QKAN-FWP+", "hqkan": "HQKAN-Δ", "static": "QKAN-FWP-O features, static observable",
         "om": "QKAN-FWP-O"}
MODELS = ["authors", "authors_tuned", "fwp", "hqkan", "static", "om"]


def gmean(xs):
    return float(np.exp(np.mean(np.log(xs))))


def fl(x):
    return max(float(x), FLOOR)


def big(x):
    return f"{x:.2g}" if x < 10 else f"{x:.0f}" if x < 1e4 else f"{x:.1e}".replace("e+0", "e")


def load():
    """{(dataset, window, variant): {seed: record}}"""
    runs = defaultdict(dict)
    path = RES / "code_protocol.jsonl"
    if path.exists():
        for line in path.read_text().splitlines():
            r = json.loads(line)
            if r["protocol"] == "paper":
                runs[(r["dataset"], r["window"], r["variant"])][r["seed"]] = r
    return runs


def timeseries_part(out):
    runs = load()
    if not runs:
        return
    refs = json.loads((RES / "reference_linear_ar.json").read_text())

    def vals(d, w, model, epoch=None):
        """Test MSE of every seed; ``epoch`` picks an intermediate evaluation (every 5 epochs)."""
        rs = runs.get((d, w, variant(model, d)), {})
        if epoch is None:
            return np.array([r["final"]["test"] for r in rs.values()])
        return np.array([r["history"]["test"][epoch // 5 - 1] for r in rs.values()])

    def mean(d, w, model):
        v = vals(d, w, model, 50) if model == "authors" else vals(d, w, model)
        return float(v.mean()) if len(v) else None

    params = {}
    for m in MODELS:
        ps = sorted({r["params"] for (d, w, v), rs in runs.items() for r in rs.values() if v == variant(m, d)})
        params[m] = "–" if not ps else str(ps[0]) if len(ps) == 1 else f"{ps[0]}–{ps[-1]}"
    printed = {(d, w): PAPER[d[2:]]["own"][i] for d in DATASETS for i, w in enumerate(WINDOWS)}
    best_printed = {(d, w): min(PAPER[d[2:]]["best"][i], PAPER_CMG[d[2:]][i]) for d in DATASETS for i, w in enumerate(WINDOWS)}
    lin = lambda d, w: refs[f"{d}|{w}|8"]["test"]  # noqa: E731
    quad = lambda d, w: refs[f"{d}|{w}|q"]["test"]  # noqa: E731

    # ---- does the authors' model on the authors' data reproduce the printed numbers? ----
    out += ["## Reproduction with the authors' settings (GQKAN-QKANFWP as in the released code, lr 1e-3, batch 4; test MSE)\n",
            "The paper states 50 epochs; the README of the code gives 100 epochs as the benchmark configuration, so both are listed. "
            "\"Printed\" is the GQKAN-QKANFWP entry of Tables 3–6 of arXiv:2605.06734.\n",
            "| Dataset | N | Printed | 50 epochs: mean ± std | 50 epochs: median | 100 epochs: mean | Seeds | Mean at 50 epochs ÷ printed |",
            "|---|---|---|---|---|---|---|---|"]
    f50, f100, fmed = [], [], []
    for d in DATASETS:
        for w in WINDOWS:
            v50, v100 = vals(d, w, "authors", 50), vals(d, w, "authors", 100)
            if not len(v50):
                continue
            f50.append(v50.mean() / printed[(d, w)])
            f100.append(v100.mean() / printed[(d, w)])
            fmed.append(np.median(v50) / printed[(d, w)])
            out.append(f"| {TITLES[d]} | {w} | {printed[(d, w)]:.1e} | {v50.mean():.1e} ± {v50.std():.1e} | {np.median(v50):.1e} "
                       f"| {v100.mean():.1e} | {len(v50)} | {big(v50.mean() / printed[(d, w)])}× |")
    out.append("")
    if f50:
        out += [f"- Geometric mean over the {len(f50)} cells of (re-run ÷ printed): {big(gmean(f50))}× with the mean at 50 epochs, "
                f"{big(gmean(fmed))}× with the median at 50 epochs, {big(gmean(f100))}× with the mean at 100 epochs.", ""]

    # ---- per-dataset summary ----
    def gm(d, model):
        v = [fl(mean(d, w, model)) for w in WINDOWS if mean(d, w, model) is not None]
        return gmean(v) if len(v) == len(WINDOWS) else None

    out += ["## Authors' datasets: per-dataset summary (geometric mean over N ∈ {8, 16, 32, 64} of the seed-mean test MSE)\n",
            "On the two NARMA tasks the window holds the drive u and the target is y: the models have no residual read-out there, "
            "and QKAN-FWP-O solves its measurement operator from the labelled training windows instead of from the context.\n",
            "| Dataset | Best printed in the two papers | " + " | ".join(f"{NAMES[m]} ({params[m]})" for m in MODELS)
            + " | *Linear on the last 8 inputs (9)* | *Ridge on quadratic features of the last 12 inputs* |",
            "|---|---|" + "---|" * (len(MODELS) + 2)]
    for d in DATASETS:
        g = {m: gm(d, m) for m in MODELS}
        have = [m for m in MODELS if g[m] is not None]
        best = min(have, key=lambda m: g[m]) if have else None
        out.append(f"| {TITLES[d]} | {gmean([best_printed[(d, w)] for w in WINDOWS]):.1e} | "
                   + " | ".join("–" if g[m] is None else f"**{g[m]:.1e}**" if m == best else f"{g[m]:.1e}" for m in MODELS)
                   + f" | *{gmean([fl(lin(d, w)) for w in WINDOWS]):.1e}* | "
                   + (f"*{gmean([quad(d, w) for w in WINDOWS]):.1e}*" if d in NARMA else "–") + " |")
    out.append("")

    # ---- QKAN-FWP-O against each model ----
    out += ["## Authors' datasets: QKAN-FWP-O against each model (reference test MSE ÷ QKAN-FWP-O test MSE; above 1: QKAN-FWP-O is lower)\n",
            f"Geometric mean over the four windows per dataset; values below {FLOOR:g} are clipped first.\n",
            "| Compared with | " + " | ".join(TITLES[d].split(" (")[0] for d in DATASETS) + " | Cells where QKAN-FWP-O is lower | Smallest … largest factor |",
            "|---|" + "---|" * (len(DATASETS) + 2)]
    rows = [(NAMES[m], lambda d, w, m=m: mean(d, w, m)) for m in MODELS if m != "om"]
    rows += [("*Best printed number of the two papers*", lambda d, w: best_printed[(d, w)]),
             ("*Linear on the last 8 inputs*", lin),
             ("*Ridge on quadratic features (NARMA only)*", lambda d, w: quad(d, w) if d in NARMA else None)]
    for label, get in rows:
        per, allr = [], []
        for d in DATASETS:
            rs_ = [fl(get(d, w)) / fl(mean(d, w, "om")) for w in WINDOWS if mean(d, w, "om") is not None and get(d, w) is not None]
            per.append(big(gmean(rs_)) + "×" if len(rs_) == len(WINDOWS) else "–")
            allr += rs_
        if allr:
            out.append(f"| {label} | " + " | ".join(per) + f" | {sum(r_ > 1 for r_ in allr)}/{len(allr)} | {big(min(allr))}× … {big(max(allr))}× |")
    out.append("")

    # ---- all cells ----
    out += ["## Authors' datasets: all cells (test MSE, mean ± std over the seeds)\n",
            "| Dataset | N | Seeds | " + " | ".join(NAMES[m] for m in MODELS) + " | *Linear, last 8 inputs* | *Quadratic ridge* |",
            "|---|---|---|" + "---|" * (len(MODELS) + 2)]
    for d in DATASETS:
        for w in WINDOWS:
            cell, ms, n = [], {}, 0
            for m in MODELS:
                v = vals(d, w, m, 50) if m == "authors" else vals(d, w, m)
                if len(v):
                    ms[m] = v.mean()
                    n = max(n, len(v))
            if not ms:
                continue
            best = min(ms, key=ms.get)
            for m in MODELS:
                v = vals(d, w, m, 50) if m == "authors" else vals(d, w, m)
                txt = f"{v.mean():.2e} ± {v.std():.1e}" if len(v) else "–"
                cell.append(f"**{txt}**" if m == best else txt)
            out.append(f"| {TITLES[d]} | {w} | {n} | " + " | ".join(cell) + f" | *{lin(d, w):.1e}* | "
                       + (f"*{quad(d, w):.1e}*" if d in NARMA else "–") + " |")
    out.append("")

    # ---- figure ----
    fig, axes = plt.subplots(2, 3, figsize=(11.5, 6.4), sharex=True)
    series = [("authors", BLUE, "s", "-"), ("authors_tuned", BLUE, "s", (0, (4, 2))), ("fwp", ORANGE, "D", "-"),
              ("hqkan", MAGENTA, "P", "-"), ("om", VIOLET, "*", "-")]
    xs = np.arange(len(WINDOWS))
    for ax, d in zip(axes.ravel(), DATASETS):
        ax.plot(xs, [printed[(d, w)] for w in WINDOWS], color=INK2, linestyle=(0, (1, 2)), marker="o", markersize=3.5,
                label="printed in arXiv:2605.06734")
        for m, color, marker, ls in series:
            ys = [mean(d, w, m) for w in WINDOWS]
            if all(y is not None for y in ys):
                ax.plot(xs, [fl(y) for y in ys], color=color, marker=marker, markersize=8 if marker == "*" else 5, linestyle=ls,
                        markerfacecolor="white" if ls != "-" else color, label=NAMES[m])
        ax.plot(xs, [fl(lin(d, w)) for w in WINDOWS], color=GREEN, linestyle=(0, (5, 2)), linewidth=1.2,
                label="closed form: linear on the last 8 inputs")
        if d in NARMA:
            ax.plot(xs, [quad(d, w) for w in WINDOWS], color=GREEN, linestyle=(0, (1, 1.5)), linewidth=1.6,
                    label="closed form: ridge on quadratic features (NARMA)")
        ax.set_yscale("log")
        ax.set_xticks(xs, [str(w) for w in WINDOWS])
        ax.set_title(TITLES[d], fontsize=10)
    for ax in axes[1]:
        ax.set_xlabel("window N")
    for ax in axes[:, 0]:
        ax.set_ylabel("test MSE (log scale)")
    handles, labels = [], []
    for ax in axes.ravel():
        for h_, l_ in zip(*ax.get_legend_handles_labels()):
            if l_ not in labels:
                handles.append(h_)
                labels.append(l_)
    fig.legend(handles, labels, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.0), fontsize=8.5)
    fig.tight_layout(rect=(0, 0, 1, 0.89))
    fig.savefig(FIG / "code_protocol.png", dpi=200)
    plt.close(fig)


SOLAR_MODELS = [("authors", "GQKAN-QKANFWP, authors' code"), ("mtg_cyc_pm", "QKAN-FWP+"),
                ("om_static", "QKAN-FWP-O without fast weights (static observable)"), ("om", "QKAN-FWP-O")]


def solar_anchor(purge: bool) -> dict:
    """Repeat the last cycle (13-month smoothed) on the test windows of the authors' file."""
    import torch

    from experiments.run_solar import HORIZON, VARIANTS, WINDOW, build
    from qkanfwp import data

    _, scaled, (lo, hi) = data.load_sunspots(3265)
    x, y = data.make_windows(scaled, WINDOW, HORIZON)
    x, y = torch.tensor(x), torch.tensor(y)
    te = np.arange(int(0.8 * len(x)) + int(0.1 * len(x)), len(x))
    with torch.no_grad():
        pred, tgt = build(VARIANTS["mtg_cyc_pm"]).cycle_anchor(x[te]), y[te]
    return dict(mse=((pred - tgt) ** 2).mean().item(),
                pae=((tgt.max(1).values - pred.max(1).values).abs() * (hi - lo)).mean().item(),
                pte=(tgt.argmax(1) - pred.argmax(1)).abs().float().mean().item())


def solar_part(out):
    path = RES / "solar_code_protocol.jsonl"
    if not path.exists():
        return
    rows = defaultdict(list)
    for line in path.read_text().splitlines():
        r = json.loads(line)
        rows[(bool(r.get("purge")), r["variant"])].append(r)
    if not rows:
        return
    anchor = solar_anchor(False)
    out += ["## Solar cycle with the file, split and model of the authors' code (3,265 records to 2021-01; 2,606 windows; lr 2.5e-3)\n",
            "Test windows 2345–2606 (targets 1988-04 … 2021-01) in both splits; test metrics at the best-validation checkpoint, mean ± std over seeds.\n"]
    for purge, title in ((False, "window-index split 2084 / 260 / 262 (the authors' split; targets of neighbouring splits overlap by 131 months)"),
                         (True, "split by target time (the last 131 windows of train and validation removed)")):
        if not any(k[0] == purge for k in rows):
            continue
        out += [f"### {title}\n", "| Model | Params | Seeds | Scaled MSE ↓ | PAE ↓ | PTE ↓ |", "|---|---|---|---|---|---|"]
        for v, label in SOLAR_MODELS:
            rs = rows.get((purge, v))
            if not rs:
                continue
            f = lambda k, p_: "{:.{p}f} ± {:.{p}f}".format(np.mean([r["test"][k] for r in rs]), np.std([r["test"][k] for r in rs]), p=p_)  # noqa: E731
            out.append(f"| {label} | {rs[0]['params']:,} | {len(rs)} | {f('mse', 4)} | {f('pae', 1)} | {f('pte', 1)} |")
        out.append(f"| *Reference: repeat the last cycle, 13-month smoothed (no training)* | 0 | – | {anchor['mse']:.4f} | {anchor['pae']:.1f} | {anchor['pte']:.1f} |")
        if not purge:
            ps = PAPER_SOLAR
            out.append(f"| *Printed in arXiv:2605.06734 for GQKAN-QKANFWP* | {ps['params']:,} | 5 | {ps['mse'][0]:.4f} ± {ps['mse'][1]:.4f} "
                       f"| {ps['pae'][0]:.2f} ± {ps['pae'][1]:.2f} | {ps['pte'][0]:.2f} ± {ps['pte'][1]:.2f} |")
        out.append("")


def main():
    out = []
    timeseries_part(out)
    solar_part(out)
    (RES / "tables_code.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
