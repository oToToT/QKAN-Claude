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
    axes[1].set_title("Multi-timescale gates: 5 of 20 gate groups")
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


def main():
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
        fig_base_vs_ext(c, [("base", INK2, "Baseline, paper protocol", "s"), ("base_tuned", BLUE, "Baseline, tuned lr", "o"),
                            ("skip_dif3@cos30", ORANGE, "Extended, tuned lr", "D"),
                            ("skip_mtg_dif3@cos30", AQUA, "Extended + multi-timescale gates", "^")],
                        FIG / "timeseries_main.png")
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
        fig_ablation(sub, groups, NAMES, FIG / "timeseries_ablation.png",
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
        fig_solar_forecast(by, [("base", BLUE, "Baseline (scalar gate)"), ("mtg", ORANGE, "Multi-timescale gates")],
                           FIG / "solar_forecast.png")
        fig_memory_kernel(FIG / "solar_memory_kernel.png")
        pair = [("base", BLUE, "Baseline (scalar gate)"), ("mtg", ORANGE, "Multi-timescale gates")]
        fig_solar_error_by_start(pair, FIG / "solar_error_by_start.png")
        fig_solar_error_by_start(pair, FIG / "solar_error_by_start_split622.png", RES / "solar_preds_split622")
    (RES / "tables.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
