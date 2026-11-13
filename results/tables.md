## Time series: main comparison (test MSE, mean ± std over 5 seeds)

| Dataset | N | Baseline, paper protocol (lr 1e-3) | Baseline, tuned lr | Extended (residual + Δ-tokens), tuned lr | Extended + multi-timescale gates, tuned lr |
|---|---|---|---|---|---|
| Bessel J2 | 8 | 5.49e-04 ± 5.2e-04 | 6.14e-06 ± 1.5e-06 | 5.25e-07 ± 3.9e-07 | **4.05e-07 ± 5.3e-07** |
| Bessel J2 | 16 | 8.35e-04 ± 7.2e-04 | 4.27e-06 ± 3.0e-06 | 3.52e-07 ± 4.3e-07 | **2.79e-07 ± 3.0e-07** |
| Bessel J2 | 32 | 6.90e-04 ± 5.3e-04 | 4.74e-06 ± 3.3e-06 | **2.34e-07 ± 1.9e-07** | 1.08e-06 ± 1.8e-06 |
| Bessel J2 | 64 | 5.81e-04 ± 5.8e-04 | 3.39e-06 ± 2.0e-06 | 4.00e-07 ± 3.4e-07 | **3.61e-07 ± 2.4e-07** |
| Damped SHM | 8 | 8.72e-05 ± 5.5e-05 | 1.78e-05 ± 5.0e-06 | **2.67e-07 ± 1.7e-07** | 4.60e-07 ± 3.2e-07 |
| Damped SHM | 16 | 1.18e-04 ± 7.2e-05 | 1.15e-05 ± 6.7e-06 | **1.44e-07 ± 1.1e-07** | 3.34e-07 ± 3.9e-07 |
| Damped SHM | 32 | 6.98e-05 ± 5.4e-05 | 7.67e-06 ± 2.0e-06 | **2.54e-07 ± 2.3e-07** | 3.56e-07 ± 3.3e-07 |
| Damped SHM | 64 | 1.42e-04 ± 9.8e-05 | 1.23e-05 ± 7.0e-06 | 7.30e-07 ± 6.6e-07 | **1.98e-07 ± 9.4e-08** |
| NARMA5 | 8 | 1.79e-03 ± 1.2e-03 | 2.78e-04 ± 6.6e-05 | 3.91e-05 ± 4.9e-06 | **3.47e-05 ± 7.7e-06** |
| NARMA5 | 16 | 1.94e-03 ± 1.1e-03 | 2.29e-04 ± 5.7e-05 | 3.16e-05 ± 1.2e-05 | **2.84e-05 ± 1.1e-05** |
| NARMA5 | 32 | 2.23e-03 ± 1.2e-03 | 2.46e-04 ± 5.1e-05 | 3.10e-05 ± 7.2e-06 | **2.81e-05 ± 6.9e-06** |
| NARMA5 | 64 | 1.40e-03 ± 7.7e-04 | 1.67e-04 ± 5.9e-05 | 2.72e-05 ± 7.2e-06 | **2.45e-05 ± 9.1e-06** |
| NARMA10 | 8 | 2.48e-03 ± 1.6e-03 | 1.33e-03 ± 3.1e-04 | 1.33e-04 ± 7.9e-05 | **7.02e-05 ± 3.9e-05** |
| NARMA10 | 16 | 2.70e-03 ± 1.9e-03 | 5.24e-04 ± 4.5e-05 | 7.26e-06 ± 1.8e-06 | **5.57e-06 ± 9.3e-07** |
| NARMA10 | 32 | 2.89e-03 ± 1.8e-03 | 5.56e-04 ± 3.1e-05 | 1.29e-05 ± 7.9e-06 | **5.87e-06 ± 1.2e-06** |
| NARMA10 | 64 | 2.75e-03 ± 1.5e-03 | 5.83e-04 ± 5.1e-05 | 1.03e-05 ± 7.1e-06 | **5.48e-06 ± 1.3e-06** |
| Delayed quantum control | 8 | 2.56e-03 ± 1.1e-03 | 5.83e-04 ± 1.5e-04 | 3.12e-05 ± 8.8e-06 | **2.53e-05 ± 1.0e-05** |
| Delayed quantum control | 16 | 2.04e-03 ± 4.3e-04 | 4.63e-04 ± 1.3e-04 | 3.25e-05 ± 2.3e-05 | **1.88e-05 ± 5.9e-06** |
| Delayed quantum control | 32 | 1.91e-03 ± 6.1e-04 | 3.96e-04 ± 9.7e-05 | 2.10e-05 ± 8.0e-06 | **1.49e-05 ± 6.4e-06** |
| Delayed quantum control | 64 | 1.20e-03 ± 3.3e-04 | 3.37e-04 ± 8.5e-05 | 2.17e-05 ± 1.1e-05 | **1.36e-05 ± 4.6e-06** |
| Jaynes–Cummings | 8 | 2.75e-05 ± 1.7e-05 | 1.95e-05 ± 2.5e-06 | 3.93e-08 ± 4.2e-08 | **2.66e-09 ± 2.4e-09** |
| Jaynes–Cummings | 16 | 4.25e-05 ± 4.8e-05 | 2.24e-05 ± 3.5e-06 | 6.22e-08 ± 9.9e-08 | **4.12e-09 ± 3.0e-09** |
| Jaynes–Cummings | 32 | 3.38e-05 ± 4.1e-05 | 1.42e-05 ± 3.6e-06 | 4.63e-08 ± 5.2e-08 | **8.50e-09 ± 1.1e-08** |
| Jaynes–Cummings | 64 | 6.66e-05 ± 5.4e-05 | 1.42e-05 ± 2.6e-06 | 4.73e-08 ± 3.8e-08 | **2.12e-08 ± 3.4e-08** |

## Time series: ablation (5 series × N ∈ {16, 64}; ratio of seed-mean test MSE to the paper-protocol baseline)

| Variant | Params | Geo-mean MSE ratio vs baseline | Cells better than baseline | Bessel J2 | Damped SHM | NARMA5 | NARMA10 | Delayed quantum control |
|---|---|---|---|---|---|---|---|---|
| Ungated (additive) FWP, lr 1e-3 | 148 | **4** | 3/10 | 1.8 | 24 | 3.1 | 1.4 | 5.5 |
| Baseline + multi-timescale gates, lr 1e-3 | 180 | **0.53** | 8/10 | 0.081 | 0.67 | 0.62 | 0.72 | 1.7 |
| Baseline + residual read-out, lr 1e-3 | 152 | **0.18** | 8/10 | 0.013 | 0.16 | 0.2 | 0.36 | 1.2 |
| Baseline + Δ-tokens, lr 1e-3 | 162 | **0.3** | 8/10 | 0.33 | 2.7 | 0.18 | 0.044 | 0.38 |
| Extended (residual + Δ-tokens), lr 1e-3 | 162 | **0.035** | 10/10 | 0.011 | 0.062 | 0.052 | 0.02 | 0.073 |
| Baseline, tuned lr | 152 | **0.079** | 10/10 | 0.0055 | 0.092 | 0.12 | 0.2 | 0.25 |
| Larger baseline (193 params), tuned lr | 193 | **0.074** | 10/10 | 0.0038 | 0.092 | 0.11 | 0.2 | 0.28 |
| Baseline + multi-timescale gates, tuned lr | 180 | **0.056** | 10/10 | 0.005 | 0.064 | 0.12 | 0.058 | 0.24 |
| Baseline + residual read-out, tuned lr | 152 | **0.062** | 10/10 | 0.0023 | 0.02 | 0.18 | 0.26 | 0.43 |
| Baseline + residual + multi-timescale gates, tuned lr | 180 | **0.038** | 10/10 | 0.0013 | 0.0091 | 0.19 | 0.1 | 0.34 |
| Baseline + Δ-tokens, tuned lr | 162 | **0.019** | 10/10 | 0.0092 | 0.047 | 0.032 | 0.005 | 0.033 |
| Extended (residual + Δ-tokens), tuned lr | 162 | **0.0042** | 10/10 | 0.00054 | 0.0025 | 0.018 | 0.0032 | 0.017 |
| Extended + multi-timescale gates, tuned lr | 190 | **0.0031** | 10/10 | 0.00046 | 0.002 | 0.016 | 0.002 | 0.01 |
| No fast-weight memory: HQKAN on last Δ-token, tuned lr | 149 | **0.0078** | 10/10 | 0.00032 | 0.0086 | 0.027 | 0.015 | 0.026 |
| LSTM (hidden 5), tuned lr | 166 | **0.03** | 10/10 | 0.00098 | 0.061 | 0.091 | 0.068 | 0.068 |
| LSTM + residual + Δ-tokens, tuned lr | 149 | **0.0034** | 10/10 | 0.00042 | 0.0023 | 0.013 | 0.0042 | 0.0088 |

## Time series: all 24 cells

| Variant | Params | Geo-mean MSE ratio vs baseline | Cells better than baseline | Bessel J2 | Damped SHM | NARMA5 | NARMA10 | Delayed quantum control | Jaynes–Cummings |
|---|---|---|---|---|---|---|---|---|---|
| Baseline, tuned lr | 152 | **0.12** | 24/24 | 0.0069 | 0.12 | 0.12 | 0.26 | 0.23 | 0.43 |
| Extended (residual + Δ-tokens), tuned lr | 162 | **0.0039** | 24/24 | 0.00055 | 0.0029 | 0.018 | 0.007 | 0.014 | 0.0012 |
| Extended + multi-timescale gates, tuned lr | 190 | **0.0025** | 24/24 | 0.0007 | 0.0032 | 0.016 | 0.0039 | 0.0095 | 0.00017 |

## Other paper variants (N = 16)

| Dataset | N | GQKAN-FWP, paper protocol | GQKAN-FWP, tuned lr | GQKAN-FWP extended, tuned lr | G-QKANFWP, paper protocol | G-QKANFWP, tuned lr | G-QKANFWP extended, tuned lr |
|---|---|---|---|---|---|---|---|
| Bessel J2 | 16 | 1.68e-03 ± 1.5e-03 | 6.23e-06 ± 5.6e-06 | **1.10e-07 ± 1.1e-07** | 3.56e-04 ± 4.8e-04 | 2.62e-06 ± 2.8e-07 | 2.47e-07 ± 1.4e-07 |
| Damped SHM | 16 | 1.01e-03 ± 1.2e-03 | 2.71e-06 ± 2.5e-06 | **1.67e-07 ± 1.4e-07** | 5.80e-05 ± 5.3e-05 | 1.00e-05 ± 3.8e-06 | 4.39e-07 ± 2.9e-07 |
| NARMA5 | 16 | 1.65e-03 ± 7.3e-04 | 3.87e-04 ± 2.0e-04 | 2.85e-05 ± 5.2e-06 | 1.54e-03 ± 7.0e-04 | 1.66e-04 ± 2.3e-05 | **2.67e-05 ± 6.0e-06** |
| NARMA10 | 16 | 2.53e-03 ± 1.2e-03 | 6.28e-04 ± 1.2e-04 | **5.97e-06 ± 1.3e-06** | 2.01e-03 ± 1.1e-03 | 4.79e-04 ± 9.5e-06 | 6.54e-06 ± 3.2e-06 |
| Delayed quantum control | 16 | 2.53e-02 ± 3.5e-02 | 1.55e-03 ± 2.4e-04 | 3.10e-05 ± 5.1e-06 | 1.63e-03 ± 8.7e-04 | 4.72e-04 ± 6.8e-05 | **2.03e-05 ± 4.4e-06** |

## Solar: validation-period scaled MSE of the selected checkpoint

| Model | Val. MSE | Best epoch |
|---|---|---|
| GQKAN-QKANFWP baseline (scalar gate) | 0.0136 ± 0.0004 | 78 |
| + chrono gate initialisation (scalar gate) | 0.0135 ± 0.0003 | 77 |
| + multi-timescale gates (20 groups, chrono init) | 0.0139 ± 0.0007 | 31 |
| + multi-timescale gates + yearly patch tokens | 0.0137 ± 0.0006 | 22 |
| Baseline, lr 1e-3 | 0.0135 ± 0.0006 | 90 |
| + multi-timescale gates, lr 1e-3 | 0.0140 ± 0.0005 | 34 |

## Solar cycle forecasting (test split, best-validation checkpoint)

| Model | Params | Scaled MSE ↓ | PAE ↓ | PTE ↓ | Val. loss ↓ | Seeds |
|---|---|---|---|---|---|---|
| GQKAN-QKANFWP baseline (scalar gate) | 12,423 | 0.0184 ± 0.0005 | 45.17 ± 2.10 | 29.76 ± 2.93 | 2.534 ± 0.053 | 5 |
| + chrono gate initialisation (scalar gate) | 12,423 | 0.0185 ± 0.0016 | 46.27 ± 2.13 | 29.63 ± 2.26 | 2.520 ± 0.057 | 5 |
| + multi-timescale gates (20 groups, chrono init) | 12,632 | **0.0135 ± 0.0013** | 42.19 ± 0.92 | 29.59 ± 4.13 | 2.651 ± 0.151 | 5 |
| + multi-timescale gates + yearly patch tokens | 12,852 | 0.0139 ± 0.0009 | 40.94 ± 1.81 | 25.24 ± 4.86 | 2.627 ± 0.130 | 5 |
| Baseline, lr 1e-3 | 12,423 | 0.0177 ± 0.0010 | 45.78 ± 2.77 | 26.06 ± 2.16 | 2.509 ± 0.112 | 5 |
| + multi-timescale gates, lr 1e-3 | 12,632 | 0.0137 ± 0.0011 | **40.84 ± 1.68** | **23.32 ± 6.34** | 2.666 ± 0.116 | 5 |

- + chrono gate initialisation (scalar gate): scaled MSE +0.9% vs baseline, Welch p = 0.85
- + multi-timescale gates (20 groups, chrono init): scaled MSE -26.7% vs baseline, Welch p = 0.000763
- + multi-timescale gates + yearly patch tokens: scaled MSE -24.3% vs baseline, Welch p = 0.000142
- Baseline, lr 1e-3: scaled MSE -3.4% vs baseline, Welch p = 0.289
- + multi-timescale gates, lr 1e-3: scaled MSE -25.2% vs baseline, Welch p = 0.000382

## Solar robustness check: 60/20/20 split (test targets 1970.8–2026.1, five cycles)

| Model | Params | Scaled MSE ↓ | PAE ↓ | PTE ↓ | Val. loss ↓ | Seeds |
|---|---|---|---|---|---|---|
| GQKAN-QKANFWP baseline (scalar gate) | 12,423 | 0.0175 ± 0.0006 | **76.19 ± 6.64** | **29.13 ± 2.03** | 4.039 ± 0.165 | 5 |
| + multi-timescale gates (20 groups, chrono init) | 12,632 | **0.0162 ± 0.0010** | 79.85 ± 5.03 | 31.35 ± 0.49 | 3.494 ± 0.191 | 5 |

- + multi-timescale gates (20 groups, chrono init): scaled MSE -7.4% vs baseline, Welch p = 0.0663

