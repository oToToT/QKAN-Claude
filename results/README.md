# Result files

Every line of a `*.jsonl` file is one training run (dataset or family, window,
variant, seed, protocol, parameter count, metrics).  Runs are appended, and the
runners skip runs that are already present.

## One-step time-series benchmarks (`experiments/run_timeseries.py`)

| File | Content |
|---|---|
| `dev_baseline_arch.jsonl` | Validation runs used to choose the layer sizes of the re-implemented baseline |
| `dev_screen.jsonl` | Validation runs for single changes (learning rate, residual read-out, tokens, gates) |
| `dev_param_matched.jsonl`, `dev_other_lr*.jsonl` | Validation runs used to choose QKAN-FWP+, HQKAN-Δ and the learning rates of the other models |
| `dev_om.jsonl` | Validation runs used to choose the configuration of QKAN-FWP-O (token length, circuits, prior, masking, tangent features) |
| `final_timeseries.jsonl` | Paper protocol, seeds 0–4: re-implemented GQKAN-QKANFWP (lr 1e-3 and tuned), GQKAN-FWP, G-QKANFWP |
| `final_timeseries_abl.jsonl` | Paper protocol: one change at a time on top of the baseline (appendix A of the report) |
| `final_timeseries_pm.jsonl` | Paper protocol: QKAN-FWP+, HQKAN-Δ, their ablations and the LSTM control |
| `dev_cmg.jsonl` | Validation runs used to choose the learning rates of the CMG baselines |
| `final_cmg.jsonl` | Paper protocol: complementary matrix gate (CMG) baselines |
| `final_om.jsonl` | Paper protocol: QKAN-FWP-O, its ablations, the float32 version, the controls with the same memory on other features (Fourier, tanh, quadratic polynomial, small MLP, linear only) and with other memory rules (RLS, delta rule, no gate, no memory) |
| `extra_seeds.jsonl` | Seeds 5–14 for the QKAN-FWP+ vs HQKAN-Δ comparison |
| `robust_exactz.jsonl` | Physical ⟨Z⟩ read-out instead of the `qkan` default |
| `robust_norm.jsonl` | Min–max scaling fitted on the training part only (`norm: "train"`), or no scaling (`norm: "none"`) |
| `robust_burnin.jsonl` | NARMA with 200 burn-in steps discarded |
| `robust_writefirst.jsonl` | Baselines with the write-then-read order |
| `reference_linear_ar.json` | Closed-form linear AR(p) on the same train / test windows, scored on the same float32 targets as the models (`experiments/reference_baselines.py`) |

## Settings of the authors' released code (`experiments/run_timeseries.py`, datasets `c_*`)

| File | Content |
|---|---|
| `dev_code_protocol.jsonl` | Validation runs on the datasets as the authors' code generates them: learning rates of every model, and the configuration of the history-solved observable for NARMA |
| `code_protocol.jsonl` | Paper split, seeds 0–4: the ported GQKAN-QKANFWP (`authors`: lr 1e-3, 100 epochs with an evaluation every 5; `authors@cos…`: tuned), QKAN-FWP+, HQKAN-Δ, QKAN-FWP-O and its static control. On NARMA (drive u → output y) the variants without residual read-out (`_noskip`) and the observable solved from the training windows (`_hist`) |
| `solar_code_protocol.jsonl` | Solar cycle on the authors' 3,265-record file (`--records 3265`) with the ported 12,474-parameter model, window-index split and split by target time |

`reference_linear_ar.json` also holds the closed-form references on these datasets (keys `c_…`).

## Families of systems (`experiments/run_family.py`)

| File | Content |
|---|---|
| `family_lr.jsonl` | Seed 0 at three learning rates for every model and cell, plus the closed-form references |
| `family.jsonl` | The same runs plus seeds 1–2 at the learning rate with the lowest validation MSE |
| `dev_family_tangent.jsonl` | Seed-0 runs of the 4-circuit QKAN-FWP-O with and without tangent features on the Hénon and Duffing families |

## Memory weights (`experiments/memory_probe.py`)

`memory_probe.json`: mean weight of every context pair learned by QKAN-FWP-O on each benchmark (window 32, seeds 0–2).

## Finite shots (`experiments/shot_noise.py`)

`shot_noise.jsonl`: test MSE as a function of the shot budget per circuit and input (split over the three bases for
QKAN-FWP-O, binomial sampling), for models trained with exact expectations and with a budget of 10⁴; also the number of
circuit evaluations per prediction and the condition number of the Gram matrix of QKAN-FWP-O.

`shot_decomposition.jsonl` (`--decompose`): for QKAN-FWP-O, the test MSE when only the query circuits, only the context
circuits or all circuits are sampled, with the query read in the X, Y, Z bases or along the axis programmed by the
context; and the closed-form variance of the query read-out.

## Static device errors (`experiments/device_noise.py`)

`device_noise.jsonl`: models trained on ideal circuits and evaluated, without retraining, with a read-out error,
depolarising noise or an over-rotation of every gate; for QKAN-FWP-O also with the error only in the query or only in
the context circuits.

## Cost and resources (`experiments/cost.py`, `experiments/resources.py`)

`cost.json`: forward-pass time of the least-squares read-out, the delta rule and the static model.
`resources.json`: per prediction, the number of circuits, circuit runs and measurement settings, the gate angles that
have to be reloaded, the size of the fast state kept in classical memory and the multiply-adds of the memory update.

## Solar cycle (`experiments/run_solar.py`)

| File | Content |
|---|---|
| `dev_solar.jsonl` | Pilot runs (seeds 100–101) |
| `dev_solar_om.jsonl` | Configuration sweep of QKAN-FWP-O on the paper split (compared on validation loss) |
| `final_solar.jsonl`, `final_solar_lr1.jsonl` | Baseline and single changes on the paper split; learning rate 1e-3 |
| `final_solar_pm.jsonl` | QKAN-FWP+ and its two parts; the paper's learning-rate grid |
| `final_solar_split622.jsonl`, `final_solar_split71515.jsonl` | 60/20/20 and 70/15/15 chronological splits |
| `final_solar_om.jsonl` | QKAN-FWP-O with and without fast weights, all three splits |
| `solar_purged.jsonl` | Baseline, QKAN-FWP+ and both versions of QKAN-FWP-O with splits by target time (`--purge`): the last 131 windows of train and validation are dropped, so no target of one split lies inside the next |
| `solar_preds*/` | Test forecasts of the selected checkpoints (used for the figures) |

## Generated tables

`tables_final.md`, `tables_single_change.md` (from `experiments/make_figures.py`), `tables_om.md` (from
`experiments/make_om_report.py`) and `tables_code.md` (from `experiments/make_code_report.py`) hold the tables that `experiments/report/build_report.py` inserts into `REPORT.md`.
