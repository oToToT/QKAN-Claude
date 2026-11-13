#!/usr/bin/env bash
# Reproduce every number in REPORT.md.  ~7 CPU-core-hours in total; finished
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
               lstm@cos10 lstm@cos30 skip_dif2@cos30 dif3@cos30 skip_dif3@lr30 \
    --out results/dev_screen.jsonl
python experiments/run_timeseries.py --protocol dev --datasets jc --windows 16 --seeds 100 \
    --variants base@cos10 base@cos30 skip_dif3@cos10 skip_dif3@cos30 --out results/dev_screen.jsonl
python experiments/run_solar.py --seeds 100 101 --out results/dev_solar.jsonl \
    --variants base base@cos5 base@cos10 mtg ctx12s12 mtg_ctx12s12 full_s12 ungated

# ---- final numbers (paper protocol split, seeds 0-4) ----------------------
F=results/final_timeseries.jsonl
python experiments/run_timeseries.py --protocol paper --variants base base@cos30 skip_dif3@cos30 --out $F
python experiments/run_timeseries.py --protocol paper --datasets jc --variants base@cos10 --out $F
python experiments/run_timeseries.py --protocol paper --datasets $SMALL --windows 16 64 --out $F \
    --variants skip_dif3 skip_mtg_dif3@cos30 ar_hqkan@cos30 lstm@cos30 \
               skip@cos30 dif3@cos30 mtg@cos30 skip_mtg@cos30 skip dif3 mtg ungated base_big@cos30
python experiments/run_timeseries.py --protocol paper --datasets $SMALL --windows 16 --out $F \
    --variants gqkan_fwp gqkan_fwp@cos30 gqkan_fwp_ext@cos30 g_qkanfwp g_qkanfwp@cos30 g_qkanfwp_ext@cos30
python experiments/run_solar.py --variants base mtg chrono mtg_ctx12s12 --save-dir results/solar_preds \
    --out results/final_solar.jsonl
python experiments/run_solar.py --variants lstm_s --seeds 0 1 2 --out results/final_solar.jsonl

python experiments/make_figures.py
