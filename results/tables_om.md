## Per-dataset summary (geometric mean over N ∈ {8, 16, 32, 64} of the seed-mean test MSE)

| Dataset | Best printed in the two papers | GQKAN-QKANFWP, tuned lr (152) | CMG, tuned lr (188) | CMG + Δ-tokens + residual (173) | QKAN-FWP+ (149) | HQKAN-Δ (136) | QKAN-FWP-O (130–154) | *Linear AR(8) (9)* |
|---|---|---|---|---|---|---|---|---|
| Bessel J2 | 5.3e-06 | 4.5e-06 | 2.7e-06 | 8.6e-07 | 1.5e-06 | 1.4e-07 | **2.8e-12** | *5.3e-24* |
| Damped SHM | 8.8e-06 | 1.2e-05 | 2.5e-06 | 7.7e-07 | 1.9e-06 | 3.2e-07 | **5.9e-12** | *9.0e-14* |
| NARMA5 | 6.5e-06 | 2.3e-04 | 2.8e-04 | 5.4e-06 | 6.0e-06 | 2.9e-06 | **4.0e-07** | *1.3e-06* |
| NARMA10 | 9.5e-06 | 6.9e-04 | 7.6e-04 | 6.3e-06 | 8.1e-06 | 2.7e-06 | **3.2e-07** | *1.7e-06* |
| Delayed quantum control | 5.5e-06 | 4.4e-04 | 7.5e-04 | 4.4e-06 | 8.0e-06 | 3.5e-06 | **2.2e-08** | *2.6e-07* |
| Jaynes–Cummings | 7.6e-06 | 1.7e-05 | 6.5e-06 | 2.5e-09 | 7.4e-09 | 1.7e-09 | **4.7e-13** | *1.1e-31* |

## Each model against every reference (geometric-mean test-MSE factor; in brackets: cells where the model is lower)

| Reference | Params | QKAN-FWP+ (149) | HQKAN-Δ (136) | QKAN-FWP-O (130–154) |
|---|---|---|---|---|
| GQKAN-QKANFWP, paper protocol | 152 | 380× lower (24/24) | 1495× lower (24/24) | 1.0e6× lower (24/24) |
| GQKAN-QKANFWP, tuned lr | 152 | 45× lower (24/24) | 175× lower (24/24) | 1.2e5× lower (24/24) |
| GQKAN-FWP, tuned lr | 114 | 74× lower (22/24) | 290× lower (24/24) | 2.0e5× lower (24/24) |
| G-QKANFWP, tuned lr | 175 | 33× lower (23/24) | 129× lower (24/24) | 8.8e4× lower (24/24) |
| CMG, lr 1e-3 | 188 | 123× lower (20/20) | 478× lower (20/20) | 2.3e5× lower (20/20) |
| CMG, tuned lr | 188 | 31× lower (21/24) | 122× lower (24/24) | 8.3e4× lower (24/24) |
| CMG + Δ-tokens + residual | 173 | 1.8× higher (2/24) | 2.2× lower (22/24) | 1495× lower (24/24) |
| QKAN-FWP+ | 149 | – | 3.9× lower (24/24) | 2688× lower (24/24) |
| HQKAN-Δ | 136 | 3.9× higher (0/24) | – | 683× lower (23/24) |
| *Printed for GQKAN-QKANFWP in arXiv:2605.06734* | 159 | 40× lower (23/24) | 158× lower (24/24) | 1.1e5× lower (24/24) |
| *Best printed number of arXiv:2605.06734 and 2607.27945* | – | 5× lower (18/24) | 20× lower (21/24) | 1.3e4× lower (23/24) |
| *Linear AR(8), least squares* | 9 | 2.5e8× higher (2/24) | 6.4e7× higher (3/24) | 9.3e4× higher (11/24) |

## All cells: test MSE (paper protocol, mean ± std over 5 seeds)

| Dataset | N | GQKAN-QKANFWP, paper protocol (152) | GQKAN-QKANFWP, tuned lr (152) | GQKAN-FWP, tuned lr (114) | G-QKANFWP, tuned lr (175) | CMG, lr 1e-3 (188) | CMG, tuned lr (188) | CMG + Δ-tokens + residual (173) | QKAN-FWP+ (149) | HQKAN-Δ (136) | QKAN-FWP-O (130–154) | *Linear AR(8) (9)* |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Bessel J2 | 8 | 5.49e-04 ± 5.2e-04 | 6.14e-06 ± 1.5e-06 | 1.08e-04 ± 1.9e-04 | 4.77e-06 ± 2.4e-06 | 7.34e-05 ± 5.9e-05 | 4.84e-06 ± 5.3e-06 | 7.53e-07 ± 4.5e-07 | 1.09e-06 ± 5.2e-07 | 8.39e-08 ± 5.4e-08 | **1.08e-12 ± 1.2e-12** | *1.3e-23* |
| Bessel J2 | 16 | 8.35e-04 ± 7.2e-04 | 4.27e-06 ± 3.0e-06 | 2.87e-06 ± 1.4e-06 | 2.62e-06 ± 2.8e-07 | 9.77e-05 ± 1.1e-04 | 1.43e-06 ± 3.8e-07 | 4.24e-06 ± 7.6e-06 | 1.64e-06 ± 1.4e-06 | 1.21e-07 ± 9.7e-08 | **1.01e-12 ± 8.9e-13** | *1.0e-23* |
| Bessel J2 | 32 | 6.90e-04 ± 5.3e-04 | 4.74e-06 ± 3.3e-06 | 1.22e-06 ± 7.7e-07 | 4.10e-06 ± 1.3e-06 | 9.86e-05 ± 7.3e-05 | 5.27e-06 ± 6.5e-06 | 5.24e-07 ± 5.2e-07 | 1.43e-06 ± 4.0e-07 | 1.24e-07 ± 1.1e-07 | **4.68e-12 ± 1.9e-12** | *5.7e-24* |
| Bessel J2 | 64 | 5.81e-04 ± 5.8e-04 | 3.39e-06 ± 2.0e-06 | 4.09e-06 ± 3.2e-06 | 1.44e-06 ± 3.1e-07 | 5.54e-05 ± 4.8e-05 | 1.36e-06 ± 4.6e-07 | 3.23e-07 ± 2.6e-07 | 2.00e-06 ± 1.3e-06 | 2.74e-07 ± 1.9e-07 | **1.18e-11 ± 5.3e-12** | *1.0e-24* |
| Damped SHM | 8 | 8.72e-05 ± 5.5e-05 | 1.78e-05 ± 5.0e-06 | 4.42e-06 ± 1.9e-06 | 9.08e-06 ± 3.8e-06 | 5.46e-05 ± 2.2e-05 | 2.94e-06 ± 8.4e-07 | 1.04e-06 ± 4.9e-07 | 1.56e-06 ± 7.6e-07 | 2.48e-07 ± 2.5e-08 | **1.60e-12 ± 7.1e-13** | *1.1e-13* |
| Damped SHM | 16 | 1.18e-04 ± 7.2e-05 | 1.15e-05 ± 6.7e-06 | 3.99e-05 ± 7.7e-05 | 1.00e-05 ± 3.8e-06 | 1.38e-04 ± 1.0e-04 | 1.87e-06 ± 8.7e-07 | 8.12e-07 ± 9.4e-07 | 1.38e-06 ± 6.5e-07 | 2.01e-07 ± 7.8e-08 | **2.10e-12 ± 5.1e-13** | *1.6e-13* |
| Damped SHM | 32 | 6.98e-05 ± 5.4e-05 | 7.67e-06 ± 2.0e-06 | 4.27e-06 ± 5.6e-06 | 5.49e-06 ± 1.6e-06 | 8.55e-05 ± 4.1e-05 | 2.40e-06 ± 1.9e-06 | 5.77e-07 ± 3.0e-07 | 2.54e-06 ± 1.4e-06 | 5.21e-07 ± 5.1e-07 | **2.16e-11 ± 1.6e-11** | *8.9e-14* |
| Damped SHM | 64 | 1.42e-04 ± 9.8e-05 | 1.23e-05 ± 7.0e-06 | 1.47e-06 ± 5.6e-07 | 5.46e-06 ± 1.9e-06 | 9.25e-05 ± 5.1e-05 | 3.03e-06 ± 2.5e-06 | 7.26e-07 ± 7.0e-07 | 2.20e-06 ± 1.4e-06 | 4.24e-07 ± 4.9e-07 | **1.63e-11 ± 1.7e-11** | *4.3e-14* |
| NARMA5 | 8 | 1.79e-03 ± 1.2e-03 | 2.78e-04 ± 6.6e-05 | 5.63e-04 ± 6.0e-04 | 1.85e-04 ± 3.6e-05 | 8.80e-04 ± 4.6e-04 | 3.13e-04 ± 5.6e-05 | 2.35e-05 ± 1.7e-05 | 3.55e-05 ± 1.2e-05 | **1.41e-05 ± 3.6e-06** | 1.68e-05 ± 3.7e-06 | *3.8e-05* |
| NARMA5 | 16 | 1.94e-03 ± 1.1e-03 | 2.29e-04 ± 5.7e-05 | 9.22e-04 ± 1.4e-03 | 1.66e-04 ± 2.3e-05 | 8.71e-04 ± 6.6e-04 | 2.98e-04 ± 2.5e-05 | 2.81e-06 ± 2.0e-06 | 3.67e-06 ± 1.5e-06 | 1.79e-06 ± 2.2e-07 | **7.00e-08 ± 1.1e-08** | *5.3e-07* |
| NARMA5 | 32 | 2.23e-03 ± 1.2e-03 | 2.46e-04 ± 5.1e-05 | 3.28e-04 ± 1.1e-04 | 1.78e-04 ± 1.7e-05 | 1.09e-03 ± 1.1e-03 | 3.09e-04 ± 5.2e-05 | 3.57e-06 ± 1.8e-06 | 3.84e-06 ± 1.5e-06 | 2.05e-06 ± 9.2e-07 | **4.91e-08 ± 3.9e-09** | *4.7e-07* |
| NARMA5 | 64 | 1.40e-03 ± 7.7e-04 | 1.67e-04 ± 5.9e-05 | 5.38e-04 ± 8.0e-04 | 1.42e-04 ± 6.0e-05 | 6.51e-04 ± 4.7e-04 | 2.28e-04 ± 4.3e-05 | 3.50e-06 ± 2.2e-06 | 2.57e-06 ± 6.6e-07 | 1.39e-06 ± 3.1e-07 | **4.34e-07 ± 7.9e-08** | *3.1e-07* |
| NARMA10 | 8 | 2.48e-03 ± 1.6e-03 | 1.33e-03 ± 3.1e-04 | 9.50e-03 ± 8.4e-03 | 7.07e-04 ± 9.7e-05 | 1.79e-03 ± 2.5e-04 | 1.03e-03 ± 1.8e-04 | 5.01e-05 ± 2.5e-05 | 8.14e-05 ± 4.7e-05 | 4.34e-05 ± 1.3e-05 | **2.09e-05 ± 3.5e-06** | *1.1e-03* |
| NARMA10 | 16 | 2.70e-03 ± 1.9e-03 | 5.24e-04 ± 4.5e-05 | 5.43e-04 ± 3.6e-05 | 4.79e-04 ± 9.5e-06 | 1.58e-03 ± 4.1e-04 | 6.49e-04 ± 2.1e-04 | 4.18e-06 ± 1.1e-06 | 4.31e-06 ± 1.7e-06 | 2.14e-06 ± 3.3e-07 | **1.90e-06 ± 6.8e-07** | *3.1e-06* |
| NARMA10 | 32 | 2.89e-03 ± 1.8e-03 | 5.56e-04 ± 3.1e-05 | 5.67e-04 ± 4.7e-05 | 7.21e-04 ± 4.2e-04 | 1.75e-03 ± 6.2e-04 | 7.18e-04 ± 1.0e-04 | 2.22e-06 ± 2.0e-06 | 3.09e-06 ± 1.3e-06 | 9.47e-07 ± 3.1e-07 | **2.08e-08 ± 4.1e-09** | *4.8e-08* |
| NARMA10 | 64 | 2.75e-03 ± 1.5e-03 | 5.83e-04 ± 5.1e-05 | 4.26e-03 ± 7.4e-03 | 5.18e-04 ± 2.4e-05 | 1.65e-03 ± 5.0e-04 | 7.00e-04 ± 2.5e-04 | 3.29e-06 ± 2.1e-06 | 3.92e-06 ± 2.0e-06 | 6.43e-07 ± 2.6e-07 | **1.25e-08 ± 2.9e-09** | *4.7e-08* |
| Delayed quantum control | 8 | 2.56e-03 ± 1.1e-03 | 5.83e-04 ± 1.5e-04 | 1.16e-03 ± 1.2e-04 | 5.75e-04 ± 1.3e-04 | 3.22e-03 ± 1.3e-03 | 9.86e-04 ± 1.9e-04 | 5.12e-06 ± 4.2e-06 | 1.02e-05 ± 5.9e-06 | 3.51e-06 ± 1.4e-06 | **1.91e-07 ± 3.9e-08** | *2.3e-07* |
| Delayed quantum control | 16 | 2.04e-03 ± 4.3e-04 | 4.63e-04 ± 1.3e-04 | 1.27e-03 ± 1.9e-04 | 4.72e-04 ± 6.8e-05 | 3.42e-03 ± 1.6e-03 | 1.12e-03 ± 3.4e-04 | 4.44e-06 ± 8.2e-07 | 9.03e-06 ± 4.8e-06 | 5.92e-06 ± 5.4e-06 | **3.30e-08 ± 1.1e-08** | *3.0e-07* |
| Delayed quantum control | 32 | 1.91e-03 ± 6.1e-04 | 3.96e-04 ± 9.7e-05 | 8.12e-04 ± 2.1e-04 | 3.15e-04 ± 9.4e-05 | 2.71e-03 ± 8.4e-04 | 5.08e-04 ± 1.3e-04 | 3.30e-06 ± 2.3e-06 | 4.31e-06 ± 2.0e-06 | 2.65e-06 ± 1.6e-06 | **1.00e-08 ± 1.3e-09** | *3.0e-07* |
| Delayed quantum control | 64 | 1.20e-03 ± 3.3e-04 | 3.37e-04 ± 8.5e-05 | 8.04e-04 ± 7.4e-05 | 3.15e-04 ± 1.1e-04 | 2.90e-03 ± 1.5e-03 | 5.79e-04 ± 1.4e-04 | 4.85e-06 ± 4.1e-06 | 1.05e-05 ± 5.6e-06 | 2.80e-06 ± 1.6e-06 | **3.44e-09 ± 5.7e-10** | *2.4e-07* |
| Jaynes–Cummings | 8 | 2.75e-05 ± 1.7e-05 | 1.95e-05 ± 2.5e-06 | 5.04e-05 ± 1.1e-05 | 1.55e-05 ± 4.8e-06 | – | 1.48e-05 ± 2.1e-06 | 3.73e-09 ± 3.5e-09 | 7.71e-09 ± 6.0e-09 | 1.41e-09 ± 1.2e-09 | **1.32e-13 ± 1.5e-13** | *3.4e-31* |
| Jaynes–Cummings | 16 | 4.25e-05 ± 4.8e-05 | 2.24e-05 ± 3.5e-06 | 5.25e-05 ± 2.1e-06 | 1.01e-05 ± 2.6e-06 | – | 6.00e-06 ± 4.6e-06 | 9.79e-10 ± 7.8e-10 | 3.68e-09 ± 1.5e-09 | 1.70e-09 ± 1.2e-09 | **1.58e-13 ± 1.7e-13** | *1.2e-31* |
| Jaynes–Cummings | 32 | 3.38e-05 ± 4.1e-05 | 1.42e-05 ± 3.6e-06 | 2.02e-05 ± 4.1e-06 | 1.13e-05 ± 3.8e-06 | – | 2.94e-06 ± 3.1e-06 | 3.31e-09 ± 4.0e-09 | 6.20e-09 ± 4.2e-09 | 3.17e-09 ± 2.7e-09 | **6.68e-13 ± 3.8e-13** | *8.7e-32* |
| Jaynes–Cummings | 64 | 6.66e-05 ± 5.4e-05 | 1.42e-05 ± 2.6e-06 | 2.71e-05 ± 6.1e-06 | 1.02e-05 ± 2.9e-06 | – | 6.88e-06 ± 6.3e-06 | 3.01e-09 ± 2.5e-09 | 1.71e-08 ± 2.6e-08 | 1.22e-09 ± 1.4e-09 | **3.65e-12 ± 1.4e-12** | *4.6e-32* |

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
| Delayed quantum control | 8 | 3.5e-06 | 1.0e-05 | 3.5e-06 | **1.9e-07** | 7.3e-05 | 2.3e-07 |
| Delayed quantum control | 16 | 6.9e-06 | 9.0e-06 | 5.9e-06 | **3.3e-08** | 7.5e-05 | 3.0e-07 |
| Delayed quantum control | 32 | 7.8e-06 | 4.3e-06 | 2.7e-06 | **1.0e-08** | 6.7e-05 | 3.0e-07 |
| Delayed quantum control | 64 | 4.8e-06 | 1.1e-05 | 2.8e-06 | **3.4e-09** | 6.6e-05 | 2.4e-07 |
| Jaynes–Cummings | 8 | 1.7e-05 | 7.7e-09 | 1.4e-09 | 1.3e-13 | 3.9e-30 | **3.4e-31** |
| Jaynes–Cummings | 16 | 3.2e-06 | 3.7e-09 | 1.7e-09 | 1.6e-13 | 4.1e-30 | **1.2e-31** |
| Jaynes–Cummings | 32 | 9.1e-06 | 6.2e-09 | 3.2e-09 | 6.7e-13 | 6.3e-31 | **8.7e-32** |
| Jaynes–Cummings | 64 | 7.0e-06 | 1.7e-08 | 1.2e-09 | 3.7e-12 | 1.1e-29 | **4.6e-32** |

- Linear AR(8) is lower than QKAN-FWP+ in 22/24 cells.
- Linear AR(8) is lower than HQKAN-Δ in 21/24 cells.
- Linear AR(8) is lower than QKAN-FWP-O in 13/24 cells.
- Linear AR(8) is lower than the best printed number of the two papers in 21/24 cells.

## QKAN-FWP-O ablation on the paper benchmarks (test MSE ÷ full model, geometric mean over the cells both have)

| Variant | Params | All cells | Cells where the full model is better | Bessel J2 | Damped SHM | NARMA5 | NARMA10 | Delayed quantum control | Jaynes–Cummings |
|---|---|---|---|---|---|---|---|---|---|
| no fast weights (static observable R₀) | 79–103 | **77×** | 23/24 | 8436× | 1.6e4× | 5.2× | 6.7× | 54× | 0.85× |
| sequential delta rule instead of the least-squares solve | 130–154 | **62×** | 18/20 | 886× | 3936× | 2.3× | 4.8× | 23× | – |
| no gate (additive statistics, uniform weights) | 104–128 | **1.7×** | 14/20 | 1.2× | 0.51× | 3.1× | 4.7× | 1.4× | – |
| constant gate (not input dependent) | 105–129 | **1.4×** | 15/20 | 0.91× | 0.94× | 1.2× | 4.6× | 1.2× | – |
| one prior precision instead of one per feature | 106–130 | **1×** | 9/20 | 0.99× | 0.98× | 0.98× | 1.2× | 0.9× | – |
| no base-activation (linear) term: Bloch features only | 112–136 | **4.7×** | 18/20 | 3.8× | 25× | 1.8× | 3.2× | 4.2× | – |
| no Bloch features: linear term only (classical control) | 52–76 | **1.1×** | 14/24 | 0.5× | 3.2× | 1.6× | 1.4× | 2.2× | 0.18× |
| classical tanh(w·u + b) features instead of the Bloch features, same memory | 166 | **0.74×** | 0/2 | 0.75× | 0.73× | – | – | – | – |
| classical cos(w·u + b) features instead of the Bloch features, same memory | 166 | **0.83×** | 0/2 | 0.88× | 0.78× | – | – | – | – |
| float32 instead of float64 (features, statistics and solve) | 154 | **1.1×** | 2/3 | 1× | 0.98× | 1.5× | – | – | – |
| 4 circuits instead of 6 | 88–104 | **1.7×** | 18/20 | 1.3× | 3.6× | 1.1× | 1.6× | 1.7× | – |
| fixed token length 6 instead of min(8, N/2) | 142 | **1.9×** | 13/20 | 0.72× | 1.4× | 5.3× | 1.2× | 3.9× | – |

## Memory weights learned by QKAN-FWP-O (N = 32, 24 complete context pairs; mean over test windows and seeds)

| Dataset | Test MSE | Total weight Σβ | Effective number of pairs | Weight of the most recent pair | Weight of the 3 most recent pairs | Prior precision (median) | cond(C_T), median | cond(C_T), max |
|---|---|---|---|---|---|---|---|---|
| Bessel J2 | 3.4e-12 | 0.99 | 9.5 | 0.19 | 0.47 | – | – | – |
| Damped SHM | 2.8e-11 | 1.00 | 8.5 | 0.21 | 0.51 | – | – | – |
| NARMA5 | 4.7e-08 | 1.00 | 1.4 | 0.84 | 1.00 | – | – | – |
| NARMA10 | 2.2e-08 | 1.00 | 1.7 | 0.75 | 0.98 | – | – | – |
| Delayed quantum control | 1.0e-08 | 0.92 | 16.1 | 0.10 | 0.27 | – | – | – |
| Jaynes–Cummings | 7.0e-13 | 1.00 | 8.7 | 0.21 | 0.50 | – | – | – |

## Cost of the read-out (one CPU thread, F = 25 features, milliseconds per 1000 windows)

| Window N | Context pairs | Memory rule | Memory update and solve | Whole forward pass (features included) |
|---|---|---|---|---|
| 16 | 8 | static (no memory) | 0.02 | 8.2 |
| 16 | 8 | sequential delta rule | 4.48 | 15.6 |
| 16 | 8 | gated least squares | 10.22 | 26.3 |
| 64 | 56 | static (no memory) | 0.02 | 39.5 |
| 64 | 56 | sequential delta rule | 16.33 | 64.6 |
| 64 | 56 | gated least squares | 18.36 | 62.0 |
| 256 | 248 | static (no memory) | 0.01 | 202.8 |
| 256 | 248 | sequential delta rule | 66.35 | 284.3 |
| 256 | 248 | gated least squares | 57.78 | 224.7 |

## Families of systems (window N = 16; test MSE on unseen sequences)

Mean ± std over 3 seeds at the learning rate chosen on validation (one of 3e-3, 1e-2, 3e-2, cosine); each model is evaluated at its best-validation epoch. References are closed-form.

| Model | Params | Damped oscillation, noise 0 | Two tones, noise 0 | Jaynes–Cummings, noise 0 | Hénon map, noise 0 | Duffing, noise 0 | Damped oscillation, noise 0.02 | Two tones, noise 0.02 | Jaynes–Cummings, noise 0.02 | Hénon map, noise 0.02 | Duffing, noise 0.02 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| *Reference: repeat the last value* | – | *7.48e-02* | *5.13e-02* | *2.74e-02* | *7.07e-01* | *1.12e-02* | *7.61e-02* | *5.24e-02* | *2.79e-02* | *7.09e-01* | *1.20e-02* |
| *Reference: one linear AR(p) for all sequences* | – | *6.95e-08* | *4.63e-08* | *1.34e-08* | *4.60e-02* | *2.25e-06* | *5.86e-03* | *5.11e-03* | *4.55e-03* | *4.66e-02* | *1.18e-03* |
| *Reference: ridge AR(q) fitted inside each window* | – | *4.55e-26* | *1.08e-15* | *1.82e-08* | *5.99e-02* | *1.49e-06* | *7.53e-04* | *2.51e-03* | *4.05e-03* | *6.09e-02* | *9.34e-04* |
| GQKAN-QKANFWP (scalar gate) | 152 | 1.64e-02 ± 2.8e-04 | 1.47e-02 ± 6.1e-05 | 6.77e-03 ± 1.3e-04 | 1.70e-03 ± 1.0e-03 | 1.62e-04 ± 8.2e-06 | 1.77e-02 ± 7.8e-05 | 1.60e-02 ± 1.2e-04 | 8.18e-03 ± 2.5e-05 | 3.47e-03 ± 8.6e-04 | 1.51e-03 ± 3.5e-05 |
| CMG (scalar tokens) | 188 | 4.83e-03 ± 2.9e-03 | 1.07e-02 ± 1.6e-03 | 6.27e-03 ± 9.8e-04 | 5.07e-04 ± 5.6e-05 | 3.10e-04 ± 6.9e-05 | 6.25e-03 ± 2.8e-03 | 1.36e-02 ± 7.1e-04 | 7.72e-03 ± 8.5e-04 | 2.33e-03 ± 1.6e-04 | 1.56e-03 ± 6.3e-05 |
| CMG + Δ-tokens + residual | 173 | 4.72e-05 ± 2.8e-06 | 1.04e-04 ± 1.8e-05 | 2.77e-05 ± 1.4e-06 | 6.04e-04 ± 1.4e-04 | 3.40e-06 ± 1.4e-06 | 1.64e-03 ± 3.9e-05 | 5.26e-03 ± 1.2e-04 | 3.68e-03 ± 1.1e-04 | 1.86e-03 ± 9.0e-05 | 9.75e-04 ± 2.7e-05 |
| QKAN-FWP+ | 149 | 4.87e-05 ± 2.1e-05 | 9.73e-05 ± 1.8e-05 | 2.72e-05 ± 4.3e-06 | 9.35e-04 ± 5.5e-04 | 4.23e-06 ± 1.0e-06 | 1.75e-03 ± 2.8e-04 | 4.78e-03 ± 3.6e-04 | 3.58e-03 ± 1.1e-04 | 1.76e-03 ± 1.6e-04 | 1.11e-03 ± 3.2e-05 |
| HQKAN-Δ (static) | 136 | 9.83e-05 ± 1.2e-05 | 1.18e-04 ± 1.6e-05 | 2.78e-05 ± 1.2e-06 | 1.48e-03 ± 1.5e-04 | 3.49e-06 ± 2.7e-06 | 3.38e-03 ± 1.8e-04 | 5.94e-03 ± 2.9e-05 | 4.31e-03 ± 3.8e-05 | 2.86e-03 ± 5.3e-05 | 1.21e-03 ± 2.2e-05 |
| LSTM, same tokens (not QKAN) | 160 | 4.03e-05 ± 5.6e-06 | 7.71e-05 ± 6.4e-06 | 1.89e-05 ± 1.9e-06 | 9.27e-04 ± 3.7e-04 | 2.52e-06 ± 2.9e-07 | 1.91e-03 ± 5.2e-04 | 4.57e-03 ± 1.3e-04 | 3.31e-03 ± 1.5e-05 | 2.80e-03 ± 8.4e-05 | 1.05e-03 ± 3.1e-05 |
| Same memory on classical tanh features (not QKAN) | 166 | 2.84e-09 ± 1.8e-09 | **3.36e-08 ± 5.4e-09** | **1.74e-07 ± 6.7e-08** | 3.53e-05 ± 1.3e-05 | 1.67e-07 ± 5.6e-08 | 1.05e-03 ± 3.0e-05 | 2.02e-03 ± 1.4e-05 | 2.85e-03 ± 5.6e-06 | 1.58e-03 ± 8.7e-05 | 9.01e-04 ± 3.7e-05 |
| Same memory on classical cos features (not QKAN) | 166 | 1.01e-08 ± 8.8e-09 | 1.11e-06 ± 1.4e-06 | 2.33e-07 ± 7.6e-08 | **2.35e-05 ± 6.0e-06** | 1.79e-07 ± 9.4e-08 | **8.85e-04 ± 2.5e-05** | 1.99e-03 ± 3.2e-05 | **2.83e-03 ± 1.7e-05** | **1.56e-03 ± 4.3e-05** | **8.59e-04 ± 1.4e-05** |
| QKAN-FWP-O | 154 | **2.29e-09 ± 2.1e-09** | 4.40e-08 ± 1.4e-08 | 2.00e-07 ± 8.4e-08 | 3.42e-05 ± 4.9e-06 | **1.54e-07 ± 3.5e-08** | 9.05e-04 ± 9.2e-06 | **1.97e-03 ± 2.6e-05** | 2.87e-03 ± 1.7e-05 | 1.79e-03 ± 4.4e-05 | 8.67e-04 ± 3.4e-06 |

## QKAN-FWP-O against each model on the families (geometric mean over the cells)

| Compared with | Params | Geo-mean test MSE of QKAN-FWP-O | Cells where it is lower | Smallest … largest factor |
|---|---|---|---|---|
| GQKAN-QKANFWP (scalar gate) | 152 | **303× lower** | 10/10 | 1.7× … 7.2e6× |
| CMG (scalar tokens) | 188 | **207× lower** | 10/10 | 1.3× … 2.1e6× |
| CMG + Δ-tokens + residual | 173 | **21× lower** | 10/10 | 1× … 2.1e4× |
| QKAN-FWP+ | 149 | **23× lower** | 9/10 | 0.98× … 2.1e4× |
| HQKAN-Δ (static) | 136 | **30× lower** | 10/10 | 1.4× … 4.3e4× |
| LSTM, same tokens (not QKAN) | 160 | **21× lower** | 10/10 | 1.2× … 1.8e4× |
| Same memory on classical tanh features (not QKAN) | 166 | equal (1.00×) | 6/10 | 0.76× … 1.2× |
| Same memory on classical cos features (not QKAN) | 166 | **1.6× lower** | 5/10 | 0.69× … 25× |
| *one linear AR(p) for all sequences* | – | **5.8× lower** | 9/10 | 0.067× … 1345× |
| *ridge AR(q) fitted inside each window* | – | 87× higher | 6/10 | 2e-17× … 1752× |

## QKAN-FWP-O ablation on the families (test MSE ÷ full model)

| Variant | Params | Geo-mean, all cells | Damped oscillation, noise 0 | Two tones, noise 0 | Jaynes–Cummings, noise 0 | Hénon map, noise 0 | Duffing, noise 0 | Damped oscillation, noise 0.02 | Two tones, noise 0.02 | Jaynes–Cummings, noise 0.02 | Hénon map, noise 0.02 | Duffing, noise 0.02 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| no fast weights (static observable R₀) | 103 | **24×** | 2.6e4× | 1957× | 113× | 49× | 5.1× | 3.8× | 3× | 1.5× | 1.7× | 1.4× |
| sequential delta rule instead of the least-squares solve | 154 | **7.4×** | 1149× | 508× | 21× | 4.1× | 4.2× | 1.2× | 1.8× | 1.2× | 0.93× | 1.1× |
| no gate (additive statistics, uniform weights) | 128 | **1.5×** | 0.41× | 0.67× | 0.57× | 1.4× | 1.3× | 3.5× | 3× | 2.4× | 3.1× | 2.7× |
| no Bloch features: linear term only (classical control) | 76 | **1.1×** | 0.012× | 0.046× | 0.056× | 1164× | 2.4× | 0.97× | 1.1× | 1× | 22× | 1× |
| classical tanh(w·u + b) features instead of the Bloch features, same memory | 166 | **1×** | 1.2× | 0.76× | 0.87× | 1× | 1.1× | 1.2× | 1× | 1× | 0.88× | 1× |
| classical cos(w·u + b) features instead of the Bloch features, same memory | 166 | **1.6×** | 4.4× | 25× | 1.2× | 0.69× | 1.2× | 0.98× | 1× | 0.99× | 0.87× | 0.99× |
| float32 instead of float64 (features, statistics and solve) | 154 | **1×** | 1.4× | 1.1× | 0.92× | 1.1× | 0.97× | 0.99× | 1× | 1× | 0.99× | 1× |

## Finite-shot sensitivity (N = 16; test MSE against the shot budget S per circuit and input, mean over 3 seeds)

S shots are available to every circuit for every input it processes. A ⟨Z⟩ read-out spends them in one basis; QKAN-FWP-O splits them over the X, Y and Z bases (⌊S/3⌋ each). Outcomes are binomial. "Circuit runs" is the number of circuit evaluations per prediction, so the total number of shots per prediction is circuit runs × S. Training used exact expectations, or the same finite-shot sampling at S = 10⁴ ("noise-aware").

| Task | Model | Circuit runs per prediction | Trained with | S = 10² | 10³ | 10⁴ | 10⁵ | 10⁶ | exact |
|---|---|---|---|---|---|---|---|---|---|
| Bessel J2 | QKAN-FWP-O | 54 | exact | 5.1e-06 | 6.9e-07 | 9.0e-08 | 1.3e-08 | 1.7e-09 | 1.4e-12 |
| Bessel J2 | QKAN-FWP-O | 54 | S = 10⁴ | 8.7e-11 | 1.4e-11 | 3.1e-12 | 3.0e-13 | 5.8e-14 | 2.7e-14 |
| Bessel J2 | QKAN-FWP-O, float32 | 54 | exact | 5.4e-06 | 7.0e-07 | 8.7e-08 | 1.3e-08 | 1.7e-09 | 1.4e-12 |
| Bessel J2 | QKAN-FWP-O, float32 | 54 | S = 10⁴ | 7.0e-11 | 1.6e-11 | 3.6e-12 | 4.0e-13 | 6.6e-14 | 3.2e-14 |
| Bessel J2 | HQKAN-Δ, ⟨Z⟩ read-out | 12 | exact | 2.2e-03 | 2.4e-04 | 2.3e-05 | 2.5e-06 | 5.2e-07 | 2.8e-07 |
| Bessel J2 | HQKAN-Δ, ⟨Z⟩ read-out | 12 | S = 10⁴ | 6.8e-04 | 6.7e-05 | 7.8e-06 | 1.4e-06 | 8.9e-07 | 8.1e-07 |
| Bessel J2 | QKAN-FWP+, ⟨Z⟩ read-out | 92 | exact | 3.6e-03 | 3.4e-04 | 3.6e-05 | 4.3e-06 | 1.2e-06 | 8.2e-07 |
| Bessel J2 | QKAN-FWP+, ⟨Z⟩ read-out | 92 | S = 10⁴ | 1.5e-03 | 1.6e-04 | 1.6e-05 | 2.2e-06 | 9.1e-07 | 7.4e-07 |
| NARMA10 | QKAN-FWP-O | 54 | exact | 1.4e-04 | 3.1e-05 | 8.8e-06 | 3.7e-06 | 2.2e-06 | 2.0e-06 |
| NARMA10 | QKAN-FWP-O | 54 | S = 10⁴ | 7.3e-05 | 1.6e-05 | 8.0e-06 | 5.9e-06 | 5.4e-06 | 5.3e-06 |
| NARMA10 | QKAN-FWP-O, float32 | 54 | exact | 4.1e-04 | 9.1e-05 | 2.2e-05 | 1.1e-05 | 9.2e-06 | 8.9e-06 |
| NARMA10 | QKAN-FWP-O, float32 | 54 | S = 10⁴ | 1.1e-04 | 2.1e-05 | 6.5e-06 | 3.9e-06 | 3.4e-06 | 3.3e-06 |
| NARMA10 | HQKAN-Δ, ⟨Z⟩ read-out | 12 | exact | 1.4e-03 | 1.4e-04 | 1.7e-05 | 4.3e-06 | 3.0e-06 | 2.9e-06 |
| NARMA10 | HQKAN-Δ, ⟨Z⟩ read-out | 12 | S = 10⁴ | 7.2e-04 | 7.3e-05 | 1.1e-05 | 4.8e-06 | 4.3e-06 | 4.2e-06 |
| NARMA10 | QKAN-FWP+, ⟨Z⟩ read-out | 92 | exact | 2.7e-03 | 2.8e-04 | 3.4e-05 | 1.1e-05 | 8.2e-06 | 8.0e-06 |
| NARMA10 | QKAN-FWP+, ⟨Z⟩ read-out | 92 | S = 10⁴ | 1.7e-03 | 2.1e-04 | 2.9e-05 | 1.3e-05 | 1.1e-05 | 1.1e-05 |
| Delayed quantum control | QKAN-FWP-O | 54 | exact | 7.8e-05 | 1.2e-05 | 2.5e-06 | 5.0e-07 | 1.2e-07 | 3.2e-08 |
| Delayed quantum control | QKAN-FWP-O | 54 | S = 10⁴ | 7.8e-07 | 1.8e-07 | 7.4e-08 | 5.1e-08 | 4.9e-08 | 4.8e-08 |
| Delayed quantum control | QKAN-FWP-O, float32 | 54 | exact | 6.5e-05 | 9.8e-06 | 1.9e-06 | 4.1e-07 | 1.1e-07 | 3.5e-08 |
| Delayed quantum control | QKAN-FWP-O, float32 | 54 | S = 10⁴ | 7.2e-07 | 1.3e-07 | 5.0e-08 | 3.6e-08 | 3.3e-08 | 3.3e-08 |
| Delayed quantum control | HQKAN-Δ, ⟨Z⟩ read-out | 12 | exact | 2.6e-03 | 2.7e-04 | 3.9e-05 | 1.6e-05 | 1.4e-05 | 1.4e-05 |
| Delayed quantum control | HQKAN-Δ, ⟨Z⟩ read-out | 12 | S = 10⁴ | 1.8e-03 | 1.7e-04 | 3.0e-05 | 1.7e-05 | 1.5e-05 | 1.5e-05 |
| Delayed quantum control | QKAN-FWP+, ⟨Z⟩ read-out | 92 | exact | 3.9e-03 | 3.7e-04 | 4.1e-05 | 8.9e-06 | 6.1e-06 | 5.8e-06 |
| Delayed quantum control | QKAN-FWP+, ⟨Z⟩ read-out | 92 | S = 10⁴ | 2.5e-03 | 2.2e-04 | 3.1e-05 | 8.4e-06 | 6.3e-06 | 6.1e-06 |
| Family: damped oscillation, noise 0.02 | QKAN-FWP-O | 54 | exact | 9.4e-04 | 9.1e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 |
| Family: damped oscillation, noise 0.02 | QKAN-FWP-O | 54 | S = 10⁴ | 9.4e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 |
| Family: damped oscillation, noise 0.02 | QKAN-FWP-O, float32 | 54 | exact | 9.2e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 |
| Family: damped oscillation, noise 0.02 | QKAN-FWP-O, float32 | 54 | S = 10⁴ | 9.4e-04 | 9.1e-04 | 9.1e-04 | 9.1e-04 | 9.1e-04 | 9.1e-04 |
| Family: damped oscillation, noise 0.02 | HQKAN-Δ, ⟨Z⟩ read-out | 12 | exact | 8.7e-03 | 4.0e-03 | 3.5e-03 | 3.4e-03 | 3.4e-03 | 3.4e-03 |
| Family: damped oscillation, noise 0.02 | HQKAN-Δ, ⟨Z⟩ read-out | 12 | S = 10⁴ | 8.5e-03 | 4.0e-03 | 3.5e-03 | 3.4e-03 | 3.4e-03 | 3.4e-03 |
| Family: damped oscillation, noise 0.02 | QKAN-FWP+, ⟨Z⟩ read-out | 92 | exact | 1.5e-02 | 3.3e-03 | 2.2e-03 | 2.1e-03 | 2.1e-03 | 2.1e-03 |
| Family: damped oscillation, noise 0.02 | QKAN-FWP+, ⟨Z⟩ read-out | 92 | S = 10⁴ | 1.0e-02 | 3.0e-03 | 2.3e-03 | 2.2e-03 | 2.2e-03 | 2.2e-03 |
| Family: Hénon map | QKAN-FWP-O | 54 | exact | 1.2e-01 | 1.7e-02 | 2.3e-03 | 3.2e-04 | 6.6e-05 | 3.4e-05 |
| Family: Hénon map | QKAN-FWP-O | 54 | S = 10⁴ | 1.4e-02 | 1.6e-03 | 2.8e-04 | 1.5e-04 | 1.4e-04 | 1.4e-04 |
| Family: Hénon map | QKAN-FWP-O, float32 | 54 | exact | 1.2e-01 | 1.6e-02 | 2.3e-03 | 3.2e-04 | 6.8e-05 | 3.8e-05 |
| Family: Hénon map | QKAN-FWP-O, float32 | 54 | S = 10⁴ | 1.4e-02 | 1.6e-03 | 2.8e-04 | 1.4e-04 | 1.3e-04 | 1.3e-04 |
| Family: Hénon map | HQKAN-Δ, ⟨Z⟩ read-out | 12 | exact | 1.0e-02 | 2.4e-03 | 1.6e-03 | 1.5e-03 | 1.5e-03 | 1.5e-03 |
| Family: Hénon map | HQKAN-Δ, ⟨Z⟩ read-out | 12 | S = 10⁴ | 9.0e-03 | 2.3e-03 | 1.6e-03 | 1.5e-03 | 1.5e-03 | 1.5e-03 |
| Family: Hénon map | QKAN-FWP+, ⟨Z⟩ read-out | 92 | exact | 1.4e-02 | 1.9e-03 | 7.1e-04 | 5.9e-04 | 5.8e-04 | 5.8e-04 |
| Family: Hénon map | QKAN-FWP+, ⟨Z⟩ read-out | 92 | S = 10⁴ | 1.5e-02 | 2.3e-03 | 1.0e-03 | 9.2e-04 | 9.0e-04 | 9.0e-04 |

## Condition number of the Gram matrix C_T of QKAN-FWP-O (median over test windows, mean over 3 seeds)

| Task | Model | Trained with | S = 10² | 10³ | 10⁴ | 10⁵ | 10⁶ | exact |
|---|---|---|---|---|---|---|---|---|
| Bessel J2 | QKAN-FWP-O | exact | 9e+05 | 9e+05 | 9e+05 | 9e+05 | 9e+05 | 9e+05 |
| Bessel J2 | QKAN-FWP-O | S = 10⁴ | 1e+06 | 1e+06 | 1e+06 | 1e+06 | 1e+06 | 1e+06 |
| Bessel J2 | QKAN-FWP-O, float32 | exact | 9e+05 | 9e+05 | 9e+05 | 9e+05 | 9e+05 | 9e+05 |
| Bessel J2 | QKAN-FWP-O, float32 | S = 10⁴ | 1e+06 | 1e+06 | 1e+06 | 1e+06 | 1e+06 | 1e+06 |
| NARMA10 | QKAN-FWP-O | exact | 2e+06 | 2e+06 | 2e+06 | 2e+06 | 2e+06 | 2e+06 |
| NARMA10 | QKAN-FWP-O | S = 10⁴ | 1e+05 | 1e+05 | 1e+05 | 1e+05 | 1e+05 | 1e+05 |
| NARMA10 | QKAN-FWP-O, float32 | exact | 1e+06 | 1e+06 | 1e+06 | 1e+06 | 1e+06 | 1e+06 |
| NARMA10 | QKAN-FWP-O, float32 | S = 10⁴ | 8e+04 | 8e+04 | 8e+04 | 8e+04 | 8e+04 | 8e+04 |
| Delayed quantum control | QKAN-FWP-O | exact | 1e+06 | 1e+06 | 1e+06 | 1e+06 | 1e+06 | 1e+06 |
| Delayed quantum control | QKAN-FWP-O | S = 10⁴ | 3e+05 | 3e+05 | 3e+05 | 3e+05 | 3e+05 | 3e+05 |
| Delayed quantum control | QKAN-FWP-O, float32 | exact | 1e+06 | 1e+06 | 1e+06 | 1e+06 | 1e+06 | 1e+06 |
| Delayed quantum control | QKAN-FWP-O, float32 | S = 10⁴ | 6e+05 | 6e+05 | 6e+05 | 6e+05 | 6e+05 | 6e+05 |
| Family: damped oscillation, noise 0.02 | QKAN-FWP-O | exact | 2e+02 | 2e+02 | 2e+02 | 2e+02 | 2e+02 | 2e+02 |
| Family: damped oscillation, noise 0.02 | QKAN-FWP-O | S = 10⁴ | 2e+02 | 2e+02 | 2e+02 | 2e+02 | 2e+02 | 2e+02 |
| Family: damped oscillation, noise 0.02 | QKAN-FWP-O, float32 | exact | 2e+02 | 2e+02 | 2e+02 | 2e+02 | 2e+02 | 2e+02 |
| Family: damped oscillation, noise 0.02 | QKAN-FWP-O, float32 | S = 10⁴ | 1e+02 | 1e+02 | 1e+02 | 1e+02 | 1e+02 | 1e+02 |
| Family: Hénon map | QKAN-FWP-O | exact | 1e+05 | 1e+05 | 1e+05 | 2e+05 | 2e+05 | 2e+05 |
| Family: Hénon map | QKAN-FWP-O | S = 10⁴ | 2e+04 | 2e+04 | 2e+04 | 2e+04 | 2e+04 | 2e+04 |
| Family: Hénon map | QKAN-FWP-O, float32 | exact | 1e+05 | 1e+05 | 1e+05 | 1e+05 | 2e+05 | 2e+05 |
| Family: Hénon map | QKAN-FWP-O, float32 | S = 10⁴ | 3e+03 | 3e+03 | 3e+03 | 3e+03 | 3e+03 | 3e+03 |

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

### 60/20/20 (test targets 1971–2026)

| Model | Params | lr (by validation) | Seeds | Val. loss | Scaled MSE ↓ | PAE ↓ | PTE ↓ |
|---|---|---|---|---|---|---|---|
| GQKAN-QKANFWP (re-implemented baseline) | 12,423 | 0.0025 | 5 | 4.04 | 0.0175 ± 0.0006 | 76.2 ± 6.6 | 29.1 ± 2.0 |
| QKAN-FWP+ | 11,732 | 0.0025 | 5 | 4.17 | 0.0184 ± 0.0012 | 65.9 ± 4.2 | 27.2 ± 1.5 |
| QKAN-FWP-O without fast weights (static observable) | 496 | 0.0025 | 5 | 3.77 | 0.0137 ± 0.0001 | 67.1 ± 0.4 | 29.4 ± 0.9 |
| QKAN-FWP-O | 547 | 0.0025 | 5 | 3.67 | 0.0140 ± 0.0004 | 63.7 ± 2.7 | 27.5 ± 3.0 |
| *Reference: repeat the last cycle, 13-month smoothed (no training)* | 0 | – | – | – | 0.0166 | 53.1 | 18.7 |

### 70/15/15 (test targets 1982–2026)

| Model | Params | lr (by validation) | Seeds | Val. loss | Scaled MSE ↓ | PAE ↓ | PTE ↓ |
|---|---|---|---|---|---|---|---|
| GQKAN-QKANFWP (re-implemented baseline) | 12,423 | 0.0025 | 3 | 3.85 | 0.0168 ± 0.0005 | 56.1 ± 5.1 | 26.5 ± 2.0 |
| QKAN-FWP+ | 11,732 | 0.0025 | 3 | 4.60 | 0.0156 ± 0.0004 | 44.8 ± 3.3 | 24.1 ± 0.7 |
| QKAN-FWP-O without fast weights (static observable) | 496 | 0.0025 | 3 | 3.41 | 0.0126 ± 0.0003 | 47.4 ± 3.0 | 20.1 ± 1.5 |
| QKAN-FWP-O | 547 | 0.0025 | 3 | 3.97 | 0.0139 ± 0.0007 | 45.1 ± 0.4 | 28.6 ± 0.6 |
| *Reference: repeat the last cycle, 13-month smoothed (no training)* | 0 | – | – | – | 0.0168 | 38.5 | 18.8 |

