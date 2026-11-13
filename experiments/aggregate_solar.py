"""Summarise solar runs: validation metrics (used for model selection) and test metrics."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--variants", nargs="*")
    ap.add_argument("--split", nargs=3, type=float, default=[0.8, 0.1, 0.1])
    ap.add_argument("--seeds", nargs="*", type=int)
    args = ap.parse_args()

    groups = defaultdict(list)
    for f in args.files:
        for line in Path(f).read_text().splitlines():
            r = json.loads(line)
            if list(r.get("split") or [0.8, 0.1, 0.1]) != list(args.split):
                continue
            if args.seeds and r["seed"] not in args.seeds:
                continue
            groups[r["variant"]].append(r)
    variants = args.variants or sorted(groups)

    def ms(rows, part, key):
        v = np.array([r[part][key] for r in rows])
        return v.mean(), v.std()

    print(f"{'variant':18s} {'params':>6s} {'n':>2s} | {'val loss':>14s} {'val mse':>8s} {'val pae':>7s} {'val pte':>7s} {'ep':>3s}"
          f" | {'test mse':>15s} {'pae':>11s} {'pte':>11s} | {'last-epoch mse':>14s}")
    for v in variants:
        rows = groups.get(v)
        if not rows:
            continue
        vl, vls = ms(rows, "val", "loss")
        tm, tms = ms(rows, "test", "mse")
        tp, tps = ms(rows, "test", "pae")
        tt, tts = ms(rows, "test", "pte")
        fm, fms = ms(rows, "test_final", "mse")
        print(f"{v:18s} {rows[0]['params']:6d} {len(rows):2d} | {vl:6.3f} ± {vls:5.3f} {ms(rows, 'val', 'mse')[0]:8.4f} "
              f"{ms(rows, 'val', 'pae')[0]:7.1f} {ms(rows, 'val', 'pte')[0]:7.1f} {np.mean([r['val']['epoch'] for r in rows]):3.0f}"
              f" | {tm:.4f} ± {tms:.4f} {tp:5.1f} ± {tps:3.1f} {tt:5.1f} ± {tts:3.1f} | {fm:.4f} ± {fms:.4f}")


if __name__ == "__main__":
    main()
