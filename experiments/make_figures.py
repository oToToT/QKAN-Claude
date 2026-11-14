"""Figures and markdown tables for the gated fast-weight programmers.

single_change_report()  one change at a time on top of the re-implemented
                        baseline -> results/tables_single_change.md,
                        figures/single_change_ablation.png
final_report()          parameter-matched models (QKAN-FWP+, HQKAN-Δ), the
                        reproduction gap, robustness checks and the solar
                        benchmark -> results/tables_final.md, figures/*.png

The comparison that also includes CMG and the observable-memory FWP is built
by experiments/make_om_report.py.
"""

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
    rows_ = 1 if len(series) <= 4 else 2  # wrap long legends instead of clipping them
    fig.legend(handles, labels, loc="upper center", ncol=-(-len(series) // rows_), bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout(rect=(0, 0, 1, 0.94 if rows_ == 1 else 0.90))
    fig.savefig(path, dpi=200)
    plt.close(fig)


def fig_ablation(c, groups, labels, path, title):
    """Geometric-mean test-MSE ratio to the baseline; one row per variant,
    rows grouped under headings.  ``groups``: [(heading, [variant, ...]), ...]."""
    rows = []  # (kind, payload)
    for heading, variants in groups:
        variants = [v for v in variants if any(k[2] == v for k in c)]
        if not variants:
            continue
        rows.append(("head", heading))
        for v in variants:
            ratio, wins, n = geo_ratio(c, v, "base")
            per = [geo_ratio(c, v, "base", datasets=[d])[0] for d in DATASETS]
            rows.append(("row", (v, ratio, wins, n, per)))
    fig, ax = plt.subplots(figsize=(9.6, 0.4 * len(rows) + 1.6))
    ys = np.arange(len(rows))[::-1]
    ticks, ticklabels, first = [], [], True
    for yi, (kind, payload) in zip(ys, rows):
        if kind == "head":
            ax.text(0.0, yi - 0.1, payload, transform=ax.get_yaxis_transform(), ha="left", va="center",
                    fontsize=9.5, fontweight="bold", color=INK)
            continue
        v, ratio, wins, n, per = payload
        ax.scatter(per, [yi] * len(per), s=16, color=SEQ[1], zorder=2, label="one dataset" if first else None)
        ax.plot([1.0, ratio], [yi, yi], color=BLUE, linewidth=2, zorder=3)
        ax.scatter([ratio], [yi], s=46, color=BLUE, zorder=4,
                   label="geometric mean of all cells" if first else None)
        first = False
        ax.annotate(f"{ratio:.2g}×", (ratio, yi), xytext=(0, 7), textcoords="offset points",
                    ha="center", fontsize=8.5, color=INK2)
        ticks.append(yi)
        ticklabels.append(labels.get(v, v))
    ax.axvline(1.0, color=INK2, linewidth=1)
    ax.set_xscale("log")
    ax.set_yticks(ticks, ticklabels)
    ax.set_ylim(-0.7, len(rows) - 0.4)
    ax.set_xlabel("test MSE ÷ paper-protocol baseline (log scale; left of 1 = better)")
    ax.grid(axis="y", visible=False)
    fig.suptitle(title, x=0.01, ha="left", fontsize=11, fontweight="bold")
    fig.legend(loc="upper right", ncol=2, fontsize=8.5, bbox_to_anchor=(0.99, 0.995))
    fig.tight_layout(rect=(0, 0, 1, 0.97))
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


def table_ratio(c, variants, names, params, datasets=None):
    datasets = datasets or DATASETS
    lines = ["| Variant | Params | Geo-mean MSE ratio vs baseline | Cells better than baseline | "
             + " | ".join(TITLES[d] for d in datasets) + " |",
             "|---|---|---|---|" + "---|" * len(datasets)]
    for v in variants:
        ratio, wins, n = geo_ratio(c, v, "base")
        if n == 0:
            continue
        per = []
        for d in datasets:
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


def fig_solar_error_by_start(variants, path, pred_dir=RES / "solar_preds", split=(0.8, 0.1, 0.1)):
    """Per-window test MSE as a function of the forecast start date."""
    from qkanfwp import data
    from experiments.run_solar import HORIZON, WINDOW

    raw, scaled, _ = data.load_sunspots()
    _, y = data.make_windows(scaled, WINDOW, HORIZON)
    dates = 1749 + (np.arange(len(raw)) + 0.5) / 12
    fig, ax = plt.subplots(figsize=(8.6, 3.4))
    drawn = False
    for v, color, label in variants:
        files = sorted(pred_dir.glob(f"{v}_seed*.npz"))
        if not files:
            continue
        loaded = [np.load(f) for f in files]
        idx = loaded[0]["test_index"]
        err = np.stack([((f["preds"].astype(np.float32) - y[idx]) ** 2).mean(1) for f in loaded])
        t = dates[idx + WINDOW]
        ax.fill_between(t, err.mean(0) - err.std(0), err.mean(0) + err.std(0), color=color, alpha=0.18, linewidth=0)
        ax.plot(t, err.mean(0), color=color, label=label)
        drawn = True
    if not drawn:
        plt.close(fig)
        return
    ax.set_xlabel("forecast start (first month of the 132-month target)")
    ax.set_ylabel("scaled MSE of that window")
    ax.set_title("Test error by forecast start date (mean ± std over seeds)")
    ax.legend(loc="upper right")
    fig.tight_layout()
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
    axes[1].set_title(f"Multi-timescale gates: 5 of {km.shape[1]} gate groups")
    axes[1].legend(fontsize=8.5, title="gate group", title_fontsize=8.5, loc="lower left", ncol=2)
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
    "base_tuned": "Baseline",
    "skip_dif3@cos30": "Extended (residual + Δ-tokens)",
    "skip_dif3": "Extended (residual + Δ-tokens)",
    "skip_mtg_dif3@cos30": "Extended + multi-timescale gates",
    "skip@cos30": "Baseline + residual read-out",
    "dif3@cos30": "Baseline + Δ-tokens",
    "mtg@cos30": "Baseline + multi-timescale gates",
    "skip_mtg@cos30": "Baseline + residual + multi-timescale gates",
    "skip": "Baseline + residual read-out",
    "dif3": "Baseline + Δ-tokens",
    "mtg": "Baseline + multi-timescale gates",
    "ungated": "Ungated (additive) FWP",
    "base_big": "Larger baseline",
    "base_big@cos30": "Larger baseline (193 params)",
    "ar_hqkan@cos30": "No fast-weight memory: HQKAN on last Δ-token",
    "lstm@cos100": "LSTM (hidden 5)",
    "lstm_ext@cos30": "LSTM + residual + Δ-tokens",
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
    "base@lr1": "Baseline, lr 1e-3",
    "mtg@lr1": "+ multi-timescale gates, lr 1e-3",
}


class TableNames(dict):
    """Row / column labels for tables: the figure labels plus the protocol."""

    def get(self, v, default=None):
        name = NAMES.get(v, default or v)
        if v == "base" or name.endswith("protocol") or "lr" in name:
            return name
        return name + (", tuned lr" if ("@cos" in v or v == "base_tuned") else ", lr 1e-3")

    __getitem__ = get


def single_change_report():
    """Effect of each individual change (learning rate, residual read-out,
    Δ-tokens, grouped gates) on the re-implemented baseline."""
    FIG.mkdir(exist_ok=True)
    out = []
    ts_files = sorted(RES.glob("final_timeseries*.jsonl"))
    if ts_files:
        rows = load(ts_files, protocol="paper")
        c = cells(rows)
        params = {r["variant"]: r["params"] for r in rows}
        # "tuned baseline" = baseline with its validated learning rate (1e-2 on JC, 3e-2 elsewhere)
        for (d, w, v), vals in list(c.items()):
            if (v == "base@cos10" and d == "jc") or (v == "base@cos30" and d != "jc"):
                c[(d, w, "base_tuned")] = vals
        params["base_tuned"] = params.get("base", 0)
        main_v = ["base", "base_tuned", "skip_dif3@cos30", "skip_mtg_dif3@cos30"]
        out += ["## Time series: main comparison (test MSE, mean ± std over 5 seeds)\n",
                table_cells(c, main_v, TableNames()), ""]
        groups = [
            ("Paper protocol (lr 1e-3)", ["ungated", "mtg", "skip", "dif3", "skip_dif3"]),
            ("Tuned learning rate", ["base_tuned", "base_big@cos30", "mtg@cos30", "skip@cos30", "skip_mtg@cos30",
                                     "dif3@cos30", "skip_dif3@cos30", "skip_mtg_dif3@cos30"]),
            ("Controls (tuned learning rate)", ["ar_hqkan@cos30", "lstm@cos100", "lstm_ext@cos30"]),
        ]
        abl = [v for _, vs in groups for v in vs if any(k[2] == v for k in c)]
        # restrict the ablation to the cells every ablation variant was run on
        sub = {k: v for k, v in c.items() if k[0] != "jc" and k[1] in (16, 64)}
        fig_ablation(sub, groups, NAMES, FIG / "single_change_ablation.png",
                     "Ablation: test MSE relative to the paper-protocol baseline")
        abl_names = TableNames()
        out += ["## Time series: ablation (5 series × N ∈ {16, 64}; ratio of seed-mean test MSE to the paper-protocol baseline)\n",
                table_ratio(sub, abl, abl_names, params, datasets=[d for d in DATASETS if d != "jc"]), ""]
        full = ["base_tuned", "skip_dif3@cos30", "skip_mtg_dif3@cos30"]
        out += ["## Time series: all 24 cells\n", table_ratio(c, full, TableNames(), params), ""]
        other = ["gqkan_fwp", "gqkan_fwp@cos30", "gqkan_fwp_ext@cos30", "g_qkanfwp", "g_qkanfwp@cos30", "g_qkanfwp_ext@cos30"]
        if any(k[2] in other for k in c):
            out += ["## Other paper variants (N = 16)\n", table_cells(c, [v for v in other if any(k[2] == v for k in c)], TableNames()), ""]

    solar_files = [f for f in sorted(RES.glob("final_solar*.jsonl")) if f.stat().st_size]
    if solar_files:
        by, by622 = {}, {}
        for f in solar_files:
            for k, v in solar_rows(f).items():
                for r in v:
                    paper_split = tuple(r.get("split") or (0.8, 0.1, 0.1)) == (0.8, 0.1, 0.1)
                    (by if paper_split else by622).setdefault(k, []).append(r)
        order = [v for v in ["base", "chrono", "mtg", "mtg_ctx12s12", "ctx12s12", "ungated", "lstm_s",
                             "base@lr1", "mtg@lr1"] if v in by]
        # validation-period MSE of the selected checkpoint, for the val-vs-test discussion
        out += ["## Solar: validation-period scaled MSE of the selected checkpoint\n",
                "| Model | Val. MSE | Best epoch |", "|---|---|---|"]
        for v in order:
            vm = np.array([r["val"]["mse"] for r in by[v]])
            ep = np.array([r["val"]["epoch"] for r in by[v]])
            out.append(f"| {SOLAR_NAMES[v]} | {vm.mean():.4f} ± {vm.std():.4f} | {ep.mean():.0f} |")
        out.append("")
        out += ["## Solar cycle forecasting (test split, best-validation checkpoint)\n", table_solar(by, order, SOLAR_NAMES), ""]
        if "base" in by:
            b = np.array([r["test"]["mse"] for r in by["base"]])
            for v in order:
                if v == "base":
                    continue
                a = np.array([r["test"]["mse"] for r in by[v]])
                out.append(f"- {SOLAR_NAMES[v]}: scaled MSE {a.mean() / b.mean() - 1:+.1%} vs baseline, Welch p = {welch_p(a, b):.3g}")
            out.append("")
        if by622:
            order2 = [v for v in order if v in by622]
            out += ["## Solar robustness check: 60/20/20 split (test targets 1970.8–2026.1, five cycles)\n",
                    table_solar(by622, order2, SOLAR_NAMES), ""]
            if "base" in by622:
                b = np.array([r["test"]["mse"] for r in by622["base"]])
                for v in order2:
                    if v != "base":
                        a = np.array([r["test"]["mse"] for r in by622[v]])
                        out.append(f"- {SOLAR_NAMES[v]}: scaled MSE {a.mean() / b.mean() - 1:+.1%} vs baseline, Welch p = {welch_p(a, b):.3g}")
                out.append("")
    (RES / "tables_single_change.md").write_text("\n".join(out) + "\n")


# ===========================================================================
# Final, parameter-matched comparison
# ===========================================================================
OM = "om_c0h6r1_p5@cos30"  # observable-memory FWP (QKAN-FWP-O), see qkanfwp/obsmem.py
OURS = "pmx_diff8_edge_h3l2@cos30"  # improved gated QKAN-FWP (paper's read-before-write order)
OURS_WF = "pmx_diff8_edge_h3l2_wf@cos30"  # same, write-then-read
STATIC = "ar_hqkan8@cos30"  # static HQKAN on the last token (no fast weights)
SOLAR_OURS = "mtg_cyc_pm"

# Test MSE reported in the paper (Tables 4-6): its GQKAN-QKANFWP, and the best
# of the four models it lists for that cell.
PAPER = {
    "bessel": dict(own=[2.5e-5, 1.1e-5, 1.5e-5, 2.1e-5], best=[2.5e-5, 1.1e-5, 1.5e-5, 2.1e-5]),
    "shm": dict(own=[8.9e-5, 3.6e-5, 1.9e-5, 4.3e-5], best=[8.9e-5, 3.6e-5, 1.9e-5, 4.3e-5]),
    "narma5": dict(own=[2.0e-5, 2.8e-5, 4.8e-5, 8.7e-5], best=[5e-6, 1.2e-5, 1.1e-5, 1.0e-5]),
    "narma10": dict(own=[1.00e-4, 5.2e-5, 5.5e-5, 1.08e-4], best=[4.3e-5, 2e-6, 1.6e-5, 2.0e-5]),
    "dqc": dict(own=[4.8e-5, 4.1e-5, 8.9e-5, 2.21e-4], best=[3.3e-5, 4.1e-5, 5.3e-5, 1.17e-4]),
    "jc": dict(own=[2.01e-4, 1.59e-4, 1.96e-4, 3.22e-4], best=[9.2e-5, 7.0e-5, 1.96e-4, 3.7e-5]),
}
# Best printed test MSE of the follow-up paper arXiv:2607.27945 (Tables II-V; 100 epochs,
# best of its five selected models), for N = 8, 16, 32, 64.
PAPER_CMG = {
    "bessel": [8.73e-6, 4.94e-6, 2.90e-6, 6.37e-6],
    "shm": [1.17e-5, 1.42e-5, 3.60e-6, 1.00e-5],
    "narma5": [4.91e-6, 5.21e-6, 7.13e-6, 9.58e-6],
    "narma10": [2.25e-5, 2.55e-6, 1.33e-5, 1.36e-5],
    "dqc": [3.52e-6, 6.94e-6, 7.82e-6, 4.77e-6],
    "jc": [1.66e-5, 3.18e-6, 9.10e-6, 7.04e-6],
}
PAPER_SOLAR = dict(params=12474, mse=(0.0168, 0.0016), pae=(39.59, 2.82), pte=(21.89, 1.57))

FINAL_NAMES = {
    "base": "Baseline GQKAN-QKANFWP, paper protocol",
    "base_tuned": "Baseline GQKAN-QKANFWP, tuned lr",
    "gqkan_fwp_tuned": "GQKAN-FWP, tuned lr",
    "g_qkanfwp_tuned": "G-QKANFWP, tuned lr",
    OURS: "QKAN-FWP+",
    OURS_WF: "QKAN-FWP+ write-first",
    STATIC: "HQKAN-Δ, no fast weights",
    "pmx_diff8_edge_h3l2_noskip@cos30": "QKAN-FWP+ without residual read-out",
    "pmx_diff8_scalar_h3l2@cos30": "QKAN-FWP+ with the paper's scalar gate",
    "pm_diff8_edge_h3l2@cos30": "QKAN-FWP+ with float32 differences",
    "pmx_diff3_edge_h3l2@cos30": "QKAN-FWP+ with 3-dim instead of 8-dim Δ-tokens",
    "pmx_diff1_edge_h3l2@cos30": "QKAN-FWP+ without Δ-tokens (scalar input)",
    "ar_hqkan8": "HQKAN-Δ: no fast weights (static HQKAN, same tokens)",
    "lstm_ext8": "LSTM with the same tokens and residual (not QKAN)",
}


def ratio_stats(c, v, ref):
    r, wins, n = geo_ratio(c, v, ref)
    rat = [np.mean(list(c[(d, w, v)].values())) / np.mean(list(c[(d, w, ref)].values()))
           for (d, w, vv) in c if vv == v and (d, w, ref) in c]
    return r, wins, n, (min(rat), max(rat)) if rat else (np.nan, np.nan)


def solar_eval_anchor(split):
    """Metrics of the zero-parameter seasonal-naive anchor (the untrained
    ``skip='cycle'`` model): repeat the last 132 months, 13-month smoothed."""
    import torch

    from experiments.run_solar import HORIZON, VARIANTS, WINDOW, build
    from qkanfwp import data

    raw, scaled, (lo, hi) = data.load_sunspots()
    x, y = data.make_windows(scaled, WINDOW, HORIZON)
    x, y = torch.tensor(x), torch.tensor(y)
    parts = data.chrono_split(len(x), split)
    model = build(VARIANTS[SOLAR_OURS])
    out = {}
    with torch.no_grad():
        for name, idx in zip(("val", "test"), parts[1:]):
            pred = model.cycle_anchor(x[idx])
            tgt = y[idx]
            out[name] = dict(
                mse=((pred - tgt) ** 2).mean().item(),
                pae=((tgt.max(1).values - pred.max(1).values).abs() * (hi - lo)).mean().item(),
                pte=(tgt.argmax(1) - pred.argmax(1)).abs().float().mean().item(),
            )
    return out


def reference_tables(c, baselines, tuned_b, names, params):
    """Closed-form linear reference, reproduction gap to the printed numbers,
    and robustness checks (read-out, normalisation, NARMA transient)."""
    out = []
    gmean = lambda xs: float(np.exp(np.mean(np.log(xs))))  # noqa: E731
    m = lambda d, w, v, cc=None: float(np.mean(list((cc or c)[(d, w, v)].values())))  # noqa: E731

    # ---- (a) linear autoregression fitted by least squares ----
    ref_file = RES / "reference_linear_ar.json"
    if ref_file.exists():
        ar = json.loads(ref_file.read_text())
        out += ["## Closed-form linear reference vs every model (test MSE)\n",
                "| Dataset | N | Best tuned re-implemented baseline | QKAN-FWP+ | HQKAN-Δ | Printed best, 2605.06734 | Printed best, 2607.27945 | Linear AR(3), 4 params | Linear AR(8), 9 params |",
                "|---|---|---|---|---|---|---|---|---|"]
        n = n_ar8_ours = n_ar8_paper = n_ar3_ours = 0
        for d in DATASETS:
            for i, w in enumerate(WINDOWS):
                vals = [min(m(d, w, b) for b in tuned_b), m(d, w, OURS), m(d, w, STATIC), PAPER[d]["best"][i],
                        PAPER_CMG[d][i], ar[f"{d}|{w}|3"]["test"], ar[f"{d}|{w}|8"]["test"]]
                lo = min(vals)
                out.append(f"| {TITLES[d]} | {w} | " + " | ".join(f"**{v:.1e}**" if v == lo else f"{v:.1e}" for v in vals) + " |")
                n += 1
                n_ar8_ours += vals[6] < vals[2]
                n_ar3_ours += vals[5] < vals[2]
                n_ar8_paper += vals[6] < min(vals[3], vals[4])
        out += ["", f"- Linear AR(8) is below HQKAN-Δ in {n_ar8_ours}/{n} cells and linear AR(3) in {n_ar3_ours}/{n} cells.",
                f"- Linear AR(8) is below the best printed number of both papers in {n_ar8_paper}/{n} cells.", ""]

    # ---- (b) reproduction gap ----
    wf = cells(load([RES / "robust_writefirst.jsonl"], protocol="paper")) if (RES / "robust_writefirst.jsonl").exists() else {}
    out += ["## Reproduction gap: re-implemented GQKAN-QKANFWP (paper protocol) vs the number printed in the paper\n",
            "| Dataset | N | Printed (2605.06734) | Re-implementation, read-then-write | ratio | Re-implementation, write-then-read | ratio |",
            "|---|---|---|---|---|---|---|"]
    r_rf, r_wf = [], []
    for d in DATASETS:
        for i, w in enumerate(WINDOWS):
            p_ = PAPER[d]["own"][i]
            a = m(d, w, "base")
            r_rf.append(a / p_)
            row = f"| {TITLES[d]} | {w} | {p_:.1e} | {a:.2e} | {a / p_:.1f}× |"
            if (d, w, "base+wf") in wf:
                b = m(d, w, "base+wf", wf)
                r_wf.append(b / p_)
                row += f" {b:.2e} | {b / p_:.1f}× |"
            else:
                row += " – | – |"
            out.append(row)
    out += ["", f"- Geometric-mean ratio over the 24 cells (read-then-write): {gmean(r_rf):.1f}×; over the 20 cells of the five 300-point series: "
            f"read-then-write {gmean(r_rf[:20]):.1f}×, write-then-read {gmean(r_wf):.1f}×." if r_wf else "", ""]
    # how far are our final models from the printed numbers, in the same terms
    for o in (OURS, STATIC):
        if any(k[2] == o for k in c):
            r_own = [m(d, w, o) / PAPER[d]["own"][i] for d in DATASETS for i, w in enumerate(WINDOWS)]
            r_best = [m(d, w, o) / min(PAPER[d]["best"][i], PAPER_CMG[d][i]) for d in DATASETS for i, w in enumerate(WINDOWS)]
            out.append(f"- {names[o]}: {1 / gmean(r_own):.0f}× below the printed GQKAN-QKANFWP numbers (geometric mean, 24 cells); "
                       f"{1 / gmean(r_best):.1f}× below the best printed number of either paper, lower in {sum(r < 1 for r in r_best)}/24 cells.")
    out.append("")

    # ---- (c) robustness at N = 16 ----
    conds = [("Default (as in all tables above)", c, {"base": "base", "tuned": "base_tuned", "fwp": OURS, "static": STATIC}, c)]
    f = RES / "robust_exactz.jsonl"
    if f.exists():
        cz = cells(load([f], protocol="paper"))
        for (d, w, v), vals in list(cz.items()):
            if (v == "base+z@cos10" and d == "jc") or (v == "base+z@cos30" and d != "jc"):
                cz[(d, w, "tuned+z")] = vals
        # QKAN-FWP-O always measures physical <X>, <Y>, <Z>: its default numbers apply here
        conds.append(("Physical read-out ⟨Z⟩ = |a|² − |b|² in every DARUAN circuit", cz,
                      {"base": "base+z", "tuned": "tuned+z", "fwp": "pmx_diff8_edge_h3l2+z@cos30", "static": "ar_hqkan8+z@cos30"}, c))
    f = RES / "robust_norm.jsonl"
    if f.exists():
        rows_n = [r for r in load([f], protocol="paper") if r.get("norm") == "train"]
        cn = cells(rows_n)
        for (d, w, v), vals in list(cn.items()):
            if (v == "base@cos10" and d == "jc") or (v == "base@cos30" and d != "jc"):
                cn[(d, w, "base_tuned")] = vals
        conds.append(("Min–max scaling fitted on the training part only", cn,
                      {"base": "base", "tuned": "base_tuned", "fwp": OURS, "static": STATIC}, cn))
    out += ["## Robustness checks at N = 16 (test MSE, 5 seeds)\n"]
    for title, cc, v, c_om in conds:
        ds = [d for d in DATASETS if all((d, 16, v[k]) in cc for k in v)]
        if not ds:
            continue
        has_om = all((d, 16, OM) in c_om for d in ds)
        out += [f"**{title}**\n", "| Dataset | Baseline, paper protocol | Baseline, tuned lr | QKAN-FWP+ | HQKAN-Δ |" + (" QKAN-FWP-O |" if has_om else ""),
                "|---|---|---|---|---|" + ("---|" if has_om else "")]
        for d in ds:
            out.append(f"| {TITLES[d]} | " + " | ".join(f"{m(d, 16, v[k], cc):.2e}" for k in ("base", "tuned", "fwp", "static"))
                       + (f" | {m(d, 16, OM, c_om):.2e}" if has_om else "") + " |")
        rf = gmean([m(d, 16, v["fwp"], cc) / m(d, 16, v["tuned"], cc) for d in ds])
        rs = gmean([m(d, 16, v["static"], cc) / m(d, 16, v["tuned"], cc) for d in ds])
        wf_ = sum(m(d, 16, v["fwp"], cc) < m(d, 16, v["tuned"], cc) for d in ds)
        ws = sum(m(d, 16, v["static"], cc) < m(d, 16, v["tuned"], cc) for d in ds)
        line = (f"- vs the tuned baseline over {len(ds)} datasets: QKAN-FWP+ {1 / rf:.0f}× lower ({wf_}/{len(ds)}), "
                f"HQKAN-Δ {1 / rs:.0f}× lower ({ws}/{len(ds)})")
        if has_om:
            ro = gmean([m(d, 16, OM, c_om) / m(d, 16, v["tuned"], cc) for d in ds])
            wo = sum(m(d, 16, OM, c_om) < m(d, 16, v["tuned"], cc) for d in ds)
            line += f", QKAN-FWP-O {1 / ro:.2g}× lower ({wo}/{len(ds)})"
        out += ["", line + ".", ""]

    # ---- (d) NARMA without the start-up transient ----
    f = RES / "robust_burnin.jsonl"
    if f.exists():
        cb = cells(load([f], protocol="paper"))
        bcols = ["base", "base@cos30", OURS, STATIC] + ([OM] if any(k[2] == OM for k in cb) else [])
        out += ["## NARMA without the start-up transient (200 burn-in steps discarded; test MSE, 5 seeds)\n",
                "| Dataset | N | Baseline, paper protocol | Baseline, tuned lr | QKAN-FWP+ | HQKAN-Δ |" + (" QKAN-FWP-O |" if OM in bcols else ""),
                "|---|---|---|---|---|---|" + ("---|" if OM in bcols else "")]
        for d, t_ in (("narma5b", "NARMA5"), ("narma10b", "NARMA10")):
            for w in (8, 16):
                if all((d, w, v) in cb for v in bcols):
                    out.append(f"| {t_} | {w} | " + " | ".join(f"{m(d, w, v, cb):.2e}" for v in bcols) + " |")
        out.append("")
    return out


def final_report():
    out = []
    rows = load(sorted(RES.glob("final_timeseries*.jsonl")) + [f for f in (RES / "final_om.jsonl",) if f.exists()],
                protocol="paper")
    c = cells(rows)
    params = {r["variant"]: r["params"] for r in rows}
    # each baseline with its validated learning rate
    for (d, w, v), vals in list(c.items()):
        if (v == "base@cos10" and d == "jc") or (v == "base@cos30" and d != "jc"):
            c[(d, w, "base_tuned")] = vals
    params["base_tuned"] = params["base"]
    # the paper's other QKAN variants, each with its validated learning rate
    tuned = {"gqkan_fwp_tuned": {"jc": "gqkan_fwp@cos30", "default": "gqkan_fwp@cos100"},
             "g_qkanfwp_tuned": {"jc": "g_qkanfwp@cos10", "default": "g_qkanfwp@cos30"}}
    for name, lr in tuned.items():
        for (d, w, v), vals in list(c.items()):
            if v == lr.get(d, lr["default"]):
                c[(d, w, name)] = vals
                params[name] = params[v]
    controls = {}
    for fam in ("ar_hqkan8", "lstm_ext8"):
        got = sorted({k[2] for k in c if k[2].startswith(fam + "@")})
        if got:
            controls[fam] = got[-1]
            params[fam] = params[got[-1]]
            for (d, w, v), vals in list(c.items()):
                if v == got[-1]:
                    c[(d, w, fam)] = vals
    if not any(k[2] == OURS for k in c):
        return
    names = dict(FINAL_NAMES)
    baselines = [v for v in ("base", "base_tuned", "gqkan_fwp_tuned", "g_qkanfwp_tuned") if any(k[2] == v for k in c)]

    def label(v):
        return f"{names[v]} ({params[v]} params)"

    ours_all = [v for v in (OURS, OURS_WF, STATIC) if any(k[2] == v and k[1] == 8 for k in c)]
    out += ["## Final time-series comparison (test MSE, mean ± std over 5 seeds)\n",
            table_cells(c, baselines + ours_all, {v: label(v) for v in baselines + ours_all}), ""]
    for ours in ours_all:
        out += [f"## {names[ours]} ({params[ours]} params) vs each baseline over the 24 cells\n",
                "| Baseline | Params | Model ÷ baseline (geo-mean test MSE) | Cells where the model is better | Smallest / largest factor |",
                "|---|---|---|---|---|"]
        for b in baselines:
            r, wins, n, (lo_, hi_) = ratio_stats(c, ours, b)
            out.append(f"| {names[b]} | {params[b]} | {r:.2g} (**{1 / r:.0f}× lower**) | {wins}/{n} | {1 / hi_:.1f}× / {1 / lo_:.0f}× |")
        # best baseline in each cell (the hardest comparison)
        best_wins = n_cells = 0
        for d in DATASETS:
            for w in WINDOWS:
                if (d, w, ours) not in c:
                    continue
                bb = min(np.mean(list(c[(d, w, b)].values())) for b in baselines if (d, w, b) in c)
                n_cells += 1
                best_wins += np.mean(list(c[(d, w, ours)].values())) < bb
        out += ["", f"Better than the best of all re-implemented baselines in {best_wins}/{n_cells} cells.", ""]

    # per-dataset summary: geometric mean over the four windows of the seed-mean test MSE
    def gm(d, v):
        vals = [np.mean(list(c[(d, w, v)].values())) for w in WINDOWS if (d, w, v) in c]
        return float(np.exp(np.mean(np.log(vals)))) if len(vals) == len(WINDOWS) else float("nan")

    tuned_b = [b for b in baselines if b != "base"]
    head = [o for o in (OURS, STATIC) if o in ours_all]  # the two headline models
    short = {OURS: "QKAN-FWP+", STATIC: "HQKAN-Δ"}
    ar_ref = json.loads((RES / "reference_linear_ar.json").read_text()) if (RES / "reference_linear_ar.json").exists() else None
    gm_list = lambda xs: float(np.exp(np.mean(np.log(xs))))  # noqa: E731
    out += ["## Per-dataset summary (geometric mean over N ∈ {8, 16, 32, 64} of the seed-mean test MSE)\n",
            "| Dataset | Printed in 2605.06734 (its GQKAN-QKANFWP) | Re-implemented baseline, paper protocol | Best tuned re-implemented baseline | "
            + " | ".join(f"{short[o]} ({params[o]} params)" for o in head) + " | Linear AR(8), least squares (9 params) |",
            "|---|---|---|---|" + "---|" * (len(head) + 1)]
    for d in DATASETS:
        bb = min(gm(d, b) for b in tuned_b)
        row = f"| {TITLES[d]} | {gm_list(PAPER[d]['own']):.1e} | {gm(d, 'base'):.1e} | {bb:.1e} | " + " | ".join(f"{gm(d, o):.1e}" for o in head)
        row += f" | {gm_list([ar_ref[f'{d}|{w}|8']['test'] for w in WINDOWS]):.1e} |" if ar_ref else " | – |"
        out.append(row)
    out.append("")

    out += ["## Models of this repository vs the numbers printed in the paper (Tables 4–6)\n",
            "| Dataset | N | Paper: GQKAN-QKANFWP | Paper: best of its models | " + " | ".join(names[o] for o in ours_all) + " |",
            "|---|---|---|---|" + "---|" * len(ours_all)]
    tally = {o: [0, 0, 0] for o in ours_all}
    for d in DATASETS:
        for i, w in enumerate(WINDOWS):
            own, best = PAPER[d]["own"][i], PAPER[d]["best"][i]
            cols = []
            for o in ours_all:
                if (d, w, o) not in c:
                    cols.append("–")
                    continue
                m, sd = mean_std(c[(d, w, o)])
                tally[o][0] += 1
                tally[o][1] += m < own
                tally[o][2] += m < best
                txt = f"{m:.2e} ± {sd:.1e}"
                cols.append(f"**{txt}**" if m < best else txt)
            out.append(f"| {TITLES[d]} | {w} | {own:.1e} | {best:.1e} | " + " | ".join(cols) + " |")
    out.append("")
    for o in ours_all:
        n_all, n_own, n_best = tally[o]
        out.append(f"- {names[o]}: below the paper's GQKAN-QKANFWP number in {n_own}/{n_all} cells, below the paper's best number in {n_best}/{n_all} cells (bold).")
    out.append("")

    abl = [OURS, OURS_WF, "pmx_diff8_edge_h3l2_noskip@cos30", "pmx_diff1_edge_h3l2@cos30", "pmx_diff3_edge_h3l2@cos30",
           "pm_diff8_edge_h3l2@cos30", "pmx_diff8_scalar_h3l2@cos30", "ar_hqkan8", "lstm_ext8"]
    abl = [v for v in abl if any(k[2] == v for k in c)]
    sub = {k: v for k, v in c.items() if k[0] != "jc" and k[1] in (16, 64)}
    groups = [("Re-implemented paper models (tuned learning rate)", [b for b in baselines if b != "base"]),
              ("QKAN-FWP+ and what each part contributes", [v for v in abl if v not in ("ar_hqkan8", "lstm_ext8")]),
              ("Without fast weights", [v for v in ("ar_hqkan8", "lstm_ext8") if v in abl])]
    fig_ablation(sub, groups, {v: f"{names[v]} ({params[v]})" for v in names if v in params}, FIG / "timeseries_ablation.png",
                 "QKAN-FWP+ and its parts: test MSE relative to the paper-protocol baseline")
    out += ["## QKAN-FWP+ ablation (5 series × N ∈ {16, 64}; ratio to the paper-protocol baseline)\n",
            table_ratio(sub, [b for b in baselines if b != "base"] + abl, {v: names[v] for v in names}, params,
                        datasets=[d for d in DATASETS if d != "jc"]), ""]
    out += reference_tables(c, baselines, tuned_b, names, params)

    # ---------------- solar ----------------
    by, by622, by715 = {}, {}, {}
    for f in sorted(RES.glob("final_solar*.jsonl")):
        for k, v in solar_rows(f).items():
            for r in v:
                split = tuple(r.get("split") or (0.8, 0.1, 0.1))
                {(0.8, 0.1, 0.1): by, (0.6, 0.2, 0.2): by622, (0.7, 0.15, 0.15): by715}[split].setdefault(k, []).append(r)
    if SOLAR_OURS in by:
        snames = {"base": "Baseline GQKAN-QKANFWP (scalar gate)", SOLAR_OURS: "QKAN-FWP+: grouped gates + last-cycle residual read-out",
                  "mtg_pm": "QKAN-FWP+ without the last-cycle read-out (gates only)", "base_cyc": "QKAN-FWP+ without grouped gates (read-out only)",
                  "base@lr1": "Baseline, lr 1e-3", "base@lr2": "Baseline, lr 2e-3",
                  SOLAR_OURS + "@lr1": "QKAN-FWP+, lr 1e-3", SOLAR_OURS + "@lr2": "QKAN-FWP+, lr 2e-3"}

        def srow(name, params_, m, extra=""):
            return f"| {name} | {params_} | {m['mse']} | {m['pae']} | {m['pte']} | {extra} |"

        def fmt(rs, part="test"):
            f = lambda k, p: "{:.{p}f} ± {:.{p}f}".format(np.mean([r[part][k] for r in rs]), np.std([r[part][k] for r in rs]), p=p)  # noqa: E731
            return dict(mse=f("mse", 4), pae=f("pae", 1), pte=f("pte", 1))

        anchor = solar_eval_anchor((0.8, 0.1, 0.1))
        out += ["## Solar cycle: final comparison (paper split and protocol, lr 2.5e-3, 5 seeds, test metrics)\n",
                "| Model | Params | Scaled MSE ↓ | PAE ↓ | PTE ↓ | Val. loss |", "|---|---|---|---|---|---|"]
        for v in ["base", SOLAR_OURS, "mtg_pm", "base_cyc"]:
            if v in by:
                vl = np.array([r["val"]["loss"] for r in by[v]])
                out.append(srow(snames[v], f"{by[v][0]['params']:,}", fmt(by[v]), f"{vl.mean():.2f} ± {vl.std():.2f}"))
        a = anchor["test"]
        out.append(f"| *Reference: repeat the last cycle, 13-month smoothed (no training)* | 0 | {a['mse']:.4f} | {a['pae']:.1f} | {a['pte']:.1f} | – |")
        ps = PAPER_SOLAR
        out.append(f"| *Paper's reported GQKAN-QKANFWP* | {ps['params']:,} | {ps['mse'][0]:.4f} ± {ps['mse'][1]:.4f} | {ps['pae'][0]:.2f} ± {ps['pae'][1]:.2f} | {ps['pte'][0]:.2f} ± {ps['pte'][1]:.2f} | – |")
        out.append("")
        b = by["base"]
        for k in ("mse", "pae", "pte"):
            x_, y_ = np.array([r["test"][k] for r in by[SOLAR_OURS]]), np.array([r["test"][k] for r in b])
            out.append(f"- QKAN-FWP+ vs baseline, {k.upper()}: {x_.mean() / y_.mean() - 1:+.1%} (Welch p = {welch_p(x_, y_):.2g})")
        out.append("")

        out += ["## Solar cycle: the paper's learning-rate grid (5 seeds each)\n",
                "| Model | lr | Val. loss (selection criterion) | Scaled MSE | PAE | PTE |", "|---|---|---|---|---|---|"]
        for fam, tag in (("base", "Baseline"), (SOLAR_OURS, "QKAN-FWP+")):
            grid = [(lr, v) for lr, v in (("1e-3", fam + "@lr1"), ("2e-3", fam + "@lr2"), ("2.5e-3", fam)) if v in by]
            best = min(grid, key=lambda g: np.mean([r["val"]["loss"] for r in by[g[1]]]))[1] if grid else None
            for lr, v in grid:
                m = fmt(by[v])
                vl = np.mean([r["val"]["loss"] for r in by[v]])
                mark = " ← selected" if v == best else ""
                out.append(f"| {tag} | {lr} | {vl:.3f}{mark} | {m['mse']} | {m['pae']} | {m['pte']} |")
        out.append("")

        if SOLAR_OURS in by622 and "base" in by622:
            anchor2 = solar_eval_anchor((0.6, 0.2, 0.2))["test"]
            out += ["## Solar cycle: second split (60/20/20, test targets 1971–2026, five cycles)\n",
                    "| Model | Params | Scaled MSE ↓ | PAE ↓ | PTE ↓ | Val. loss |", "|---|---|---|---|---|---|"]
            for v in ["base", SOLAR_OURS, "mtg"]:
                if v in by622:
                    vl = np.array([r["val"]["loss"] for r in by622[v]])
                    nm = snames.get(v, "Baseline + grouped gates (12,632 parameters)")
                    out.append(srow(nm, f"{by622[v][0]['params']:,}", fmt(by622[v]), f"{vl.mean():.2f} ± {vl.std():.2f}"))
            out.append(f"| *Reference: repeat the last cycle, 13-month smoothed* | 0 | {anchor2['mse']:.4f} | {anchor2['pae']:.1f} | {anchor2['pte']:.1f} | – |")
            out.append("")
            for k in ("mse", "pae", "pte"):
                x_, y_ = np.array([r["test"][k] for r in by622[SOLAR_OURS]]), np.array([r["test"][k] for r in by622["base"]])
                out.append(f"- QKAN-FWP+ vs baseline, {k.upper()}: {x_.mean() / y_.mean() - 1:+.1%} (Welch p = {welch_p(x_, y_):.2g})")
            out.append("")
        if SOLAR_OURS in by715 and "base" in by715:
            anchor3 = solar_eval_anchor((0.7, 0.15, 0.15))["test"]
            out += ["## Solar cycle: third split (70/15/15, test targets 1982–2026, four cycles; 3 seeds)\n",
                    "| Model | Params | Scaled MSE ↓ | PAE ↓ | PTE ↓ | Val. loss |", "|---|---|---|---|---|---|"]
            for v in ["base", SOLAR_OURS]:
                vl = np.array([r["val"]["loss"] for r in by715[v]])
                out.append(srow(snames[v], f"{by715[v][0]['params']:,}", fmt(by715[v]), f"{vl.mean():.2f} ± {vl.std():.2f}"))
            out.append(f"| *Reference: repeat the last cycle, 13-month smoothed* | 0 | {anchor3['mse']:.4f} | {anchor3['pae']:.1f} | {anchor3['pte']:.1f} | – |")
            out.append("")
            for k in ("mse", "pae", "pte"):
                x_, y_ = np.array([r["test"][k] for r in by715[SOLAR_OURS]]), np.array([r["test"][k] for r in by715["base"]])
                out.append(f"- QKAN-FWP+ vs baseline, {k.upper()}: {x_.mean() / y_.mean() - 1:+.1%} (Welch p = {welch_p(x_, y_):.2g})")
            out.append("")
        pair = [("base", BLUE, "Baseline (scalar gate)"), (SOLAR_OURS, ORANGE, "QKAN-FWP+")]
        fig_solar_forecast(by, pair, FIG / "solar_forecast.png")
        fig_memory_kernel(FIG / "solar_memory_kernel.png", multi=SOLAR_OURS)
        fig_solar_error_by_start(pair, FIG / "solar_error_by_start.png")
        fig_solar_error_by_start(pair, FIG / "solar_error_by_start_split622.png", RES / "solar_preds_split622")
    (RES / "tables_final.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    single_change_report()
    final_report()
