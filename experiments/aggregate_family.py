"""Summarise run_family.py results: mean test MSE (validation-selected
checkpoint) per family / window / noise, plus the closed-form references."""

from __future__ import annotations

import argparse
import json
import signal
from collections import defaultdict

import numpy as np

signal.signal(signal.SIGPIPE, signal.SIG_DFL)


def load(paths):
    runs, refs = defaultdict(list), {}
    params = {}
    for path in paths:
        for line in open(path):
            r = json.loads(line)
            cell = (r["family"], r["window"], r["noise"])
            if "refs" in r:
                refs[cell] = r["refs"]
            else:
                runs[(cell, r["variant"])].append((r["seed"], r["best"]["test"], r["best"]["val"]))
                params[r["variant"]] = r["params"]
    return runs, refs, params


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--metric", choices=["test", "val"], default="test")
    ap.add_argument("--variants", nargs="*")
    args = ap.parse_args()
    runs, refs, params = load(args.files)
    col = 1 if args.metric == "test" else 2
    cells = sorted({c for c, _ in runs} | set(refs))
    variants = args.variants or sorted({v for _, v in runs})
    geo = defaultdict(list)
    print(f"mean {args.metric} MSE over seeds (n seeds in brackets)\n")
    head = f"{'variant':28s} {'par':>4s} " + " ".join(f"{c[0][:6]}/{c[1]}/{c[2]:g}".rjust(15) for c in cells)
    print(head)
    for name in ("persist", "lin_global", "lin_ctx"):
        print(f"{name:28s} {'':>4s} " + " ".join(
            (f"{refs[c][name][args.metric]:.2e}" if c in refs else "-").rjust(15) for c in cells))
    for v in variants:
        row = []
        for c in cells:
            vals = [x[col] for x in runs.get((c, v), [])]
            if vals:
                row.append(f"{np.mean(vals):.2e}[{len(vals)}]".rjust(15))
                geo[v].append((c, np.mean(vals)))
            else:
                row.append("-".rjust(15))
        print(f"{v:28s} {params.get(v, 0):4d} " + " ".join(row))
    # geometric-mean ratio to the first variant over the cells both have
    ref_v = variants[0]
    base = dict(geo[ref_v])
    print(f"\ngeometric-mean MSE ratio to {ref_v} (shared cells; > 1 = worse than {ref_v})")
    for v in variants:
        ratios = [m / base[c] for c, m in geo[v] if c in base]
        if ratios:
            wins = sum(r < 1 for r in ratios)
            print(f"{v:28s} {np.exp(np.mean(np.log(ratios))):8.2f}   better in {wins}/{len(ratios)} cells")


if __name__ == "__main__":
    main()
