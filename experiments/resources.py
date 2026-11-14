"""Quantum and classical resources per prediction of every QKAN model.

Trainable parameter counts hide most of the cost of a fast-weight programmer.
This script counts, for one prediction from a window of N steps:

  circuits            distinct single-qubit DARUAN circuits in the model
  circuit runs        circuit evaluations (one circuit, one input)
  settings            measurement settings per circuit run (1 = Z only,
                      3 = X, Y and Z, which do not commute)
  reprogrammed        gate angles that have to be loaded into the circuits anew
                      for this prediction (the fast weights of an angle-space
                      programmer; 0 when the circuits do not depend on the memory)
  fast state          numbers kept in classical memory between steps
  classical flops     multiply-adds of the memory update and the read-out
                      (slow-programmer decoders for the angle-space models; the
                      gated statistics and one F x F solve for QKAN-FWP-O)

Writes results/resources.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))


def resources(model, window: int) -> dict:
    from qkanfwp.models import ARHQKAN, GatedFWP, count_parameters
    from qkanfwp.obsmem import ObservableMemoryFWP

    out = dict(params=count_parameters(model))
    if isinstance(model, ObservableMemoryFWP):
        c = model.cfg
        f, k = model.n_feat, model.n_out
        if c.d_out > 1:  # direct multi-step: every pair_stride-th token with all successors inside the window
            need = max(c.pool * c.context if c.pool > 1 else c.context, c.d_out if c.anchor == "cycle" else 1)
            pairs = len([t for t in range(window - c.d_out - 1, -1, -c.pair_stride) if t >= need - 1])
        else:
            pairs = max(window - c.context, 0)
        tokens = pairs + 1
        memory = c.memory != "none"
        out.update(
            circuits=c.hidden if c.quantum else 0,
            circuit_runs=(c.hidden * tokens if memory else c.hidden) * (3 if c.tangent else 1) if c.quantum else 0,
            settings=3 if c.quantum else 0,
            reprogrammed=0,
            fast_state=(f * (f + 1) // 2 + f * k) if memory else 0,  # C (symmetric) and b
            classical_flops=(pairs * (f * f + f * k) + f**3 // 3 + f * f * k + f * k) if memory else f * k,
        )
    elif isinstance(model, ARHQKAN):
        q = model.net.qkan
        out.update(circuits=q.in_dim * q.out_dim, circuit_runs=q.in_dim * q.out_dim, settings=1, reprogrammed=0,
                   fast_state=0, classical_flops=model.net.enc.weight.numel() + model.net.dec.weight.numel())
    elif isinstance(model, GatedFWP):
        c = model.cfg
        tokens = window if c.write_first else window - 1
        slow = model.slow.qkan.in_dim * model.slow.qkan.out_dim if c.slow == "hqkan" else 0
        fast = c.fast_in * c.fast_out if c.fast == "hqkan" else 0
        dec = model.slow.dec.weight.numel()
        out.update(circuits=slow + fast, circuit_runs=slow * tokens + fast, settings=1,
                   reprogrammed=model.n_fast if c.fast == "hqkan" else 0, fast_state=model.n_fast,
                   classical_flops=tokens * (dec + model.slow.enc.weight.numel() + 2 * model.n_fast))
    else:
        raise TypeError(type(model))
    out["settings_total"] = out["circuit_runs"] * out["settings"]
    return out


def main():
    from run_solar import HORIZON, VARIANTS as SOLAR, WINDOW, build
    from run_timeseries import build_model, resolve

    rows = []
    ts = [("base", "GQKAN-QKANFWP"), ("cmg", "CMG"), ("pmx_diff8_edge_h3l2", "QKAN-FWP+"), ("ar_hqkan8", "HQKAN-Δ"),
          ("om_c0h6r1_p5", "QKAN-FWP-O")]
    for window in (16, 64):
        x = torch.zeros(4, window, 1, dtype=torch.float64)
        for v, name in ts:
            rows.append(dict(task=f"one step, N = {window}", model=name, **resources(build_model(resolve(v), window, x), window)))
    for v, name in (("base", "GQKAN-QKANFWP"), ("mtg_cyc_pm", "QKAN-FWP+"), ("om_static", "QKAN-FWP-O, static"), ("om", "QKAN-FWP-O")):
        rows.append(dict(task=f"solar, {WINDOW} → {HORIZON} months", model=name, **resources(build(SOLAR[v]), WINDOW)))
    Path("results/resources.json").write_text(json.dumps(rows, indent=1))
    for r in rows:
        print(r)


if __name__ == "__main__":
    main()
