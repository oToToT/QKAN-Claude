"""Closed-form references for the one-step benchmarks.

A linear autoregression  x_t ~ w . (x_{t-p}, ..., x_{t-1}) + c  is fitted by
least squares on exactly the training windows the neural models see (paper
protocol: [-1, 1] min-max scaling, chronological 80/20 split) and scored on the
same test windows.  It has p + 1 parameters and needs no training loop, so it
shows how much of each benchmark is a (near-)exact linear recurrence.

The targets are rounded to float32, as for every neural model (inputs stay in
float64): an error below about 1e-15 is then rounding of the targets, not
model quality, for the references and the networks alike.

The same references are computed for the datasets of the authors' released
code (``c_*``, see qkanfwp/data.py): there the regression maps the last p
*inputs* of the window to the target, which for NARMA means the drive u to the
output y.  ``mean`` is the error of predicting the mean of the training
targets; ``order = 0`` in the key stands for a regression on the whole window.
For the two NARMA tasks the key ``...|q`` holds a ridge regression on the last
12 inputs and their pairwise products (the NARMA output is a quadratic function
of the drive); its ridge strength is chosen on the last eighth of the training
windows.

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
CODE_DATASETS = ["c_bessel", "c_shm", "c_narma5", "c_narma10", "c_dqc", "c_jc"]
WINDOWS = [8, 16, 32, 64]
ORDERS = [3, 8]


def linear_ar(name: str, window: int, order: int) -> dict:
    series = data.load_series(name, dtype=np.float64)
    x, y = data.make_windows(series, window)
    x, y = x[..., 0], y[:, 0].astype(np.float32).astype(np.float64)  # the targets the networks are trained and scored on
    tr, te = data.chrono_split(len(x), (0.8, 0.2))
    design = np.c_[x[:, -order:], np.ones(len(x))]
    w = np.linalg.lstsq(design[tr], y[tr], rcond=None)[0]
    err = (design @ w - y) ** 2
    return dict(train=float(err[tr].mean()), test=float(err[te].mean()),
                persistence=float(((x[te, -1] - y[te]) ** 2).mean()))


def linear_code(name: str, window: int, order: int) -> dict:
    """Least-squares map from the last ``order`` inputs (0: the whole window) to the
    target, on the windows and the split of the authors' code."""
    x, y = data.code_windows(name, window)
    x, y = x[..., 0], y[:, 0].astype(np.float64)
    tr, te = data.code_split(len(x))
    design = np.c_[x[:, -order:] if order else x, np.ones(len(x))]
    w = np.linalg.lstsq(design[tr], y[tr], rcond=None)[0]
    err = (design @ w - y) ** 2
    return dict(train=float(err[tr].mean()), test=float(err[te].mean()),
                persistence=float(((x[te, -1] - y[te]) ** 2).mean()),
                mean=float(((y[tr].mean() - y[te]) ** 2).mean()))


def quadratic_code(name: str, window: int, lags: int = 12) -> dict:
    """Ridge regression on the last ``lags`` inputs and their pairwise products."""
    x, y = data.code_windows(name, window)
    x, y = x[..., 0], y[:, 0].astype(np.float64)
    tr, te = data.code_split(len(x))
    lag = x[:, -min(lags, window):]
    p = lag.shape[1]
    design = np.c_[lag, np.stack([lag[:, i] * lag[:, j] for i in range(p) for j in range(i, p)], 1), np.ones(len(x))]
    fit_part, held = tr[: len(tr) * 7 // 8], tr[len(tr) * 7 // 8 :]

    def solve(idx, lam):
        a = design[idx]
        return np.linalg.solve(a.T @ a + lam * np.eye(a.shape[1]), a.T @ y[idx])

    grid = [1e-14, 1e-12, 1e-10, 1e-8, 1e-6, 1e-4]
    lam = min(grid, key=lambda v: ((design[held] @ solve(fit_part, v) - y[held]) ** 2).mean())
    err = (design @ solve(tr, lam) - y) ** 2
    return dict(train=float(err[tr].mean()), test=float(err[te].mean()), ridge=lam, features=design.shape[1])


def main():
    out = {}
    for d in DATASETS:
        for w in WINDOWS:
            for p in ORDERS:
                out[f"{d}|{w}|{p}"] = linear_ar(d, w, p)
    for d in CODE_DATASETS:
        for w in WINDOWS:
            for p in ORDERS + [0]:
                out[f"{d}|{w}|{p}"] = linear_code(d, w, p)
            if "narma" in d:
                out[f"{d}|{w}|q"] = quadratic_code(d, w)
    (ROOT / "results" / "reference_linear_ar.json").write_text(json.dumps(out, indent=1))
    print("| Dataset | N | Persistence (x̂ = last value) | Linear AR(3), 4 params | Linear AR(8), 9 params |")
    print("|---|---|---|---|---|")
    for d in DATASETS:
        for w in WINDOWS:
            a, b = out[f"{d}|{w}|3"], out[f"{d}|{w}|8"]
            print(f"| {d} | {w} | {a['persistence']:.1e} | {a['test']:.1e} | {b['test']:.1e} |")
    print("\n| Dataset (authors' code) | N | Mean of the training targets | Linear, last 3 inputs | Linear, last 8 inputs | Linear, whole window |")
    print("|---|---|---|---|---|---|")
    for d in CODE_DATASETS:
        for w in WINDOWS:
            a, b, c = (out[f"{d}|{w}|{p}"] for p in (3, 8, 0))
            q = out.get(f"{d}|{w}|q")
            print(f"| {d} | {w} | {a['mean']:.1e} | {a['test']:.1e} | {b['test']:.1e} | {c['test']:.1e} |"
                  + (f" quadratic ridge: {q['test']:.1e} |" if q else ""))


if __name__ == "__main__":
    main()
