# Data from the authors' released code

`jaynes_cummings.csv` — qubit excitation of the open Jaynes–Cummings model (3000 samples, t ∈ [0, 50]), the
trace that the authors' time-series benchmark loads.

- Source: <https://github.com/MatthewPeng57/Gated-QKAN-FWP>, file
  `times_series_benchmark/cuda_q_data/jaynes_cummings.csv`, commit `2cf0457` (2026-08-11), unchanged.
- Copyright 2026 Kuo-Chung Peng and Samuel Yen-Chi Chen. The file is generated data which that repository
  distributes under the Apache License 2.0 (`times_series_benchmark/cuda_q_data/README.md`); `LICENSE` and `NOTICE`
  in this directory are copies of the repository's licence and notice files.
- It was produced with NVIDIA CUDA-Q's ODE integrator and differs from the exact solution of the same master
  equation (`qkanfwp.data.jaynes_cummings`) by up to 9e-5. The difference is not smooth: on this file a linear
  AR(8) fitted by least squares reaches a test MSE of 1.5e-13, on the exact solution 7e-32. Results on the
  dataset `c_jc` therefore have a floor of about 1e-13.

The other series of the authors' benchmark (`c_bessel`, `c_shm`, `c_dqc`, `c_narma5`, `c_narma10`) are generated
by `qkanfwp/data.py` with the settings of the authors' code.
