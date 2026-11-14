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
| `dev_om.jsonl` | Validation runs used to choose the configuration of QKAN-FWP-O (token length, circuits, prior, masking) |
| `final_timeseries.jsonl` | Paper protocol, seeds 0–4: re-implemented GQKAN-QKANFWP (lr 1e-3 and tuned), GQKAN-FWP, G-QKANFWP |
| `final_timeseries_abl.jsonl` | Paper protocol: one change at a time on top of the baseline (appendix A of the report) |
| `final_timeseries_pm.jsonl` | Paper protocol: QKAN-FWP+, HQKAN-Δ, their ablations and the LSTM control |
| `final_cmg.jsonl` | Paper protocol: complementary matrix gate (CMG) baselines |
| `final_om.jsonl` | Paper protocol: QKAN-FWP-O and its ablations |
| `extra_seeds.jsonl` | Seeds 5–14 for the QKAN-FWP+ vs HQKAN-Δ comparison |
| `robust_exactz.jsonl` | Physical ⟨Z⟩ read-out instead of the `qkan` default |
| `robust_norm.jsonl` | Min–max scaling fitted on the training part only (`norm: "train"`), or no scaling (`norm: "none"`) |
| `robust_burnin.jsonl` | NARMA with 200 burn-in steps discarded |
| `robust_writefirst.jsonl` | Baselines with the write-then-read order |
| `reference_linear_ar.json` | Closed-form linear AR(p) on the same train / test windows (`experiments/reference_baselines.py`) |

## Families of systems (`experiments/run_family.py`)

| File | Content |
|---|---|
| `family_lr.jsonl` | Seed 0 at three learning rates for every model and cell, plus the closed-form references |
| `family.jsonl` | The same runs plus seeds 1–2 at the learning rate with the lowest validation MSE |

## Finite shots (`experiments/shot_noise.py`)

`shot_noise.jsonl`: test MSE as a function of the number of shots per measured expectation, for models trained with exact
expectations and with 10⁴ shots.

## Solar cycle (`experiments/run_solar.py`)

| File | Content |
|---|---|
| `dev_solar.jsonl` | Pilot runs (seeds 100–101) |
| `dev_solar_om.jsonl` | Configuration sweep of QKAN-FWP-O on the paper split (compared on validation loss) |
| `final_solar.jsonl`, `final_solar_lr1.jsonl` | Baseline and single changes on the paper split; learning rate 1e-3 |
| `final_solar_pm.jsonl` | QKAN-FWP+ and its two parts; the paper's learning-rate grid |
| `final_solar_split622.jsonl`, `final_solar_split71515.jsonl` | 60/20/20 and 70/15/15 chronological splits |
| `final_solar_om.jsonl` | QKAN-FWP-O with and without fast weights, all three splits |
| `solar_preds*/` | Test forecasts of the selected checkpoints (used for the figures) |

## Generated tables

`tables_final.md`, `tables_single_change.md` (from `experiments/make_figures.py`) and `tables_om.md` (from
`experiments/make_om_report.py`) hold the tables that `experiments/report/build_report.py` inserts into `REPORT.md`.
