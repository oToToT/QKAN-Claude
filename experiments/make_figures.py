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
def fig_base_vs_ext(c, series, path):
    """Small multiples: test MSE vs input window for the main models."""
    fig, axes = plt.subplots(2, 3, figsize=(10.5, 5.8), sharex=True)
    for ax, d in zip(axes.ravel(), DATASETS):
        for v, color, label, marker in series:
            if isinstance(v, dict):
                v = v.get(d, v["default"])
            ms = [mean_std(c[(d, w, v)]) if (d, w, v) in c else (np.nan, np.nan) for w in WINDOWS]
            m = np.array([a for a, _ in ms])
            sd = np.array([b for _, b in ms])
            ax.errorbar(range(4), m, yerr=[np.minimum(sd, m * 0.9), sd], color=color, marker=marker,
                        markersize=5, capsize=2.5, elinewidth=1, label=label)
        ax.set_yscale("log")
        ax.set_title(TITLES[d])
        ax.set_xticks(range(4), [str(w) for w in WINDOWS])
    for ax in axes[-1]:
        ax.set_xlabel("input window N")
    for ax in axes[:, 0]:
        ax.set_ylabel("test MSE (log scale)")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=len(series), bbox_to_anchor=(0.5, 1.0))
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
        ax.annotate(f"{ratio:.2g}×  ({wins}/{n})", (ratio, yi), xytext=(0, 8), textcoords="offset points",
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
            per.append(f"{r:.2g}" if k else "–")
        lines.append(f"| {names.get(v, v)} | {params.get(v, '')} | **{ratio:.2g}** | {wins}/{n} | " + " | ".join(per) + " |")
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


def welch_p(a, b):
    from scipy.stats import ttest_ind

    return float(ttest_ind(a, b, equal_var=False).pvalue)


def fig_solar_forecast(by_variant, variants, path, pred_dir=RES / "solar_preds"):
    """Seed-averaged 132-month forecasts for three test windows."""
    from qkanfwp import data
    from experiments.run_solar import HORIZON, WINDOW

    raw, scaled, (lo, hi) = data.load_sunspots()
    dates = 1749 + (np.arange(len(raw)) + 0.5) / 12
    n_win = len(raw) - WINDOW - HORIZON + 1
    picks = {}
    for v, _, _ in variants:
        files = sorted(pred_dir.glob(f"{v}_seed*.npz"))
        if files:
            picks[v] = [np.load(f) for f in files]
    if not picks:
        return
    test_index = next(iter(picks.values()))[0]["test_index"]
    # windows whose forecast starts at the minima before SC23 / SC24 and the last window
    starts = {"Solar cycle 23": 1996.6, "Solar cycle 24": 2008.9, "Latest window (SC25 rise)": None}
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.6), sharey=True)
    for ax, (title, year) in zip(axes, starts.items()):
        if year is None:
            k = len(test_index) - 1
        else:
            k = int(np.argmin(np.abs(dates[test_index + WINDOW] - year)))
        i = int(test_index[k])
        t = dates[i + WINDOW : i + WINDOW + HORIZON]
        ax.plot(t, raw[i + WINDOW : i + WINDOW + HORIZON], color=INK2, linewidth=1, label="Observed (monthly)")
        for v, color, label in variants:
            if v not in picks:
                continue
            p = np.stack([f["preds"][k].astype(np.float32) for f in picks[v]]) * (hi - lo) + lo
            ax.fill_between(t, p.mean(0) - p.std(0), p.mean(0) + p.std(0), color=color, alpha=0.18, linewidth=0)
            ax.plot(t, p.mean(0), color=color, label=label)
        ax.set_title(title)
        ax.set_xlabel("year")
    axes[0].set_ylabel("sunspot number")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=len(handles), bbox_to_anchor=(0.5, 1.02))
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(path, dpi=200)
    plt.close(fig)


def fig_memory_kernel(path, base="base", multi="mtg", pred_dir=RES / "solar_preds", seed=0):
    """Learned memory kernel beta_k (Eq. 5) on the last test window."""
    fb, fm = pred_dir / f"{base}_seed{seed}.npz", pred_dir / f"{multi}_seed{seed}.npz"
    if not (fb.exists() and fm.exists()):
        return
    kb, km = np.load(fb)["kernel"], np.load(fm)["kernel"]
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 3.5), sharey=True)
    age = np.arange(kb.shape[0], 0, -1)
    axes[0].plot(age, kb[:, 0], color=BLUE)
    axes[0].set_title("Scalar gate (paper): one kernel for all fast weights")
    order = np.argsort((km * age[:, None]).sum(0) / km.sum(0))  # sort groups by mean memory age
    idx = np.linspace(0, len(order) - 1, 5).round().astype(int)
    for j, g in enumerate(order[idx]):
        mean_age = (km[:, g] * age).sum() / km[:, g].sum()
        axes[1].plot(age, km[:, g], color=SEQ[1 + j], label=f"mean age {mean_age:.0f} mo")
    axes[1].set_title("Multi-timescale gates: 5 of 20 gate groups")
    axes[1].legend(fontsize=8.5, title="gate group", title_fontsize=8.5)
    for ax in axes:
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_ylim(1e-6, 1.5)
        ax.set_xlabel("age of the input (months before the forecast start, log scale)")
    axes[0].set_ylabel("memory weight  β_k")
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


NAMES = {
    "base": "Baseline, paper protocol (lr 1e-3)",
    "base@cos30": "Baseline, tuned lr (cosine 3e-2)",
    "base@cos10": "Baseline, tuned lr (cosine 1e-2)",
    "base_tuned": "Baseline, tuned lr",
    "skip_dif3@cos30": "Extended (residual + Δ-tokens), tuned lr",
    "skip_dif3": "Extended, paper protocol (lr 1e-3)",
    "skip_mtg_dif3@cos30": "Extended + multi-timescale gates, tuned lr",
    "skip@cos30": "Baseline + residual read-out",
    "dif3@cos30": "Baseline + Δ-tokens",
    "mtg@cos30": "Baseline + multi-timescale gates",
    "skip_mtg@cos30": "Baseline + residual + multi-timescale gates",
    "skip": "+ residual read-out (lr 1e-3)",
    "dif3": "+ Δ-tokens (lr 1e-3)",
    "mtg": "+ multi-timescale gates, chrono init (lr 1e-3)",
    "ungated": "Ungated (additive) FWP (lr 1e-3)",
    "base_big": "Larger baseline",
    "base_big@cos30": "Larger baseline (193 params), tuned lr",
    "ar_hqkan@cos30": "No fast-weight memory: HQKAN on last Δ-token",
    "lstm@cos30": "LSTM (hidden 5), tuned lr",
    "gqkan_fwp": "GQKAN-FWP, paper protocol",
    "gqkan_fwp@cos30": "GQKAN-FWP, tuned lr",
    "gqkan_fwp_ext@cos30": "GQKAN-FWP extended, tuned lr",
    "g_qkanfwp": "G-QKANFWP, paper protocol",
    "g_qkanfwp@cos30": "G-QKANFWP, tuned lr",
    "g_qkanfwp_ext@cos30": "G-QKANFWP extended, tuned lr",
}
SOLAR_NAMES = {
    "base": "GQKAN-QKANFWP baseline (scalar gate)",
    "chrono": "+ chrono gate initialisation (scalar gate)",
    "mtg": "+ multi-timescale gates (20 groups, chrono init)",
    "mtg_ctx12s12": "+ multi-timescale gates + yearly patch tokens",
    "ctx12s12": "+ yearly patch tokens",
    "ungated": "Ungated (additive) FWP",
    "lstm_s": "LSTM-S (paper baseline, re-run here)",
}


def main():
    FIG.mkdir(exist_ok=True)
    out = []
    ts_file = RES / "final_timeseries.jsonl"
    if ts_file.exists():
        rows = load([ts_file], protocol="paper")
        c = cells(rows)
        params = {r["variant"]: r["params"] for r in rows}
        # "tuned baseline" = baseline with its validated learning rate (1e-2 on JC, 3e-2 elsewhere)
        for (d, w, v), vals in list(c.items()):
            if (v == "base@cos10" and d == "jc") or (v == "base@cos30" and d != "jc"):
                c[(d, w, "base_tuned")] = vals
        params["base_tuned"] = params.get("base", 0)
        main_v = ["base", "base_tuned", "skip_dif3@cos30"]
        fig_base_vs_ext(c, [("base", INK2, NAMES["base"], "s"), ("base_tuned", BLUE, NAMES["base_tuned"], "o"),
                            ("skip_dif3@cos30", ORANGE, NAMES["skip_dif3@cos30"], "D")],
                        FIG / "timeseries_main.png")
        out += ["## Time series: main comparison (test MSE, mean ± std over 5 seeds)\n",
                table_cells(c, main_v, NAMES), ""]
        abl = ["base_tuned", "skip@cos30", "dif3@cos30", "mtg@cos30", "skip_mtg@cos30", "skip_dif3@cos30",
               "skip_mtg_dif3@cos30", "base_big@cos30", "ar_hqkan@cos30", "lstm@cos30",
               "skip", "dif3", "mtg", "skip_dif3", "ungated"]
        abl = [v for v in abl if any(k[2] == v for k in c)]
        # restrict the ablation to the cells every ablation variant was run on
        sub = {k: v for k, v in c.items() if k[0] != "jc" and k[1] in (16, 64)}
        fig_ablation(sub, abl, NAMES, FIG / "timeseries_ablation.png",
                     "Test MSE relative to the paper-protocol baseline (5 series × N ∈ {16, 64})")
        out += ["## Time series: ablation (5 series × N ∈ {16, 64}; ratio of seed-mean test MSE to the paper-protocol baseline)\n",
                table_ratio(sub, abl, NAMES, params), ""]
        full = ["base_tuned", "skip_dif3@cos30"]
        out += ["## Time series: all 24 cells\n", table_ratio(c, full, NAMES, params), ""]
        other = ["gqkan_fwp", "gqkan_fwp@cos30", "gqkan_fwp_ext@cos30", "g_qkanfwp", "g_qkanfwp@cos30", "g_qkanfwp_ext@cos30"]
        if any(k[2] in other for k in c):
            out += ["## Other paper variants (N = 16)\n", table_cells(c, [v for v in other if any(k[2] == v for k in c)], NAMES), ""]

    solar_file = RES / "final_solar.jsonl"
    if solar_file.exists() and solar_file.stat().st_size:
        by = solar_rows(solar_file)
        order = [v for v in ["base", "chrono", "mtg", "mtg_ctx12s12", "ctx12s12", "ungated", "lstm_s"] if v in by]
        out += ["## Solar cycle forecasting (test split, best-validation checkpoint)\n", table_solar(by, order, SOLAR_NAMES), ""]
        if "base" in by:
            b = np.array([r["test"]["mse"] for r in by["base"]])
            for v in order:
                if v == "base":
                    continue
                a = np.array([r["test"]["mse"] for r in by[v]])
                out.append(f"- {SOLAR_NAMES[v]}: scaled MSE {a.mean() / b.mean() - 1:+.1%} vs baseline, Welch p = {welch_p(a, b):.3g}")
            out.append("")
        fig_solar_forecast(by, [("base", BLUE, "Baseline (scalar gate)"), ("mtg", ORANGE, "Multi-timescale gates")],
                           FIG / "solar_forecast.png")
        fig_memory_kernel(FIG / "solar_memory_kernel.png")
    (RES / "tables.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
