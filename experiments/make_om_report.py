"""Tables and figures that compare all models of this repository, including
the observable-memory FWP (QKAN-FWP-O).

Reads results/final_timeseries*.jsonl, final_om.jsonl, final_cmg.jsonl,
family.jsonl, shot_noise.jsonl and final_solar*.jsonl; writes
results/tables_om.md and figures/om_*.png.
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
from experiments.aggregate import cells, geo_ratio, load  # noqa: E402
from experiments.make_figures import (  # noqa: E402
    BLUE, DATASETS, FIG, INK, INK2, ORANGE, OURS, PAPER, PAPER_CMG, RES, STATIC, TITLES, WINDOWS, mean_std,
)

GREEN, VIOLET, MAGENTA = "#008300", "#6250d6", "#e87ba4"  # palette slots 6, 7, 5
OM = "om_c0h6r1_p5@cos30"
OM_SMALL = "om_c0h4r1_p5@cos30"
OM_BASE = OM.partition("@")[0]

NAMES = {
    "base": "GQKAN-QKANFWP, paper protocol",
    "base_tuned": "GQKAN-QKANFWP, tuned lr",
    "gqkan_fwp_tuned": "GQKAN-FWP, tuned lr",
    "g_qkanfwp_tuned": "G-QKANFWP, tuned lr",
    "cmg": "CMG, lr 1e-3",
    "cmg_tuned": "CMG, tuned lr",
    "cmg_plus@cos30": "CMG + Δ-tokens + residual",
    OURS: "QKAN-FWP+",
    STATIC: "HQKAN-Δ",
    OM: "QKAN-FWP-O",
}
OUR_MODELS = [OURS, STATIC, OM]
EXTRA_ABLATIONS = [  # size / token-length variants of the full model
    (OM_SMALL, "4 circuits instead of 6"),
    ("om_c6h6r1_p5@cos30", "fixed token length 6 instead of min(8, N/2)"),
]
ABLATIONS = [
    ("static", "no fast weights (static observable R₀)"),
    ("delta", "sequential delta rule instead of the least-squares solve"),
    ("gnone", "no gate (additive statistics, uniform weights)"),
    ("gconst", "constant gate (not input dependent)"),
    ("pscalar", "one prior precision instead of one per feature"),
    ("nobase", "no base-activation (linear) term: Bloch features only"),
    ("classical", "no Bloch features: linear term only (classical control)"),
]
FAMILY_TITLES = {"shm": "Damped oscillation", "tones": "Two tones", "jc": "Jaynes–Cummings",
                 "henon": "Hénon map", "duffing": "Duffing"}
FAMILY_MODELS = [
    ("base", "GQKAN-QKANFWP (scalar gate)"),
    ("cmg", "CMG (scalar tokens)"),
    ("cmg_plus", "CMG + Δ-tokens + residual"),
    ("pmx_diff8_edge_h3l2", "QKAN-FWP+"),
    ("ar_hqkan8", "HQKAN-Δ (static)"),
    ("lstm_ext8", "LSTM, same tokens (not QKAN)"),
    (OM_BASE, "QKAN-FWP-O"),
]


def gmean(xs):
    return float(np.exp(np.mean(np.log(xs))))


def big(x):
    """Compact factor: 0.66, 3.4, 120, 5.4e5."""
    if x < 10:
        return f"{x:.2g}"
    if x < 10000:
        return f"{x:.0f}"
    mant, exp = f"{x:.1e}".split("e")
    return f"{mant}e{int(exp)}"


def m(c, d, w, v):
    return float(np.mean(list(c[(d, w, v)].values())))


# ---------------------------------------------------------------------------
def timeseries_part(out):
    files = sorted(RES.glob("final_timeseries*.jsonl")) + [p for p in (RES / "final_om.jsonl", RES / "final_cmg.jsonl") if p.exists()]
    rows = load(files, protocol="paper")
    c = cells(rows)
    sizes = defaultdict(set)
    for r in rows:
        sizes[r["variant"]].add(r["params"])
    # the token length of QKAN-FWP-O follows the window, so its size does too
    params = {v: (str(min(p)) if len(p) == 1 else f"{min(p)}–{max(p)}") for v, p in sizes.items()}
    if not any(k[2] == OM for k in c):
        return None, None
    for (d, w, v), vals in list(c.items()):
        if (v == "base@cos10" and d == "jc") or (v == "base@cos30" and d != "jc"):
            c[(d, w, "base_tuned")] = vals
    params["base_tuned"] = params["base"]
    # CMG with the better of its two tuned learning rates per dataset (judged on
    # the test split: this favours the baseline)
    for d in DATASETS:
        cand = {}
        for tag in ("cmg@cos10", "cmg@cos30"):
            ws = [w for w in WINDOWS if (d, w, tag) in c]
            if len(ws) == len(WINDOWS):
                cand[tag] = gmean([m(c, d, w, tag) for w in ws])
        if cand:
            best = min(cand, key=cand.get)
            for w in WINDOWS:
                c[(d, w, "cmg_tuned")] = c[(d, w, best)]
            params["cmg_tuned"] = params[best]
    ar_ref = json.loads((RES / "reference_linear_ar.json").read_text())
    lin = lambda d, w: ar_ref[f"{d}|{w}|8"]["test"]  # noqa: E731

    # the paper's other two QKAN variants, each with its validated learning rate
    for name, lr in {"gqkan_fwp_tuned": {"jc": "gqkan_fwp@cos30", "default": "gqkan_fwp@cos100"},
                     "g_qkanfwp_tuned": {"jc": "g_qkanfwp@cos10", "default": "g_qkanfwp@cos30"}}.items():
        for (d, w, v), vals in list(c.items()):
            if v == lr.get(d, lr["default"]):
                c[(d, w, name)] = vals
                params[name] = params[v]
    cells_ = [(d, w) for d in DATASETS for w in WINDOWS if (d, w, OM) in c]
    printed = {(d, w): min(PAPER[d]["best"][i], PAPER_CMG[d][i]) for d in DATASETS for i, w in enumerate(WINDOWS)}
    refs = [v for v in ("base", "base_tuned", "gqkan_fwp_tuned", "g_qkanfwp_tuned", "cmg", "cmg_tuned", "cmg_plus@cos30")
            if any(k[2] == v for k in c)]
    ours = [v for v in OUR_MODELS if any(k[2] == v for k in c)]

    # ---- per-dataset summary ----
    def gm(d, v):
        vals = [m(c, d, w, v) for w in WINDOWS if (d, w, v) in c]
        return gmean(vals) if len(vals) == len(WINDOWS) else float("nan")

    scols = [v for v in ("base_tuned", "cmg_tuned", "cmg_plus@cos30") if v in refs] + ours
    out += ["## Per-dataset summary (geometric mean over N ∈ {8, 16, 32, 64} of the seed-mean test MSE)\n",
            "| Dataset | Best printed in the two papers | " + " | ".join(f"{NAMES[v]} ({params[v]})" for v in scols) + " | *Linear AR(8) (9)* |",
            "|---|---|" + "---|" * (len(scols) + 1)]
    for d in DATASETS:
        vals = {v: gm(d, v) for v in scols}
        fin = [v for v in scols if np.isfinite(vals[v])]
        best = min(fin, key=lambda v: vals[v]) if fin else None
        out.append(f"| {TITLES[d]} | {gmean([printed[(d, w)] for w in WINDOWS]):.1e} | "
                   + " | ".join(("–" if not np.isfinite(vals[v]) else f"**{vals[v]:.1e}**" if v == best else f"{vals[v]:.1e}") for v in scols)
                   + f" | *{gmean([lin(d, w) for w in WINDOWS]):.1e}* |")
    out.append("")

    # ---- each of this repository's models against every reference ----
    def versus(ours_v, get):
        pairs = [(m(c, d, w, ours_v), get(d, w)) for d, w in cells_ if (d, w, ours_v) in c and get(d, w) is not None]
        if not pairs:
            return "–"
        r = gmean([a_ / b_ for a_, b_ in pairs])
        wins = sum(a_ < b_ for a_, b_ in pairs)
        return (f"{big(1 / r)}× lower" if r < 1 else f"{big(r)}× higher") + f" ({wins}/{len(pairs)})"

    out += ["## Each model against every reference (geometric-mean test-MSE factor; in brackets: cells where the model is lower)\n",
            "| Reference | Params | " + " | ".join(f"{NAMES[v]} ({params[v]})" for v in ours) + " |", "|---|---|" + "---|" * len(ours)]
    for ref in refs:
        out.append(f"| {NAMES[ref]} | {params[ref]} | "
                   + " | ".join(versus(o, lambda d, w, ref=ref: m(c, d, w, ref) if (d, w, ref) in c else None) for o in ours) + " |")
    for o in ours:
        if o != OM:
            out.append(f"| {NAMES[o]} | {params[o]} | "
                       + " | ".join("–" if o2 == o else versus(o2, lambda d, w, o=o: m(c, d, w, o) if (d, w, o) in c else None)
                                    for o2 in ours) + " |")
    out.append("| *Printed for GQKAN-QKANFWP in arXiv:2605.06734* | 159 | "
               + " | ".join(versus(o, lambda d, w: PAPER[d]["own"][WINDOWS.index(w)]) for o in ours) + " |")
    out.append("| *Best printed number of arXiv:2605.06734 and 2607.27945* | – | "
               + " | ".join(versus(o, lambda d, w: printed[(d, w)]) for o in ours) + " |")
    out.append("| *Linear AR(8), least squares* | 9 | " + " | ".join(versus(o, lin) for o in ours) + " |")
    out.append("")

    # ---- all cells ----
    cols = refs + ours
    out += ["## All cells: test MSE (paper protocol, mean ± std over 5 seeds)\n",
            "| Dataset | N | " + " | ".join(f"{NAMES[v]} ({params[v]})" for v in cols) + " | *Linear AR(8) (9)* |",
            "|---|---|" + "---|" * (len(cols) + 1)]
    for d, w in cells_:
        have = [v for v in cols if (d, w, v) in c]
        best = min(have, key=lambda v: m(c, d, w, v))
        cell = []
        for v in cols:
            if v not in have:
                cell.append("–")
                continue
            mu, sd = mean_std(c[(d, w, v)])
            txt = f"{mu:.2e} ± {sd:.1e}"
            cell.append(f"**{txt}**" if v == best else txt)
        out.append(f"| {TITLES[d]} | {w} | " + " | ".join(cell) + f" | *{lin(d, w):.1e}* |")
    out.append("")

    # ---- closed-form linear references ----
    lin3 = lambda d, w: ar_ref[f"{d}|{w}|3"]["test"]  # noqa: E731
    out += ["## Closed-form linear autoregression against the best models (test MSE)\n",
            "| Dataset | N | Best printed in the two papers | " + " | ".join(NAMES[v] for v in ours) + " | Linear AR(3) (4) | Linear AR(8) (9) |",
            "|---|---|---|" + "---|" * (len(ours) + 2)]
    for d, w in cells_:
        vals = [printed[(d, w)]] + [m(c, d, w, v) if (d, w, v) in c else float("nan") for v in ours] + [lin3(d, w), lin(d, w)]
        lo = np.nanmin(vals)
        out.append(f"| {TITLES[d]} | {w} | " + " | ".join("–" if not np.isfinite(v) else f"**{v:.1e}**" if v == lo else f"{v:.1e}" for v in vals) + " |")
    out.append("")
    for v in ours:
        have = [(d, w) for d, w in cells_ if (d, w, v) in c]
        out.append(f"- Linear AR(8) is lower than {NAMES[v]} in {sum(lin(d, w) < m(c, d, w, v) for d, w in have)}/{len(have)} cells.")
    out.append(f"- Linear AR(8) is lower than the best printed number of the two papers in "
               f"{sum(lin(d, w) < printed[(d, w)] for d, w in cells_)}/{len(cells_)} cells.")
    out.append("")

    # ablation on the paper benchmarks
    abl = [(f"{OM_BASE}_{tag}@cos30", label) for tag, label in ABLATIONS if any(k[2] == f"{OM_BASE}_{tag}@cos30" for k in c)]
    abl += [(v, label) for v, label in EXTRA_ABLATIONS if any(k[2] == v for k in c)]
    if abl:
        ds = [d for d in DATASETS]
        out += ["## QKAN-FWP-O ablation on the paper benchmarks (test MSE ÷ full model, geometric mean over the cells both have)\n",
                "| Variant | Params | All cells | Cells where the full model is better | " + " | ".join(TITLES[d] for d in ds) + " |",
                "|---|---|---|---|" + "---|" * len(ds)]
        for v, label in abl:
            r, wins, n = geo_ratio(c, v, OM)
            per = []
            for d in ds:
                rd, _, k = geo_ratio(c, v, OM, datasets=[d])
                per.append(f"{big(rd)}×" if k else "–")
            out.append(f"| {label} | {params[v]} | **{big(r)}×** | {n - wins}/{n} | " + " | ".join(per) + " |")
        out.append("")
    fig_timeseries(c, params, lin, FIG / "om_timeseries.png")
    return c, params


def fig_timeseries(c, params, lin, path):
    series = [("base_tuned", BLUE, "GQKAN-QKANFWP, tuned lr", "o"),
              ("cmg_plus@cos30", GREEN, "CMG + Δ-tokens + residual", "v"),
              (OURS, ORANGE, f"QKAN-FWP+ ({params[OURS]} params)", "D"),
              (STATIC, MAGENTA, f"HQKAN-Δ ({params[STATIC]} params)", "P"),
              (OM, VIOLET, f"QKAN-FWP-O ({params[OM]} params)", "*")]
    series = [s for s in series if any(k[2] == s[0] for k in c)]
    fig, axes = plt.subplots(2, 3, figsize=(10.5, 6.2), sharex=True)
    for ax, d in zip(axes.ravel(), DATASETS):
        for v, color, label, marker in series:
            ms = [mean_std(c[(d, w, v)]) if (d, w, v) in c else (np.nan, np.nan) for w in WINDOWS]
            mu = np.array([a for a, _ in ms])
            sd = np.array([b for _, b in ms])
            ax.errorbar(range(4), mu, yerr=[np.minimum(sd, mu * 0.9), sd], color=color, marker=marker,
                        markersize=8 if marker == "*" else 5, capsize=2.5, elinewidth=1, label=label)
        ax.plot(range(4), [lin(d, w) for w in WINDOWS], color=INK, linestyle=(0, (4, 3)), linewidth=1.2,
                label="Linear AR(8), least squares (reference)")
        ax.set_yscale("log")
        ax.set_title(TITLES[d])
        ax.set_xticks(range(4), [str(w) for w in WINDOWS])
    for ax in axes[-1]:
        ax.set_xlabel("input window N")
    for ax in axes[:, 0]:
        ax.set_ylabel("test MSE (log scale)")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.0), fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.90))
    fig.savefig(path, dpi=200)
    plt.close(fig)


# ---------------------------------------------------------------------------
def load_family(path):
    runs, refs, params = defaultdict(lambda: defaultdict(dict)), {}, {}
    for line in Path(path).read_text().splitlines():
        r = json.loads(line)
        cell = (r["family"], r["window"], r["noise"])
        if "refs" in r:
            refs[cell] = r["refs"]
            continue
        base, _, tag = r["variant"].partition("@")
        runs[(cell, base)][tag][r["seed"]] = r["best"]["test"]
        params[base] = r["params"]
    # the selected learning rate is the tag that was run on every seed
    sel = {}
    for k, tags in runs.items():
        tag = max(tags, key=lambda t: len(tags[t]))
        sel[k] = (tag, np.array(list(tags[tag].values())))
    return sel, refs, params


def family_part(out):
    path = RES / "family.jsonl"
    if not path.exists():
        return
    sel, refs, params = load_family(path)
    cells_ = sorted(refs, key=lambda c_: (c_[2], list(FAMILY_TITLES).index(c_[0])))
    if not cells_ or not any(k[1] == OM_BASE for k in sel):
        return
    head = " | ".join(f"{FAMILY_TITLES[f]}, noise {nz:g}" for f, _, nz in cells_)
    out += ["## Families of systems (window N = 16; test MSE on unseen sequences)\n",
            "Mean ± std over 3 seeds at the learning rate chosen on validation (one of 3e-3, 1e-2, 3e-2, cosine); "
            "each model is evaluated at its best-validation epoch. References are closed-form.\n",
            "| Model | Params | " + head + " |", "|---|---|" + "---|" * len(cells_)]
    for name, label in (("persist", "*Reference: repeat the last value*"),
                        ("lin_global", "*Reference: one linear AR(p) for all sequences*"),
                        ("lin_ctx", "*Reference: ridge AR(q) fitted inside each window*")):
        out.append(f"| {label} | – | " + " | ".join(f"*{refs[c_][name]['test']:.2e}*" for c_ in cells_) + " |")
    models = [(v, lab) for v, lab in FAMILY_MODELS if any(k[1] == v for k in sel)]
    best = {c_: min((sel[(c_, v)][1].mean(), v) for v, _ in models if (c_, v) in sel)[1] for c_ in cells_}
    for v, lab in models:
        row = []
        for c_ in cells_:
            if (c_, v) not in sel:
                row.append("–")
                continue
            vals = sel[(c_, v)][1]
            txt = f"{vals.mean():.2e} ± {vals.std():.1e}"
            row.append(f"**{txt}**" if best[c_] == v else txt)
        out.append(f"| {lab} | {params[v]} | " + " | ".join(row) + " |")
    out.append("")

    out += ["## QKAN-FWP-O against each model on the families (geometric mean over the cells)\n",
            "| Compared with | Params | Geo-mean test MSE of QKAN-FWP-O | Cells where it is lower | Smallest … largest factor |", "|---|---|---|---|---|"]

    def versus(get, label, par):
        rat = [sel[(c_, OM_BASE)][1].mean() / get(c_) for c_ in cells_ if get(c_) is not None]
        if not rat:
            return
        r = gmean(rat)
        word = f"**{big(1 / r)}× lower**" if r < 1 else f"{big(r)}× higher"
        out.append(f"| {label} | {par} | {word} | {sum(x < 1 for x in rat)}/{len(rat)} | {big(1 / max(rat))}× … {big(1 / min(rat))}× |")

    for v, lab in models:
        if v != OM_BASE:
            versus(lambda c_, v=v: sel[(c_, v)][1].mean() if (c_, v) in sel else None, lab, params[v])
    versus(lambda c_: refs[c_]["lin_global"]["test"], "*one linear AR(p) for all sequences*", "–")
    versus(lambda c_: refs[c_]["lin_ctx"]["test"], "*ridge AR(q) fitted inside each window*", "–")
    out.append("")

    abl = [(f"{OM_BASE}_{tag}", label) for tag, label in ABLATIONS if any(k[1] == f"{OM_BASE}_{tag}" for k in sel)]
    if abl:
        out += ["## QKAN-FWP-O ablation on the families (test MSE ÷ full model)\n",
                "| Variant | Params | Geo-mean, all cells | " + head + " |", "|---|---|---|" + "---|" * len(cells_)]
        for v, label in abl:
            rat = {c_: sel[(c_, v)][1].mean() / sel[(c_, OM_BASE)][1].mean() for c_ in cells_ if (c_, v) in sel}
            out.append(f"| {label} | {params[v]} | **{big(gmean(list(rat.values())))}×** | "
                       + " | ".join(f"{big(rat[c_])}×" if c_ in rat else "–" for c_ in cells_) + " |")
        out.append("")
    fig_family(sel, refs, params, cells_, models, FIG / "om_family.png")


def fig_family(sel, refs, params, cells_, models, path):
    from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter

    fams = [f for f in FAMILY_TITLES if any(c_[0] == f for c_ in cells_)]
    noises = sorted({c_[2] for c_ in cells_})
    fig, axes = plt.subplots(len(noises), len(fams), figsize=(2.75 * len(fams) + 2.2, 2.6 * len(noises) + 0.9),
                             sharey=True, squeeze=False)
    ys = np.arange(len(models))[::-1]
    ref_style = [("lin_global", BLUE, (0, (4, 3)), 1.2, "one linear AR for all sequences"),
                 ("lin_ctx", ORANGE, (0, (1, 2)), 1.6, "ridge AR fitted inside each window")]
    for i, nz in enumerate(noises):
        for j, f in enumerate(fams):
            ax = axes[i, j]
            c_ = next(c0 for c0 in cells_ if c0[0] == f and c0[2] == nz)
            lo, hi = np.inf, 0.0
            for (v, _), y in zip(models, ys):
                if (c_, v) not in sel:
                    continue
                vals = sel[(c_, v)][1]
                lo, hi = min(lo, vals.min()), max(hi, vals.max())
                color = VIOLET if v == OM_BASE else INK2
                ax.plot([vals.min(), vals.max()], [y, y], color=color, linewidth=1.5, zorder=2)
                ax.scatter([vals.mean()], [y], s=70 if v == OM_BASE else 36, color=color, zorder=3,
                           marker="*" if v == OM_BASE else "o")
            # the axis follows the models; a reference far below it is marked at the left edge
            ref_vals = [refs[c_][k]["test"] for k, *_ in ref_style]
            lo_ax = min([lo] + [r for r in ref_vals if r > lo / 1e3]) / 2.5
            hi_ax = max([hi] + ref_vals) * 2.5
            ax.set_xscale("log")
            ax.set_xlim(lo_ax, hi_ax)
            off = 0
            for (k, color, ls, lw, label), r in zip(ref_style, ref_vals):
                if r >= lo_ax:
                    ax.axvline(r, color=color, linestyle=ls, linewidth=lw, label=label)
                else:
                    ax.plot([], [], color=color, linestyle=ls, linewidth=lw, label=label)
                    ax.scatter([0.035], [0.5 - 0.16 * off], marker="<", s=40, color=color, transform=ax.transAxes, zorder=4,
                               clip_on=False)
                    ax.text(0.075, 0.5 - 0.16 * off, f"{r:.0e}".replace("e-0", "e-"), transform=ax.transAxes, va="center",
                            fontsize=8, color=INK2)
                    off += 1
            span = np.log10(hi_ax / lo_ax)
            ax.xaxis.set_major_locator(LogLocator(base=10, subs=(1.0,) if span > 2.5 else (1.0, 3.0), numticks=5))
            ax.xaxis.set_major_formatter(FuncFormatter(lambda val, _: f"{val:.0e}".replace("e-0", "e-")))
            ax.xaxis.set_minor_formatter(NullFormatter())
            ax.tick_params(axis="x", labelsize=8)
            ax.set_ylim(-0.6, len(models) - 0.4)
            ax.grid(axis="y", visible=False)
            ax.set_title(f"{FAMILY_TITLES[f]}" + (f", noise {nz:g}" if nz else ", no noise"), fontsize=10)
            if i == len(noises) - 1:
                ax.set_xlabel("test MSE (log scale)")
        axes[i, 0].set_yticks(ys, [f"{lab} ({params[v]})" for v, lab in models], fontsize=8.5)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.0), fontsize=9,
               title="closed-form references (◂ with a number: below the plotted range)")
    fig.tight_layout(rect=(0, 0, 1, 0.90))
    fig.savefig(path, dpi=200)
    plt.close(fig)


# ---------------------------------------------------------------------------
SHOT_MODELS = [(OM, "QKAN-FWP-O", VIOLET, "*"),
               ("ar_hqkan8+z@cos30", "HQKAN-Δ, ⟨Z⟩ read-out", MAGENTA, "P"),
               ("pmx_diff8_edge_h3l2+z@cos30", "QKAN-FWP+, ⟨Z⟩ read-out", ORANGE, "D")]
SHOT_TASKS = {"bessel": "Bessel J2", "narma10": "NARMA10", "dqc": "Delayed quantum control",
              "family:shm:0.02": "Family: damped oscillation, noise 0.02", "family:henon:0": "Family: Hénon map"}
SHOT_KEYS = ["100", "1000", "10000", "100000", "1e+06", "inf"]


def shots_part(out):
    path = RES / "shot_noise.jsonl"
    if not path.exists():
        return
    data = defaultdict(list)
    for line in path.read_text().splitlines():
        r = json.loads(line)
        data[(r["task"], r["variant"], r["train_shots"])].append([r["test"][k] for k in SHOT_KEYS])
    tasks = [t for t in SHOT_TASKS if any(k[0] == t for k in data)]
    if not tasks:
        return
    labels = ["10²", "10³", "10⁴", "10⁵", "10⁶", "exact"]
    out += ["## Finite-shot sensitivity (N = 16; test MSE vs shots per measured expectation, mean over 3 seeds)\n",
            "Training with exact expectations, or with 10⁴ shots per expectation (\"noise-aware\"). All read-outs are physical ⟨X⟩, ⟨Y⟩, ⟨Z⟩.\n",
            "| Task | Model | Trained with | " + " | ".join(labels) + " |", "|---|---|---|" + "---|" * len(labels)]
    for t in tasks:
        for v, lab, _, _ in SHOT_MODELS:
            for ts, tlab in ((None, "exact"), (1e4, "10⁴ shots")):
                if (t, v, ts) in data:
                    mu = np.mean(data[(t, v, ts)], 0)
                    out.append(f"| {SHOT_TASKS[t]} | {lab} | {tlab} | " + " | ".join(f"{x:.1e}" for x in mu) + " |")
    out.append("")
    fig, axes = plt.subplots(1, len(tasks), figsize=(3.1 * len(tasks), 3.9), squeeze=False)
    xs = np.arange(len(SHOT_KEYS))
    for ax, t in zip(axes[0], tasks):
        for v, lab, color, marker in SHOT_MODELS:
            for ts, ls in ((None, "-"), (1e4, (0, (4, 2)))):
                if (t, v, ts) in data:
                    mu = np.mean(data[(t, v, ts)], 0)
                    ax.plot(xs, mu, color=color, marker=marker, markersize=8 if marker == "*" else 5, linestyle=ls,
                            label=f"{lab}, trained {'exact' if ts is None else 'with 10⁴ shots'}")
        ax.set_yscale("log")
        ax.set_xticks(xs, labels)
        ax.set_title(SHOT_TASKS[t], fontsize=9.5)
        ax.set_xlabel("shots per expectation at test time")
    axes[0, 0].set_ylabel("test MSE (log scale)")
    handles, labs = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labs, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.0), fontsize=8.5)
    fig.tight_layout(rect=(0, 0, 1, 0.84))
    fig.savefig(FIG / "om_shots.png", dpi=200)
    plt.close(fig)


SOLAR_SPLITS = {(0.8, 0.1, 0.1): "paper split 80/10/10",
                (0.6, 0.2, 0.2): "60/20/20 (test targets 1971–2026)",
                (0.7, 0.15, 0.15): "70/15/15 (test targets 1982–2026)"}
SOLAR_MODELS = [("base", "GQKAN-QKANFWP (re-implemented baseline)"),
                ("mtg_cyc_pm", "QKAN-FWP+"),
                ("om_static", "QKAN-FWP-O without fast weights (static observable)"),
                ("om", "QKAN-FWP-O")]


def solar_part(out):
    from experiments.make_figures import PAPER_SOLAR, solar_eval_anchor

    rows = defaultdict(list)
    for f in sorted(RES.glob("final_solar*.jsonl")):
        for line in f.read_text().splitlines():
            r = json.loads(line)
            base, _, tag = r["variant"].partition("@")
            lr = {"lr1": 1e-3, "lr2": 2e-3}.get(tag, r["lr"])
            rows[(tuple(r.get("split") or (0.8, 0.1, 0.1)), base, lr)].append(r)
    if not any(k[1] == "om" for k in rows):
        return
    out += ["## Solar cycle: all models (528 → 132 months, paper protocol: peak-aware loss, best-validation checkpoint)\n",
            "For every model the learning rate is the one with the lowest validation loss among those run "
            "(the paper's grid); test metrics are mean ± std over seeds.\n"]
    for split, title in SOLAR_SPLITS.items():
        if not any(k[0] == split and k[1] == "om" for k in rows):
            continue
        anchor = solar_eval_anchor(split)["test"]
        out += [f"### {title}\n",
                "| Model | Params | lr (by validation) | Seeds | Val. loss | Scaled MSE ↓ | PAE ↓ | PTE ↓ |", "|---|---|---|---|---|---|---|---|"]
        for v, label in SOLAR_MODELS:
            cand = {lr: rs for (sp, vv, lr), rs in rows.items() if sp == split and vv == v}
            if not cand:
                continue
            lr = min(cand, key=lambda k: np.mean([r["val"]["loss"] for r in cand[k]]))
            rs = cand[lr]
            f = lambda k, p: "{:.{p}f} ± {:.{p}f}".format(np.mean([r["test"][k] for r in rs]), np.std([r["test"][k] for r in rs]), p=p)  # noqa: E731
            vl = np.mean([r["val"]["loss"] for r in rs])
            out.append(f"| {label} | {rs[0]['params']:,} | {lr:g} | {len(rs)} | {vl:.2f} | {f('mse', 4)} | {f('pae', 1)} | {f('pte', 1)} |")
        out.append(f"| *Reference: repeat the last cycle, 13-month smoothed (no training)* | 0 | – | – | – | {anchor['mse']:.4f} | {anchor['pae']:.1f} | {anchor['pte']:.1f} |")
        if split == (0.8, 0.1, 0.1):
            ps = PAPER_SOLAR
            out.append(f"| *Printed in arXiv:2605.06734 for GQKAN-QKANFWP* | {ps['params']:,} | – | 5 | – | {ps['mse'][0]:.4f} ± {ps['mse'][1]:.4f} "
                       f"| {ps['pae'][0]:.2f} ± {ps['pae'][1]:.2f} | {ps['pte'][0]:.2f} ± {ps['pte'][1]:.2f} |")
        out.append("")


def main():
    out = []
    timeseries_part(out)
    family_part(out)
    shots_part(out)
    solar_part(out)
    (RES / "tables_om.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
