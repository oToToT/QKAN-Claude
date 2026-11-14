## Final time-series comparison (test MSE, mean ± std over 5 seeds)

| Dataset | N | Baseline GQKAN-QKANFWP, paper protocol (152 params) | Baseline GQKAN-QKANFWP, tuned lr (152 params) | GQKAN-FWP, tuned lr (114 params) | G-QKANFWP, tuned lr (175 params) | QKAN-FWP+ (149 params) | QKAN-FWP+ write-first (149 params) | HQKAN-Δ, no fast weights (136 params) |
|---|---|---|---|---|---|---|---|---|
| Bessel J2 | 8 | 5.49e-04 ± 5.2e-04 | 6.14e-06 ± 1.5e-06 | 1.08e-04 ± 1.9e-04 | 4.77e-06 ± 2.4e-06 | 1.09e-06 ± 5.2e-07 | 7.64e-07 ± 6.0e-07 | **8.39e-08 ± 5.4e-08** |
| Bessel J2 | 16 | 8.35e-04 ± 7.2e-04 | 4.27e-06 ± 3.0e-06 | 2.87e-06 ± 1.4e-06 | 2.62e-06 ± 2.8e-07 | 1.64e-06 ± 1.4e-06 | 1.78e-06 ± 1.7e-06 | **1.21e-07 ± 9.7e-08** |
| Bessel J2 | 32 | 6.90e-04 ± 5.3e-04 | 4.74e-06 ± 3.3e-06 | 1.22e-06 ± 7.7e-07 | 4.10e-06 ± 1.3e-06 | 1.43e-06 ± 4.0e-07 | 1.53e-06 ± 3.3e-07 | **1.24e-07 ± 1.1e-07** |
| Bessel J2 | 64 | 5.81e-04 ± 5.8e-04 | 3.39e-06 ± 2.0e-06 | 4.09e-06 ± 3.2e-06 | 1.44e-06 ± 3.1e-07 | 2.00e-06 ± 1.3e-06 | 1.61e-06 ± 7.7e-07 | **2.74e-07 ± 1.9e-07** |
| Damped SHM | 8 | 8.72e-05 ± 5.5e-05 | 1.78e-05 ± 5.0e-06 | 4.42e-06 ± 1.9e-06 | 9.08e-06 ± 3.8e-06 | 1.56e-06 ± 7.6e-07 | 1.52e-06 ± 8.3e-07 | **2.48e-07 ± 2.5e-08** |
| Damped SHM | 16 | 1.18e-04 ± 7.2e-05 | 1.15e-05 ± 6.7e-06 | 3.99e-05 ± 7.7e-05 | 1.00e-05 ± 3.8e-06 | 1.38e-06 ± 6.5e-07 | 1.12e-06 ± 1.2e-06 | **2.01e-07 ± 7.8e-08** |
| Damped SHM | 32 | 6.98e-05 ± 5.4e-05 | 7.67e-06 ± 2.0e-06 | 4.27e-06 ± 5.6e-06 | 5.49e-06 ± 1.6e-06 | 2.54e-06 ± 1.4e-06 | 2.53e-06 ± 1.1e-06 | **5.21e-07 ± 5.1e-07** |
| Damped SHM | 64 | 1.42e-04 ± 9.8e-05 | 1.23e-05 ± 7.0e-06 | 1.47e-06 ± 5.6e-07 | 5.46e-06 ± 1.9e-06 | 2.20e-06 ± 1.4e-06 | 2.22e-06 ± 2.4e-06 | **4.24e-07 ± 4.9e-07** |
| NARMA5 | 8 | 1.79e-03 ± 1.2e-03 | 2.78e-04 ± 6.6e-05 | 5.63e-04 ± 6.0e-04 | 1.85e-04 ± 3.6e-05 | 3.55e-05 ± 1.2e-05 | 1.69e-05 ± 5.5e-06 | **1.41e-05 ± 3.6e-06** |
| NARMA5 | 16 | 1.94e-03 ± 1.1e-03 | 2.29e-04 ± 5.7e-05 | 9.22e-04 ± 1.4e-03 | 1.66e-04 ± 2.3e-05 | 3.67e-06 ± 1.5e-06 | 2.96e-06 ± 8.6e-07 | **1.79e-06 ± 2.2e-07** |
| NARMA5 | 32 | 2.23e-03 ± 1.2e-03 | 2.46e-04 ± 5.1e-05 | 3.28e-04 ± 1.1e-04 | 1.78e-04 ± 1.7e-05 | 3.84e-06 ± 1.5e-06 | 3.69e-06 ± 1.9e-06 | **2.05e-06 ± 9.2e-07** |
| NARMA5 | 64 | 1.40e-03 ± 7.7e-04 | 1.67e-04 ± 5.9e-05 | 5.38e-04 ± 8.0e-04 | 1.42e-04 ± 6.0e-05 | 2.57e-06 ± 6.6e-07 | 3.34e-06 ± 7.1e-07 | **1.39e-06 ± 3.1e-07** |
| NARMA10 | 8 | 2.48e-03 ± 1.6e-03 | 1.33e-03 ± 3.1e-04 | 9.50e-03 ± 8.4e-03 | 7.07e-04 ± 9.7e-05 | 8.14e-05 ± 4.7e-05 | 8.17e-05 ± 3.2e-05 | **4.34e-05 ± 1.3e-05** |
| NARMA10 | 16 | 2.70e-03 ± 1.9e-03 | 5.24e-04 ± 4.5e-05 | 5.43e-04 ± 3.6e-05 | 4.79e-04 ± 9.5e-06 | 4.31e-06 ± 1.7e-06 | 5.06e-06 ± 2.3e-06 | **2.14e-06 ± 3.3e-07** |
| NARMA10 | 32 | 2.89e-03 ± 1.8e-03 | 5.56e-04 ± 3.1e-05 | 5.67e-04 ± 4.7e-05 | 7.21e-04 ± 4.2e-04 | 3.09e-06 ± 1.3e-06 | 2.79e-06 ± 1.6e-06 | **9.47e-07 ± 3.1e-07** |
| NARMA10 | 64 | 2.75e-03 ± 1.5e-03 | 5.83e-04 ± 5.1e-05 | 4.26e-03 ± 7.4e-03 | 5.18e-04 ± 2.4e-05 | 3.92e-06 ± 2.0e-06 | 2.84e-06 ± 1.7e-06 | **6.43e-07 ± 2.6e-07** |
| Delayed quantum control | 8 | 2.56e-03 ± 1.1e-03 | 5.83e-04 ± 1.5e-04 | 1.16e-03 ± 1.2e-04 | 5.75e-04 ± 1.3e-04 | 1.02e-05 ± 5.9e-06 | 1.14e-05 ± 6.9e-06 | **3.51e-06 ± 1.4e-06** |
| Delayed quantum control | 16 | 2.04e-03 ± 4.3e-04 | 4.63e-04 ± 1.3e-04 | 1.27e-03 ± 1.9e-04 | 4.72e-04 ± 6.8e-05 | 9.03e-06 ± 4.8e-06 | 9.91e-06 ± 3.5e-06 | **5.92e-06 ± 5.4e-06** |
| Delayed quantum control | 32 | 1.91e-03 ± 6.1e-04 | 3.96e-04 ± 9.7e-05 | 8.12e-04 ± 2.1e-04 | 3.15e-04 ± 9.4e-05 | 4.31e-06 ± 2.0e-06 | 8.26e-06 ± 6.3e-06 | **2.65e-06 ± 1.6e-06** |
| Delayed quantum control | 64 | 1.20e-03 ± 3.3e-04 | 3.37e-04 ± 8.5e-05 | 8.04e-04 ± 7.4e-05 | 3.15e-04 ± 1.1e-04 | 1.05e-05 ± 5.6e-06 | 7.10e-06 ± 3.3e-06 | **2.80e-06 ± 1.6e-06** |
| Jaynes–Cummings | 8 | 2.75e-05 ± 1.7e-05 | 1.95e-05 ± 2.5e-06 | 5.04e-05 ± 1.1e-05 | 1.55e-05 ± 4.8e-06 | 7.71e-09 ± 6.0e-09 | 4.43e-09 ± 4.1e-09 | **1.41e-09 ± 1.2e-09** |
| Jaynes–Cummings | 16 | 4.25e-05 ± 4.8e-05 | 2.24e-05 ± 3.5e-06 | 5.25e-05 ± 2.1e-06 | 1.01e-05 ± 2.6e-06 | 3.68e-09 ± 1.5e-09 | 7.99e-09 ± 9.0e-09 | **1.70e-09 ± 1.2e-09** |
| Jaynes–Cummings | 32 | 3.38e-05 ± 4.1e-05 | 1.42e-05 ± 3.6e-06 | 2.02e-05 ± 4.1e-06 | 1.13e-05 ± 3.8e-06 | 6.20e-09 ± 4.2e-09 | 6.62e-09 ± 5.3e-09 | **3.17e-09 ± 2.7e-09** |
| Jaynes–Cummings | 64 | 6.66e-05 ± 5.4e-05 | 1.42e-05 ± 2.6e-06 | 2.71e-05 ± 6.1e-06 | 1.02e-05 ± 2.9e-06 | 1.71e-08 ± 2.6e-08 | 1.03e-08 ± 1.5e-08 | **1.22e-09 ± 1.4e-09** |

## QKAN-FWP+ (149 params) vs each baseline over the 24 cells

| Baseline | Params | Model ÷ baseline (geo-mean test MSE) | Cells where the model is better | Smallest / largest factor |
|---|---|---|---|---|
| Baseline GQKAN-QKANFWP, paper protocol | 152 | 0.0026 (**380× lower**) | 24/24 | 27.5× / 11572× |
| Baseline GQKAN-QKANFWP, tuned lr | 152 | 0.022 (**45× lower**) | 24/24 | 1.7× / 6099× |
| GQKAN-FWP, tuned lr | 114 | 0.014 (**74× lower**) | 22/24 | 0.7× / 14282× |
| G-QKANFWP, tuned lr | 175 | 0.031 (**33× lower**) | 23/24 | 0.7× / 2757× |

Better than the best of all re-implemented baselines in 21/24 cells.

## QKAN-FWP+ write-first (149 params) vs each baseline over the 24 cells

| Baseline | Params | Model ÷ baseline (geo-mean test MSE) | Cells where the model is better | Smallest / largest factor |
|---|---|---|---|---|
| Baseline GQKAN-QKANFWP, paper protocol | 152 | 0.0025 (**403× lower**) | 24/24 | 27.6× / 6469× |
| Baseline GQKAN-QKANFWP, tuned lr | 152 | 0.021 (**47× lower**) | 24/24 | 2.1× / 4408× |
| GQKAN-FWP, tuned lr | 114 | 0.013 (**78× lower**) | 22/24 | 0.7× / 11359× |
| G-QKANFWP, tuned lr | 175 | 0.029 (**35× lower**) | 23/24 | 0.9× / 3507× |

Better than the best of all re-implemented baselines in 21/24 cells.

## HQKAN-Δ, no fast weights (136 params) vs each baseline over the 24 cells

| Baseline | Params | Model ÷ baseline (geo-mean test MSE) | Cells where the model is better | Smallest / largest factor |
|---|---|---|---|---|
| Baseline GQKAN-QKANFWP, paper protocol | 152 | 0.00067 (**1495× lower**) | 24/24 | 57.2× / 54415× |
| Baseline GQKAN-QKANFWP, tuned lr | 152 | 0.0057 (**175× lower**) | 24/24 | 12.4× / 13879× |
| GQKAN-FWP, tuned lr | 114 | 0.0035 (**290× lower**) | 24/24 | 3.5× / 35763× |
| G-QKANFWP, tuned lr | 175 | 0.0078 (**129× lower**) | 24/24 | 5.3× / 11042× |

Better than the best of all re-implemented baselines in 24/24 cells.

## Per-dataset summary (geometric mean over N ∈ {8, 16, 32, 64} of the seed-mean test MSE)

| Dataset | Printed in 2605.06734 (its GQKAN-QKANFWP) | Re-implemented baseline, paper protocol | Best tuned re-implemented baseline | QKAN-FWP+ (149 params) | HQKAN-Δ (136 params) | Linear AR(8), least squares (9 params) |
|---|---|---|---|---|---|---|
| Bessel J2 | 1.7e-05 | 6.5e-04 | 2.9e-06 | 1.5e-06 | 1.4e-07 | 5.3e-24 |
| Damped SHM | 4.0e-05 | 1.0e-04 | 5.8e-06 | 1.9e-06 | 3.2e-07 | 9.0e-14 |
| NARMA5 | 3.9e-05 | 1.8e-03 | 1.7e-04 | 6.0e-06 | 2.9e-06 | 1.3e-06 |
| NARMA10 | 7.5e-05 | 2.7e-03 | 6.0e-04 | 8.1e-06 | 2.7e-06 | 1.7e-06 |
| Delayed quantum control | 7.9e-05 | 1.9e-03 | 4.1e-04 | 8.0e-06 | 3.5e-06 | 2.6e-07 |
| Jaynes–Cummings | 2.1e-04 | 4.0e-05 | 1.2e-05 | 7.4e-09 | 1.7e-09 | 1.1e-31 |

## Models of this repository vs the numbers printed in the paper (Tables 4–6)

| Dataset | N | Paper: GQKAN-QKANFWP | Paper: best of its models | QKAN-FWP+ | QKAN-FWP+ write-first | HQKAN-Δ, no fast weights |
|---|---|---|---|---|---|---|
| Bessel J2 | 8 | 2.5e-05 | 2.5e-05 | **1.09e-06 ± 5.2e-07** | **7.64e-07 ± 6.0e-07** | **8.39e-08 ± 5.4e-08** |
| Bessel J2 | 16 | 1.1e-05 | 1.1e-05 | **1.64e-06 ± 1.4e-06** | **1.78e-06 ± 1.7e-06** | **1.21e-07 ± 9.7e-08** |
| Bessel J2 | 32 | 1.5e-05 | 1.5e-05 | **1.43e-06 ± 4.0e-07** | **1.53e-06 ± 3.3e-07** | **1.24e-07 ± 1.1e-07** |
| Bessel J2 | 64 | 2.1e-05 | 2.1e-05 | **2.00e-06 ± 1.3e-06** | **1.61e-06 ± 7.7e-07** | **2.74e-07 ± 1.9e-07** |
| Damped SHM | 8 | 8.9e-05 | 8.9e-05 | **1.56e-06 ± 7.6e-07** | **1.52e-06 ± 8.3e-07** | **2.48e-07 ± 2.5e-08** |
| Damped SHM | 16 | 3.6e-05 | 3.6e-05 | **1.38e-06 ± 6.5e-07** | **1.12e-06 ± 1.2e-06** | **2.01e-07 ± 7.8e-08** |
| Damped SHM | 32 | 1.9e-05 | 1.9e-05 | **2.54e-06 ± 1.4e-06** | **2.53e-06 ± 1.1e-06** | **5.21e-07 ± 5.1e-07** |
| Damped SHM | 64 | 4.3e-05 | 4.3e-05 | **2.20e-06 ± 1.4e-06** | **2.22e-06 ± 2.4e-06** | **4.24e-07 ± 4.9e-07** |
| NARMA5 | 8 | 2.0e-05 | 5.0e-06 | 3.55e-05 ± 1.2e-05 | 1.69e-05 ± 5.5e-06 | 1.41e-05 ± 3.6e-06 |
| NARMA5 | 16 | 2.8e-05 | 1.2e-05 | **3.67e-06 ± 1.5e-06** | **2.96e-06 ± 8.6e-07** | **1.79e-06 ± 2.2e-07** |
| NARMA5 | 32 | 4.8e-05 | 1.1e-05 | **3.84e-06 ± 1.5e-06** | **3.69e-06 ± 1.9e-06** | **2.05e-06 ± 9.2e-07** |
| NARMA5 | 64 | 8.7e-05 | 1.0e-05 | **2.57e-06 ± 6.6e-07** | **3.34e-06 ± 7.1e-07** | **1.39e-06 ± 3.1e-07** |
| NARMA10 | 8 | 1.0e-04 | 4.3e-05 | 8.14e-05 ± 4.7e-05 | 8.17e-05 ± 3.2e-05 | 4.34e-05 ± 1.3e-05 |
| NARMA10 | 16 | 5.2e-05 | 2.0e-06 | 4.31e-06 ± 1.7e-06 | 5.06e-06 ± 2.3e-06 | 2.14e-06 ± 3.3e-07 |
| NARMA10 | 32 | 5.5e-05 | 1.6e-05 | **3.09e-06 ± 1.3e-06** | **2.79e-06 ± 1.6e-06** | **9.47e-07 ± 3.1e-07** |
| NARMA10 | 64 | 1.1e-04 | 2.0e-05 | **3.92e-06 ± 2.0e-06** | **2.84e-06 ± 1.7e-06** | **6.43e-07 ± 2.6e-07** |
| Delayed quantum control | 8 | 4.8e-05 | 3.3e-05 | **1.02e-05 ± 5.9e-06** | **1.14e-05 ± 6.9e-06** | **3.51e-06 ± 1.4e-06** |
| Delayed quantum control | 16 | 4.1e-05 | 4.1e-05 | **9.03e-06 ± 4.8e-06** | **9.91e-06 ± 3.5e-06** | **5.92e-06 ± 5.4e-06** |
| Delayed quantum control | 32 | 8.9e-05 | 5.3e-05 | **4.31e-06 ± 2.0e-06** | **8.26e-06 ± 6.3e-06** | **2.65e-06 ± 1.6e-06** |
| Delayed quantum control | 64 | 2.2e-04 | 1.2e-04 | **1.05e-05 ± 5.6e-06** | **7.10e-06 ± 3.3e-06** | **2.80e-06 ± 1.6e-06** |
| Jaynes–Cummings | 8 | 2.0e-04 | 9.2e-05 | **7.71e-09 ± 6.0e-09** | **4.43e-09 ± 4.1e-09** | **1.41e-09 ± 1.2e-09** |
| Jaynes–Cummings | 16 | 1.6e-04 | 7.0e-05 | **3.68e-09 ± 1.5e-09** | **7.99e-09 ± 9.0e-09** | **1.70e-09 ± 1.2e-09** |
| Jaynes–Cummings | 32 | 2.0e-04 | 2.0e-04 | **6.20e-09 ± 4.2e-09** | **6.62e-09 ± 5.3e-09** | **3.17e-09 ± 2.7e-09** |
| Jaynes–Cummings | 64 | 3.2e-04 | 3.7e-05 | **1.71e-08 ± 2.6e-08** | **1.03e-08 ± 1.5e-08** | **1.22e-09 ± 1.4e-09** |

- QKAN-FWP+: below the paper's GQKAN-QKANFWP number in 23/24 cells, below the paper's best number in 21/24 cells (bold).
- QKAN-FWP+ write-first: below the paper's GQKAN-QKANFWP number in 24/24 cells, below the paper's best number in 21/24 cells (bold).
- HQKAN-Δ, no fast weights: below the paper's GQKAN-QKANFWP number in 24/24 cells, below the paper's best number in 21/24 cells (bold).

## QKAN-FWP+ ablation (5 series × N ∈ {16, 64}; ratio to the paper-protocol baseline)

| Variant | Params | Geo-mean MSE ratio vs baseline | Cells better than baseline | Bessel J2 | Damped SHM | NARMA5 | NARMA10 | Delayed quantum control |
|---|---|---|---|---|---|---|---|---|
| Baseline GQKAN-QKANFWP, tuned lr | 152 | **0.079** | 10/10 | 0.0055 | 0.092 | 0.12 | 0.2 | 0.25 |
| GQKAN-FWP, tuned lr | 114 | **0.13** | 9/10 | 0.0049 | 0.059 | 0.43 | 0.56 | 0.65 |
| G-QKANFWP, tuned lr | 175 | **0.058** | 10/10 | 0.0028 | 0.057 | 0.093 | 0.18 | 0.25 |
| QKAN-FWP+ | 149 | **0.0036** | 10/10 | 0.0026 | 0.013 | 0.0019 | 0.0015 | 0.0062 |
| QKAN-FWP+ write-first | 149 | **0.0033** | 10/10 | 0.0024 | 0.012 | 0.0019 | 0.0014 | 0.0054 |
| QKAN-FWP+ without residual read-out | 149 | **0.029** | 10/10 | 0.03 | 0.096 | 0.015 | 0.0062 | 0.083 |
| QKAN-FWP+ without Δ-tokens (scalar input) | 114 | **0.064** | 10/10 | 0.0031 | 0.019 | 0.2 | 0.29 | 0.33 |
| QKAN-FWP+ with 3-dim instead of 8-dim Δ-tokens | 124 | **0.0048** | 10/10 | 0.00048 | 0.0064 | 0.018 | 0.003 | 0.015 |
| QKAN-FWP+ with float32 differences | 149 | **0.0036** | 10/10 | 0.0026 | 0.013 | 0.0018 | 0.0016 | 0.0062 |
| QKAN-FWP+ with the paper's scalar gate | 146 | **0.0031** | 10/10 | 0.0019 | 0.0099 | 0.0027 | 0.0016 | 0.0035 |
| HQKAN-Δ: no fast weights (static HQKAN, same tokens) | 136 | **0.00091** | 10/10 | 0.00026 | 0.0023 | 0.00095 | 0.00043 | 0.0026 |
| LSTM with the same tokens and residual (not QKAN) | 160 | **0.00093** | 10/10 | 0.0004 | 0.0013 | 0.0012 | 0.0006 | 0.0018 |

## Closed-form linear reference vs every model (test MSE)

| Dataset | N | Best tuned re-implemented baseline | QKAN-FWP+ | HQKAN-Δ | Printed best, 2605.06734 | Printed best, 2607.27945 | Linear AR(3), 4 params | Linear AR(8), 9 params |
|---|---|---|---|---|---|---|---|---|
| Bessel J2 | 8 | 4.8e-06 | 1.1e-06 | 8.4e-08 | 2.5e-05 | 8.7e-06 | 7.4e-10 | **1.3e-23** |
| Bessel J2 | 16 | 2.6e-06 | 1.6e-06 | 1.2e-07 | 1.1e-05 | 4.9e-06 | 7.2e-10 | **1.0e-23** |
| Bessel J2 | 32 | 1.2e-06 | 1.4e-06 | 1.2e-07 | 1.5e-05 | 2.9e-06 | 6.1e-10 | **5.7e-24** |
| Bessel J2 | 64 | 1.4e-06 | 2.0e-06 | 2.7e-07 | 2.1e-05 | 6.4e-06 | 2.1e-10 | **1.0e-24** |
| Damped SHM | 8 | 4.4e-06 | 1.6e-06 | 2.5e-07 | 8.9e-05 | 1.2e-05 | 1.7e-08 | **1.1e-13** |
| Damped SHM | 16 | 1.0e-05 | 1.4e-06 | 2.0e-07 | 3.6e-05 | 1.4e-05 | 9.8e-09 | **1.6e-13** |
| Damped SHM | 32 | 4.3e-06 | 2.5e-06 | 5.2e-07 | 1.9e-05 | 3.6e-06 | 6.7e-09 | **8.9e-14** |
| Damped SHM | 64 | 1.5e-06 | 2.2e-06 | 4.2e-07 | 4.3e-05 | 1.0e-05 | 4.5e-09 | **4.3e-14** |
| NARMA5 | 8 | 1.9e-04 | 3.6e-05 | 1.4e-05 | 5.0e-06 | **4.9e-06** | 8.0e-05 | 3.8e-05 |
| NARMA5 | 16 | 1.7e-04 | 3.7e-06 | 1.8e-06 | 1.2e-05 | 5.2e-06 | 5.6e-05 | **5.3e-07** |
| NARMA5 | 32 | 1.8e-04 | 3.8e-06 | 2.1e-06 | 1.1e-05 | 7.1e-06 | 5.7e-05 | **4.7e-07** |
| NARMA5 | 64 | 1.4e-04 | 2.6e-06 | 1.4e-06 | 1.0e-05 | 9.6e-06 | 4.3e-05 | **3.1e-07** |
| NARMA10 | 8 | 7.1e-04 | 8.1e-05 | 4.3e-05 | 4.3e-05 | **2.3e-05** | 1.2e-03 | 1.1e-03 |
| NARMA10 | 16 | 4.8e-04 | 4.3e-06 | 2.1e-06 | **2.0e-06** | 2.6e-06 | 5.0e-05 | 3.1e-06 |
| NARMA10 | 32 | 5.6e-04 | 3.1e-06 | 9.5e-07 | 1.6e-05 | 1.3e-05 | 5.2e-05 | **4.8e-08** |
| NARMA10 | 64 | 5.2e-04 | 3.9e-06 | 6.4e-07 | 2.0e-05 | 1.4e-05 | 4.8e-05 | **4.7e-08** |
| Delayed quantum control | 8 | 5.7e-04 | 1.0e-05 | 3.5e-06 | 3.3e-05 | 3.5e-06 | 7.3e-05 | **2.3e-07** |
| Delayed quantum control | 16 | 4.6e-04 | 9.0e-06 | 5.9e-06 | 4.1e-05 | 6.9e-06 | 7.5e-05 | **3.0e-07** |
| Delayed quantum control | 32 | 3.2e-04 | 4.3e-06 | 2.7e-06 | 5.3e-05 | 7.8e-06 | 6.7e-05 | **3.0e-07** |
| Delayed quantum control | 64 | 3.1e-04 | 1.1e-05 | 2.8e-06 | 1.2e-04 | 4.8e-06 | 6.6e-05 | **2.4e-07** |
| Jaynes–Cummings | 8 | 1.6e-05 | 7.7e-09 | 1.4e-09 | 9.2e-05 | 1.7e-05 | 3.9e-30 | **3.4e-31** |
| Jaynes–Cummings | 16 | 1.0e-05 | 3.7e-09 | 1.7e-09 | 7.0e-05 | 3.2e-06 | 4.1e-30 | **1.2e-31** |
| Jaynes–Cummings | 32 | 1.1e-05 | 6.2e-09 | 3.2e-09 | 2.0e-04 | 9.1e-06 | 6.3e-31 | **8.7e-32** |
| Jaynes–Cummings | 64 | 1.0e-05 | 1.7e-08 | 1.2e-09 | 3.7e-05 | 7.0e-06 | 1.1e-29 | **4.6e-32** |

- Linear AR(8) is below HQKAN-Δ in 21/24 cells and linear AR(3) in 12/24 cells.
- Linear AR(8) is below the best printed number of both papers in 21/24 cells.

## Reproduction gap: re-implemented GQKAN-QKANFWP (paper protocol) vs the number printed in the paper

| Dataset | N | Printed (2605.06734) | Re-implementation, read-then-write | ratio | Re-implementation, write-then-read | ratio |
|---|---|---|---|---|---|---|
| Bessel J2 | 8 | 2.5e-05 | 5.49e-04 | 22.0× | 9.50e-04 | 38.0× |
| Bessel J2 | 16 | 1.1e-05 | 8.35e-04 | 75.9× | 1.04e-03 | 95.0× |
| Bessel J2 | 32 | 1.5e-05 | 6.90e-04 | 46.0× | 9.26e-04 | 61.7× |
| Bessel J2 | 64 | 2.1e-05 | 5.81e-04 | 27.7× | 7.82e-04 | 37.2× |
| Damped SHM | 8 | 8.9e-05 | 8.72e-05 | 1.0× | 1.85e-03 | 20.8× |
| Damped SHM | 16 | 3.6e-05 | 1.18e-04 | 3.3× | 1.75e-03 | 48.5× |
| Damped SHM | 32 | 1.9e-05 | 6.98e-05 | 3.7× | 1.62e-03 | 85.4× |
| Damped SHM | 64 | 4.3e-05 | 1.42e-04 | 3.3× | 1.73e-03 | 40.3× |
| NARMA5 | 8 | 2.0e-05 | 1.79e-03 | 89.7× | 1.36e-03 | 67.9× |
| NARMA5 | 16 | 2.8e-05 | 1.94e-03 | 69.5× | 1.41e-03 | 50.4× |
| NARMA5 | 32 | 4.8e-05 | 2.23e-03 | 46.4× | 1.60e-03 | 33.3× |
| NARMA5 | 64 | 8.7e-05 | 1.40e-03 | 16.1× | 1.03e-03 | 11.9× |
| NARMA10 | 8 | 1.0e-04 | 2.48e-03 | 24.8× | 2.26e-03 | 22.6× |
| NARMA10 | 16 | 5.2e-05 | 2.70e-03 | 51.9× | 2.11e-03 | 40.6× |
| NARMA10 | 32 | 5.5e-05 | 2.89e-03 | 52.5× | 2.23e-03 | 40.6× |
| NARMA10 | 64 | 1.1e-04 | 2.75e-03 | 25.4× | 2.02e-03 | 18.7× |
| Delayed quantum control | 8 | 4.8e-05 | 2.56e-03 | 53.4× | 5.70e-03 | 118.9× |
| Delayed quantum control | 16 | 4.1e-05 | 2.04e-03 | 49.8× | 5.04e-03 | 122.9× |
| Delayed quantum control | 32 | 8.9e-05 | 1.91e-03 | 21.5× | 4.73e-03 | 53.2× |
| Delayed quantum control | 64 | 2.2e-04 | 1.20e-03 | 5.4× | 4.16e-03 | 18.8× |
| Jaynes–Cummings | 8 | 2.0e-04 | 2.75e-05 | 0.1× | – | – |
| Jaynes–Cummings | 16 | 1.6e-04 | 4.25e-05 | 0.3× | – | – |
| Jaynes–Cummings | 32 | 2.0e-04 | 3.38e-05 | 0.2× | – | – |
| Jaynes–Cummings | 64 | 3.2e-04 | 6.66e-05 | 0.2× | – | – |

- Geometric-mean ratio over the 24 cells (read-then-write): 9.5×; over the 20 cells of the five 300-point series: read-then-write 20.7×, write-then-read 42.6×.

- QKAN-FWP+: 40× below the printed GQKAN-QKANFWP numbers (geometric mean, 24 cells); 5.0× below the best printed number of either paper, lower in 18/24 cells.
- HQKAN-Δ, no fast weights: 158× below the printed GQKAN-QKANFWP numbers (geometric mean, 24 cells); 19.5× below the best printed number of either paper, lower in 21/24 cells.

## Robustness checks at N = 16 (test MSE, 5 seeds)

**Default (as in all tables above)**

| Dataset | Baseline, paper protocol | Baseline, tuned lr | QKAN-FWP+ | HQKAN-Δ |
|---|---|---|---|---|
| Bessel J2 | 8.35e-04 | 4.27e-06 | 1.64e-06 | 1.21e-07 |
| Damped SHM | 1.18e-04 | 1.15e-05 | 1.38e-06 | 2.01e-07 |
| NARMA5 | 1.94e-03 | 2.29e-04 | 3.67e-06 | 1.79e-06 |
| NARMA10 | 2.70e-03 | 5.24e-04 | 4.31e-06 | 2.14e-06 |
| Delayed quantum control | 2.04e-03 | 4.63e-04 | 9.03e-06 | 5.92e-06 |
| Jaynes–Cummings | 4.25e-05 | 2.24e-05 | 3.68e-09 | 1.70e-09 |

- vs the tuned baseline over 6 datasets: QKAN-FWP+ 61× lower (6/6), HQKAN-Δ 201× lower (6/6).

**Physical read-out ⟨Z⟩ = |a|² − |b|² in every DARUAN circuit**

| Dataset | Baseline, paper protocol | Baseline, tuned lr | QKAN-FWP+ | HQKAN-Δ |
|---|---|---|---|---|
| Bessel J2 | 5.90e-04 | 6.54e-06 | 1.53e-06 | 1.98e-07 |
| Damped SHM | 1.24e-04 | 1.85e-05 | 1.30e-06 | 4.62e-07 |
| NARMA5 | 1.89e-03 | 2.33e-04 | 4.80e-06 | 2.24e-06 |
| NARMA10 | 2.49e-03 | 5.37e-04 | 8.45e-06 | 2.73e-06 |
| Delayed quantum control | 1.73e-03 | 5.64e-04 | 1.27e-05 | 8.70e-06 |
| Jaynes–Cummings | 4.53e-05 | 1.98e-05 | 1.41e-08 | 5.77e-09 |

- vs the tuned baseline over 6 datasets: QKAN-FWP+ 48× lower (6/6), HQKAN-Δ 135× lower (6/6).

**Min–max scaling fitted on the training part only**

| Dataset | Baseline, paper protocol | Baseline, tuned lr | QKAN-FWP+ | HQKAN-Δ |
|---|---|---|---|---|
| Bessel J2 | 8.35e-04 | 4.27e-06 | 1.64e-06 | 1.21e-07 |
| Damped SHM | 1.18e-04 | 1.15e-05 | 1.38e-06 | 2.01e-07 |
| NARMA5 | 1.99e-03 | 2.31e-04 | 3.71e-06 | 1.80e-06 |
| NARMA10 | 2.70e-03 | 5.24e-04 | 4.31e-06 | 2.14e-06 |
| Delayed quantum control | 2.04e-03 | 4.63e-04 | 9.03e-06 | 5.92e-06 |
| Jaynes–Cummings | 4.25e-05 | 2.24e-05 | 3.68e-09 | 1.70e-09 |

- vs the tuned baseline over 6 datasets: QKAN-FWP+ 61× lower (6/6), HQKAN-Δ 201× lower (6/6).

## NARMA without the start-up transient (200 burn-in steps discarded; test MSE, 5 seeds)

| Dataset | N | Baseline, paper protocol | Baseline, tuned lr | QKAN-FWP+ | HQKAN-Δ |
|---|---|---|---|---|---|
| NARMA5 | 8 | 3.17e-03 | 3.13e-03 | 1.33e-05 | 6.60e-06 |
| NARMA5 | 16 | 3.02e-03 | 2.54e-03 | 1.18e-05 | 5.55e-06 |
| NARMA10 | 8 | 5.29e-03 | 4.79e-03 | 9.90e-06 | 3.90e-06 |
| NARMA10 | 16 | 5.46e-03 | 7.70e-03 | 9.52e-06 | 3.98e-06 |

## Solar cycle: final comparison (paper split and protocol, lr 2.5e-3, 5 seeds, test metrics)

| Model | Params | Scaled MSE ↓ | PAE ↓ | PTE ↓ | Val. loss |
|---|---|---|---|---|---|
| Baseline GQKAN-QKANFWP (scalar gate) | 12,423 | 0.0184 ± 0.0005 | 45.2 ± 2.1 | 29.8 ± 2.9 | 2.53 ± 0.05 |
| QKAN-FWP+: grouped gates + last-cycle residual read-out | 11,732 | 0.0134 ± 0.0008 | 37.8 ± 2.4 | 17.5 ± 1.5 | 3.75 ± 0.19 |
| QKAN-FWP+ without the last-cycle read-out (gates only) | 11,732 | 0.0139 ± 0.0008 | 40.9 ± 0.7 | 27.0 ± 2.4 | 2.60 ± 0.05 |
| QKAN-FWP+ without grouped gates (read-out only) | 12,423 | 0.0179 ± 0.0006 | 34.2 ± 0.4 | 19.6 ± 0.9 | 2.80 ± 0.05 |
| *Reference: repeat the last cycle, 13-month smoothed (no training)* | 0 | 0.0156 | 35.9 | 16.2 | – |
| *Paper's reported GQKAN-QKANFWP* | 12,474 | 0.0168 ± 0.0016 | 39.59 ± 2.82 | 21.89 ± 1.57 | – |

- QKAN-FWP+ vs baseline, MSE: -26.8% (Welch p = 2.2e-05)
- QKAN-FWP+ vs baseline, PAE: -16.2% (Welch p = 0.0017)
- QKAN-FWP+ vs baseline, PTE: -41.2% (Welch p = 0.00032)

## Solar cycle: the paper's learning-rate grid (5 seeds each)

| Model | lr | Val. loss (selection criterion) | Scaled MSE | PAE | PTE |
|---|---|---|---|---|---|
| Baseline | 1e-3 | 2.509 ← selected | 0.0177 ± 0.0010 | 45.8 ± 2.8 | 26.1 ± 2.2 |
| Baseline | 2e-3 | 2.535 | 0.0177 ± 0.0010 | 44.9 ± 2.3 | 28.6 ± 3.3 |
| Baseline | 2.5e-3 | 2.534 | 0.0184 ± 0.0005 | 45.2 ± 2.1 | 29.8 ± 2.9 |
| QKAN-FWP+ | 1e-3 | 3.290 ← selected | 0.0146 ± 0.0010 | 36.0 ± 0.4 | 18.6 ± 1.7 |
| QKAN-FWP+ | 2e-3 | 3.756 | 0.0129 ± 0.0006 | 37.1 ± 2.3 | 19.1 ± 1.8 |
| QKAN-FWP+ | 2.5e-3 | 3.749 | 0.0134 ± 0.0008 | 37.8 ± 2.4 | 17.5 ± 1.5 |

## Solar cycle: second split (60/20/20, test targets 1971–2026, five cycles)

| Model | Params | Scaled MSE ↓ | PAE ↓ | PTE ↓ | Val. loss |
|---|---|---|---|---|---|
| Baseline GQKAN-QKANFWP (scalar gate) | 12,423 | 0.0175 ± 0.0006 | 76.2 ± 6.6 | 29.1 ± 2.0 | 4.04 ± 0.16 |
| QKAN-FWP+: grouped gates + last-cycle residual read-out | 11,732 | 0.0184 ± 0.0012 | 65.9 ± 4.2 | 27.2 ± 1.5 | 4.17 ± 0.16 |
| Baseline + grouped gates (12,632 parameters) | 12,632 | 0.0162 ± 0.0010 | 79.8 ± 5.0 | 31.3 ± 0.5 | 3.49 ± 0.19 |
| *Reference: repeat the last cycle, 13-month smoothed* | 0 | 0.0166 | 53.1 | 18.7 | – |

- QKAN-FWP+ vs baseline, MSE: +5.1% (Welch p = 0.23)
- QKAN-FWP+ vs baseline, PAE: -13.6% (Welch p = 0.035)
- QKAN-FWP+ vs baseline, PTE: -6.5% (Welch p = 0.17)

## Solar cycle: third split (70/15/15, test targets 1982–2026, four cycles; 3 seeds)

| Model | Params | Scaled MSE ↓ | PAE ↓ | PTE ↓ | Val. loss |
|---|---|---|---|---|---|
| Baseline GQKAN-QKANFWP (scalar gate) | 12,423 | 0.0168 ± 0.0005 | 56.1 ± 5.1 | 26.5 ± 2.0 | 3.85 ± 0.15 |
| QKAN-FWP+: grouped gates + last-cycle residual read-out | 11,732 | 0.0156 ± 0.0004 | 44.8 ± 3.3 | 24.1 ± 0.7 | 4.60 ± 0.26 |
| *Reference: repeat the last cycle, 13-month smoothed* | 0 | 0.0168 | 38.5 | 18.8 | – |

- QKAN-FWP+ vs baseline, MSE: -7.0% (Welch p = 0.071)
- QKAN-FWP+ vs baseline, PAE: -20.2% (Welch p = 0.067)
- QKAN-FWP+ vs baseline, PTE: -8.8% (Welch p = 0.23)

