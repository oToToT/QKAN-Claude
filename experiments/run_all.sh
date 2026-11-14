#!/usr/bin/env bash
# Reproduce every number in REPORT.md.  ~25 CPU-core-hours in total; finished
# jobs are skipped on rerun.  Run from the repository root.
#
#   1. re-implemented baseline and single changes on top of it
#   2. parameter-matched gated model (QKAN-FWP+) and static control (HQKAN-Δ)
#   3. references and robustness checks
#   4. observable-memory FWP (QKAN-FWP-O), CMG baselines, controls that swap the
#      features or the memory rule, families of systems, finite shots, static
#      device errors, solar cycle
#   5. the same benchmarks with the settings of the authors' released code
#   6. tables, figures and the report
set -euo pipefail
SMALL="bessel shm narma5 narma10 dqc"

# ===========================================================================
# 1. Re-implemented baseline and single changes
# ===========================================================================
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
# 2. Parameter-matched models: QKAN-based, parameter count <= the paper's
#    model, every dataset, every baseline with a validated learning rate
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

# final numbers: QKAN-FWP+ (both read/write orders), HQKAN-Δ and the two other tuned paper variants on all 24 cells
P=results/final_timeseries_pm.jsonl
python experiments/run_timeseries.py --protocol paper --out $P \
    --variants pmx_diff8_edge_h3l2@cos30 pmx_diff8_edge_h3l2_wf@cos30 ar_hqkan8@cos30
python experiments/run_timeseries.py --protocol paper --datasets $SMALL --variants gqkan_fwp@cos100 g_qkanfwp@cos30 --out $P
python experiments/run_timeseries.py --protocol paper --datasets jc --variants gqkan_fwp@cos30 g_qkanfwp@cos10 --out $P
# ablations of QKAN-FWP+ and the LSTM control
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
# 3. References and robustness checks
# ===========================================================================
FWP=pmx_diff8_edge_h3l2
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
    --variants base+z base+z@cos30 $FWP+z@cos30 ar_hqkan8+z@cos30
python experiments/run_timeseries.py --protocol paper --datasets jc --windows 16 --out results/robust_exactz.jsonl \
    --variants base+z base+z@cos10 $FWP+z@cos30 ar_hqkan8+z@cos30
python experiments/run_timeseries.py --protocol paper --datasets $SMALL --windows 16 --norm train --out results/robust_norm.jsonl \
    --variants base base@cos30 $FWP@cos30 ar_hqkan8@cos30
python experiments/run_timeseries.py --protocol paper --datasets jc --windows 16 --norm train --out results/robust_norm.jsonl \
    --variants base base@cos10 $FWP@cos30 ar_hqkan8@cos30
python experiments/run_timeseries.py --protocol paper --datasets narma5b narma10b --windows 8 16 --out results/robust_burnin.jsonl \
    --variants base base@cos30 $FWP@cos30 ar_hqkan8@cos30

# ===========================================================================
# 4. Observable-memory FWP (QKAN-FWP-O), CMG baselines, families, shots, solar
# ===========================================================================
OM=om_c0h6r1_p5
# configuration of QKAN-FWP-O (validation split)
python experiments/run_timeseries.py --protocol dev --datasets $SMALL --windows 8 16 64 --seeds 0 1 2 --out results/dev_om.jsonl \
    --variants om_c4h4r2_p3@cos30 om_c4h4r2_p5@cos30 om_c4h4r2_p7@cos30 om_c8h4r2_p3@cos30 om_c8h4r2_p5@cos30 om_c8h4r2_p7@cos30 \
               om_c8h4r2_p5_m2@cos30 om_c8h4r2_p5_m4@cos30 om_c8h4r2_p5_m6@cos30 om_c8h4r2_p5_nomask@cos30 \
               om_c5h4r2_p5@cos30 om_c6h4r2_p5@cos30 om_c7h4r2_p5@cos30 om_c6h5r2_p5@cos30 om_c6h4r1_p5@cos30 om_c6h4r3_p5@cos30 \
               om_c6h4r2_p7@cos30 om_c6h4r2_p3@cos30 om_c6h6r1_p5@cos30 $OM@cos30
python experiments/run_timeseries.py --protocol dev --datasets jc --windows 8 16 64 --seeds 0 1 --out results/dev_om.jsonl \
    --variants om_c6h6r1_p5@cos30 om_c6h6r1_p5@cos10
# final numbers: QKAN-FWP-O, its ablations, and the CMG baselines
python experiments/run_timeseries.py --datasets $SMALL --out results/final_om.jsonl \
    --variants $OM@cos30 om_c0h4r1_p5@cos30 om_c6h6r1_p5@cos30 ${OM}_static@cos30 ${OM}_classical@cos30 ${OM}_nobase@cos30 \
               ${OM}_gconst@cos30 ${OM}_gnone@cos30 ${OM}_delta@cos30 ${OM}_pscalar@cos30
python experiments/run_timeseries.py --datasets jc --out results/final_om.jsonl \
    --variants $OM@cos30 ${OM}_static@cos30 ${OM}_classical@cos30
# controls: single precision, and classical tanh / cos features read by the same memory
python experiments/run_timeseries.py --out results/final_om.jsonl \
    --variants ${OM}_single@cos30 ${OM}_tanh@cos30 ${OM}_fourier@cos30
# controls with the same memory on other features (first-harmonic Fourier, quadratic polynomial, small MLP),
# other memory rules (exponentially weighted RLS, delta rule with four sweeps) and a static model of the same size
python experiments/run_timeseries.py --datasets $SMALL --out results/final_om.jsonl \
    --variants ${OM}_fourier1@cos30 om_c0h8r1_p5_fourier1@cos30 ${OM}_poly2@cos30 ${OM}_mlp@cos30 \
               om_c0h9r1_p5_static@cos30 ${OM}_delta4@cos30 ${OM}_rls@cos30
python experiments/run_timeseries.py --datasets jc --out results/final_om.jsonl \
    --variants om_c0h8r1_p5_fourier1@cos30 ${OM}_poly2@cos30 ${OM}_mlp@cos30 om_c0h9r1_p5_static@cos30
# CMG baselines: learning rate chosen on the validation split, then the final runs
python experiments/run_timeseries.py --protocol dev --datasets $SMALL --windows 16 64 --seeds 100 101 102 \
    --variants cmg@cos10 cmg@cos30 cmg@cos100 cmg_plus@cos10 cmg_plus@cos30 cmg_plus@cos100 --out results/dev_cmg.jsonl
python experiments/run_timeseries.py --protocol dev --datasets jc --windows 16 --seeds 100 \
    --variants cmg@cos10 cmg@cos30 cmg_plus@cos10 cmg_plus@cos30 --out results/dev_cmg.jsonl
python experiments/run_timeseries.py --datasets $SMALL --variants cmg cmg@cos30 cmg_plus@cos30 --out results/final_cmg.jsonl
python experiments/run_timeseries.py --datasets jc --variants cmg@cos10 cmg_plus@cos10 cmg_plus@cos30 --out results/final_cmg.jsonl
# robustness of QKAN-FWP-O: train-only normalisation, NARMA without the start-up transient
python experiments/run_timeseries.py --windows 16 --norm train --variants $OM@cos30 --out results/robust_norm.jsonl
python experiments/run_timeseries.py --datasets narma5b narma10b --windows 8 16 --variants $OM@cos30 --out results/robust_burnin.jsonl

# families of systems: learning-rate sweep on seed 0, then seeds 1-2 at the rate with the lowest validation MSE
FV=""
for v in $OM ${OM}_static ${OM}_classical ${OM}_gnone ${OM}_delta ${OM}_single ${OM}_tanh ${OM}_fourier \
         ${OM}_fourier1 om_c0h8r1_p5_fourier1 ${OM}_poly2 ${OM}_mlp om_c0h9r1_p5_static ${OM}_delta4 ${OM}_rls \
         ar_hqkan8 pmx_diff8_edge_h3l2 cmg_plus cmg base lstm_ext8; do
    FV="$FV $v@cos3 $v@cos10 $v@cos30"
done
python experiments/run_family.py --windows 16 --noise 0 0.02 --variants refs $FV --seeds 0 --out results/family_lr.jsonl
[ -f results/family.jsonl ] || cp results/family_lr.jsonl results/family.jsonl
python experiments/run_family.py --windows 16 --noise 0 0.02 --best-lr-from results/family_lr.jsonl --seeds 0 1 2 \
    --out results/family.jsonl

# what the memory of QKAN-FWP-O uses (weights of the context pairs)
python experiments/memory_probe.py

# cost of the read-out rules (timing) and resources per prediction (circuit runs, measurement settings, classical state)
python experiments/cost.py
python experiments/resources.py

# finite shots (budget per circuit and input, split over the measurement bases; binomial sampling)
python experiments/shot_noise.py --variants $OM@cos30 ${OM}_single@cos30 ${OM}_axis@cos30 ar_hqkan8+z@cos30 pmx_diff8_edge_h3l2+z@cos30 \
    --train-shots 0 1e4 --out results/shot_noise.jsonl
# where the shot noise enters (query / context circuits; X, Y, Z or the programmed axis) and the closed-form variance
python experiments/shot_noise.py --decompose --variants $OM@cos30 --train-shots 0 1e4 --out results/shot_decomposition.jsonl

# static device errors switched on at test time (read-out error, depolarising noise, over-rotation), no retraining
python experiments/device_noise.py --out results/device_noise.jsonl \
    --variants $OM@cos30 ${OM}_rls@cos30 ${OM}_static@cos30 om_c0h9r1_p5_static@cos30 ar_hqkan8+z@cos30 pmx_diff8_edge_h3l2+z@cos30

# solar cycle: configuration sweep (compared on validation loss), then both versions on the three splits
python experiments/run_solar.py --seeds 0 1 --out results/dev_solar_om.jsonl \
    --variants om om_static om_gnone om_classical om_last om_b8 om_b24 om_h4 om_h10 om_c6 om_c22p6 om_p1 om_p4 om_s1 om@lr1 om_static@lr1
for lr in 2.5e-3 1e-3; do
    python experiments/run_solar.py --variants om_static om --lr $lr --out results/final_solar_om.jsonl
done
python experiments/run_solar.py --variants om_static om --split 0.6 0.2 0.2 --out results/final_solar_om.jsonl
python experiments/run_solar.py --variants om_static om --split 0.7 0.15 0.15 --seeds 0 1 2 --out results/final_solar_om.jsonl
# the same models with splits by target time: the last 131 windows of train and validation are dropped, so that no
# target of one split lies inside the next split
for lr in 2.5e-3 1e-3; do
    python experiments/run_solar.py --purge --variants om_static om base mtg_cyc_pm --lr $lr --out results/solar_purged.jsonl
done
python experiments/run_solar.py --purge --variants om_static om base mtg_cyc_pm --split 0.6 0.2 0.2 --out results/solar_purged.jsonl
python experiments/run_solar.py --purge --variants om_static om base mtg_cyc_pm --split 0.7 0.15 0.15 --seeds 0 1 2 \
    --out results/solar_purged.jsonl

# ===========================================================================
# 5. Settings of the authors' released code (github.com/MatthewPeng57/Gated-QKAN-FWP):
#    datasets c_* (NARMA reads the drive u), the ported 159- and 12,474-parameter models
# ===========================================================================
C=results/code_protocol.jsonl
FWP=pmx_diff8_edge_h3l2
# learning rates on the validation part of these datasets
python experiments/run_timeseries.py --protocol dev --datasets c_bessel c_shm --windows 16 64 --seeds 100 101 \
    --variants authors@cos3 authors@cos10 authors@cos30 $OM@cos10 $OM@cos30 ar_hqkan8@cos10 ar_hqkan8@cos30 $FWP@cos10 $FWP@cos30 \
    --out results/dev_code_protocol.jsonl
python experiments/run_timeseries.py --protocol dev --datasets c_narma5 c_narma10 --windows 16 64 --seeds 100 101 \
    --variants authors@cos3 authors@cos10 authors@cos30 ${OM}_static_noskip@cos10 ${OM}_static_noskip@cos30 \
               om_c0h9r1_p5_static_noskip@cos10 om_c0h9r1_p5_static_noskip@cos30 ar_hqkan8_noskip@cos10 ar_hqkan8_noskip@cos30 \
               ${FWP}_noskip@cos10 ${FWP}_noskip@cos30 ${OM}_hist@cos10 ${OM}_hist@cos30 \
               om_c0h9r1_p5_hist_pscalar@cos10 om_c0h9r1_p5_hist_pscalar@cos30 \
    --out results/dev_code_protocol.jsonl
python experiments/run_timeseries.py --protocol dev --datasets c_dqc c_jc --windows 16 --seeds 100 \
    --variants authors@cos3 authors@cos10 authors@cos30 $OM@cos10 $OM@cos30 ar_hqkan8@cos10 ar_hqkan8@cos30 $FWP@cos10 $FWP@cos30 \
    --out results/dev_code_protocol.jsonl
# the authors' model at the paper's learning rate (evaluated every 5 epochs up to 100), then all models
python experiments/run_timeseries.py --datasets c_bessel c_shm c_narma5 c_narma10 c_dqc c_jc --variants authors --epochs 100 --out $C
python experiments/run_timeseries.py --datasets c_bessel c_shm --out $C \
    --variants authors@cos30 ar_hqkan8@cos30 $FWP@cos10 $OM@cos30 om_c0h9r1_p5_static@cos30
python experiments/run_timeseries.py --datasets c_narma5 c_narma10 --out $C \
    --variants authors@cos30 ar_hqkan8_noskip@cos30 ${FWP}_noskip@cos30 ${OM}_static_noskip@cos30 om_c0h9r1_p5_static_noskip@cos30 \
               ${OM}_hist@cos30 om_c0h9r1_p5_hist_pscalar@cos30
python experiments/run_timeseries.py --datasets c_dqc --out $C \
    --variants authors@cos30 ar_hqkan8@cos30 $FWP@cos30 $OM@cos30 om_c0h9r1_p5_static@cos30
python experiments/run_timeseries.py --datasets c_jc --out $C \
    --variants authors@cos10 ar_hqkan8@cos30 $FWP@cos10 $OM@cos30 om_c0h9r1_p5_static@cos30
# solar cycle on the authors' 3,265-record file with the ported model, both splits
python experiments/run_solar.py --records 3265 --variants om_static om authors mtg_cyc_pm --out results/solar_code_protocol.jsonl
python experiments/run_solar.py --records 3265 --purge --variants om_static om authors mtg_cyc_pm --out results/solar_code_protocol.jsonl

# ===========================================================================
# 6. Tables, figures, report
# ===========================================================================
python experiments/make_figures.py
python experiments/make_om_report.py
python experiments/make_code_report.py
python experiments/report/build_report.py
