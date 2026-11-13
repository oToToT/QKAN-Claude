# QKAN-Claude — 改進 Gated QKAN-FWP 的 MSE

針對 [*Gated QKAN-FWP: Scalable Quantum-inspired Sequence Learning*](https://arxiv.org/abs/2605.06734)
（arXiv:2605.06734）的重現、分析與改進實驗。

**完整分析與結果請看 [`REPORT.md`](REPORT.md)。**

## 主要結果

| | 重現的 baseline | 改進後 | 變化 |
|---|---|---|---|
| Time-series（6 個 dataset × 4 個 window，test MSE 幾何平均），baseline 用論文協定 | 1 | 0.0025 | 低 408 倍，24/24 格 |
| 同上，baseline 也用調好的 learning rate | 1 | 0.021 | 低 48 倍，24/24 格 |
| Solar cycle scaled MSE（論文 split，5 seeds） | 0.0184 ± 0.0005 | 0.0135 ± 0.0013 | −27%（p < 0.001）；60/20/20 split 上只有 −7% |

改進內容：調 learning rate（cosine）、residual 讀出、Δ-token `(x_t, Δx_t, Δ²x_t)`、多時間尺度（分組）gate。
同大小的 LSTM 套用相同的 residual＋Δ-token 後表現與改進後的 FWP 相當——詳見 REPORT 4.3 節。

![time-series main](figures/timeseries_main.png)

## 內容

| 路徑 | 說明 |
|---|---|
| `REPORT.md` | 論文分析、改進方向（含近期文獻）、實驗結果與結論 |
| `qkanfwp/daruan.py` | DARUAN / QKAN layer 的函數式實作（支援每個樣本各自的 fast 角度），與官方 `qkan` 套件數值一致 |
| `qkanfwp/models.py` | Gated fast-weight programmer（論文 Eq. 3–4）與本 repo 的擴充：residual 讀出、差分 token、多時間尺度 gate、chrono 初始化 |
| `qkanfwp/data.py` | Bessel、Damped SHM、NARMA5/10、Delayed Quantum Control、Jaynes–Cummings、SILSO 太陽黑子 |
| `experiments/run_timeseries.py` | 一步預測 benchmark（論文 Sec. 6.1） |
| `experiments/run_solar.py` | 太陽黑子週期 direct multi-step 預測（論文 Sec. 6.2） |
| `experiments/make_figures.py` | 由 `results/*.jsonl` 產生 `figures/` 與 `results/tables.md` |
| `experiments/run_all.sh` | 重現所有數字的完整指令 |
| `results/` | 所有 run 的原始結果（JSON lines） |
| `tests/` | 單元測試（DARUAN 與官方 solver 等價、closed-form memory kernel 與逐步遞迴等價、有界性…） |

## 快速開始

```bash
pip install -r requirements.txt
python -m pytest tests -q

# 單一比較：baseline vs 改進版，NARMA10、window 16、5 seeds
python experiments/run_timeseries.py --datasets narma10 --windows 16 \
    --variants base base@cos30 skip_dif3@cos30 --out results/quick.jsonl
python experiments/aggregate.py results/quick.jsonl

# 全部重現（約 7 CPU core-hours，可中斷續跑）
bash experiments/run_all.sh
```

Variant 名稱後的 `@cos30` 表示「cosine schedule、初始 lr = 30e-3」，`@lr3` 表示固定 lr = 3e-3；
不加則是論文的 lr（time-series 1e-3、solar 2.5e-3）。

## 資料來源

太陽黑子資料來自 WDC-SILSO（Royal Observatory of Belgium, Brussels），CC BY-NC 4.0，見 `data/README.md`。
