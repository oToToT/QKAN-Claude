"""Summarise JSON-lines results: mean +- std per cell and ratios to a reference."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np


def load(paths, protocol=None, epochs=None):
    rows = []
    for p in paths:
        for line in Path(p).read_text().splitlines():
            r = json.loads(line)
            if protocol and r["protocol"] != protocol:
                continue
            if epochs and r["epochs"] != epochs:
                continue
            rows.append(r)
    return rows


def cells(rows, metric="test"):
    """{(dataset, window, variant): {seed: value}}"""
    out = defaultdict(dict)
    for r in rows:
        out[(r["dataset"], r["window"], r["variant"])][r["seed"]] = r["final"][metric]
    return out


def geo_ratio(c, variant, ref, datasets=None, windows=None):
    """Geometric mean over (dataset, window) cells of mean_seed(variant) / mean_seed(ref),
    plus the number of cells where the variant has the lower seed-mean."""
    logs, wins, n = [], 0, 0
    for (d, w, v), vals in c.items():
        if v != variant or (d, w, ref) not in c:
            continue
        if datasets and d not in datasets or windows and w not in windows:
            continue
        a, b = np.mean(list(vals.values())), np.mean(list(c[(d, w, ref)].values()))
        logs.append(np.log(a / b))
        wins += a < b
        n += 1
    return (float(np.exp(np.mean(logs))) if logs else float("nan")), wins, n


def fmt(vals):
    v = np.array(list(vals.values()))
    return f"{v.mean():.2e} ± {v.std():.1e}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--metric", default="test")
    ap.add_argument("--ref", default="base")
    ap.add_argument("--variants", nargs="*")
    ap.add_argument("--protocol")
    ap.add_argument("--epochs", type=int)
    ap.add_argument("--by-dataset", action="store_true")
    args = ap.parse_args()

    rows = load(args.files, args.protocol, args.epochs)
    c = cells(rows, args.metric)
    params = {r["variant"]: r["params"] for r in rows}
    variants = args.variants or sorted({k[2] for k in c})
    datasets = sorted({k[0] for k in c})
    windows = sorted({k[1] for k in c})

    print(f"metric={args.metric}  ref={args.ref}  ({len(rows)} runs)\n")
    header = f"{'variant':16s} {'params':>6s} {'geo-ratio':>9s} {'wins':>7s}"
    if args.by_dataset:
        header += "".join(f" {d:>8s}" for d in datasets)
    print(header)
    for v in variants:
        ratio, wins, n = geo_ratio(c, v, args.ref)
        line = f"{v:16s} {params.get(v, 0):6d} {ratio:9.3f} {wins:3d}/{n:<3d}"
        if args.by_dataset:
            for d in datasets:
                line += f" {geo_ratio(c, v, args.ref, datasets=[d])[0]:8.3f}"
        print(line)

    print()
    for d in datasets:
        for w in windows:
            got = [(v, c[(d, w, v)]) for v in variants if (d, w, v) in c]
            if not got:
                continue
            print(f"{d:8s} N={w:<3d} " + " | ".join(f"{v}: {fmt(vals)} (n={len(vals)})" for v, vals in got))


if __name__ == "__main__":
    main()
