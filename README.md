# QKAN-Claude — 改進 Gated QKAN-FWP 的 MSE

針對 [*Gated QKAN-FWP: Scalable Quantum-inspired Sequence Learning*](https://arxiv.org/abs/2605.06734)
（arXiv:2605.06734）的重現、分析與改進實驗。

**完整分析與結果請看 [`REPORT.md`](REPORT.md)。**

## 結論（依外部審查修訂後）

**不能主張的：**

- **架構新穎性**：「多時間尺度（分組）gate」已被原團隊的 CMG（arXiv:2607.27945）涵蓋；Δ-token 與 residual 讀出是標準做法。
- **重現了論文的 baseline**：重現的 GQKAN-QKANFWP 在論文協定下比論文印出的數字差 21 倍（幾何平均），原因未明。
- **這組 benchmark 上的 MSE 代表模型能力**：9 參數的線性 AR(8)（最小平方法）在 21/24 格贏過我們最好的模型，
  也在 21/24 格贏過兩篇論文印出的最佳數字。
- **太陽黑子上穩健的改進**：論文的 split 上三個指標都贏，換 split 後 MSE 的優勢消失。

**仍然成立的**（同一份資料、同一個 pipeline；模型都是 QKAN-based 且參數量不超過論文）：

| 模型 | 參數量（論文 159） | 對重現的 GQKAN-QKANFWP（調過 lr） | 對兩篇論文印出的最佳數字 |
|---|---|---|---|
| HQKAN-Δ：靜態 HQKAN ＋ Δ-token ＋ residual 讀出 | 136 | 24/24 格較低，幾何平均低 175 倍 | 21/24 格較低，低 19.5 倍 |
| QKAN-FWP+：保留 gated fast-weight 架構 | 149 | 24/24 格較低，低 45 倍 | 18/24 格較低，低 5 倍 |

這些結論在改用物理的 ⟨Z⟩ 讀出、只用訓練段正規化、NARMA 去掉暫態之後都不變。

沒有做：MiniGrid RL、真機實驗、CMG 與 VQC 系列模型的重現。逐條審查回應見 `REPORT.md` 第 0 節。

![time-series main](figures/timeseries_main.png)

## 內容

| 路徑 | 說明 |
|---|---|
| `REPORT.md` | 論文分析、改進方向（含近期文獻）、實驗結果與結論 |
| `qkanfwp/daruan.py` | DARUAN / QKAN layer 的函數式實作（支援每個樣本各自的 fast 角度），與官方 `qkan` 套件數值一致 |
| `qkanfwp/models.py` | Gated fast-weight programmer（論文 Eq. 3–4）與本 repo 的擴充：residual 讀出（last value / last cycle）、差分 token、多時間尺度 gate、chrono 初始化、write-first；以及靜態的 HQKAN-Δ |
| `qkanfwp/data.py` | Bessel、Damped SHM、NARMA5/10、Delayed Quantum Control、Jaynes–Cummings、SILSO 太陽黑子 |
| `experiments/run_timeseries.py` | 一步預測 benchmark（論文 Sec. 6.1） |
| `experiments/run_solar.py` | 太陽黑子週期 direct multi-step 預測（論文 Sec. 6.2） |
| `experiments/reference_baselines.py` | 線性 AR 參考線（最小平方法，與神經模型相同的 train/test window） |
| `experiments/make_figures.py` | 由 `results/*.jsonl` 產生 `figures/`、`results/tables_final.md`、`results/tables_stage1.md` |
| `experiments/run_all.sh` | 重現所有數字的完整指令 |
| `results/` | 所有 run 的原始結果（JSON lines） |
| `tests/` | 單元測試（DARUAN 與官方 solver 等價、closed-form memory kernel 與逐步遞迴等價、有界性…） |

## 快速開始

```bash
pip install -r requirements.txt
python -m pytest tests -q

# 單一比較：baseline（論文協定 / 調過 lr）vs QKAN-FWP+ vs HQKAN-Δ，NARMA10、window 16、5 seeds
python experiments/run_timeseries.py --datasets narma10 --windows 16 \
    --variants base base@cos30 pmx_diff8_edge_h3l2@cos30 ar_hqkan8@cos30 --out results/quick.jsonl
python experiments/aggregate.py results/quick.jsonl

# 全部重現（約 15 CPU core-hours，可中斷續跑）
bash experiments/run_all.sh
```

Variant 名稱後的 `@cos30` 表示「cosine schedule、初始 lr = 30e-3」，`@lr3` 表示固定 lr = 3e-3；
不加則是論文的 lr（time-series 1e-3、solar 2.5e-3）。

## 資料來源

太陽黑子資料來自 WDC-SILSO（Royal Observatory of Belgium, Brussels），CC BY-NC 4.0，見 `data/README.md`。
