## Time series: main comparison (test MSE, mean ± std over 5 seeds)

| Dataset | N | Baseline, paper protocol (lr 1e-3) | Baseline, tuned lr | Extended (residual + Δ-tokens), tuned lr |
|---|---|---|---|---|
| Jaynes–Cummings | 64 | 6.66e-05 ± 5.4e-05 | – | **5.39e-08 ± 4.0e-08** |

## Time series: ablation (5 series × N ∈ {16, 64}; ratio of seed-mean test MSE to the paper-protocol baseline)

| Variant | Params | Geo-mean MSE ratio vs baseline | Cells better than baseline | Bessel J2 | Damped SHM | NARMA5 | NARMA10 | Delayed quantum control | Jaynes–Cummings |
|---|---|---|---|---|---|---|---|---|---|

## Time series: all 24 cells

| Variant | Params | Geo-mean MSE ratio vs baseline | Cells better than baseline | Bessel J2 | Damped SHM | NARMA5 | NARMA10 | Delayed quantum control | Jaynes–Cummings |
|---|---|---|---|---|---|---|---|---|---|
| Extended (residual + Δ-tokens), tuned lr | 162 | **0.001** | 1/1 | – | – | – | – | – | 0.00 |

