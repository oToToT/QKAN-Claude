"""Build the figures and markdown tables of REPORT.md from results/*.jsonl."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from experiments.aggregate import cells, geo_ratio, load  # noqa: E402

RES = ROOT / "results"
FIG = ROOT / "figures"

# categorical slots / inks of the validated reference palette (light surface)
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, INK2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
SEQ = ["#b7d3f6", "#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#104281", "#0d366b"]

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "text.color": INK,
    "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "axes.titlesize": 11, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "legend.frameon": False, "lines.linewidth": 2.0,
})

DATASETS = ["bessel", "shm", "narma5", "narma10", "dqc", "jc"]
TITLES = {"bessel": "Bessel J2", "shm": "Damped SHM", "narma5": "NARMA5", "narma10": "NARMA10",
          "dqc": "Delayed quantum control", "jc": "Jaynes–Cummings"}
WINDOWS = [8, 16, 32, 64]


def mean_std(vals):
    v = np.array(list(vals.values()))
    return v.mean(), v.std()


# ---------------------------------------------------------------------------
def fig_base_vs_full(c, path):
    fig, axes = plt.subplots(2, 3, figsize=(10.5, 5.6), sharex=True)
    for ax, d in zip(axes.ravel(), DATASETS):
        for v, color, label in (("base", BLUE, "Baseline (paper mechanism)"), ("full", ORANGE, "Extended (this work)")):
            ms = [mean_std(c[(d, w, v)]) if (d, w, v) in c else (np.nan, np.nan) for w in WINDOWS]
            m = np.array([a for a, _ in ms])
            s = np.array([b for _, b in ms])
            ax.errorbar(range(4), m, yerr=[np.minimum(s, m * 0.999), s], color=color, marker="o",
                        markersize=5, capsize=2.5, elinewidth=1, label=label)
        ax.set_yscale("log")
        ax.set_title(TITLES[d])
        ax.set_xticks(range(4), [str(w) for w in WINDOWS])
    for ax in axes[-1]:
        ax.set_xlabel("input window N")
    for ax in axes[:, 0]:
        ax.set_ylabel("test MSE (log scale)")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(path, dpi=200)
    plt.close(fig)


def fig_ablation(c, variants, labels, path, title):
    """Geometric-mean test-MSE ratio to the baseline, one row per variant."""
    rows = []
    for v in variants:
        ratio, wins, n = geo_ratio(c, v, "base")
        per = [geo_ratio(c, v, "base", datasets=[d])[0] for d in DATASETS]
        rows.append((v, ratio, wins, n, per))
    fig, ax = plt.subplots(figsize=(8.6, 0.42 * len(rows) + 1.5))
    y = np.arange(len(rows))[::-1]
    for yi, (v, ratio, wins, n, per) in zip(y, rows):
        ax.scatter(per, [yi] * len(per), s=16, color=SEQ[1], zorder=2,
                   label="single dataset" if yi == y[0] else None)
        ax.plot([1.0, ratio], [yi, yi], color=BLUE, linewidth=2, zorder=3)
        ax.scatter([ratio], [yi], s=46, color=BLUE, zorder=4,
                   label="geometric mean over all cells" if yi == y[0] else None)
        ax.annotate(f"{ratio:.2f}×  ({wins}/{n})", (ratio, yi), xytext=(0, 8), textcoords="offset points",
                    ha="center", fontsize=8.5, color=INK2)
    ax.axvline(1.0, color=INK2, linewidth=1)
    ax.set_xscale("log")
    ax.set_yticks(y, [labels.get(r[0], r[0]) for r in rows])
    ax.set_ylim(-0.6, len(rows) - 0.3)
    ax.set_xlabel("test MSE relative to the baseline (log scale; left of 1 = better)")
    ax.set_title(title)
    ax.grid(axis="y", visible=False)
    ax.legend(loc="lower left", fontsize=8.5)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def table_cells(c, variants, names):
    lines = ["| Dataset | N | " + " | ".join(names[v] for v in variants) + " |",
             "|---|---|" + "---|" * len(variants)]
    for d in DATASETS:
        for w in WINDOWS:
            if not any((d, w, v) in c for v in variants):
                continue
            means = {v: mean_std(c[(d, w, v)])[0] for v in variants if (d, w, v) in c}
            best = min(means, key=means.get)
            cells_ = []
            for v in variants:
                if (d, w, v) not in c:
                    cells_.append("–")
                    continue
                m, s = mean_std(c[(d, w, v)])
                txt = f"{m:.2e} ± {s:.1e}"
                cells_.append(f"**{txt}**" if v == best else txt)
            lines.append(f"| {TITLES[d]} | {w} | " + " | ".join(cells_) + " |")
    return "\n".join(lines)


def table_ratio(c, variants, names, params):
    lines = ["| Variant | Params | Geo-mean MSE ratio vs baseline | Cells better than baseline | "
             + " | ".join(TITLES[d] for d in DATASETS) + " |",
             "|---|---|---|---|" + "---|" * len(DATASETS)]
    for v in variants:
        ratio, wins, n = geo_ratio(c, v, "base")
        if n == 0:
            continue
        per = []
        for d in DATASETS:
            r, _, k = geo_ratio(c, v, "base", datasets=[d])
            per.append(f"{r:.2f}" if k else "–")
        lines.append(f"| {names.get(v, v)} | {params.get(v, '')} | **{ratio:.3f}** | {wins}/{n} | " + " | ".join(per) + " |")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
def solar_rows(path):
    rows = [json.loads(line) for line in Path(path).read_text().splitlines()]
    out = {}
    for r in rows:
        out.setdefault(r["variant"], []).append(r)
    return out


def table_solar(by_variant, variants, names):
    lines = ["| Model | Params | Scaled MSE ↓ | PAE ↓ | PTE ↓ | Val. loss ↓ | Seeds |", "|---|---|---|---|---|---|---|"]
    best = {k: min(np.mean([r["test"][k] for r in by_variant[v]]) for v in variants if v in by_variant)
            for k in ("mse", "pae", "pte")}
    for v in variants:
        if v not in by_variant:
            continue
        rs = by_variant[v]
        cols = []
        for k, f in (("mse", "{:.4f} ± {:.4f}"), ("pae", "{:.2f} ± {:.2f}"), ("pte", "{:.2f} ± {:.2f}")):
            vals = np.array([r["test"][k] for r in rs])
            txt = f.format(vals.mean(), vals.std())
            cols.append(f"**{txt}**" if np.isclose(vals.mean(), best[k]) else txt)
        val = np.array([r["val"]["loss"] for r in rs])
        lines.append(f"| {names.get(v, v)} | {rs[0]['params']:,} | " + " | ".join(cols)
                     + f" | {val.mean():.3f} ± {val.std():.3f} | {len(rs)} |")
    return "\n".join(lines)


if __name__ == "__main__":
    FIG.mkdir(exist_ok=True)
    rows = load([RES / "final_timeseries.jsonl"], protocol="paper")
    c = cells(rows)
    fig_base_vs_full(c, FIG / "timeseries_base_vs_full.png")
    print("wrote figures to", FIG)
