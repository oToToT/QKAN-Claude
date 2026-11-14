# QKAN-Claude

[*Gated QKAN-FWP: Scalable Quantum-inspired Sequence Learning*](https://arxiv.org/abs/2605.06734)（arXiv:2605.06734）的
獨立重新實作、分析與改進。**完整的分析與所有結果在 [`REPORT.md`](REPORT.md)。**

論文把 fast-weight programmer 的 slow／fast 兩個網路都換成 QKAN（edge activation 是單 qubit 的 data re-uploading 電路），
並用 scalar gate 更新 fast weights。這個 repo 包含：

- 論文模型（GQKAN-QKANFWP 與另外兩個 QKAN 變體）以及後續論文的 CMG gate（arXiv:2607.27945）的重新實作；
- 三個 QKAN-based、參數量不超過論文（159）的模型：

  | 模型 | 是什麼 | 參數量 |
  |---|---|---|
  | **QKAN-FWP+** | 論文的 gated fast-weight 架構 ＋ 差分 token ＋ residual 讀出 ＋ 每個電路一個 gate | 149 |
  | **HQKAN-Δ** | 同樣的 token 與讀出，但沒有 fast weights 的靜態網路（對照組） | 136 |
  | **QKAN-FWP-O** | Fast weights 是電路的**量測算符**而不是旋轉角；QKAN 對量測算符是線性的，所以 context 可以用 gated 最小平方以封閉形式寫入 | 130–154 |

- 對 benchmark 的檢查：線性 AR 參考線、與論文印出數字的可比性、實作選擇與有限量測次數的影響。

## 主要結果

![paper benchmarks](figures/om_timeseries.png)

論文的六個一步預測 benchmark（test MSE，對 window N ∈ {8, 16, 32, 64} 取幾何平均，5 seeds，同一份資料與同一個 pipeline）：

| 資料集 | 兩篇論文印出的最佳數字 | 重新實作的 GQKAN-QKANFWP（調過 lr） | QKAN-FWP+ | HQKAN-Δ | **QKAN-FWP-O** | 線性 AR(8)（9 參數，最小平方） |
|---|---|---|---|---|---|---|
| Bessel J2 | 5.3e-06 | 4.5e-06 | 1.5e-06 | 1.4e-07 | **2.8e-12** | 5.3e-24 |
| Damped SHM | 8.8e-06 | 1.2e-05 | 1.9e-06 | 3.2e-07 | **5.9e-12** | 9.0e-14 |
| NARMA5 | 6.5e-06 | 2.3e-04 | 6.0e-06 | 2.9e-06 | **4.0e-07** | 1.3e-06 |
| NARMA10 | 9.5e-06 | 6.9e-04 | 8.1e-06 | 2.7e-06 | **3.2e-07** | 1.7e-06 |
| Delayed quantum control | 5.5e-06 | 4.4e-04 | 8.0e-06 | 3.5e-06 | **2.2e-08** | 2.6e-07 |
| Jaynes–Cummings | 7.6e-06 | 1.7e-05 | 7.4e-09 | 1.7e-09 | **4.7e-13** | 1.1e-31 |

- **QKAN-FWP-O 在 24 格中的 23 格是所有訓練出來的模型裡最低的**，幾何平均比 HQKAN-Δ 低約 700 倍、比 QKAN-FWP+ 與 CMG 低三個數量級以上、
  比調過 learning rate 的 GQKAN-QKANFWP 低五個數量級。在五個 300 點序列上，拿掉 fast weights 差一到四個數量級：收益來自閉迴路的記憶。
- 論文型態的記憶（由 slow programmer 產生旋轉角）在這些 benchmark 上沒有幫助：沒有 fast weights 的 HQKAN-Δ 在每一格都比
  QKAN-FWP+ 好，也比給了相同 token 的 CMG 好。
- 在「每條序列物理參數都不同」的系統族上（模型必須從 16 步的視窗辨識系統；`qkanfwp/families.py`），QKAN-FWP-O 在 10 格中的
  9 格比其他架構（GQKAN-QKANFWP、CMG、QKAN-FWP+、HQKAN-Δ、LSTM）低：沒有雜訊時低 15 倍到 2 萬倍，有雜訊時低 1.1–2.3 倍；
  在非線性的 Hénon map 上比線性參考線低 30–1300 倍。
- 太陽黑子週期預測：QKAN-FWP-O 的參數化以約 500 個參數（論文模型的 4%）在三種資料切分上都得到比重新實作的 baseline 低 19–25% 的 MSE
  （這個收益來自精簡的參數化，不是記憶）。

## 解讀時要注意

- **六個 benchmark 幾乎是線性問題**：9 個參數的線性 AR(8)（最小平方，不需要訓練）在 24 格中的 21 格贏過兩篇論文印出的最佳數字；
  QKAN-FWP-O 只在 NARMA 與 DQC 的 11 格低於它。QKAN-FWP-O 對其他神經模型的差距，主要是「在 context 內直接解最小平方」
  對「用 SGD 逼近線性映射」的差距。
- **起作用的是閉迴路的記憶，不是量子電路**：把 Bloch 特徵換成同樣數目的古典 tanh 特徵、記憶與求解完全不變，結果沒有差別；
  float32 與 float64 也沒有差別。非線性系統需要某種非線性特徵（只留線性項在 Hénon map 上差 22–1164 倍），但 Bloch 向量沒有比
  古典特徵更好的歸納偏置。模型可以古典模擬，不主張量子優勢；對 QKAN-FWP 的意義是 fast weights 應該放在讀出為線性的量測算符空間。
- **沒有重現論文印出的 baseline 數字**（論文協定下差 21 倍，調過 learning rate 後差 1.9 倍），所以倍數都是同一個 pipeline 內的比較。
- In-context 最小平方本身是既有方法（ALPaCA、mesa-layer、delta rule）；這裡的貢獻是把它接到 QKAN-FWP 上並保留論文 gated 遞迴的封閉形式。
- **有限量測次數**只做了統計雜訊的模擬（REPORT 第 7 節）：以精確期望值訓練的 QKAN-FWP-O 對量測雜訊很敏感，訓練時加入量測雜訊可以修正；
  在需要量子特徵的 Hénon map 上，每個電路約 10⁴ 次量測以上才優於靜態模型。
- 太陽黑子的峰值指標沒有模型穩定贏過「重複上一個週期」。
- 沒有做：MiniGrid 強化學習、真機實驗、以多 qubit VQC 為 fast programmer 的模型。

## 內容

| 路徑 | 說明 |
|---|---|
| `REPORT.md` | 論文機制、相關研究、模型、實驗設定、所有結果與限制 |
| `qkanfwp/daruan.py` | DARUAN / QKAN layer 的函數式實作（支援每個樣本各自的角度、Bloch vector 輸出、有限量測次數模擬），與官方 `qkan` 套件數值一致 |
| `qkanfwp/models.py` | Gated fast-weight programmer（論文 Eq. 3–4；scalar／分組／CMG gate）、差分 token、residual 讀出、HQKAN-Δ、LSTM 對照 |
| `qkanfwp/obsmem.py` | QKAN-FWP-O：以量測算符為 fast weights 的閉迴路記憶（一步與 direct multi-step） |
| `qkanfwp/data.py`, `qkanfwp/families.py` | 論文的資料集；參數逐序列隨機的系統族 |
| `experiments/run_timeseries.py` | 一步預測 benchmark（論文 Sec. 6.1） |
| `experiments/run_family.py` | 系統族上的 in-context 預測與封閉形式的參考線 |
| `experiments/run_solar.py` | 太陽黑子週期 direct multi-step 預測（論文 Sec. 6.2） |
| `experiments/shot_noise.py` | 有限量測次數的敏感度 |
| `experiments/memory_probe.py` | QKAN-FWP-O 學到的記憶權重（每個 context 配對的權重） |
| `experiments/reference_baselines.py` | 線性 AR 參考線 |
| `experiments/make_figures.py`, `experiments/make_om_report.py` | 由 `results/*.jsonl` 產生表格與 `figures/` |
| `experiments/report/` | `REPORT.md` 的文字來源與組裝程式 |
| `experiments/run_all.sh` | 重現所有數字的完整指令 |
| `results/` | 所有 run 的原始結果（說明見 `results/README.md`） |
| `tests/` | 單元測試 |

## 快速開始

```bash
pip install -r requirements.txt
python -m pytest tests -q

# NARMA10、window 16、5 seeds：論文協定的 baseline、調過 lr 的 baseline、HQKAN-Δ、QKAN-FWP-O
python experiments/run_timeseries.py --datasets narma10 --windows 16 \
    --variants base base@cos30 ar_hqkan8@cos30 om_c0h6r1_p5@cos30 --out results/quick.jsonl
python experiments/aggregate.py results/quick.jsonl

# 全部重現（約 25 CPU core-hours，可中斷續跑）
bash experiments/run_all.sh
```

Variant 名稱後的 `@cos30` 表示 cosine schedule、初始 learning rate 30e-3；不加則是論文的設定（1e-3、固定）。

## 資料來源

太陽黑子資料來自 WDC-SILSO（Royal Observatory of Belgium, Brussels），CC BY-NC 4.0，見 `data/README.md`。
