## Reproduction with the authors' settings (GQKAN-QKANFWP as in the released code, lr 1e-3, batch 4; test MSE)

The paper states 50 epochs; the README of the code gives 100 epochs as the benchmark configuration, so both are listed. "Printed" is the GQKAN-QKANFWP entry of Tables 3–6 of arXiv:2605.06734.

| Dataset | N | Printed | 50 epochs: mean ± std | 50 epochs: median | 100 epochs: mean | Seeds | Mean at 50 epochs ÷ printed |
|---|---|---|---|---|---|---|---|
| Bessel J2 (256 samples) | 8 | 2.5e-05 | 1.4e-04 ± 1.9e-04 | 3.0e-05 | 2.0e-05 | 5 | 5.5× |
| Bessel J2 (256 samples) | 16 | 1.1e-05 | 4.2e-05 ± 5.1e-05 | 2.2e-05 | 5.1e-06 | 5 | 3.8× |
| Bessel J2 (256 samples) | 32 | 1.5e-05 | 6.2e-04 ± 1.2e-03 | 3.4e-05 | 6.8e-04 | 5 | 42× |
| Bessel J2 (256 samples) | 64 | 2.1e-05 | 1.1e-03 ± 2.2e-03 | 8.4e-05 | 6.3e-04 | 5 | 55× |
| Damped SHM (240 samples) | 8 | 8.9e-05 | 3.9e-05 ± 1.9e-05 | 3.3e-05 | 6.7e-05 | 5 | 0.44× |
| Damped SHM (240 samples) | 16 | 3.6e-05 | 8.7e-05 ± 6.9e-05 | 5.3e-05 | 4.9e-05 | 5 | 2.4× |
| Damped SHM (240 samples) | 32 | 1.9e-05 | 1.6e-05 ± 8.0e-06 | 1.5e-05 | 1.9e-05 | 5 | 0.83× |
| Damped SHM (240 samples) | 64 | 4.3e-05 | 1.2e-04 ± 1.3e-04 | 5.8e-05 | 2.5e-05 | 5 | 2.8× |
| NARMA5, u → y (300 samples) | 8 | 2.0e-05 | 1.6e-05 ± 9.2e-06 | 1.3e-05 | 9.3e-06 | 5 | 0.78× |
| NARMA5, u → y (300 samples) | 16 | 2.8e-05 | 1.6e-05 ± 9.0e-06 | 1.1e-05 | 1.2e-05 | 5 | 0.59× |
| NARMA5, u → y (300 samples) | 32 | 4.8e-05 | 1.6e-05 ± 2.8e-06 | 1.5e-05 | 9.8e-06 | 5 | 0.34× |
| NARMA5, u → y (300 samples) | 64 | 8.7e-05 | 2.5e-05 ± 7.9e-06 | 2.0e-05 | 1.5e-05 | 5 | 0.29× |
| NARMA10, u → y (300 samples) | 8 | 1.0e-04 | 8.1e-05 ± 2.8e-05 | 6.9e-05 | 7.0e-05 | 5 | 0.81× |
| NARMA10, u → y (300 samples) | 16 | 5.2e-05 | 3.9e-05 ± 1.8e-05 | 4.5e-05 | 8.3e-06 | 5 | 0.76× |
| NARMA10, u → y (300 samples) | 32 | 5.5e-05 | 4.1e-05 ± 1.7e-05 | 3.0e-05 | 1.6e-05 | 5 | 0.75× |
| NARMA10, u → y (300 samples) | 64 | 1.1e-04 | 5.5e-05 ± 2.2e-05 | 5.3e-05 | 2.2e-05 | 5 | 0.51× |
| Delayed quantum control (2200 samples) | 8 | 4.8e-05 | 3.8e-05 ± 4.5e-05 | 1.9e-05 | 3.4e-05 | 5 | 0.79× |
| Delayed quantum control (2200 samples) | 16 | 4.1e-05 | 5.2e-05 ± 6.5e-05 | 2.3e-05 | 5.3e-05 | 5 | 1.3× |
| Delayed quantum control (2200 samples) | 32 | 8.9e-05 | 9.9e-05 ± 6.9e-05 | 1.0e-04 | 5.5e-05 | 5 | 1.1× |
| Delayed quantum control (2200 samples) | 64 | 2.2e-04 | 6.1e-05 ± 6.0e-05 | 3.1e-05 | 5.5e-05 | 5 | 0.28× |
| Jaynes–Cummings (3000 samples) | 8 | 2.0e-04 | 6.4e-05 ± 2.4e-05 | 7.3e-05 | 1.0e-04 | 5 | 0.32× |
| Jaynes–Cummings (3000 samples) | 16 | 1.6e-04 | 7.6e-05 ± 6.9e-05 | 6.7e-05 | 3.8e-05 | 5 | 0.48× |
| Jaynes–Cummings (3000 samples) | 32 | 2.0e-04 | 6.3e-05 ± 4.7e-05 | 5.7e-05 | 5.6e-05 | 5 | 0.32× |
| Jaynes–Cummings (3000 samples) | 64 | 3.2e-04 | 1.9e-04 ± 2.7e-04 | 5.7e-05 | 1.6e-04 | 5 | 0.6× |

- Geometric mean over the 24 cells of (re-run ÷ printed): 1.1× with the mean at 50 epochs, 0.62× with the median at 50 epochs, 0.65× with the mean at 100 epochs.

## Authors' datasets: per-dataset summary (geometric mean over N ∈ {8, 16, 32, 64} of the seed-mean test MSE)

On the two NARMA tasks the window holds the drive u and the target is y: the models have no residual read-out there, and QKAN-FWP-O solves its measurement operator from the labelled training windows instead of from the context.

| Dataset | Best printed in the two papers | GQKAN-QKANFWP, authors' code, lr 1e-3 (159) | GQKAN-QKANFWP, authors' code, tuned lr (159) | QKAN-FWP+ (149) | HQKAN-Δ (136) | QKAN-FWP-O features, static observable (118–154) | QKAN-FWP-O (104–154) | *Linear on the last 8 inputs (9)* | *Ridge on quadratic features of the last 12 inputs* |
|---|---|---|---|---|---|---|---|---|---|
| Bessel J2 (256 samples) | 5.3e-06 | 2.5e-04 | 2.5e-06 | 3.4e-06 | 4.3e-07 | 8.4e-08 | **8.2e-12** | *2.7e-14* | – |
| Damped SHM (240 samples) | 8.8e-06 | 5.0e-05 | 2.6e-05 | 8.0e-06 | 9.0e-07 | 2.7e-07 | **7.3e-12** | *2.0e-12* | – |
| NARMA5, u → y (300 samples) | 6.5e-06 | 1.8e-05 | 6.6e-06 | 9.7e-06 | 2.6e-06 | 2.4e-06 | **2.8e-07** | *5.3e-06* | *2.8e-09* |
| NARMA10, u → y (300 samples) | 9.5e-06 | 5.2e-05 | 1.1e-05 | 8.5e-06 | 4.2e-06 | 2.5e-06 | **9.7e-07** | *4.8e-06* | *9.4e-08* |
| Delayed quantum control (2200 samples) | 5.5e-06 | 5.9e-05 | 5.6e-05 | 4.7e-09 | 1.3e-08 | 6.0e-12 | **3.5e-13** | *2.8e-14* | – |
| Jaynes–Cummings (3000 samples) | 7.6e-06 | 8.8e-05 | 4.9e-05 | 5.9e-09 | 6.4e-09 | 5.4e-12 | **2.1e-12** | *1.5e-13* | – |

## Authors' datasets: QKAN-FWP-O against each model (reference test MSE ÷ QKAN-FWP-O test MSE; above 1: QKAN-FWP-O is lower)

Geometric mean over the four windows per dataset; values below 1e-15 are clipped first.

| Compared with | Bessel J2 | Damped SHM | NARMA5, u → y | NARMA10, u → y | Delayed quantum control | Jaynes–Cummings | Cells where QKAN-FWP-O is lower | Smallest … largest factor |
|---|---|---|---|---|---|---|---|---|
| GQKAN-QKANFWP, authors' code, lr 1e-3 | 3.1e7× | 6.9e6× | 65× | 54× | 1.7e8× | 4.1e7× | 24/24 | 11× … 2.3e8× |
| GQKAN-QKANFWP, authors' code, tuned lr | 3.0e5× | 3.5e6× | 24× | 11× | 1.6e8× | 2.3e7× | 24/24 | 1.7× … 1.9e10× |
| QKAN-FWP+ | 4.1e5× | 1.1e6× | 35× | 8.8× | 1.3e4× | 2750× | 24/24 | 1× … 2.8e6× |
| HQKAN-Δ | 5.2e4× | 1.2e5× | 9.3× | 4.3× | 3.9e4× | 3007× | 23/24 | 0.59× … 2.4e5× |
| QKAN-FWP-O features, static observable | 1.0e4× | 3.7e4× | 8.8× | 2.6× | 17× | 2.5× | 21/24 | 0.17× … 5.5e4× |
| *Best printed number of the two papers* | 6.5e5× | 1.2e6× | 23× | 9.8× | 1.6e7× | 3.6e6× | 24/24 | 3.6× … 2.1e7× |
| *Linear on the last 8 inputs* | 0.0033× | 0.28× | 19× | 4.9× | 0.081× | 0.068× | 9/24 | 0.00066× … 234× |
| *Ridge on quadratic features (NARMA only)* | – | – | 0.01× | 0.097× | – | – | 0/8 | 0.0015× … 0.64× |

## Authors' datasets: all cells (test MSE, mean ± std over the seeds)

| Dataset | N | Seeds | GQKAN-QKANFWP, authors' code, lr 1e-3 | GQKAN-QKANFWP, authors' code, tuned lr | QKAN-FWP+ | HQKAN-Δ | QKAN-FWP-O features, static observable | QKAN-FWP-O | *Linear, last 8 inputs* | *Quadratic ridge* |
|---|---|---|---|---|---|---|---|---|---|---|
| Bessel J2 (256 samples) | 8 | 5 | 1.37e-04 ± 1.9e-04 | 1.28e-06 ± 5.7e-07 | 2.13e-06 ± 2.0e-06 | 1.82e-07 ± 8.5e-08 | 2.37e-08 ± 1.2e-08 | **7.10e-12 ± 4.6e-12** | *1.2e-13* | – |
| Bessel J2 (256 samples) | 16 | 5 | 4.16e-05 ± 5.1e-05 | 1.28e-06 ± 6.4e-07 | 3.23e-06 ± 2.4e-06 | 3.03e-07 ± 1.8e-07 | 9.23e-08 ± 3.7e-08 | **8.09e-12 ± 1.2e-11** | *6.7e-14* | – |
| Bessel J2 (256 samples) | 32 | 5 | 6.23e-04 ± 1.2e-03 | 4.36e-06 ± 5.7e-06 | 6.70e-06 ± 4.2e-06 | 5.04e-07 ± 4.3e-07 | 1.34e-07 ± 3.3e-08 | **1.59e-11 ± 5.9e-12** | *2.0e-14* | – |
| Bessel J2 (256 samples) | 64 | 5 | 1.15e-03 ± 2.2e-03 | 5.16e-06 ± 4.3e-06 | 2.75e-06 ± 1.6e-06 | 1.18e-06 ± 1.0e-06 | 1.68e-07 ± 4.0e-08 | **4.90e-12 ± 3.0e-12** | *3.2e-15* | – |
| Damped SHM (240 samples) | 8 | 5 | 3.88e-05 ± 1.9e-05 | 2.17e-05 ± 7.1e-06 | 1.09e-05 ± 9.1e-06 | 7.14e-07 ± 4.7e-07 | 1.48e-07 ± 1.7e-07 | **3.89e-12 ± 1.2e-12** | *3.3e-12* | – |
| Damped SHM (240 samples) | 16 | 5 | 8.70e-05 ± 6.9e-05 | 4.83e-06 ± 1.5e-06 | 7.25e-06 ± 7.3e-06 | 5.09e-07 ± 2.4e-07 | 1.84e-07 ± 1.1e-07 | **3.35e-12 ± 1.5e-12** | *4.4e-12* | – |
| Damped SHM (240 samples) | 32 | 5 | 1.57e-05 ± 8.0e-06 | 2.42e-04 ± 4.7e-04 | 7.51e-06 ± 6.4e-06 | 1.04e-06 ± 8.4e-07 | 4.66e-07 ± 1.9e-07 | **2.14e-11 ± 5.9e-12** | *1.5e-12* | – |
| Damped SHM (240 samples) | 64 | 5 | 1.21e-04 ± 1.3e-04 | 1.74e-05 ± 7.9e-06 | 6.80e-06 ± 5.6e-06 | 1.70e-06 ± 1.1e-06 | 4.34e-07 ± 7.3e-08 | **1.01e-11 ± 3.7e-12** | *7.6e-13* | – |
| NARMA5, u → y (300 samples) | 8 | 5 | 1.56e-05 ± 9.2e-06 | 2.07e-06 ± 3.4e-06 | 4.11e-06 ± 1.1e-06 | 1.08e-06 ± 8.5e-07 | 2.04e-06 ± 1.8e-07 | **2.02e-08 ± 6.2e-09** | *4.7e-06* | *8.6e-09* |
| NARMA5, u → y (300 samples) | 16 | 5 | 1.64e-05 ± 9.0e-06 | 1.97e-06 ± 1.5e-06 | 5.50e-06 ± 2.3e-06 | 8.25e-07 ± 8.2e-07 | 1.58e-06 ± 1.8e-07 | **6.24e-07 ± 8.3e-07** | *4.4e-06* | *3.2e-09* |
| NARMA5, u → y (300 samples) | 32 | 5 | 1.65e-05 ± 2.8e-06 | 9.25e-06 ± 1.2e-05 | 1.21e-05 ± 6.6e-06 | 8.34e-06 ± 1.5e-05 | 1.84e-06 ± 4.0e-07 | **9.39e-07 ± 8.1e-07** | *4.7e-06* | *3.0e-09* |
| NARMA5, u → y (300 samples) | 64 | 5 | 2.48e-05 ± 7.9e-06 | 5.18e-05 ± 8.4e-05 | 3.23e-05 ± 2.2e-05 | 6.08e-06 ± 2.3e-06 | 5.97e-06 ± 1.1e-06 | **4.99e-07 ± 1.3e-07** | *8.0e-06* | *7.4e-10* |
| NARMA10, u → y (300 samples) | 8 | 5 | 8.07e-05 ± 2.8e-05 | 4.02e-05 ± 3.2e-06 | 4.25e-06 ± 1.7e-06 | 2.42e-06 ± 8.1e-07 | **1.99e-06 ± 1.1e-07** | 4.10e-06 ± 9.2e-07 | *6.7e-06* | *2.6e-06* |
| NARMA10, u → y (300 samples) | 16 | 5 | 3.93e-05 ± 1.8e-05 | 1.73e-06 ± 3.8e-07 | 6.52e-06 ± 2.4e-06 | 1.59e-06 ± 1.4e-06 | 2.32e-06 ± 2.7e-07 | **1.78e-07 ± 7.5e-08** | *4.9e-06* | *6.8e-08* |
| NARMA10, u → y (300 samples) | 32 | 5 | 4.14e-05 ± 1.7e-05 | 6.24e-06 ± 2.0e-06 | 7.93e-06 ± 2.7e-06 | 1.66e-05 ± 3.1e-05 | **1.83e-06 ± 2.9e-07** | 3.66e-06 ± 3.4e-07 | *4.0e-06* | *1.8e-08* |
| NARMA10, u → y (300 samples) | 64 | 5 | 5.51e-05 ± 2.2e-05 | 2.81e-05 ± 3.0e-05 | 2.42e-05 ± 1.8e-05 | 4.85e-06 ± 3.4e-06 | 4.70e-06 ± 1.5e-06 | **3.29e-07 ± 1.5e-07** | *4.1e-06* | *2.4e-08* |
| Delayed quantum control (2200 samples) | 8 | 5 | 3.77e-05 ± 4.5e-05 | 3.90e-06 ± 1.0e-06 | 1.04e-08 ± 1.0e-08 | 6.70e-09 ± 4.9e-09 | 2.77e-12 ± 6.1e-13 | **1.82e-13 ± 1.3e-13** | *2.8e-14* | – |
| Delayed quantum control (2200 samples) | 16 | 5 | 5.19e-05 ± 6.5e-05 | 5.63e-05 ± 1.0e-04 | 2.66e-09 ± 2.0e-09 | 1.02e-08 ± 1.4e-08 | 7.77e-12 ± 1.2e-11 | **3.31e-13 ± 1.7e-13** | *2.8e-14* | – |
| Delayed quantum control (2200 samples) | 32 | 5 | 9.89e-05 ± 6.9e-05 | 4.77e-06 ± 1.9e-06 | 4.64e-09 ± 6.0e-09 | 2.42e-08 ± 4.1e-08 | 7.91e-12 ± 8.5e-12 | **4.92e-13 ± 2.5e-13** | *2.8e-14* | – |
| Delayed quantum control (2200 samples) | 64 | 5 | 6.10e-05 ± 6.0e-05 | 9.67e-03 ± 1.9e-02 | 3.71e-09 ± 3.6e-09 | 2.00e-08 ± 2.5e-08 | 7.64e-12 ± 4.0e-12 | **4.99e-13 ± 2.4e-13** | *2.9e-14* | – |
| Jaynes–Cummings (3000 samples) | 8 | 5 | 6.44e-05 ± 2.4e-05 | 2.56e-05 ± 3.0e-06 | 4.59e-09 ± 3.0e-09 | 2.32e-09 ± 2.0e-09 | **5.96e-13 ± 2.1e-13** | 3.44e-12 ± 4.0e-13 | *1.5e-13* | – |
| Jaynes–Cummings (3000 samples) | 16 | 5 | 7.62e-05 ± 6.9e-05 | 5.43e-05 ± 6.0e-06 | 6.96e-09 ± 9.2e-09 | 7.73e-09 ± 9.3e-09 | 6.80e-12 ± 7.5e-12 | **1.18e-12 ± 1.3e-13** | *1.5e-13* | – |
| Jaynes–Cummings (3000 samples) | 32 | 5 | 6.29e-05 ± 4.7e-05 | 2.92e-05 ± 3.9e-06 | 9.41e-09 ± 9.4e-09 | 9.83e-09 ± 1.5e-08 | 1.12e-11 ± 1.3e-11 | **1.40e-12 ± 6.3e-13** | *1.5e-13* | – |
| Jaynes–Cummings (3000 samples) | 64 | 5 | 1.92e-04 ± 2.7e-04 | 1.40e-04 ± 2.3e-04 | 4.02e-09 ± 5.0e-09 | 9.83e-09 ± 1.2e-08 | 1.93e-11 ± 2.1e-11 | **3.73e-12 ± 1.0e-12** | *1.5e-13* | – |

## Solar cycle with the file, split and model of the authors' code (3,265 records to 2021-01; 2,606 windows; lr 2.5e-3)

Test windows 2345–2606 (targets 1988-05 … 2021-01) in both splits; test metrics at the best-validation checkpoint, mean ± std over seeds.

### window-index split 2084 / 260 / 262 (the authors' split; targets of neighbouring splits overlap by 131 months)

| Model | Params | Seeds | Scaled MSE ↓ | PAE ↓ | PTE ↓ |
|---|---|---|---|---|---|
| GQKAN-QKANFWP, authors' code | 12,474 | 5 | 0.0169 ± 0.0017 | 46.4 ± 7.0 | 23.0 ± 1.3 |
| QKAN-FWP+ | 11,732 | 5 | 0.0155 ± 0.0015 | 34.5 ± 2.3 | 17.6 ± 1.9 |
| QKAN-FWP-O without fast weights (static observable) | 496 | 5 | 0.0156 ± 0.0003 | 35.0 ± 1.0 | 18.6 ± 0.7 |
| QKAN-FWP-O | 547 | 5 | 0.0145 ± 0.0009 | 33.5 ± 0.3 | 18.6 ± 1.6 |
| *Reference: repeat the last cycle, 13-month smoothed (no training)* | 0 | – | 0.0177 | 31.8 | 11.7 |
| *Printed in arXiv:2605.06734 for GQKAN-QKANFWP* | 12,474 | 5 | 0.0168 ± 0.0016 | 39.59 ± 2.82 | 21.89 ± 1.57 |

### split by target time (the last 131 windows of train and validation removed)

| Model | Params | Seeds | Scaled MSE ↓ | PAE ↓ | PTE ↓ |
|---|---|---|---|---|---|
| GQKAN-QKANFWP, authors' code | 12,474 | 5 | 0.0185 ± 0.0020 | 46.2 ± 5.0 | 24.3 ± 1.9 |
| QKAN-FWP+ | 11,732 | 5 | 0.0165 ± 0.0018 | 32.6 ± 3.1 | 15.8 ± 2.9 |
| QKAN-FWP-O without fast weights (static observable) | 496 | 5 | 0.0160 ± 0.0002 | 34.9 ± 0.5 | 19.4 ± 1.7 |
| QKAN-FWP-O | 547 | 5 | 0.0184 ± 0.0004 | 43.4 ± 2.5 | 32.5 ± 1.7 |
| *Reference: repeat the last cycle, 13-month smoothed (no training)* | 0 | – | 0.0177 | 31.8 | 11.7 |

