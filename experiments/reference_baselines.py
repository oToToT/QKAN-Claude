"""Closed-form references for the one-step benchmarks.

A linear autoregression  x_t ~ w . (x_{t-p}, ..., x_{t-1}) + c  is fitted by
least squares on exactly the training windows the neural models see (paper
protocol: [-1, 1] min-max scaling, chronological 80/20 split) and scored on the
same test windows.  It has p + 1 parameters and needs no training loop, so it
shows how much of each benchmark is a (near-)exact linear recurrence.

Writes results/reference_linear_ar.json and prints a markdown table.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from qkanfwp import data  # noqa: E402

DATASETS = ["bessel", "shm", "narma5", "narma10", "dqc", "jc"]
WINDOWS = [8, 16, 32, 64]
ORDERS = [3, 8]


def linear_ar(name: str, window: int, order: int) -> dict:
    series = data.load_series(name, dtype=np.float64)
    x, y = data.make_windows(series, window)
    x, y = x[..., 0], y[:, 0]
    tr, te = data.chrono_split(len(x), (0.8, 0.2))
    design = np.c_[x[:, -order:], np.ones(len(x))]
    w = np.linalg.lstsq(design[tr], y[tr], rcond=None)[0]
    err = (design @ w - y) ** 2
    return dict(train=float(err[tr].mean()), test=float(err[te].mean()),
                persistence=float(((x[te, -1] - y[te]) ** 2).mean()))


def main():
    out = {}
    for d in DATASETS:
        for w in WINDOWS:
            for p in ORDERS:
                out[f"{d}|{w}|{p}"] = linear_ar(d, w, p)
    (ROOT / "results" / "reference_linear_ar.json").write_text(json.dumps(out, indent=1))
    print("| Dataset | N | Persistence (x̂ = last value) | Linear AR(3), 4 params | Linear AR(8), 9 params |")
    print("|---|---|---|---|---|")
    for d in DATASETS:
        for w in WINDOWS:
            a, b = out[f"{d}|{w}|3"], out[f"{d}|{w}|8"]
            print(f"| {d} | {w} | {a['persistence']:.1e} | {a['test']:.1e} | {b['test']:.1e} |")


if __name__ == "__main__":
    main()
