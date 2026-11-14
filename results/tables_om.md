## Per-dataset summary (geometric mean over N ∈ {8, 16, 32, 64} of the seed-mean test MSE)

| Dataset | Best printed in the two papers | GQKAN-QKANFWP, tuned lr (152) | QKAN-FWP+ (149) | HQKAN-Δ (136) | QKAN-FWP-O (130–154) | *Linear AR(8) (9)* |
|---|---|---|---|---|---|---|
| Bessel J2 | 5.3e-06 | 4.5e-06 | 1.5e-06 | 1.4e-07 | **2.8e-12** | *5.3e-24* |
| Damped SHM | 8.8e-06 | 1.2e-05 | 1.9e-06 | 3.2e-07 | **5.9e-12** | *9.0e-14* |
| NARMA5 | 6.5e-06 | 2.3e-04 | 6.0e-06 | 2.9e-06 | **4.0e-07** | *1.3e-06* |
| NARMA10 | 9.5e-06 | 6.9e-04 | 8.1e-06 | 2.7e-06 | **3.2e-07** | *1.7e-06* |
| Delayed quantum control | 5.5e-06 | 4.4e-04 | 8.0e-06 | **3.5e-06** | – | *2.6e-07* |
| Jaynes–Cummings | 7.6e-06 | 1.7e-05 | 7.4e-09 | **1.7e-09** | – | *1.1e-31* |

## Each model against every reference (geometric-mean test-MSE factor; in brackets: cells where the model is lower)

| Reference | Params | QKAN-FWP+ (149) | HQKAN-Δ (136) | QKAN-FWP-O (130–154) |
|---|---|---|---|---|
| GQKAN-QKANFWP, paper protocol | 152 | 222× lower (19/19) | 873× lower (19/19) | 5.1e5× lower (19/19) |
| GQKAN-QKANFWP, tuned lr | 152 | 19× lower (19/19) | 75× lower (19/19) | 4.4e4× lower (19/19) |
| GQKAN-FWP, tuned lr | 114 | 30× lower (17/19) | 118× lower (19/19) | 6.9e4× lower (19/19) |
| G-QKANFWP, tuned lr | 175 | 14× lower (18/19) | 55× lower (19/19) | 3.2e4× lower (19/19) |
| QKAN-FWP+ | 149 | – | 3.9× lower (19/19) | 2282× lower (19/19) |
| HQKAN-Δ | 136 | 3.9× higher (0/19) | – | 580× lower (18/19) |
| *Printed for GQKAN-QKANFWP in arXiv:2605.06734* | 159 | 11× lower (18/19) | 44× lower (19/19) | 2.6e4× lower (19/19) |
| *Best printed number of arXiv:2605.06734 and 2607.27945* | – | 1.9× lower (14/19) | 7.3× lower (16/19) | 4239× lower (18/19) |
| *Linear AR(8), least squares* | 9 | 5.3e5× higher (2/19) | 1.3e5× higher (3/19) | 230× higher (10/19) |

## All cells: test MSE (paper protocol, mean ± std over 5 seeds)

| Dataset | N | GQKAN-QKANFWP, paper protocol (152) | GQKAN-QKANFWP, tuned lr (152) | GQKAN-FWP, tuned lr (114) | G-QKANFWP, tuned lr (175) | QKAN-FWP+ (149) | HQKAN-Δ (136) | QKAN-FWP-O (130–154) | *Linear AR(8) (9)* |
|---|---|---|---|---|---|---|---|---|---|
| Bessel J2 | 8 | 5.49e-04 ± 5.2e-04 | 6.14e-06 ± 1.5e-06 | 1.08e-04 ± 1.9e-04 | 4.77e-06 ± 2.4e-06 | 1.09e-06 ± 5.2e-07 | 8.39e-08 ± 5.4e-08 | **1.08e-12 ± 1.2e-12** | *1.3e-23* |
| Bessel J2 | 16 | 8.35e-04 ± 7.2e-04 | 4.27e-06 ± 3.0e-06 | 2.87e-06 ± 1.4e-06 | 2.62e-06 ± 2.8e-07 | 1.64e-06 ± 1.4e-06 | 1.21e-07 ± 9.7e-08 | **1.01e-12 ± 8.9e-13** | *1.0e-23* |
| Bessel J2 | 32 | 6.90e-04 ± 5.3e-04 | 4.74e-06 ± 3.3e-06 | 1.22e-06 ± 7.7e-07 | 4.10e-06 ± 1.3e-06 | 1.43e-06 ± 4.0e-07 | 1.24e-07 ± 1.1e-07 | **4.68e-12 ± 1.9e-12** | *5.7e-24* |
| Bessel J2 | 64 | 5.81e-04 ± 5.8e-04 | 3.39e-06 ± 2.0e-06 | 4.09e-06 ± 3.2e-06 | 1.44e-06 ± 3.1e-07 | 2.00e-06 ± 1.3e-06 | 2.74e-07 ± 1.9e-07 | **1.18e-11 ± 5.3e-12** | *1.0e-24* |
| Damped SHM | 8 | 8.72e-05 ± 5.5e-05 | 1.78e-05 ± 5.0e-06 | 4.42e-06 ± 1.9e-06 | 9.08e-06 ± 3.8e-06 | 1.56e-06 ± 7.6e-07 | 2.48e-07 ± 2.5e-08 | **1.60e-12 ± 7.1e-13** | *1.1e-13* |
| Damped SHM | 16 | 1.18e-04 ± 7.2e-05 | 1.15e-05 ± 6.7e-06 | 3.99e-05 ± 7.7e-05 | 1.00e-05 ± 3.8e-06 | 1.38e-06 ± 6.5e-07 | 2.01e-07 ± 7.8e-08 | **2.10e-12 ± 5.1e-13** | *1.6e-13* |
| Damped SHM | 32 | 6.98e-05 ± 5.4e-05 | 7.67e-06 ± 2.0e-06 | 4.27e-06 ± 5.6e-06 | 5.49e-06 ± 1.6e-06 | 2.54e-06 ± 1.4e-06 | 5.21e-07 ± 5.1e-07 | **2.16e-11 ± 1.6e-11** | *8.9e-14* |
| Damped SHM | 64 | 1.42e-04 ± 9.8e-05 | 1.23e-05 ± 7.0e-06 | 1.47e-06 ± 5.6e-07 | 5.46e-06 ± 1.9e-06 | 2.20e-06 ± 1.4e-06 | 4.24e-07 ± 4.9e-07 | **1.63e-11 ± 1.7e-11** | *4.3e-14* |
| NARMA5 | 8 | 1.79e-03 ± 1.2e-03 | 2.78e-04 ± 6.6e-05 | 5.63e-04 ± 6.0e-04 | 1.85e-04 ± 3.6e-05 | 3.55e-05 ± 1.2e-05 | **1.41e-05 ± 3.6e-06** | 1.68e-05 ± 3.7e-06 | *3.8e-05* |
| NARMA5 | 16 | 1.94e-03 ± 1.1e-03 | 2.29e-04 ± 5.7e-05 | 9.22e-04 ± 1.4e-03 | 1.66e-04 ± 2.3e-05 | 3.67e-06 ± 1.5e-06 | 1.79e-06 ± 2.2e-07 | **7.00e-08 ± 1.1e-08** | *5.3e-07* |
| NARMA5 | 32 | 2.23e-03 ± 1.2e-03 | 2.46e-04 ± 5.1e-05 | 3.28e-04 ± 1.1e-04 | 1.78e-04 ± 1.7e-05 | 3.84e-06 ± 1.5e-06 | 2.05e-06 ± 9.2e-07 | **4.91e-08 ± 3.9e-09** | *4.7e-07* |
| NARMA5 | 64 | 1.40e-03 ± 7.7e-04 | 1.67e-04 ± 5.9e-05 | 5.38e-04 ± 8.0e-04 | 1.42e-04 ± 6.0e-05 | 2.57e-06 ± 6.6e-07 | 1.39e-06 ± 3.1e-07 | **4.34e-07 ± 7.9e-08** | *3.1e-07* |
| NARMA10 | 8 | 2.48e-03 ± 1.6e-03 | 1.33e-03 ± 3.1e-04 | 9.50e-03 ± 8.4e-03 | 7.07e-04 ± 9.7e-05 | 8.14e-05 ± 4.7e-05 | 4.34e-05 ± 1.3e-05 | **2.09e-05 ± 3.5e-06** | *1.1e-03* |
| NARMA10 | 16 | 2.70e-03 ± 1.9e-03 | 5.24e-04 ± 4.5e-05 | 5.43e-04 ± 3.6e-05 | 4.79e-04 ± 9.5e-06 | 4.31e-06 ± 1.7e-06 | 2.14e-06 ± 3.3e-07 | **1.90e-06 ± 6.8e-07** | *3.1e-06* |
| NARMA10 | 32 | 2.89e-03 ± 1.8e-03 | 5.56e-04 ± 3.1e-05 | 5.67e-04 ± 4.7e-05 | 7.21e-04 ± 4.2e-04 | 3.09e-06 ± 1.3e-06 | 9.47e-07 ± 3.1e-07 | **2.08e-08 ± 4.1e-09** | *4.8e-08* |
| NARMA10 | 64 | 2.75e-03 ± 1.5e-03 | 5.83e-04 ± 5.1e-05 | 4.26e-03 ± 7.4e-03 | 5.18e-04 ± 2.4e-05 | 3.92e-06 ± 2.0e-06 | 6.43e-07 ± 2.6e-07 | **1.25e-08 ± 2.9e-09** | *4.7e-08* |
| Delayed quantum control | 16 | 2.04e-03 ± 4.3e-04 | 4.63e-04 ± 1.3e-04 | 1.27e-03 ± 1.9e-04 | 4.72e-04 ± 6.8e-05 | 9.03e-06 ± 4.8e-06 | 5.92e-06 ± 5.4e-06 | **3.30e-08 ± 1.1e-08** | *3.0e-07* |
| Delayed quantum control | 32 | 1.91e-03 ± 6.1e-04 | 3.96e-04 ± 9.7e-05 | 8.12e-04 ± 2.1e-04 | 3.15e-04 ± 9.4e-05 | 4.31e-06 ± 2.0e-06 | 2.65e-06 ± 1.6e-06 | **1.00e-08 ± 1.3e-09** | *3.0e-07* |
| Delayed quantum control | 64 | 1.20e-03 ± 3.3e-04 | 3.37e-04 ± 8.5e-05 | 8.04e-04 ± 7.4e-05 | 3.15e-04 ± 1.1e-04 | 1.05e-05 ± 5.6e-06 | 2.80e-06 ± 1.6e-06 | **3.44e-09 ± 5.7e-10** | *2.4e-07* |

## Closed-form linear autoregression against the best models (test MSE)

| Dataset | N | Best printed in the two papers | QKAN-FWP+ | HQKAN-Δ | QKAN-FWP-O | Linear AR(3) (4) | Linear AR(8) (9) |
|---|---|---|---|---|---|---|---|
| Bessel J2 | 8 | 8.7e-06 | 1.1e-06 | 8.4e-08 | 1.1e-12 | 7.4e-10 | **1.3e-23** |
| Bessel J2 | 16 | 4.9e-06 | 1.6e-06 | 1.2e-07 | 1.0e-12 | 7.2e-10 | **1.0e-23** |
| Bessel J2 | 32 | 2.9e-06 | 1.4e-06 | 1.2e-07 | 4.7e-12 | 6.1e-10 | **5.7e-24** |
| Bessel J2 | 64 | 6.4e-06 | 2.0e-06 | 2.7e-07 | 1.2e-11 | 2.1e-10 | **1.0e-24** |
| Damped SHM | 8 | 1.2e-05 | 1.6e-06 | 2.5e-07 | 1.6e-12 | 1.7e-08 | **1.1e-13** |
| Damped SHM | 16 | 1.4e-05 | 1.4e-06 | 2.0e-07 | 2.1e-12 | 9.8e-09 | **1.6e-13** |
| Damped SHM | 32 | 3.6e-06 | 2.5e-06 | 5.2e-07 | 2.2e-11 | 6.7e-09 | **8.9e-14** |
| Damped SHM | 64 | 1.0e-05 | 2.2e-06 | 4.2e-07 | 1.6e-11 | 4.5e-09 | **4.3e-14** |
| NARMA5 | 8 | **4.9e-06** | 3.6e-05 | 1.4e-05 | 1.7e-05 | 8.0e-05 | 3.8e-05 |
| NARMA5 | 16 | 5.2e-06 | 3.7e-06 | 1.8e-06 | **7.0e-08** | 5.6e-05 | 5.3e-07 |
| NARMA5 | 32 | 7.1e-06 | 3.8e-06 | 2.1e-06 | **4.9e-08** | 5.7e-05 | 4.7e-07 |
| NARMA5 | 64 | 9.6e-06 | 2.6e-06 | 1.4e-06 | 4.3e-07 | 4.3e-05 | **3.1e-07** |
| NARMA10 | 8 | 2.3e-05 | 8.1e-05 | 4.3e-05 | **2.1e-05** | 1.2e-03 | 1.1e-03 |
| NARMA10 | 16 | 2.0e-06 | 4.3e-06 | 2.1e-06 | **1.9e-06** | 5.0e-05 | 3.1e-06 |
| NARMA10 | 32 | 1.3e-05 | 3.1e-06 | 9.5e-07 | **2.1e-08** | 5.2e-05 | 4.8e-08 |
| NARMA10 | 64 | 1.4e-05 | 3.9e-06 | 6.4e-07 | **1.2e-08** | 4.8e-05 | 4.7e-08 |
| Delayed quantum control | 16 | 6.9e-06 | 9.0e-06 | 5.9e-06 | **3.3e-08** | 7.5e-05 | 3.0e-07 |
| Delayed quantum control | 32 | 7.8e-06 | 4.3e-06 | 2.7e-06 | **1.0e-08** | 6.7e-05 | 3.0e-07 |
| Delayed quantum control | 64 | 4.8e-06 | 1.1e-05 | 2.8e-06 | **3.4e-09** | 6.6e-05 | 2.4e-07 |

- Linear AR(8) is lower than QKAN-FWP+ in 17/19 cells.
- Linear AR(8) is lower than HQKAN-Δ in 16/19 cells.
- Linear AR(8) is lower than QKAN-FWP-O in 9/19 cells.
- Linear AR(8) is lower than the best printed number of the two papers in 16/19 cells.

## QKAN-FWP-O ablation on the paper benchmarks (test MSE ÷ full model, geometric mean over the cells both have)

| Variant | Params | All cells | Cells where the full model is better | Bessel J2 | Damped SHM | NARMA5 | NARMA10 | Delayed quantum control | Jaynes–Cummings |
|---|---|---|---|---|---|---|---|---|---|
| no fast weights (static observable R₀) | 79–103 | **202×** | 19/19 | 8436× | 1.6e4× | 5.2× | 6.7× | 52× | – |
| sequential delta rule instead of the least-squares solve | 130–154 | **83×** | 16/18 | 886× | 3936× | 2.3× | 7.7× | 26× | – |
| no gate (additive statistics, uniform weights) | 104–128 | **1.7×** | 12/18 | 1.2× | 0.51× | 3.1× | 7.2× | 1.5× | – |
| constant gate (not input dependent) | 105–129 | **1.5×** | 14/19 | 0.91× | 0.94× | 1.2× | 5× | 1.3× | – |
| one prior precision instead of one per feature | 106–130 | **1×** | 8/18 | 0.99× | 0.98× | 0.98× | 1.2× | 1× | – |
| no base-activation (linear) term: Bloch features only | 112–136 | **5×** | 17/19 | 3.8× | 25× | 1.8× | 3.2× | 5.7× | – |
| no Bloch features: linear term only (classical control) | 52–76 | **1.6×** | 13/19 | 0.5× | 3.2× | 1.6× | 1.4× | 3.3× | – |
| 4 circuits instead of 6 | 88–104 | **1.7×** | 17/19 | 1.3× | 3.6× | 1.1× | 1.6× | 1.9× | – |
| fixed token length 6 instead of min(8, N/2) | 142 | **2×** | 13/19 | 0.72× | 1.4× | 5.3× | 1.2× | 6.2× | – |

## Solar cycle: all models (528 → 132 months, paper protocol: peak-aware loss, best-validation checkpoint)

For every model the learning rate is the one with the lowest validation loss among those run (the paper's grid); test metrics are mean ± std over seeds.

### paper split 80/10/10

| Model | Params | lr (by validation) | Seeds | Val. loss | Scaled MSE ↓ | PAE ↓ | PTE ↓ |
|---|---|---|---|---|---|---|---|
| GQKAN-QKANFWP (re-implemented baseline) | 12,423 | 0.001 | 5 | 2.51 | 0.0177 ± 0.0010 | 45.8 ± 2.8 | 26.1 ± 2.2 |
| QKAN-FWP+ | 11,732 | 0.001 | 5 | 3.29 | 0.0146 ± 0.0010 | 36.0 ± 0.4 | 18.6 ± 1.7 |
| QKAN-FWP-O without fast weights (static observable) | 496 | 0.0025 | 5 | 2.37 | 0.0144 ± 0.0002 | 35.6 ± 1.1 | 21.3 ± 1.5 |
| QKAN-FWP-O | 547 | 0.0025 | 5 | 2.61 | 0.0134 ± 0.0005 | 33.1 ± 1.4 | 23.7 ± 1.1 |
| *Reference: repeat the last cycle, 13-month smoothed (no training)* | 0 | – | – | – | 0.0156 | 35.9 | 16.2 |
| *Printed in arXiv:2605.06734 for GQKAN-QKANFWP* | 12,474 | – | 5 | – | 0.0168 ± 0.0016 | 39.59 ± 2.82 | 21.89 ± 1.57 |

