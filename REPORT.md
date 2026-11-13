# Gated QKAN-FWP：論文分析、改進方向與實驗驗證

對象論文：*Gated QKAN-FWP: Scalable Quantum-inspired Sequence Learning*（arXiv:2605.06734）。
本報告做三件事：(1) 整理論文機制與其限制；(2) 提出可降低 MSE 的改進方向，並對應近期文獻；
(3) 以重現的 baseline 為基準做實驗，驗證哪些改進有效、哪些無效。

> 所有數字皆由本 repo 的程式產生（`results/*.jsonl`），重現指令見第 8 節。

<<SUMMARY>>

---

## 1. 論文在做什麼

**機制。** Fast Weight Programmer（FWP）不用 hidden state，而是讓 *slow programmer* 每一步產生
*fast programmer* 的參數更新。論文把兩個 programmer 都換成 HQKAN（Linear → QKAN → Linear，QKAN 的
edge activation 是單一 qubit 的 data re-uploading 電路 DARUAN），並把更新規則從相加改成 scalar gate：

```
y_t        = F(x_t; W_t)                      # fast programmer
(ΔW_t, g_t) = S(x_t)                          # slow programmer，只看當下輸入
W_{t+1}    = g_t · W_t + (1 − g_t) · ΔW_t     # Eq. 3，g_t ∈ [0,1] 是純量
```

**理論。** 因為 `(ΔW_t, g_t)` 不依賴 `W_{t-1}`，遞迴可展開成
`W_{T} = β_0 W_1 + Σ_k β_k ΔW_k`，`β_k = (1−g_k) Π_{s>k} g_s`（adaptive memory kernel）；
`W` 永遠落在歷史 proposals 的 convex hull 內（有界）；可用 prefix scan 平行計算；時間方向的梯度只經過
純量 `β`，不會爆炸（但論文 App. B.4 自己指出可能 vanish）。

**實驗與主要數字。**

| 實驗 | 設定 | 論文中 GQKAN-QKANFWP 的數字 |
|---|---|---|
| 6 個 time-series benchmark（Bessel、Damped SHM、NARMA5/10、DQC、Jaynes–Cummings） | 一步預測，window N ∈ {8,16,32,64}，[-1,1] 正規化，80/20 split，50 epochs、batch 4、lr 1e-3、5 seeds，報 final test MSE | 約 1e-5 ~ 3e-4（Table 3–6），159 個參數 |
| 太陽黑子週期（主結果） | 528 個月 → 132 個月 direct multi-step，80/10/10，peak-aware loss，100 epochs、batch 32 | scaled MSE **0.0168 ± 0.0016**、PAE 39.59、PTE 21.89，12,474 個參數 |
| MiniGrid RL、IonQ/IBM 真機推論 | — | 本報告未涉及 |

---

## 2. 可以改進的地方（與對應的近期研究）

下表是讀完論文後整理出的弱點。「實測」欄標示本報告是否做了實驗。

| # | 論文的做法 | 問題 | 改進方向 | 相關文獻 | 實測 |
|---|---|---|---|---|---|
| A1 | 訓練固定 lr = 1e-3、50 epochs、無 schedule，報最後一個 epoch | 模型遠未收斂；Table 3–6 的 std 常與 mean 同量級，就是訓練不足＋最後一步雜訊 | 調 learning rate ＋ cosine decay（同樣 epoch 數） | — | ✅ |
| A2 | 讀出 `y = F(x_T; W_T)` 要自己合成絕對數值 | 一步預測的主成分就是「上一個值」，網路容量花在學 identity | Residual 讀出 `ŷ = x_T + F(x_T; W_T)` | NLinear/DLinear（2205.13504）、RevIN | ✅ |
| A3 | Slow/fast programmer 每一步只看到一個純量 `x_t` | Proposal 與 gate 是 *context-free*：同一個數值在上升段與下降段得到完全相同的 `ΔW_t`、`g_t`；斜率資訊只能靠 gate 的 EMA 間接編碼 | Token 化：把 `x_t` 換成因果 patch。本報告提出用**差分座標** `(x_t, Δx_t, Δ²x_t)`（離散的相空間座標，各階差分正規化到單位變異） | PatchTST（2211.14730）；Takens delay embedding | ✅ |
| B1 | 單一純量 gate | 所有 fast weights 共用同一個記憶時間尺度；一次強寫入會把所有舊記憶一起洗掉 | 分組（vector）gate：每個 DARUAN 電路/每層一個 gate → 多時間尺度記憶；Eq. 4、有界性、平行 scan 逐組仍成立 | RWKV-7 vector-valued gating（2503.14456）、Mamba selective per-channel decay（2312.00752）、xLSTM（2405.04517）、HGRN（2311.04823） | ✅ |
| B2 | Gate 用預設初始化（g ≈ 0.5） | 初始記憶長度只有 ~2 步：`β_k ≈ 2^{-(T-k)}`，N=64 或 528 時早期輸入的梯度一開始就消失 | Chrono initialization：把 gate bias 設成對數等距的時間尺度 τ ∈ [2, N]，`g = 1 − 1/τ` | Tallec & Ollivier（1804.11188）、UR-LSTM（1910.09890）、LRU（2303.06349） | ✅ |
| B3 | 寫入與遺忘綁在一起（convex combination）；`β_k` 對年齡單調遞減 | 無法「只改寫某個 key 對應的內容」；無法選擇性記住特定 lag | Delta rule / 解耦的 erase key；momentum（二階）記憶；複數（旋轉）gate | Gated DeltaNet（2412.06464）、RWKV-7、DeltaProduct（2502.10297）、Titans（2501.00663）、Fast Weight Attention（2608.27763）、test-time regression（2501.12352） | ❌（第 7 節討論） |
| B4 | `ΔW_t` 與 fast network 的預測誤差無關 | 沒有「surprise」訊號；fast weights 不會因為預測錯了而更新更多 | 把上一步的預測誤差回饋給 slow programmer（recurrent FWP；會失去平行性） | Recurrent FWP（2106.06295）、Titans、MesaNet（2506.05233） | ❌ |
| C1 | 只有最後一步有 loss | 每個 window 只有一個監督訊號 | 每個 prefix 都算 loss（dense supervision） | — | ❌ |
| C2 | Slow decoder 直接輸出所有 fast weights | 太陽黑子模型 12.5k 參數中約 8.8k 在這個線性層 | Low-rank / outer-product / chunked hypernetwork | QFWP 的 `L ⊗ Q`（2402.17760） | ❌ |
| D1 | Sec. 6.1 沒有 classical baseline、沒有列出各層大小 | 無法判斷 benchmark 是否真的需要記憶機制；難以重現 | 加入同參數量的 LSTM 與「無記憶」對照組 | — | ✅ |

FWP 文獻整體脈絡可參考 Irie 的 review（2508.08435）與「Linear Transformers Are Secretly FWPs」
（2102.11174）：論文的 gated update 其實就是對 proposal 做 delta-rule
`W ← W + (1−g)(ΔW − W)`，而近兩年線性 RNN / state-space 模型的進展（Gated DeltaNet、RWKV-7、Mamba、
xLSTM）幾乎都集中在「更新規則的 gate 怎麼設計、怎麼初始化」——正是 B1–B3。

---

## 3. 實驗設定

### 3.1 重現 baseline

論文沒有公開 FWP 的程式，只說 QKAN 來自 [`qkan`](https://github.com/Jim137/qkan) 套件，所以本 repo 重新實作：

- **DARUAN / QKAN layer**（`qkanfwp/daruan.py`）：fast programmer 需要「每個樣本各自一組角度」，官方套件
  只支援共享參數，因此寫成 `(x, θ)` 的純函數。`tests/test_daruan.py` 驗證與官方 `torch_exact_solver`
  （`pz_encoding` ansatz）數值一致。
- **Gated FWP**（`qkanfwp/models.py`）：照論文 Eq. 3，先讀後寫（`y_T = F(x_T; W_T)`，`W_T` 只依賴
  `x_1..x_{T-1}`）。用 Eq. 4 的 closed form 在 log 空間計算 `β_k`，並測試與逐步遞迴等價。
- **層的大小論文沒有列出**，只有總參數量。我在 validation split 上比較了 5 種 ~160 參數的配置
  （`results/dev_baseline_arch.jsonl`），選最強的當 baseline，避免拿弱 baseline 當稻草人：

  | Benchmark | Slow HQKAN | Fast HQKAN | 參數量（論文） |
  |---|---|---|---|
  | Time-series | 1 → 3 → 3，reps 3 | 1 → 2 → 1，reps 3（16 個 fast 角度） | 152（159） |
  | Solar | 1 → 10 → 10，reps 3 | 1 → 10 → 20，reps 1（200 個 DARUAN 電路＝論文的數量，800 個 fast 角度）→ 132 | 12,423（12,474） |

  （一開始試的 1→6→3 / 1→2→2、reps 1 配置剛好是 159 個參數，但 validation MSE 是上表配置的 3.6 倍。）
- **資料**（`qkanfwp/data.py`）：方程式與參數照論文。論文沒寫 Bessel / SHM / DQC 的取樣點數，這裡統一用
  300 點（NARMA 的 M = 300 是論文給的；JC 3000 點也是）。因此 **time-series 的 MSE 絕對值不能直接和論文
  Table 3–6 比**，只能比同一份資料上的相對差異。太陽黑子用的是同一份 SILSO V2.0 月資料前 3,326 筆，
  絕對值可以和論文 Table 7 比。

### 3.2 兩種訓練協定

- **Paper protocol**：完全照論文（time-series：Adam、lr 1e-3、50 epochs、batch 4、報最後一個 epoch 的
  test MSE；solar：lr 2.5e-3、100 epochs、batch 32、取 validation loss 最低的 checkpoint）。
- **Tuned protocol**（只用在 time-series）：同樣 50 epochs、batch 4，但 lr 用 cosine decay 到 0，初始 lr
  由 validation 選（{1, 3, 10, 30, 100}×1e-3）。**Baseline 與改進模型各自選最好的 lr**，確保比較公平。

### 3.3 避免在 test set 上挑模型

所有設計決定（baseline 配置、要不要某個改進、lr）都只用 **dev protocol**：70/10/20 split 的 validation
部分、seeds 100–102。最終數字用論文的 80/20 split、**seeds 0–4**，這些 run 沒有參與任何決定。
Solar 照論文本來就有 validation split；pilot 用 seeds 100–101，最終用 seeds 0–4。

<<RESULTS>>
