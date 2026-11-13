#!/usr/bin/env bash
# Reproduce every number in REPORT.md.  ~15 CPU-core-hours in total; finished
# jobs are skipped on rerun.  Run from the repository root.
set -euo pipefail
SMALL="bessel shm narma5 narma10 dqc"

# ---- design decisions (validation split, seeds 100-102) -------------------
python experiments/run_timeseries.py --protocol dev --datasets $SMALL --windows 16 64 \
    --variants arch_h6l3r1 arch_r3 arch_h4l4r1 arch_f2 arch_exactz --seeds 100 101 102 103 104 105 \
    --out results/dev_baseline_arch.jsonl
python experiments/run_timeseries.py --protocol dev --datasets $SMALL --windows 16 64 --seeds 100 101 102 \
    --variants base ungated chrono mtg_edge mtg_layer_plain mtg mtg_param ctx2 ctx3 ctx4 skip cos \
               lr3 cos3 cos10 dif2 dif3 skip_mtg skip_dif2 skip_dif3 skip_mtg_dif2 skip_cos3 skip_mtg_dif2_cos3 \
               base@cos30 skip@cos10 skip@cos30 skip_dif3@cos3 skip_dif3@cos10 skip_dif3@cos30 \
               skip_mtg_dif3@cos3 skip_mtg_dif3@cos10 skip_mtg_dif3@cos30 skip_mtg@cos10 mtg@cos10 dif3@cos10 \
               base@cos100 skip_dif3@cos100 skip_mtg_dif3@cos100 ar_hqkan@cos10 ar_hqkan@cos30 ar_hqkan@cos100 \
               lstm@cos10 lstm@cos30 lstm@cos100 lstm_ext@cos10 lstm_ext@cos30 lstm_ext@cos100 \
               skip_dif2@cos30 dif3@cos30 skip_dif3@lr30 \
    --out results/dev_screen.jsonl
python experiments/run_timeseries.py --protocol dev --datasets jc --windows 16 --seeds 100 \
    --variants base@cos10 base@cos30 skip_dif3@cos10 skip_dif3@cos30 --out results/dev_screen.jsonl
python experiments/run_solar.py --seeds 100 101 --out results/dev_solar.jsonl \
    --variants base base@cos5 base@cos10 mtg ctx12s12 mtg_ctx12s12 full_s12 ungated

# ---- final numbers (paper protocol split, seeds 0-4) ----------------------
F=results/final_timeseries.jsonl
python experiments/run_timeseries.py --protocol paper --datasets jc --variants base base@cos10 skip_dif3@cos30 --out $F
python experiments/run_timeseries.py --protocol paper --datasets $SMALL --variants base base@cos30 skip_dif3@cos30 --out $F
python experiments/run_timeseries.py --protocol paper --datasets $SMALL --windows 16 64 --out results/final_timeseries_abl.jsonl \
    --variants skip_dif3 skip_mtg_dif3@cos30 ar_hqkan@cos30 lstm@cos100 lstm_ext@cos30 \
               skip@cos30 dif3@cos30 mtg@cos30 skip_mtg@cos30 skip dif3 mtg ungated base_big@cos30
python experiments/run_timeseries.py --protocol paper --variants skip_mtg_dif3@cos30 --out results/final_timeseries_abl.jsonl
python experiments/run_timeseries.py --protocol paper --datasets $SMALL --windows 16 --out $F \
    --variants gqkan_fwp gqkan_fwp@cos30 gqkan_fwp_ext@cos30 g_qkanfwp g_qkanfwp@cos30 g_qkanfwp_ext@cos30
python experiments/run_solar.py --variants base mtg chrono mtg_ctx12s12 --save-dir results/solar_preds \
    --out results/final_solar.jsonl
# robustness: a 60/20/20 split whose test targets span five cycles, and the lower lr of the paper's grid
python experiments/run_solar.py --variants base mtg --split 0.6 0.2 0.2 --save-dir results/solar_preds_split622 \
    --out results/final_solar_split622.jsonl
python experiments/run_solar.py --variants base@lr1 mtg@lr1 --save-dir results/solar_preds \
    --out results/final_solar_lr1.jsonl

# ===========================================================================
# Round 2: fair comparison (QKAN-based, parameter count <= the paper's model,
# every dataset, every baseline with a validated learning rate)
# ===========================================================================
D=results/dev_param_matched.jsonl
# candidates within the 152-parameter budget (validation split, seeds 100-102)
python experiments/run_timeseries.py --protocol dev --datasets $SMALL --windows 8 16 64 --seeds 100 101 102 --out $D \
    --variants base@cos30 skip_dif3@cos30 skip_mtg_dif3@cos30 \
               pm_diff3_layer_h3l2@cos30 pm_diff4_layer_h3l2@cos30 pm_diff5_layer_h3l2@cos30 pm_diff6_edge_h3l2@cos30 \
               pm_diff3_edge_h4l2@cos30 pm_diff3_edge_h2l3@cos30 pm_diff5_scalar_h2l3@cos30 pm_diff4_edge_h4l2@cos30 \
               pm_lags3_layer_h3l2@cos30 pm_lags5_layer_h3l2@cos30 pm_lags8_edge_h3l2@cos30 pm_lags10_layer_h2l2@cos30 \
               pm_lags6_edge_h3l2@cos30 \
               pmx_diff3_layer_h3l2@cos30 pmx_diff4_layer_h3l2@cos30 pmx_diff5_layer_h3l2@cos30 pmx_diff6_edge_h3l2@cos30 \
               pmx_diff8_edge_h3l2@cos30 pmx_diff4_edge_h4l2@cos30 pmx_diff6_layer_h2l2@cos30 pmx_diff5_scalar_h2l3@cos30 \
               pmx_diff10_layer_h2l2@cos30 pmx_diff12_edge_h2l2@cos30 pmx_diff9_scalar_h3l2@cos30 pmx_diff7_edge_h3l2@cos30 \
               pmx_diff8_edge_h3l2@cos10 pmx_diff8_edge_h3l2@cos100 \
               pmx_diff8_edge_h3l2_wf@cos30 pmx_diff8_edge_h3l2_wf@cos10 pmx_diff8_layer_h2l2_wf@cos30 pmx_diff4_layer_h3l2_wf@cos30
# learning rates of the paper's other QKAN variants and of the controls
python experiments/run_timeseries.py --protocol dev --datasets $SMALL --windows 16 64 --seeds 100 101 102 --out $D \
    --variants gqkan_fwp@cos10 gqkan_fwp@cos30 gqkan_fwp@cos100 g_qkanfwp@cos10 g_qkanfwp@cos30 g_qkanfwp@cos100 \
               ar_hqkan8@cos30 ar_hqkan8@cos100 lstm_ext8@cos30 lstm_ext8@cos100
python experiments/run_timeseries.py --protocol dev --datasets $SMALL --windows 16 64 --seeds 100 101 102 \
    --out results/dev_other_lr.jsonl --variants gqkan_fwp@cos300
python experiments/run_timeseries.py --protocol dev --datasets jc --windows 16 --seeds 100 --out $D \
    --variants pmx_diff8_edge_h3l2@cos30 pmx_diff8_edge_h3l2@cos10 base@cos10
python experiments/run_timeseries.py --protocol dev --datasets jc --windows 16 --seeds 100 --out results/dev_other_lr_jc.jsonl \
    --variants gqkan_fwp@cos30 gqkan_fwp@cos100 g_qkanfwp@cos10 g_qkanfwp@cos30 ar_hqkan8@cos30 ar_hqkan8@cos10

# final numbers: our three QKAN-based models and the two extra tuned baselines on all 24 cells
P=results/final_timeseries_pm.jsonl
python experiments/run_timeseries.py --protocol paper --out $P \
    --variants pmx_diff8_edge_h3l2@cos30 pmx_diff8_edge_h3l2_wf@cos30 ar_hqkan8@cos30
python experiments/run_timeseries.py --protocol paper --datasets $SMALL --variants gqkan_fwp@cos100 g_qkanfwp@cos30 --out $P
python experiments/run_timeseries.py --protocol paper --datasets jc --variants gqkan_fwp@cos30 g_qkanfwp@cos10 --out $P
# ablations and the LSTM control of the final model
python experiments/run_timeseries.py --protocol paper --datasets $SMALL --windows 16 64 --out $P \
    --variants pmx_diff8_edge_h3l2_noskip@cos30 pmx_diff1_edge_h3l2@cos30 pmx_diff3_edge_h3l2@cos30 \
               pm_diff8_edge_h3l2@cos30 pmx_diff8_scalar_h3l2@cos30 lstm_ext8@cos30
# ten extra seeds for the QKAN-FWP+ vs HQKAN-Delta comparison
python experiments/run_timeseries.py --protocol paper --datasets $SMALL --windows 16 64 --seeds 5 6 7 8 9 10 11 12 13 14 \
    --out results/extra_seeds.jsonl --variants ar_hqkan8@cos30 pmx_diff8_edge_h3l2@cos30

# solar: parameter-matched variants (pilot, seeds 100-101), then the final model, its ablations,
# the paper's learning-rate grid and two more chronological splits
python experiments/run_solar.py --seeds 100 101 --out results/dev_solar.jsonl \
    --variants mtg_b24 mtg_y_b24 base_b24 mtg_pm mtg_y_pm mtg_b16 mtg_b40 base_cyc mtg_cyc_pm base_cyc_b24 mtg_cyc_b24
python experiments/run_solar.py --variants mtg_cyc_pm mtg_pm base_cyc --save-dir results/solar_preds --out results/final_solar_pm.jsonl
python experiments/run_solar.py --variants mtg_cyc_pm@lr1 mtg_cyc_pm@lr2 base@lr2 --out results/final_solar_pm.jsonl
python experiments/run_solar.py --variants mtg_cyc_pm --split 0.6 0.2 0.2 --save-dir results/solar_preds_split622 \
    --out results/final_solar_split622.jsonl
python experiments/run_solar.py --variants mtg_cyc_pm base --seeds 0 1 2 --split 0.7 0.15 0.15 \
    --out results/final_solar_split71515.jsonl

# ===========================================================================
# Round 3: checks prompted by external review
# ===========================================================================
OURS=pmx_diff8_edge_h3l2
# closed-form linear autoregression on the same train / test windows
python experiments/reference_baselines.py
# does the write-then-read order (as described in arXiv:2607.27945) reproduce the printed baseline numbers?
python experiments/run_timeseries.py --protocol paper --datasets $SMALL --variants base+wf --out results/robust_writefirst.jsonl
python experiments/run_timeseries.py --protocol paper --datasets $SMALL --windows 16 --variants gqkan_fwp+wf g_qkanfwp+wf \
    --out results/robust_writefirst.jsonl
# NARMA trained on the raw (un-normalised) series
python experiments/run_timeseries.py --protocol paper --datasets narma5 narma10 --windows 16 --norm none \
    --variants base base+wf g_qkanfwp g_qkanfwp+wf --out results/robust_norm.jsonl
# physical <Z> read-out, train-only normalisation, NARMA without the start-up transient
python experiments/run_timeseries.py --protocol paper --datasets $SMALL --windows 16 --out results/robust_exactz.jsonl \
    --variants base+z base+z@cos30 $OURS+z@cos30 ar_hqkan8+z@cos30
python experiments/run_timeseries.py --protocol paper --datasets jc --windows 16 --out results/robust_exactz.jsonl \
    --variants base+z base+z@cos10 $OURS+z@cos30 ar_hqkan8+z@cos30
python experiments/run_timeseries.py --protocol paper --datasets $SMALL --windows 16 --norm train --out results/robust_norm.jsonl \
    --variants base base@cos30 $OURS@cos30 ar_hqkan8@cos30
python experiments/run_timeseries.py --protocol paper --datasets jc --windows 16 --norm train --out results/robust_norm.jsonl \
    --variants base base@cos10 $OURS@cos30 ar_hqkan8@cos30
python experiments/run_timeseries.py --protocol paper --datasets narma5b narma10b --windows 8 16 --out results/robust_burnin.jsonl \
    --variants base base@cos30 $OURS@cos30 ar_hqkan8@cos30

python experiments/make_figures.py
