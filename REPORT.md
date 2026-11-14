# Gated QKAN-FWP：重現、分析與改進

對象論文：*Gated QKAN-FWP: Scalable Quantum-inspired Sequence Learning*（arXiv:2605.06734）。

這份報告包含：

1. 論文機制的整理，以及一份獨立的重新實作（論文沒有公開 fast-weight programmer 的程式）；
2. 兩個在輸入表徵與讀出上改進的模型：**QKAN-FWP+**（保留論文的 gated fast-weight 架構）與 **HQKAN-Δ**（沒有 fast weights 的對照組）；
3. 一個新的架構 **QKAN-FWP-O**：把 fast weights 從「電路的旋轉角」換成「電路的量測算符」，讓記憶可以用 context 內的預測誤差
   以封閉形式寫入；
4. 隔離收益來源的對照：同一個記憶換成古典特徵（Fourier、tanh、二次多項式、小型 MLP）、同樣的特徵換成別的記憶規則
   （RLS、delta rule、不用 gate）、以及參數量相當的靜態模型；
5. 這個架構放上量子硬體的代價與性質：電路執行次數與古典成本、有限量測次數、由 context 決定的量測基底，
   以及對靜態硬體誤差的 in-context 校正（都是模擬）；
6. 對 benchmark 本身的檢查：線性參考線、與論文印出數字的可比性、資料切分與幾個實作選擇的影響。

所有模型都是 QKAN-based，參數量不超過論文的 159 個（太陽黑子：不超過 12,474 個）。
所有數字皆由本 repo 的程式產生（`results/*.jsonl`），重現方式見第 11 節。

## 摘要

### 模型

| 模型 | 是什麼 | 參數量（論文的 GQKAN-QKANFWP：159） |
|---|---|---|
| 重新實作的 GQKAN-QKANFWP、CMG | Baseline：論文的 scalar gate，以及後續論文的逐座標互補 gate（arXiv:2607.27945） | 152、188 |
| **QKAN-FWP+** | 論文的 gated fast-weight 架構 ＋ Δ-token ＋ residual 讀出 ＋ 每個電路一個 gate | 149 |
| **HQKAN-Δ** | 同樣的 token 與讀出，但沒有 fast weights 的靜態 HQKAN（對照組） | 136 |
| **QKAN-FWP-O** | Fast weights 是 DARUAN 電路的**量測算符**；context 以 gated 最小平方寫入（閉迴路），封閉形式沿用論文的 gated 遞迴 | 130–154 |

### 主要結果

論文的六個 benchmark（test MSE，對四個 window 取幾何平均，5 seeds）：

| Dataset | Best printed in the two papers | GQKAN-QKANFWP, tuned lr (152) | CMG, tuned lr (188) | CMG + Δ-tokens + residual, tuned lr (173) | QKAN-FWP+ (149) | HQKAN-Δ (136) | QKAN-FWP-O (130–154) | *Linear AR(8) (9)* |
|---|---|---|---|---|---|---|---|---|
| Bessel J2 | 5.3e-06 | 4.5e-06 | 2.7e-06 | 8.6e-07 | 1.5e-06 | 1.4e-07 | **2.8e-12** | *8.4e-17* |
| Damped SHM | 8.8e-06 | 1.2e-05 | 2.5e-06 | 7.7e-07 | 1.9e-06 | 3.2e-07 | **5.9e-12** | *9.0e-14* |
| NARMA5 | 6.5e-06 | 2.3e-04 | 2.8e-04 | 5.4e-06 | 6.0e-06 | 2.9e-06 | **4.0e-07** | *1.3e-06* |
| NARMA10 | 9.5e-06 | 6.9e-04 | 7.6e-04 | 6.3e-06 | 8.1e-06 | 2.7e-06 | **3.2e-07** | *1.7e-06* |
| Delayed quantum control | 5.5e-06 | 4.4e-04 | 7.5e-04 | 4.4e-06 | 8.0e-06 | 3.5e-06 | **2.2e-08** | *2.6e-07* |
| Jaynes–Cummings | 7.6e-06 | 1.7e-05 | 6.5e-06 | 1.5e-09 | 7.4e-09 | 1.7e-09 | **4.7e-13** | *2.4e-16* |

1. **在 QKAN-based 的架構之間，閉迴路的量測算符記憶明顯較準。**
   - 論文的 benchmark（24 格）：QKAN-FWP-O 在全部 24 格低於重新實作的 GQKAN-QKANFWP、CMG 與 QKAN-FWP+；對沒有記憶的 HQKAN-Δ 是
     23 格較低、NARMA5 的 N = 8 那一格輸。差距依資料集而定：對 HQKAN-Δ，NARMA 低 7–9 倍，DQC 低約 160 倍，
     Bessel 與 Damped SHM 低四到五個數量級（5.1 節）。
   - 每條序列物理參數都不同的系統族（10 格，模型必須從 16 步的視窗辨識系統）：QKAN-FWP-O 在 9 格比其他架構
     （GQKAN-QKANFWP、CMG、QKAN-FWP+、HQKAN-Δ、LSTM）低、1 格打平；沒有雜訊時低 15 倍到約 2 萬倍，有雜訊時低 1.1–2.3 倍（第 6 節）。
2. **收益來自閉迴路的記憶，不是特徵映射**（隔離對照；5.4、6.2、6.3 節）。
   - *同一個記憶換特徵。* reps = 1 的 Bloch 特徵恰好是一次諧波的 Fourier 特徵。把它換成同函數空間的 $\cos u, \sin u$、tanh、
     二次多項式或小型 MLP 而先驗、gate 與求解完全不變：論文 benchmark 上全部在 ±20% 之內；系統族上 Fourier 與 tanh 相同（1.0–1.2 倍），
     **小型 MLP 好 2.1 倍**，二次多項式整體差 1.7 倍、但在函數形式吻合的 Hénon map 上好 9 倍。
   - *同樣的特徵換記憶。* 參數量相當的靜態模型差 164 倍（論文 benchmark 的五個 300 點序列）與 23 倍（系統族），所以差距不是參數量造成的；
     normalised delta rule 差 59–62 倍與 4.6–7.4 倍；先驗只當初始值的 RLS 還略好（0.54 倍與 0.71 倍，但 NARMA 較差）；
     不用 gate 差 1.5–1.7 倍。
3. **把 fast weights 放在量測算符，對量子 FWP 帶來的可驗證性質**（3.3 節、第 7 節；硬體相關的部分都是模擬）：
   - *封閉形式的閉迴路寫入*：QKAN 層對量測算符是線性的，最佳寫入是加權最小平方，充分統計量服從論文的 gated 遞迴
     （Eq. 4、凸包、prefix scan 都保留；單元測試驗證）。
   - *電路與記憶無關*：所有 token 跑同一組固定電路，不需要逐次載入 fast 角度；多輸出不增加電路（太陽黑子 6 個電路，論文規模的模型 300 個）。
     代價是每個電路要量三個基底、每個視窗 350 個數字的古典狀態與一次 25×25 的求解；一步預測的量子成本並不比角度空間的模型低。
   - *Query 的量測基底由 context 決定*：fast weights 在硬體上就是 query 電路的量測軸，一個設定取代三個；
     query 讀出的 shot 變異數有封閉形式，量測前就能算（7.3 節）。
   - *對靜態硬體誤差的 in-context 校正*：模型用理想電路訓練、測試時加入誤差而不重新訓練，1% 的讀出誤差下 QKAN-FWP-O 的 MSE 不變、
     5% 時是 1.6 倍；HQKAN-Δ 與 QKAN-FWP+ 是 13–20 倍與約 190–290 倍。把同一個誤差只放在 query 的電路，Bessel 差 8 萬倍——
     誤差是因為同時出現在 context 與 query 才被最小平方吸收（7.4 節）。
4. **論文型態的記憶（由 slow programmer 產生旋轉角）在這些 benchmark 上沒有幫助**：沒有 fast weights 的 HQKAN-Δ
   在每一格都比 QKAN-FWP+ 好（15 個 seed 合計 2.5 倍），也在 24 格中的 21 格比給了相同 token 的 CMG 好。有用的是記憶的型態，不是有沒有記憶。
5. **太陽黑子**（第 8 節）：論文對 sliding window 的索引做切分，相鄰 split 的 targets 重疊 131 個月。改成依 target 時間切分之後，
   沒有模型穩定贏過零參數的「重複上一個週期」；QKAN-FWP-O 的靜態版本以 496 個參數（論文模型的 4%）在三種切分上都比重新實作的
   baseline 低（7–28%），有記憶的版本則比靜態版本差。

### 解讀這些數字時必須知道的事

1. **不主張量子優勢，特徵映射也不是貢獻。** 整個模型可以古典模擬；同一個記憶配上古典特徵一樣好或更好，而且不需要量測。
   QKAN 的表述帶來的是結果 3 的那些性質——它們回答的是「一個要在量子硬體上執行的 FWP，fast weights 該放在哪裡、代價是什麼」。
2. **六個 benchmark 幾乎是線性問題。** 一個 9 參數的線性 AR(8)（最小平方，不需要訓練）在 24 格中的 21 格贏過兩篇論文印出的
   最佳數字；對 QKAN-FWP-O 是 13 格較低、11 格較高（NARMA 與 DQC）（5.2 節）。QKAN-FWP-O 對其他神經模型的差距，
   主要是「在 context 內直接解最小平方」對「用 SGD 逼近線性映射」的差距。
3. **數值精度。** 所有模型與參考線都以 float32 的 targets 評分；低於 $10^{-15}$ 的 MSE 是 targets 的捨入誤差，計算倍數時先截在那裡。
   QKAN-FWP-O 內部改用 float32 幾乎沒有差別（1.2 倍與 1.0 倍）。
4. **NARMA 照論文的定義**：讀 $y$ 的歷史、預測下一個 $y$；不是 reservoir computing 文獻裡「讀 $u$ 預測 $y$」的任務（第 4、10 節）。
5. **沒有重現論文印出的 baseline 數字。** 重新實作的 GQKAN-QKANFWP 在論文協定下比論文印出的數字差 21 倍（幾何平均），
   調過 lr 後差 1.9 倍；原因沒有找到（5.3 節）。所有「低幾倍」的結論都是同一個 pipeline 內的比較。
6. **In-context 最小平方不是新方法**（ALPaCA、R2D2、mesa-layer、delta rule）。新的部分是把它接到量子 FWP 上：
   指出 QKAN 層對量測算符是線性的，以及由此得到的硬體性質（3.3 節）。
7. **有限量測次數**（7.1 節，只有模擬）：以精確期望值訓練的 QKAN-FWP-O 對量測雜訊很敏感；訓練時就加入量測雜訊可以修正，
   但在接近線性的任務上它靠的是古典計算、沒有量測雜訊的線性項。在需要非線性特徵的 Hénon map 上，每個電路每個輸入約 $10^4$ 次
   量測以上才優於靜態的 HQKAN-Δ，$10^2$ 次時反而較差。

沒有做的部分（「讀 $u$ 預測 $y$」的 NARMA、MiniGrid RL、真機實驗、以多 qubit VQC 為 fast programmer 的模型）列在第 10 節。

---

## 1. 論文在做什麼

**機制。** Fast Weight Programmer（FWP）不用 hidden state，而是讓 *slow programmer* 每一步產生
*fast programmer* 的參數更新。論文把兩個 programmer 都換成 HQKAN（Linear → QKAN → Linear，QKAN 的
edge activation 是單一 qubit 的 data re-uploading 電路 DARUAN），並把更新規則從相加改成 scalar gate：

```
y_t         = F(x_t; W_t)                      # fast programmer
(ΔW_t, g_t) = S(x_t)                           # slow programmer，只看當下輸入
W_{t+1}     = g_t · W_t + (1 − g_t) · ΔW_t     # Eq. 3，g_t ∈ [0,1] 是純量
```

**理論。** 因為 `(ΔW_t, g_t)` 不依賴 `W_{t-1}`，遞迴可展開成
`W_T = β_0 W_1 + Σ_k β_k ΔW_k`，`β_k = (1−g_k) Π_{s>k} g_s`（adaptive memory kernel）；
`W` 永遠落在歷史 proposals 的 convex hull 內（有界）；可用 prefix scan 平行計算；時間方向的梯度只經過
純量 `β`，不會爆炸（但論文 App. B.4 自己指出可能 vanish）。

**實驗與主要數字。**

| 實驗 | 設定 | 論文中 GQKAN-QKANFWP 的數字 |
|---|---|---|
| 6 個 time-series benchmark（Bessel、Damped SHM、NARMA5/10、DQC、Jaynes–Cummings） | 一步預測，window N ∈ {8,16,32,64}，[-1,1] 正規化，80/20 split，50 epochs、batch 4、lr 1e-3、5 seeds，報 final test MSE | 約 1e-5 ~ 3e-4（Table 3–6），159 個參數 |
| 太陽黑子週期（主結果） | 528 個月 → 132 個月 direct multi-step，80/10/10，peak-aware loss，100 epochs、batch 32 | scaled MSE **0.0168 ± 0.0016**、PAE 39.59、PTE 21.89，12,474 個參數 |
| MiniGrid RL、IonQ/IBM 真機推論 | — | 本報告未涉及 |

**同一團隊的後續工作**都在改更新規則：Self-Modulating QFWP（arXiv:2606.24933，對新寫入與舊記憶做逐元素調變）、
它的有界版本（arXiv:2607.02363，對舊記憶分支加 tanh），以及 Complementary Matrix-Gated QKAN-FWP
（**CMG**，arXiv:2607.27945）：把 scalar gate 換成逐座標的互補 gate `Θ_t = G_t⊙Θ_{t−1} + (1−G_t)⊙Δ_t`，
`G_t = σ(m^P (m^Q)^⊤)` 由兩個 head 的外積產生；逐座標仍有凸組合有界與 affine prefix scan。
本報告把 CMG 也重新實作並當作 baseline（3.1 節）。

---

## 2. 論文的弱點與對應的研究

「對應」欄標示本報告用哪個模型或實驗處理了這一點。

| # | 論文的做法 | 問題 | 改進方向 | 相關文獻 | 對應 |
|---|---|---|---|---|---|
| A1 | 訓練固定 lr = 1e-3、50 epochs、無 schedule，報最後一個 epoch | 在本報告的實作中模型遠未收斂；Table 3–6 的 std 常與 mean 同量級 | 調 learning rate ＋ cosine decay（同樣 epoch 數） | — | 所有模型（4.2 節） |
| A2 | 讀出 `y = F(x_T; W_T)` 要自己合成絕對數值 | 一步預測的主成分就是「上一個值」，網路容量花在學 identity | Residual 讀出 `ŷ = x_T + F(·)` | NLinear/DLinear（2205.13504）、RevIN | QKAN-FWP+、HQKAN-Δ、QKAN-FWP-O |
| A3 | 每一步只看到一個純量 `x_t` | Proposal 與 gate 是 *context-free*：同一個數值在上升段與下降段得到完全相同的 `ΔW_t`、`g_t` | 把 `x_t` 換成因果 patch，並用**差分座標** `(x_t, Δx_t, Δ²x_t, …)`（各階差分正規化到單位變異） | PatchTST（2211.14730）；Takens delay embedding | 同上 |
| B1 | 單一純量 gate | 所有 fast weights 共用同一個記憶時間尺度 | 分組／逐座標 gate | **CMG（2607.27945）**；RWKV-7（2503.14456）、Mamba（2312.00752）、xLSTM（2405.04517）、HGRN（2311.04823） | QKAN-FWP+（每個電路一個 gate）；CMG baseline |
| B2 | Gate 用預設初始化（g ≈ 0.5） | 初始記憶長度只有約 2 步，N 大時早期輸入的梯度一開始就消失 | Chrono initialization：gate bias 設成對數等距的時間尺度 | Tallec & Ollivier（1804.11188）、UR-LSTM（1910.09890）、LRU（2303.06349） | QKAN-FWP+、QKAN-FWP-O |
| B3 | 更新是實數、逐元素的 `Θ_t = A_t⊙Θ_{t−1} + B_t`，`A_t ≥ 0` | 每個座標是一條以 gate 為係數的仿射遞迴：後面的 token 只能逐座標地縮小先前寫入的內容，不能改變它的符號、把座標互相混合，或產生振盪的記憶核（適用範圍見 2.1 節） | 複數／旋轉／非交換的轉移 | Grazzi et al.（ICLR 2025）、DeltaProduct（2502.10297）、AUSSM、HyperSSM（2611.17162） | 未實作，理由見 2.1 節 |
| B4 | `ΔW_t`、`g_t` 與 fast network 的預測誤差無關（**開迴路**） | 記憶是「每個 token 各猜一次再加權平均」；預測從未和下一個觀測值比較 | 誤差驅動的寫入：delta rule、in-context 最小平方 | Schlag et al.（2102.11174）、DeltaNet（2406.06484）、Titans（2501.00663）、MesaNet（2506.05233）、ALPaCA（1807.08912） | **QKAN-FWP-O**（3.3 節） |
| C1 | 只有最後一步有 loss | 每個 window 只有一個監督訊號 | Context 內每一步都是一個監督配對 | — | QKAN-FWP-O（配對用在寫入，不是 loss） |
| C2 | Slow decoder 直接輸出所有 fast weights | 太陽黑子模型 12.5k 參數中約 8.8k 在這個線性層 | Low-rank／outer-product hypernetwork；或讓 fast weights 不需要由網路產生 | QFWP 的 `L ⊗ Q`（2402.17760） | QKAN-FWP-O（太陽黑子約 500 個參數） |
| D1 | Sec. 6.1 沒有 classical baseline、沒有列出各層大小 | 無法判斷 benchmark 是否真的需要記憶機制 | 加入無記憶的對照組、同參數量的 LSTM、線性 AR | — | HQKAN-Δ、LSTM、線性 AR（5.2 節） |

### 2.1 一個考慮過但沒有實作的方向：旋轉（SU(2)）gate

原論文、Self-Modulating 與 CMG 的 `A_t` 都是實數、逐元素的。這**不表示**這些模型分不出順序：仿射遞迴本身對順序敏感
（$h \leftarrow 0.5h + 0.5x$ 從 0 開始，輸入 $[1,2]$ 得 1.25，輸入 $[2,1]$ 得 1），gate 也讓越新的寫入權重越大。
限制比較窄，來自齊次部分 $\prod_t A_t$：

- 它是逐座標的實數乘積，彼此可交換。在 state-tracking 的設定下——沒有輸入項、要靠轉移本身把一串群運算累積起來
  （$\Theta_T = A_T\cdots A_1\Theta_0$）——這樣的模型只能表示交換群；$A_t \ge 0$ 時連 parity 都不行（Grazzi et al.）。
- 記憶核 $\beta_k$ 逐座標非負：第 $k$ 步寫入的內容之後只會被縮小，不會被旋轉或變號。

fast programmer 的每個電路本來就是 SU(2) 的元素，所以最自然的推廣是讓 gate 也是旋轉（單位四元數）：
$q_t = g_t\,p_t \otimes q_{t-1} + (1-g_t)\,d_t$，CMG 是 $p_t = 1$ 的特例，有界性與 prefix scan 都還在。
這個方向在線性遞迴模型的文獻裡已經被完整處理：

| 文獻 | 內容 |
|---|---|
| Grazzi et al., ICLR 2025 | 對角線性 RNN 做 parity 需要負的特徵值，mod-m 計數需要複數特徵值 |
| arXiv:2508.07395、AUSSM、arXiv:2605.07755、CSP（2608.03425）、Selective RoPE（2511.17388） | 輸入相依的複數／單位模轉移；旋轉與衰減都需要 |
| HyperSSM（arXiv:2611.17162） | 每個通道是結合代數（ℝ、ℂ、ℍ）上的 affine 遞迴 $x_k = a(u_k)x_{k-1} + \bar B(u_k)u_k$；證明能追蹤非交換群的最小通道是四元數；實驗包含「一串 qubit gate 之後的 Bloch vector」 |

也就是說，四元數 gate（衰減＋旋轉＋輸入項＋prefix scan）在 QFWP 上雖然沒有人做，但只是把既有結果搬過來；
而且一步預測並不需要非交換的記憶。本報告因此沒有實作它，而是處理另一個缺口 B4。

---

## 3. 模型

### 3.1 重新實作的 baseline 與 CMG

論文沒有公開 FWP 的程式，只說 QKAN 來自 [`qkan`](https://github.com/Jim137/qkan) 套件，所以本 repo 重新實作：

- **DARUAN / QKAN layer**（`qkanfwp/daruan.py`）：fast programmer 需要「每個樣本各自一組角度」，官方套件
  只支援共享參數，因此寫成 `(x, θ)` 的純函數。`tests/test_daruan.py` 驗證與官方 `torch_exact_solver`
  （`pz_encoding` ansatz）數值一致。
- **Gated FWP**（`qkanfwp/models.py`）：照論文 Eq. 3，先讀後寫（`y_T = F(x_T; W_T)`，`W_T` 只依賴
  `x_1..x_{T-1}`）。用 Eq. 4 的 closed form 在 log 空間計算 `β_k`，並測試與逐步遞迴等價。
- **層的大小論文沒有列出**，只有總參數量。這裡在 validation split 上比較了 5 種約 160 參數的配置
  （`results/dev_baseline_arch.jsonl`），選最強的當 baseline：

  | Benchmark | Slow HQKAN | Fast HQKAN | 參數量（論文） |
  |---|---|---|---|
  | Time-series | 1 → 3 → 3，reps 3 | 1 → 2 → 1，reps 3（16 個 fast 角度） | 152（159） |
  | 太陽黑子 | 1 → 10 → 10，reps 3 | 1 → 10 → 20，reps 1（200 個 DARUAN 電路＝論文的數量，800 個 fast 角度）→ 132 | 12,423（12,474） |

  （1→6→3 / 1→2→2、reps 1 的配置剛好是 159 個參數，但 validation MSE 是上表配置的 3.6 倍。）
- **論文的另外兩個 QKAN 變體**：GQKAN-FWP（HQKAN slow、線性 fast，114 參數）與 G-QKANFWP（MLP slow、HQKAN fast，175 參數）。
  以多 qubit VQC 為 fast programmer 的三個模型（QFWP、G-QFWP、GQKAN-QFWP）沒有重新實作。
- **CMG**（`gate='cmg'`）：fast 角度排成 $P\times Q$（電路數 × 每個電路的角度數），slow programmer 多輸出
  $m^P\in\mathbb R^P$、$m^Q\in\mathbb R^Q$，逐權重的 gate 是 $\sigma(m^P_p m^Q_q)$；依 CMG 論文的敘述採先寫後讀。
  同樣的 baseline 配置下是 188 個參數。另外也跑一個給了 Δ-token 與 residual 讀出的版本（173 參數），
  作為 CMG 在本報告設定下最強的形式。

### 3.2 QKAN-FWP+ 與 HQKAN-Δ：改輸入表徵與讀出

兩個模型共用三樣東西：

- **Δ-token**：每一步的輸入不是純量 `x_t`，而是 `(x_t, Δx_t, Δ²x_t, …, Δ⁷x_t)`（最近 8 個值的 backward
  differences），各階差分除以它在訓練集上的標準差。
- **Residual 讀出**：`ŷ = x_T + 網路輸出`（無參數）。
- **訓練**：和論文一樣 50 epochs、batch 4、Adam、MSE，只把固定 lr 1e-3 換成 cosine（初始 3e-2）。

| | **QKAN-FWP+**（149 參數） | **HQKAN-Δ**（136 參數） |
|---|---|---|
| 架構 | 論文的 gated fast-weight programmer | 單一 HQKAN，沒有 fast weights、沒有記憶 |
| Slow programmer | HQKAN 8 → 3 → 2（reps 3）→ 16 個 fast 角度 + 2 個 gate | — |
| Fast programmer / 主網路 | HQKAN 8 → 2 → 1（reps 3），2 個 DARUAN 電路（與 baseline 相同） | HQKAN 8 → 4 → 3 → 1（reps 3），12 個 DARUAN 電路，參數固定 |
| 記憶規則 | 論文 Eq. 3，但每個 DARUAN 電路各一個 gate（chrono 初始化） | 無（只看最後一個 token） |

HQKAN-Δ 的用途是回答「這些 benchmark 需不需要 fast-weight 記憶」：它和 QKAN-FWP+ 用同樣的 token 與讀出，只是把參數全部
放進一個靜態網路。

### 3.3 QKAN-FWP-O：以量測算符為 fast weights 的閉迴路記憶

**動機。** 論文（以及 CMG 等後續工作）的寫入是開迴路：`(ΔW_t, g_t) = S(x_t)` 只看當下的 token，所以
`W_T = Σ_k β_k ΔW(x_k)` 是「每個 token 各自猜一次該寫什麼，再做加權平均」，fast programmer 的預測從來沒有和下一個觀測值
比較過。對時間序列這特別可惜：context 裡的每一步都自帶答案（token $t$ 之後實際出現的 $x_{t+1}$）。

**關鍵觀察：QKAN 對量測算符是線性的。** DARUAN 的 activation 是 $\phi(u) = \langle 0|U^\dagger(u)\,O\,U(u)|0\rangle$。
論文把 $U$ 裡的旋轉角當 fast weights，$\phi$ 對它們是高度非線性的，「給定 context，最好的 fast weights 是什麼」沒有封閉解，
只能讓 slow programmer 去猜。但把單 qubit 的量測算符寫成 $O = r_0 I + \mathbf r\cdot\boldsymbol\sigma$，則

$$\phi(u) = r_0 + \mathbf r\cdot\mathbf n(u),\qquad \mathbf n(u) = (\langle X\rangle,\langle Y\rangle,\langle Z\rangle)\ \text{是電路輸出的 Bloch vector}.$$

同一個電路、同一組角度，activation 對 $(r_0,\mathbf r)$ 是線性的；整個 QKAN 層（各 edge 相加）也是。
於是把 fast weights 從旋轉角換成量測算符之後，「給定 context 的最佳 fast weights」就是一個加權最小平方問題。

**架構**（`qkanfwp/obsmem.py`）。令 $\tau_t$ 為第 $t$ 步的 Δ-token，

- 特徵：$u_t = E\tau_t + e$（HQKAN 的古典 encoder），$k_t = \big[1,\ u_t,\ \mathbf n_1(u_{t,1}),\dots,\mathbf n_h(u_{t,h})\big]$。
  $h$ 個單 qubit DARUAN 電路的角度是**慢參數**（不隨輸入改變）；中間的 $u_t$ 是 QKAN 的 base-activation 項
  （`qkan` 套件的 `base_activation`，這裡取恆等函數）。
- Context 內的配對：$(k_t,\ y_t)$，$y_t = x_{t+1}-x_t$，只用 token 完整的那些 $t$。
- 記憶——論文的 scalar-gated 遞迴，作用在充分統計量上：

$$C_t = g_t\,C_{t-1} + (1-g_t)\,(\Lambda_0 + k_t k_t^\top),\qquad b_t = g_t\,b_{t-1} + (1-g_t)\,(\Lambda_0 R_0 + k_t\,y_t),$$

  $C_0 = \Lambda_0$、$b_0 = \Lambda_0 R_0$；gate $g_t = \sigma(w_g\cdot k_t + c_g)$ 是同一批電路上的另一個量測算符。
- 讀出：fast observable $R_T = C_T^{-1} b_T$，預測 $\hat x_{T+1} = x_T + s_y\,k_T\cdot R_T$。

可訓練的慢參數只有 $E, e$、電路角度、先驗 $(R_0, \Lambda_0)$（$\Lambda_0$ 為對角）與 gate 的 $(w_g, c_g)$。
用論文的權重 $\beta_t = (1-g_t)\prod_{s>t} g_s$ 可以把遞迴寫成封閉形式：

$$R_T \;=\; R_0 + \Big(\Lambda_0 + \sum_t \beta_t k_t k_t^\top\Big)^{-1} \sum_t \beta_t\,k_t\,\underbrace{(y_t - k_t\cdot R_0)}_{\text{先驗 observable 的預測誤差}} .$$

這就是「閉迴路」的意思：寫進記憶的量由預測誤差決定。gate 全關（$\beta_t = 0$）時模型退化成一個量測算符可訓練的靜態 QKAN。

| 性質 | 論文（scalar gate）／CMG | QKAN-FWP-O |
|---|---|---|
| fast weights | DARUAN 的旋轉角 | DARUAN 的量測算符（每個電路 $\mathbf r\in\mathbb R^3$，加上 base 項係數） |
| 讀出對 fast weights | 非線性 | 線性 |
| 寫入 | 開迴路：$\Delta_t, g_t$ 只看 $x_t$ | 閉迴路：由 context 內的預測誤差決定 |
| 遞迴 | $\Theta_t = g\Theta_{t-1} + (1-g)\Delta_t$ | 同一個遞迴，作用在 $(C, b)$ |
| 封閉形式（Eq. 4）／prefix scan | 有 | 有（對 $(C,b)$；最後多一次 $F\times F$ 的線性求解，$F \le 25$） |
| 有界性 | $\Theta_T$ 在 proposal 的凸包內 | $C_T$ 在 $\{\Lambda_0 + k_tk_t^\top\}$ 的凸包內，且 $C_T \succeq \Lambda_0 \succ 0$：求解恆有唯一解。這只保證可逆，**不保證數值上良態**（條件數見下） |
| 量子電路是否依賴記憶 | 是（fast 角度逐樣本不同） | 否：所有 token 跑同一組固定電路、量 X／Y／Z 三個基底，記憶只出現在古典後處理 |
| 電路深度與 $T$ | 無關 | 無關 |

**可逆不等於良態。** $C_T \succeq \Lambda_0$ 給出的條件數上界是
$\kappa(C_T) \le \big(\lambda_{\max}(\Lambda_0) + \sum_t\beta_t\|k_t\|^2\big)/\lambda_{\min}(\Lambda_0)$，先驗精度很小時這個上界很大
（例如 $\mathrm{diag}(1+10^{-10}, 10^{-10})$ 是正定的，條件數卻是 $10^{10}$）。實際量到的條件數在論文的 benchmark 上是
$10^5$–$10^6$，在有雜訊的系統族上約 $10^2$（5.4、7.2 節），單精度與有限量測次數下的行為也在那裡量測。

兩個實作細節，不做會出問題：

- **先驗的處理。** 上式讓每次寫入都帶著先驗（$\Lambda_0$ 出現在 proposal 裡），所以 $C_T \succeq \Lambda_0$。另一種寫法是一般的
  指數加權 RLS：$C_t = gC_{t-1} + (1-g)k_tk_t^\top$，先驗只當初始值。此時只要有一個 gate 關到 0，先驗就和舊證據一起被忘掉，
  求解可能秩不足；完全沒有下限時，NARMA10 上 3 個 seed 有 2 個發散。給衰減後的先驗加一個很小的下限（$10^{-12}$）就不再發散，
  這個 RLS 版本作為對照列在 5.4 節與 6.3 節：它在平滑序列上比較準、在 NARMA 上較差。
- **只寫入完整的 token**。用補值的 token（視窗開頭）寫入，在五個資料集的 validation 上都比較差。因此 token 長度取
  $\min(8, N/2)$，保證視窗至少有一半能形成完整配對。

最終設定：6 個電路、reps = 1；N = 8 時 130 個參數，N ≥ 16 時 154 個（token 長度不同）。訓練同 3.2 節，另加梯度範數裁剪（1.0）。

**計算成本。** 封閉形式的讀出對每個視窗做一次 $F\times F$ 的線性求解：累積統計量是 $O(TF^2)$，求解是 $O(F^3)$
（$T$ 是完整配對的數目，$F \le 25$ 是特徵維度）。如果每一步都要輸出預測（串流），每一步都得重新求解，成本是每步 $O(F^3)$：
因為每次寫入都重新注入先驗 $\Lambda_0$（一個滿秩的對角更新），$C_t^{-1}$ 不能像一般的指數加權 RLS 那樣用 Sherman–Morrison 做
$O(F^2)$ 的秩一更新。先驗只放在初始值的 RLS 版本可以（本實作為了共用程式仍然直接求解）；它的精度見 5.4 節與 6.3 節。
逐步的 delta rule（`memory='delta'`）每步只要 $O(F)$、不需要矩陣。實測（`experiments/cost.py`）：

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

在這個大小下，求解的成本和特徵（電路）的計算同一個量級，delta rule 在本實作中也沒有比較快（它是 Python 迴圈）；
它的優勢是漸近的複雜度與不需要矩陣運算。精度的比較（5.4 節、第 6 節）只涵蓋本報告實作的幾種規則——掃一次與掃四次的
normalised delta rule，以及先驗只放在初始值的指數加權 RLS——不能推論到所有誤差驅動或遞迴最小平方的方法。

參數量之外的資源（`experiments/resources.py`；「circuit runs」是一個電路對一個輸入的執行次數，QKAN-FWP-O 的每次執行要量
X、Y、Z 三個不對易的基底）：

| Task | Model | Trainable parameters | Circuits | Circuit runs | Measurement settings per run | Runs × settings | Gate angles reloaded per prediction | Fast state kept in classical memory (numbers) | Classical multiply-adds for the memory |
|---|---|---|---|---|---|---|---|---|---|
| one step, N = 16 | GQKAN-QKANFWP | 152 | 11 | 137 | 1 | 137 | 16 | 16 | 1,290 |
| one step, N = 16 | CMG | 188 | 11 | 146 | 1 | 146 | 16 | 16 | 1,808 |
| one step, N = 16 | QKAN-FWP+ | 149 | 8 | 92 | 1 | 92 | 16 | 16 | 1,380 |
| one step, N = 16 | HQKAN-Δ | 136 | 12 | 12 | 1 | 12 | 0 | 0 | 35 |
| one step, N = 16 | QKAN-FWP-O | 154 | 6 | 54 | 3 | 162 | 0 | 350 | 11,058 |
| one step, N = 64 | GQKAN-QKANFWP | 152 | 11 | 569 | 1 | 569 | 16 | 16 | 5,418 |
| one step, N = 64 | CMG | 188 | 11 | 578 | 1 | 578 | 16 | 16 | 7,232 |
| one step, N = 64 | QKAN-FWP+ | 149 | 8 | 380 | 1 | 380 | 16 | 16 | 5,796 |
| one step, N = 64 | HQKAN-Δ | 136 | 12 | 12 | 1 | 12 | 0 | 0 | 35 |
| one step, N = 64 | QKAN-FWP-O | 154 | 6 | 342 | 3 | 1,026 | 0 | 350 | 42,258 |
| solar, 528 → 132 months | GQKAN-QKANFWP | 12,423 | 300 | 52,900 | 1 | 52,900 | 800 | 800 | 5,069,740 |
| solar, 528 → 132 months | QKAN-FWP+ | 11,732 | 290 | 47,630 | 1 | 47,630 | 800 | 800 | 4,737,730 |
| solar, 528 → 132 months | QKAN-FWP-O, static | 496 | 6 | 6 | 3 | 18 | 0 | 0 | 400 |
| solar, 528 → 132 months | QKAN-FWP-O | 547 | 6 | 540 | 3 | 1,620 | 0 | 725 | 106,833 |

- **一步預測**：QKAN-FWP-O 的量子成本（執行次數 × 量測基底數）和角度空間的模型同一個量級，不比較省；古典側比較貴——
  每個視窗要存 350 個數字的統計量（$C_T$ 的上三角與 $b_T$），而不是 16 個角度，乘加次數也多一個量級。參數少不等於運算量小。
- **不需要重新載入閘角度**：角度空間的 FWP 每一次預測都要把一組新的 fast 角度載入電路；QKAN-FWP-O 的電路固定，
  記憶只出現在量測結果的古典後處理。
- **多輸出不增加量子成本**：每個輸出只是同一批量測結果上的另一個量測算符。太陽黑子任務（132 個月的輸出）因此只用 6 個電路、
  每次預測 540 次執行，論文規模的模型是 300 個電路、約 5 萬次執行。

**把 fast weights 放在量測算符，得到的是什麼。**

- *能力*：閉迴路的寫入。模型可以在 context 內辨識系統（第 6 節），角度空間、開迴路的 QKAN-FWP 與 CMG 做不到。
- *理論性質*：最佳寫入有封閉形式；它的充分統計量服從論文的 gated 遞迴（Eq. 4、凸包、prefix scan 都保留）；
  求解恆有唯一解；讀出對記憶是線性的，所以查詢電路可以只量「context 剛決定的那一個量測算符」（7.3 節）。
- *資源*：電路與記憶無關，不必逐次載入角度；多輸出不增加電路；代價是三個量測基底與較大的古典狀態（上表）。
- *硬體誤差*：context 與 query 在同一台裝置上量測，所以兩者共同的靜態誤差（讀出誤差、去極化、過旋轉）會被 context 內的求解吸收，
  不需要校正電路或重新訓練；角度空間的模型與靜態模型的讀出權重是固定的，沒有這個機制（7.4 節）。
- *不是什麼*：reps = 1 時一個電路的三個 Bloch 分量都落在 $\mathrm{span}\{1, \cos u, \sin u\}$（數值驗證到 $10^{-15}$），
  所以特徵本身就是一次諧波的 Fourier 特徵。把它換成古典的 Fourier、tanh、多項式或小型 MLP 特徵而記憶完全不變，
  結果相當或更好（5.4 節、第 6 節）。這個架構的貢獻在「量子 FWP 的 fast weights 該放在哪裡、要付出多少量子資源」，
  不在特徵映射，也不主張量子優勢。

**與既有工作的關係。**

- 在學到的特徵上做 in-context 最小平方／Bayesian 線性回歸是既有的做法——ALPaCA（Harrison et al., 2018）、R2D2
  （Bertinetto et al., 2019）、mesa-layer（von Oswald et al., 2023）；誤差驅動的 fast-weight 寫入也是——delta rule
  （Schlag et al., 2021）、DeltaNet、Titans；可訓練或由網路產生的量測算符見 arXiv:2505.13525（開迴路）。
- 就文獻搜尋所及，量子 FWP 這一系列（arXiv:2402.17760、2605.06734、2606.24933、2607.02363、2607.27945）的 fast weights
  都是閘的角度、寫入都是開迴路。本報告新增的是：(i) 指出 QKAN 層對量測算符是線性的，因此 fast weights 可以有封閉形式的
  最佳寫入；(ii) 這個寫入的充分統計量恰好服從論文的 gated 遞迴；(iii) 由此得到電路與記憶無關的量子 FWP、
  可由 context 決定量測基底的讀出，以及對靜態硬體誤差的 in-context 校正。

### 3.4 太陽黑子用的模型

**QKAN-FWP+（11,732 參數）。** 在重新實作的 baseline（slow HQKAN 1 → 10 → 10，fast HQKAN 1 → 10 → 20 → 132，200 個 DARUAN 電路）上改三處：

- 分組 gate：fast QKAN 的 20 個輸出節點各一個 gate，chrono 初始化成對數等距的記憶長度 τ ∈ [2, 528] 個月；
- Last-cycle residual 讀出：`ŷ = smooth₁₃(最近 132 個月) + 網路輸出`，decoder 初始化為 0，所以未訓練的模型就是「重複上一個週期」；
- Slow latent 10 → 9，把多出來的 gate 參數抵掉。

**QKAN-FWP-O（547 參數）。** Token 是最近 11 個年平均；寫入的配對是（第 $t$ 個月的 token，之後 132 個月減去到 $t$ 為止的
last-cycle anchor），取視窗內後繼 132 個月都已知的每第三個月（89 個配對）；回歸目標是 132 個月在 16 個 cosine mode 上的係數。
6 個電路、reps = 1。拿掉記憶的靜態版本是 496 個參數。

---

## 4. 實驗設定

### 4.1 資料

`qkanfwp/data.py`：方程式與參數照論文。論文把六個資料集都當成單變數序列：給過去 N 個觀測值
$[x_{t-N},\dots,x_{t-1}]$，預測 $x_t$（論文 6.1 節）。NARMA 也是如此——輸入 $u_t$ 只用來產生序列 $y_t$，模型讀的是 $y$ 的歷史、
預測下一個 $y$；這和 reservoir computing 文獻裡「讀 $u$、輸出 $y$」的標準 NARMA 任務不同，本報告沒有做後者。論文沒寫 Bessel / SHM / DQC 的取樣點數，這裡統一用 300 點
（NARMA 的 M = 300 與 JC 的 3000 點是論文給的）。因此 **time-series 的 MSE 絕對值不能直接和論文 Table 3–6 比**（5.3 節）。
太陽黑子用的是同一份 SILSO V2.0 月資料前 3,326 筆，用論文的切分方式時絕對值可以和論文 Table 7 比（切分的問題見第 8 節）。

### 4.2 訓練協定

- **論文協定**：time-series 用 Adam、lr 1e-3、50 epochs、batch 4、報最後一個 epoch 的 test MSE（80/20 split）；
  太陽黑子用 lr ∈ {1, 2, 2.5}×1e-3（由 validation 選）、100 epochs、batch 32、peak-aware loss、取 validation loss 最低的 checkpoint。
- **調過 lr 的協定**（time-series）：同樣 50 epochs、batch 4，但 lr 用 cosine decay 到 0，初始 lr 由 validation 選。
  每個模型各自選：

  | 模型 | 5 個 300 點序列 | Jaynes–Cummings |
  |---|---|---|
  | GQKAN-QKANFWP（152） | 3e-2 | 1e-2 |
  | GQKAN-FWP（114） | 1e-1 | 3e-2 |
  | G-QKANFWP（175） | 3e-2 | 1e-2 |
  | CMG（188）、CMG＋Δ-token＋residual（173） | 3e-2 | 1e-2 |
  | QKAN-FWP+、HQKAN-Δ、QKAN-FWP-O | 3e-2 | 3e-2 |

  CMG 的兩個模型各自從 1e-2、3e-2、1e-1（Jaynes–Cummings：1e-2、3e-2）中由 validation MSE 選出（`results/dev_cmg.jsonl`）。

### 4.3 模型選擇只用 validation

所有設計決定（baseline 配置、token 長度、gate 分組、寬度、每個模型的 lr）都只用 70/10/20 split 的 validation 部分
（`results/dev_*.jsonl`）。最終數字用論文的 80/20 split、seeds 0–4，這些 run 沒有參與任何決定。
系統族用自己的 validation 序列；太陽黑子用論文協定裡的 validation split（切分方式見第 8 節）。

### 4.4 比較規則

- **QKAN-based**：本報告的三個模型只用 HQKAN／DARUAN。LSTM 只作為對照組出現。
- **參數量**：time-series ≤ 159（論文），太陽黑子 ≤ 12,474。
- **Baseline 都調過 lr**，並同時列出論文協定下的數字。
- 每張表都附上不需要訓練的參考線（線性 AR；太陽黑子是「重複上一個週期」）。

### 4.5 與論文實作的已知差異

| 項目 | 本 repo 的做法 | 論文 | 影響 |
|---|---|---|---|
| DARUAN 的讀出 | gated 模型與 HQKAN-Δ 沿用 `qkan` 套件預設的 `fast_measure=True`：輸出 \|a\|−\|b\|，不是物理量；QKAN-FWP-O 量的是物理的 ⟨X⟩、⟨Y⟩、⟨Z⟩ | Eq. 1 寫的是期望值 ⟨Z⟩ = \|a\|²−\|b\|² | 5.6 節用 ⟨Z⟩ 重跑，相對結論不變 |
| Data-encoding gate | `RZ(x)`，頻率固定為 1、不可訓練（`qkan` 預設） | 未說明；arXiv:2509.14026 允許可訓練的 `w_l x + b_l` | 未測 |
| 讀與寫的順序 | 先讀後寫 `y_t = F(x_t; W_t)`（原論文的式子） | 原論文同左；CMG 論文寫的是先寫後讀 | 5.3 節：先寫後讀的 baseline 再差 2 倍 |
| 正規化 | 對整條序列取 min/max，再切 train/test | 相同（兩篇論文都是先正規化再切分） | 有洩漏；5.6 節改成只用訓練段，數字幾乎不變 |
| NARMA | M = 300，從 0 起跳，沒有 burn-in | M = 300，其餘未說明 | 暫態在 N = 8 時進入訓練目標；5.6 節 |
| Bessel / SHM / DQC 的取樣點數 | 各 300 點 | 未說明 | 絕對 MSE 不可比 |
| 層的大小 | 在 validation 上從 5 種配置中選（3.1 節） | 只給總參數量 | — |
| 數值精度 | 所有模型與所有封閉形式的參考線都用 **float32 的 targets**（輸入是 float64）；QKAN-FWP-O 內部預設 float64，其餘模型 float32 | — | MSE 低於約 $10^{-15}$ 就是 targets 的捨入誤差，不代表模型好壞；計算倍數與勝負時一律先截在 $10^{-15}$。QKAN-FWP-O 改成 float32 的結果見 5.4、7.2 節 |
| NARMA 的任務定義 | 讀 $y$ 的歷史、預測下一個 $y$ | 相同（論文 6.1 節） | 不是「讀 $u$ 預測 $y$」的標準 NARMA 任務 |
| 太陽黑子的切分 | 同時報告論文的切法與依 target 時間切分的結果 | 對 sliding window 的索引做 80/10/10 | 論文的切法讓相鄰 split 的 targets 重疊 131 個月（第 8 節） |

---

## 5. 結果：論文的六個 time-series benchmark

論文協定的 split（80/20）、seeds 0–4、最後一個 epoch 的 test MSE。QKAN-FWP-O 整張表只有一組設定（3.3 節）。

### 5.1 主結果

![paper benchmarks](figures/om_timeseries.png)

每個資料集對四個 window 取幾何平均（粗體是訓練出來的模型中最低的；最右欄是不需要訓練的線性參考線）：

| Dataset | Best printed in the two papers | GQKAN-QKANFWP, tuned lr (152) | CMG, tuned lr (188) | CMG + Δ-tokens + residual, tuned lr (173) | QKAN-FWP+ (149) | HQKAN-Δ (136) | QKAN-FWP-O (130–154) | *Linear AR(8) (9)* |
|---|---|---|---|---|---|---|---|---|
| Bessel J2 | 5.3e-06 | 4.5e-06 | 2.7e-06 | 8.6e-07 | 1.5e-06 | 1.4e-07 | **2.8e-12** | *8.4e-17* |
| Damped SHM | 8.8e-06 | 1.2e-05 | 2.5e-06 | 7.7e-07 | 1.9e-06 | 3.2e-07 | **5.9e-12** | *9.0e-14* |
| NARMA5 | 6.5e-06 | 2.3e-04 | 2.8e-04 | 5.4e-06 | 6.0e-06 | 2.9e-06 | **4.0e-07** | *1.3e-06* |
| NARMA10 | 9.5e-06 | 6.9e-04 | 7.6e-04 | 6.3e-06 | 8.1e-06 | 2.7e-06 | **3.2e-07** | *1.7e-06* |
| Delayed quantum control | 5.5e-06 | 4.4e-04 | 7.5e-04 | 4.4e-06 | 8.0e-06 | 3.5e-06 | **2.2e-08** | *2.6e-07* |
| Jaynes–Cummings | 7.6e-06 | 1.7e-05 | 6.5e-06 | 1.5e-09 | 7.4e-09 | 1.7e-09 | **4.7e-13** | *2.4e-16* |

三個模型對每個參考對象的幾何平均倍數，括號內是勝出的格數：

Values below 1e-15 (rounding of the float32 targets) are clipped at 1e-15 before a factor is formed or a cell is counted.

| Reference | Params | QKAN-FWP+ (149) | HQKAN-Δ (136) | QKAN-FWP-O (130–154) |
|---|---|---|---|---|
| GQKAN-QKANFWP, paper protocol | 152 | 380× lower (24/24) | 1495× lower (24/24) | 1.0e6× lower (24/24) |
| GQKAN-QKANFWP, tuned lr | 152 | 45× lower (24/24) | 175× lower (24/24) | 1.2e5× lower (24/24) |
| GQKAN-FWP, tuned lr | 114 | 74× lower (22/24) | 290× lower (24/24) | 2.0e5× lower (24/24) |
| G-QKANFWP, tuned lr | 175 | 33× lower (23/24) | 129× lower (24/24) | 8.8e4× lower (24/24) |
| CMG, lr 1e-3 | 188 | 123× lower (20/20) | 478× lower (20/20) | 2.3e5× lower (20/20) |
| CMG, tuned lr | 188 | 31× lower (21/24) | 122× lower (24/24) | 8.3e4× lower (24/24) |
| CMG + Δ-tokens + residual, tuned lr | 173 | 2× higher (2/24) | 2× lower (21/24) | 1372× lower (24/24) |
| QKAN-FWP+ | 149 | – | 3.9× lower (24/24) | 2688× lower (24/24) |
| HQKAN-Δ | 136 | 3.9× higher (0/24) | – | 683× lower (23/24) |
| *Printed for GQKAN-QKANFWP in arXiv:2605.06734* | 159 | 40× lower (23/24) | 158× lower (24/24) | 1.1e5× lower (24/24) |
| *Best printed number of arXiv:2605.06734 and 2607.27945* | – | 5× lower (18/24) | 20× lower (21/24) | 1.3e4× lower (23/24) |
| *Linear AR(8), least squares* | 9 | 2.3e4× higher (2/24) | 5866× higher (3/24) | 8.6× higher (11/24) |

整體的幾何平均會掩蓋資料集之間的差異，所以把 QKAN-FWP-O 對每個模型的倍數按資料集分開（大於 1 表示 QKAN-FWP-O 較低）：

Geometric mean over the four windows per dataset; the last two columns count the 24 cells and give the smallest and largest per-cell factor. Values below 1e-15 are clipped first.

| Compared with | Bessel J2 | Damped SHM | NARMA5 | NARMA10 | Delayed quantum control | Jaynes–Cummings | Cells where QKAN-FWP-O is lower | Smallest … largest factor |
|---|---|---|---|---|---|---|---|---|
| GQKAN-QKANFWP, tuned lr | 1.6e6× | 2.0e6× | 568× | 2165× | 2.0e4× | 3.6e7× | 24/24 | 17× … 1.5e8× |
| CMG, tuned lr | 9.5e5× | 4.3e5× | 715× | 2388× | 3.5e4× | 1.4e7× | 24/24 | 19× … 1.1e8× |
| CMG + Δ-tokens + residual, tuned lr | 3.1e5× | 1.3e5× | 13× | 20× | 202× | 3085× | 24/24 | 1.4× … 4.2e6× |
| QKAN-FWP+ | 5.4e5× | 3.2e5× | 15× | 25× | 373× | 1.6e4× | 24/24 | 2.1× … 1.6e6× |
| HQKAN-Δ | 4.9e4× | 5.5e4× | 7.3× | 8.6× | 163× | 3677× | 23/24 | 0.84× … 1.6e5× |
| *Linear AR(8), least squares* | 0.00036× | 0.015× | 3.3× | 5.3× | 12× | 0.0021× | 11/24 | 8.4e-05× … 69× |

- **逐格的結果。** QKAN-FWP-O 在 24 格全部低於重新實作的 GQKAN-QKANFWP、CMG 與 QKAN-FWP+；對沒有記憶的 HQKAN-Δ 是 24 格中 23 格較低，
  **NARMA5 的 N = 8 那一格輸**（1.68e-5 對 1.41e-5）。
- **差距的大小依資料集而定，不能用一個數字概括。** 對 HQKAN-Δ：Bessel 與 Damped SHM 低四到五個數量級，Jaynes–Cummings 低三個數量級，
  DQC 低兩個數量級，**NARMA 只低 7–9 倍**。整體幾何平均（683 倍）主要由那三條幾乎線性的序列決定；
  其中 Jaynes–Cummings 的差距來自線性項與數值精度，不是來自記憶（5.4 節）。
- **CMG**：照 CMG 論文的設定（純量 token、188 參數），lr 由 validation 選出後和 scalar gate 的 baseline 同一個水準
  （Bessel、Damped SHM 與 Jaynes–Cummings 較好，NARMA 與 DQC 沒有改善）。給它相同的 Δ-token 與 residual 讀出之後，
  它比 QKAN-FWP+ 好 2 倍（24 格中 22 格），但整體仍比沒有記憶的 HQKAN-Δ 差 2 倍（24 格中 21 格較差；Jaynes–Cummings 上兩者相當）。
- **HQKAN-Δ 在每一格都比 QKAN-FWP+ 好**：在這些 benchmark 上，「由 slow programmer 產生旋轉角」這種型態的記憶沒有幫助，
  把同樣的參數放進靜態網路反而更好。因為這個結論重要，QKAN-FWP+ 與 HQKAN-Δ 另外各加跑 10 個 seed
  （`results/extra_seeds.jsonl`，5 個序列 × N ∈ {16, 64}）：15 個 seed 合計 HQKAN-Δ 好 2.5 倍，10 格中贏 9 格。
- QKAN-FWP-O 相對 HQKAN-Δ 的差距因此不是「加了記憶就會好」，而是**記憶的型態**：開迴路的角度記憶沒有用，
  閉迴路的量測算符記憶有用（5.4 節的對照）。

完整的表：

| Dataset | N | GQKAN-QKANFWP, paper protocol (152) | GQKAN-QKANFWP, tuned lr (152) | GQKAN-FWP, tuned lr (114) | G-QKANFWP, tuned lr (175) | CMG, lr 1e-3 (188) | CMG, tuned lr (188) | CMG + Δ-tokens + residual, tuned lr (173) | QKAN-FWP+ (149) | HQKAN-Δ (136) | QKAN-FWP-O (130–154) | *Linear AR(8) (9)* |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Bessel J2 | 8 | 5.49e-04 ± 5.2e-04 | 6.14e-06 ± 1.5e-06 | 1.08e-04 ± 1.9e-04 | 4.77e-06 ± 2.4e-06 | 7.34e-05 ± 5.9e-05 | 4.84e-06 ± 5.3e-06 | 7.53e-07 ± 4.5e-07 | 1.09e-06 ± 5.2e-07 | 8.39e-08 ± 5.4e-08 | **1.08e-12 ± 1.2e-12** | *8.9e-17* |
| Bessel J2 | 16 | 8.35e-04 ± 7.2e-04 | 4.27e-06 ± 3.0e-06 | 2.87e-06 ± 1.4e-06 | 2.62e-06 ± 2.8e-07 | 9.77e-05 ± 1.1e-04 | 1.43e-06 ± 3.8e-07 | 4.24e-06 ± 7.6e-06 | 1.64e-06 ± 1.4e-06 | 1.21e-07 ± 9.7e-08 | **1.01e-12 ± 8.9e-13** | *9.0e-17* |
| Bessel J2 | 32 | 6.90e-04 ± 5.3e-04 | 4.74e-06 ± 3.3e-06 | 1.22e-06 ± 7.7e-07 | 4.10e-06 ± 1.3e-06 | 9.86e-05 ± 7.3e-05 | 5.27e-06 ± 6.5e-06 | 5.24e-07 ± 5.2e-07 | 1.43e-06 ± 4.0e-07 | 1.24e-07 ± 1.1e-07 | **4.68e-12 ± 1.9e-12** | *8.5e-17* |
| Bessel J2 | 64 | 5.81e-04 ± 5.8e-04 | 3.39e-06 ± 2.0e-06 | 4.09e-06 ± 3.2e-06 | 1.44e-06 ± 3.1e-07 | 5.54e-05 ± 4.8e-05 | 1.36e-06 ± 4.6e-07 | 3.23e-07 ± 2.6e-07 | 2.00e-06 ± 1.3e-06 | 2.74e-07 ± 1.9e-07 | **1.18e-11 ± 5.3e-12** | *7.1e-17* |
| Damped SHM | 8 | 8.72e-05 ± 5.5e-05 | 1.78e-05 ± 5.0e-06 | 4.42e-06 ± 1.9e-06 | 9.08e-06 ± 3.8e-06 | 5.46e-05 ± 2.2e-05 | 2.94e-06 ± 8.4e-07 | 1.04e-06 ± 4.9e-07 | 1.56e-06 ± 7.6e-07 | 2.48e-07 ± 2.5e-08 | **1.60e-12 ± 7.1e-13** | *1.1e-13* |
| Damped SHM | 16 | 1.18e-04 ± 7.2e-05 | 1.15e-05 ± 6.7e-06 | 3.99e-05 ± 7.7e-05 | 1.00e-05 ± 3.8e-06 | 1.38e-04 ± 1.0e-04 | 1.87e-06 ± 8.7e-07 | 8.12e-07 ± 9.4e-07 | 1.38e-06 ± 6.5e-07 | 2.01e-07 ± 7.8e-08 | **2.10e-12 ± 5.1e-13** | *1.6e-13* |
| Damped SHM | 32 | 6.98e-05 ± 5.4e-05 | 7.67e-06 ± 2.0e-06 | 4.27e-06 ± 5.6e-06 | 5.49e-06 ± 1.6e-06 | 8.55e-05 ± 4.1e-05 | 2.40e-06 ± 1.9e-06 | 5.77e-07 ± 3.0e-07 | 2.54e-06 ± 1.4e-06 | 5.21e-07 ± 5.1e-07 | **2.16e-11 ± 1.6e-11** | *8.8e-14* |
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
| Jaynes–Cummings | 8 | 2.75e-05 ± 1.7e-05 | 1.95e-05 ± 2.5e-06 | 5.04e-05 ± 1.1e-05 | 1.55e-05 ± 4.8e-06 | – | 1.48e-05 ± 2.1e-06 | 4.89e-10 ± 1.9e-10 | 7.71e-09 ± 6.0e-09 | 1.41e-09 ± 1.2e-09 | **1.32e-13 ± 1.5e-13** | *2.4e-16* |
| Jaynes–Cummings | 16 | 4.25e-05 ± 4.8e-05 | 2.24e-05 ± 3.5e-06 | 5.25e-05 ± 2.1e-06 | 1.01e-05 ± 2.6e-06 | – | 6.00e-06 ± 4.6e-06 | 2.41e-09 ± 2.3e-09 | 3.68e-09 ± 1.5e-09 | 1.70e-09 ± 1.2e-09 | **1.58e-13 ± 1.7e-13** | *2.4e-16* |
| Jaynes–Cummings | 32 | 3.38e-05 ± 4.1e-05 | 1.42e-05 ± 3.6e-06 | 2.02e-05 ± 4.1e-06 | 1.13e-05 ± 3.8e-06 | – | 2.94e-06 ± 3.1e-06 | 2.09e-09 ± 1.9e-09 | 6.20e-09 ± 4.2e-09 | 3.17e-09 ± 2.7e-09 | **6.68e-13 ± 3.8e-13** | *2.4e-16* |
| Jaynes–Cummings | 64 | 6.66e-05 ± 5.4e-05 | 1.42e-05 ± 2.6e-06 | 2.71e-05 ± 6.1e-06 | 1.02e-05 ± 2.9e-06 | – | 6.88e-06 ± 6.3e-06 | 1.87e-09 ± 7.7e-10 | 1.71e-08 ± 2.6e-08 | 1.22e-09 ± 1.4e-09 | **3.65e-12 ± 1.4e-12** | *2.4e-16* |

### 5.2 線性參考線：這組 benchmark 有多難

最簡單的參考模型是線性自迴歸 `x̂_t = w·(x_{t−p}, …, x_{t−1}) + c`，用最小平方法在**同樣的訓練 window** 上解出來
（`experiments/reference_baselines.py`），不需要梯度訓練，參數量是 p + 1。它和所有模型一樣以 **float32 的 targets** 評分
（輸入是 float64）；targets 的捨入誤差讓 MSE 的下限落在 $10^{-16}$ 左右，所以低於 $10^{-15}$ 的數字彼此沒有差別，
計算倍數與勝負時一律先截在 $10^{-15}$。

| Dataset | N | Best printed in the two papers | QKAN-FWP+ | HQKAN-Δ | QKAN-FWP-O | Linear AR(3) (4) | Linear AR(8) (9) |
|---|---|---|---|---|---|---|---|
| Bessel J2 | 8 | 8.7e-06 | 1.1e-06 | 8.4e-08 | 1.1e-12 | 7.4e-10 | **8.9e-17** |
| Bessel J2 | 16 | 4.9e-06 | 1.6e-06 | 1.2e-07 | 1.0e-12 | 7.2e-10 | **9.0e-17** |
| Bessel J2 | 32 | 2.9e-06 | 1.4e-06 | 1.2e-07 | 4.7e-12 | 6.1e-10 | **8.5e-17** |
| Bessel J2 | 64 | 6.4e-06 | 2.0e-06 | 2.7e-07 | 1.2e-11 | 2.1e-10 | **7.1e-17** |
| Damped SHM | 8 | 1.2e-05 | 1.6e-06 | 2.5e-07 | 1.6e-12 | 1.7e-08 | **1.1e-13** |
| Damped SHM | 16 | 1.4e-05 | 1.4e-06 | 2.0e-07 | 2.1e-12 | 9.8e-09 | **1.6e-13** |
| Damped SHM | 32 | 3.6e-06 | 2.5e-06 | 5.2e-07 | 2.2e-11 | 6.7e-09 | **8.8e-14** |
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
| Jaynes–Cummings | 8 | 1.7e-05 | 7.7e-09 | 1.4e-09 | 1.3e-13 | 2.4e-16 | **2.4e-16** |
| Jaynes–Cummings | 16 | 3.2e-06 | 3.7e-09 | 1.7e-09 | 1.6e-13 | **2.4e-16** | 2.4e-16 |
| Jaynes–Cummings | 32 | 9.1e-06 | 6.2e-09 | 3.2e-09 | 6.7e-13 | **2.4e-16** | 2.4e-16 |
| Jaynes–Cummings | 64 | 7.0e-06 | 1.7e-08 | 1.2e-09 | 3.7e-12 | 2.4e-16 | **2.4e-16** |

- Linear AR(8) is lower than QKAN-FWP+ in 22/24 cells.
- Linear AR(8) is lower than HQKAN-Δ in 21/24 cells.
- Linear AR(8) is lower than QKAN-FWP-O in 13/24 cells.
- Linear AR(8) is lower than the best printed number of the two papers in 21/24 cells.

- 六個序列的一步預測幾乎是線性問題。**9 個參數的線性 AR(8) 在 24 格中的 21 格贏過兩篇論文印出的最佳數字**，也在 21–22 格贏過
  HQKAN-Δ 與 QKAN-FWP+。Jaynes–Cummings 是「衰減的常數項＋衰減的餘弦」，嚴格滿足三階線性遞迴，AR(3) 就到 targets 的捨入誤差。
- **QKAN-FWP-O 與線性 AR(8) 各有勝負**：在 NARMA 與 DQC（不是嚴格線性遞迴的序列）的 11 格 QKAN-FWP-O 較低（低 3–12 倍），
  在 Bessel、Damped SHM、Jaynes–Cummings 的 12 格與 NARMA5 的 N = 64 線性 AR(8) 較低：在那三條序列上線性最小平方解到了
  $10^{-13}$ ～ $10^{-16}$（已接近 targets 的捨入誤差），QKAN-FWP-O 是 $10^{-13}$ ～ $10^{-11}$。
- 因此在這六個序列上比較 MSE，比的主要是「誰把一個接近線性的映射擬合得比較準」。QKAN-FWP-O 之所以大幅領先其他
  神經模型，正是因為它在 context 內直接解最小平方，繞過了「用 SGD 把線性映射逼近到很多位有效數字」這件事。
  要檢驗記憶機制本身，需要第 6 節那種固定預測器不夠用的任務。

### 5.3 和論文印出的數字比較：重現缺口

5.1 節的表把論文印出的數字直接並列，但**這個比較只能參考**：論文沒有給 Bessel / SHM / DQC 的取樣點數，
而且重新實作的 GQKAN-QKANFWP 在論文協定下得到的數字和論文印的並不相同：

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

- 在論文協定下，重新實作的 GQKAN-QKANFWP 在 5 個 300 點序列上比論文印出的數字差 21 倍（幾何平均），
  Jaynes–Cummings 則反過來好 4–7 倍。
- **讀寫順序不是原因。** CMG 論文寫的是先寫後讀；先寫後讀的 baseline 更差（43 倍）。
- **主要是訓練效率。** 同一個模型把 lr 調好之後，和論文印出的數字只差 1.9 倍（20 格幾何平均，個別格子 0.2–14 倍）。
  也就是說「lr 1e-3、50 epochs」在這份實作裡收斂得比論文慢；可能是初始化、optimizer 細節或層的配置不同，無法從論文確定。
- **NARMA 的尺度。** 把 [−1, 1] 正規化資料上的 MSE 換算回原始尺度，NARMA5 / NARMA10 的 baseline 是 2.3e-5 / 3.6e-5，
  和論文印的 2.8e-5 / 5.2e-5 很接近；但直接在原始尺度上訓練得到的是 1.1e-4，並不吻合。這個解釋無法證實。
- 所以本報告所有「相對 baseline 低幾倍」的數字，都應解讀為**同一個 pipeline 內**的相對比較。

### 5.4 收益的來源：換掉特徵、換掉記憶規則

**同一個記憶，換掉特徵。** 先驗、gate 與求解完全相同，只把 Bloch 特徵換成古典特徵（`qkanfwp/obsmem.py` 的 `classical` 選項）。
最後一欄是對 QKAN-FWP-O 的幾何平均倍數（小於 1 表示比較好），為了讓每一列可以互相比較，都只算五個 300 點序列的 20 格；
Jaynes–Cummings 單獨列在它自己那一欄。

| Variant | Params | Bessel J2 | Damped SHM | NARMA5 | NARMA10 | Delayed quantum control | Jaynes–Cummings | vs first row |
|---|---|---|---|---|---|---|---|---|
| Bloch vectors of 6 circuits, reps = 1 (QKAN-FWP-O) | 130–154 | 2.8e-12 | 5.9e-12 | 4.0e-07 | 3.2e-07 | 2.2e-08 | 4.7e-13 | – |
| cos u, sin u of the same 6 units (same function space, no circuit) | 88–112 | 2.9e-12 | 6.0e-12 | 4.2e-07 | 4.3e-07 | 2.5e-08 | – | 1.1× |
| cos u, sin u of 8 units (same number of features) | 116–148 | 2.0e-12 | 4.6e-12 | 3.7e-07 | 3.1e-07 | 3.1e-08 | 5.0e-13 | 0.94× |
| cos(w·u + b), 3 per unit, w and b trainable | 142–166 | 2.7e-12 | 6.4e-12 | 4.2e-07 | 5.3e-07 | 2.0e-08 | 4.4e-13 | 1.1× |
| tanh(w·u + b), 3 per unit | 142–166 | 2.5e-12 | 5.5e-12 | 4.4e-07 | 2.9e-07 | 2.1e-08 | 3.8e-13 | 0.95× |
| products u_i·u_j (quadratic polynomial) | 115–139 | 8.8e-13 | 8.2e-12 | 5.2e-07 | 5.4e-07 | 5.3e-08 | 2.2e-13 | 1.2× |
| 8 tanh units of a second layer (small MLP) | 132–156 | 1.7e-12 | 2.9e-12 | 6.3e-07 | 3.1e-07 | 2.6e-08 | 1.6e-13 | 0.89× |
| linear term only | 52–76 | 1.4e-12 | 1.9e-11 | 6.4e-07 | 4.5e-07 | 4.9e-08 | 1.1e-13 | 1.5× |

- reps = 1 時一個電路的三個 Bloch 分量都落在 $\mathrm{span}\{1,\cos u,\sin u\}$，所以「同樣 6 個 unit 的 $\cos u$、$\sin u$」
  是同一個函數空間、不需要電路：1.1 倍；特徵數相同的 8 個 unit 是 0.94 倍。
- tanh 0.95 倍、可訓練頻率的 cos 1.1 倍、二次多項式 1.2 倍、小型 MLP 0.89 倍——**全部在 ±20% 之內**。
- 連非線性特徵都幾乎不需要：只留線性項是 1.5 倍（Bessel 好 2 倍，Damped SHM 差 3 倍，DQC 差 2 倍，NARMA 差 1.4–1.6 倍），
  在 Jaynes–Cummings 上它還更好（1.1e-13 對 4.7e-13）。
- 所以在論文的 benchmark 上，這個架構的收益與特徵是什麼無關。非線性特徵真正有用的任務見第 6 節的 Hénon map，
  那裡古典的非線性特徵同樣有效。

**同樣的特徵，換掉記憶規則。**

| Variant | Params | Bessel J2 | Damped SHM | NARMA5 | NARMA10 | Delayed quantum control | Jaynes–Cummings | vs first row |
|---|---|---|---|---|---|---|---|---|
| gated least squares, prior in every write (QKAN-FWP-O) | 130–154 | 2.8e-12 | 5.9e-12 | 4.0e-07 | 3.2e-07 | 2.2e-08 | 4.7e-13 | – |
| exponentially weighted RLS (prior only as the initial condition) | 130–154 | 8.0e-13 | 4.3e-13 | 7.4e-07 | 5.9e-07 | 1.4e-08 | – | 0.54× |
| least squares without gate (uniform weights) | 104–128 | 3.4e-12 | 3.0e-12 | 1.2e-06 | 1.5e-06 | 3.0e-08 | – | 1.7× |
| normalised delta rule, 4 sweeps over the context | 130–154 | 1.3e-09 | 3.9e-08 | 9.5e-07 | 1.5e-06 | 4.5e-07 | – | 59× |
| normalised delta rule, 1 sweep | 130–154 | 2.5e-09 | 2.3e-08 | 9.2e-07 | 1.5e-06 | 4.9e-07 | – | 62× |
| no memory, 9 circuits (same number of parameters) | 118–154 | 1.4e-08 | 8.5e-08 | 2.0e-06 | 2.0e-06 | 1.2e-06 | 1.3e-13 | 164× |
| no memory, 6 circuits | 79–103 | 2.4e-08 | 9.3e-08 | 2.1e-06 | 2.2e-06 | 1.2e-06 | 4.0e-13 | 190× |

- **沒有記憶。** 參數量相當（9 個電路，最多 154 個參數）的靜態模型在五個 300 點序列上差 164 倍，和 6 個電路的靜態模型（190 倍）同一個水準：
  Bessel 與 Damped SHM 差三到四個數量級，DQC 差 55 倍，NARMA 差 5–7 倍。差距不是參數量造成的。
  **Jaynes–Cummings 是例外**：這條 3000 點的序列嚴格滿足線性遞迴，靜態版本靠線性項就能用梯度訓練擬合到 1.3e-13（9 個電路）
  與 4.0e-13（6 個電路），和有記憶的版本（4.7e-13）相當或更低；記憶沒有帶來額外的好處。QKAN-FWP-O 在 Jaynes–Cummings 上對 HQKAN-Δ 的優勢因此來自線性項與數值精度，不是記憶。
- **指數加權 RLS**（先驗只當初始值，$C_t = gC_{t-1} + (1-g)k_tk_t^\top$）整體是 0.54 倍，也就是**比主模型好**：
  Bessel 好 3.5 倍、Damped SHM 好 14 倍、DQC 好 1.6 倍，NARMA 則差 1.8 倍。它的有效先驗是 $\Lambda_0\prod_t g_t$，context 越長越弱，
  所以在沒有雜訊的平滑序列上擬合得更準；NARMA 只用最近一兩個配對（見下），先驗被忘掉之後反而較差。
  沒有發散的格子或 seed。主模型「每次寫入都帶先驗」的設定是在這個對照之前由 validation 決定的，沒有依這裡的 test 結果更改；
  兩種寫法各有勝負，先驗怎麼處理不是這個架構的關鍵。
- **不用 gate**（等權重）整體差 1.7 倍，集中在 NARMA（3–4.7 倍）；Bessel 與 DQC 幾乎沒差，Damped SHM 還好一點。
- **Normalised delta rule**：掃一次差 62 倍，掃四次差 59 倍——在這些序列上多掃幾次幾乎沒有幫助。
  差距在 Bessel、Damped SHM（兩到四個數量級）與 DQC（20 倍）；NARMA 上只差 2–5 倍。
  這只涵蓋本報告實作的這一種 delta rule，不代表所有誤差驅動的遞迴方法。

**其他設計選擇**（數字是「該變體的 test MSE ÷ 完整模型」的幾何平均，大於 1 表示完整模型較好）：

| Variant | Params | All cells | Cells where the full model is better | Bessel J2 | Damped SHM | NARMA5 | NARMA10 | Delayed quantum control | Jaynes–Cummings |
|---|---|---|---|---|---|---|---|---|---|
| constant gate (not input dependent) | 105–129 | **1.4×** | 15/20 | 0.91× | 0.94× | 1.2× | 4.6× | 1.2× | – |
| one prior precision instead of one per feature | 106–130 | **1×** | 9/20 | 0.99× | 0.98× | 0.98× | 1.2× | 0.9× | – |
| no base-activation (linear) term: Bloch features only | 112–136 | **4.7×** | 18/20 | 3.8× | 25× | 1.8× | 3.2× | 4.2× | – |
| float32 instead of float64 (features, statistics and solve) | 130–154 | **1.2×** | 16/24 | 1× | 1× | 2.1× | 1.6× | 0.95× | 1× |
| 4 circuits instead of 6 | 88–104 | **1.7×** | 18/20 | 1.3× | 3.6× | 1.1× | 1.6× | 1.7× | – |
| fixed token length 6 instead of min(8, N/2) | 142 | **1.9×** | 13/20 | 0.72× | 1.4× | 5.3× | 1.2× | 3.9× | – |

- **Gate 是否依賴輸入**：常數 gate 整體差 1.4 倍，NARMA10 差 4.6 倍。先驗精度逐特徵或共用一個，沒有差別。
- **線性（base-activation）項很重要**（拿掉差 4.7 倍），因為這些序列接近線性。
- **float32 取代 float64**：Bessel、Damped SHM 與 Jaynes–Cummings 完全相同（1.0 倍），NARMA 上差 1.6–2.1 倍，整體 1.2 倍。
  1e-12 等級的 MSE 並不依賴雙精度（7.2 節）。
- **大小與 token 長度**：6 個電路減為 4 個差 1.7 倍；token 長度固定為 6（不用 $\min(8, N/2)$ 的規則）差 1.9 倍，主要差在 NARMA5 與 DQC。

**記憶實際用了什麼。** 下表是訓練好的模型在 test window 上的記憶權重 $\beta_t$（N = 32，共 24 個完整配對；
`experiments/memory_probe.py`）。「有效配對數」是 $(\sum_t\beta_t)^2/\sum_t\beta_t^2$。

| Dataset | Test MSE | Total weight Σβ | Effective number of pairs | Weight of the most recent pair | Weight of the 3 most recent pairs | Prior precision (median) | cond(C_T), median | cond(C_T), max |
|---|---|---|---|---|---|---|---|---|
| Bessel J2 | 3.4e-12 | 0.99 | 9.5 | 0.19 | 0.47 | 1e-05 | 8e+05 | 1e+06 |
| Damped SHM | 2.8e-11 | 1.00 | 8.5 | 0.21 | 0.51 | 1e-05 | 9e+05 | 1e+06 |
| NARMA5 | 4.7e-08 | 1.00 | 1.4 | 0.84 | 1.00 | 8e-06 | 6e+06 | 9e+06 |
| NARMA10 | 2.2e-08 | 1.00 | 1.7 | 0.75 | 0.98 | 7e-06 | 2e+06 | 2e+06 |
| Delayed quantum control | 1.0e-08 | 0.92 | 16.1 | 0.10 | 0.27 | 1e-05 | 1e+06 | 1e+06 |
| Jaynes–Cummings | 7.0e-13 | 1.00 | 8.7 | 0.21 | 0.50 | 1e-05 | 8e+05 | 9e+05 |

![memory weights](figures/om_memory.png)

模型在不同資料集學到很不一樣的記憶長度，而且權重隨配對的年齡近似幾何衰減：平滑、接近線性的序列用到十個左右的配對
（DQC 約 16 個），等於在視窗內做一次加權回歸；NARMA 幾乎只用**最近一步的預測誤差**（有效配對數不到 2）——NARMA 由一個沒有被
觀測到的緩變輸入驅動，上一步的誤差正好帶有它當下的資訊。這兩種用法都需要閉迴路；也說明了為什麼等權重的統計量（不用 gate）
在 NARMA 上明顯較差。這張表只描述學到的權重，沒有檢驗「避開起始暫態」之類的因果解釋。

### 5.5 消融：QKAN-FWP+ 的輸入表徵與讀出

5 個 300 點序列 × N ∈ {16, 64}；數字是 seed-mean test MSE ÷ 論文協定 baseline 的幾何平均（越小越好）。

![QKAN-FWP+ ablation](figures/timeseries_ablation.png)

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

- **Residual 讀出**：拿掉後變差 8 倍（0.0036 → 0.029）。
- **Δ-token**：拿掉（回到純量輸入）變差 18 倍（→ 0.064）。8 維比 3 維整體好 1.3 倍：NARMA 與 DQC 好 2–10 倍，
  Bessel 與 SHM 反而差 2–5 倍。
- **分組 gate**：換回論文的 scalar gate 是 0.0031，略好於分組 gate 的 0.0036——token 夠長之後，gate 的粒度在這組
  benchmark 上沒有差別（單獨加在 baseline 上時有 0.53–0.75 倍的增益，見附錄 A）。
- **Fast weights 本身**：拿掉整個機制（HQKAN-Δ）是 0.00091，比 QKAN-FWP+ 好 4 倍（加到 15 個 seed 是 2.5 倍，5.1 節）。
- **對照（非 QKAN）**：160 參數的 LSTM 用同樣的 token 與 residual 是 0.00093，和 HQKAN-Δ 打平。

### 5.6 穩健性：三個實作選擇會不會改變結論

N = 16、5 seeds。QKAN-FWP-O 量的本來就是物理的 ⟨X⟩、⟨Y⟩、⟨Z⟩，所以第二個條件下它的數字和預設相同。

**Default (as in all tables above)**

| Dataset | Baseline, paper protocol | Baseline, tuned lr | QKAN-FWP+ | HQKAN-Δ | QKAN-FWP-O |
|---|---|---|---|---|---|
| Bessel J2 | 8.35e-04 | 4.27e-06 | 1.64e-06 | 1.21e-07 | 1.01e-12 |
| Damped SHM | 1.18e-04 | 1.15e-05 | 1.38e-06 | 2.01e-07 | 2.10e-12 |
| NARMA5 | 1.94e-03 | 2.29e-04 | 3.67e-06 | 1.79e-06 | 7.00e-08 |
| NARMA10 | 2.70e-03 | 5.24e-04 | 4.31e-06 | 2.14e-06 | 1.90e-06 |
| Delayed quantum control | 2.04e-03 | 4.63e-04 | 9.03e-06 | 5.92e-06 | 3.30e-08 |
| Jaynes–Cummings | 4.25e-05 | 2.24e-05 | 3.68e-09 | 1.70e-09 | 1.58e-13 |

- vs the tuned baseline over 6 datasets: QKAN-FWP+ 61× lower (6/6), HQKAN-Δ 201× lower (6/6), QKAN-FWP-O 1.9e5× lower (6/6).

**Physical read-out ⟨Z⟩ = |a|² − |b|² in every DARUAN circuit**

| Dataset | Baseline, paper protocol | Baseline, tuned lr | QKAN-FWP+ | HQKAN-Δ | QKAN-FWP-O |
|---|---|---|---|---|---|
| Bessel J2 | 5.90e-04 | 6.54e-06 | 1.53e-06 | 1.98e-07 | 1.01e-12 |
| Damped SHM | 1.24e-04 | 1.85e-05 | 1.30e-06 | 4.62e-07 | 2.10e-12 |
| NARMA5 | 1.89e-03 | 2.33e-04 | 4.80e-06 | 2.24e-06 | 7.00e-08 |
| NARMA10 | 2.49e-03 | 5.37e-04 | 8.45e-06 | 2.73e-06 | 1.90e-06 |
| Delayed quantum control | 1.73e-03 | 5.64e-04 | 1.27e-05 | 8.70e-06 | 3.30e-08 |
| Jaynes–Cummings | 4.53e-05 | 1.98e-05 | 1.41e-08 | 5.77e-09 | 1.58e-13 |

- vs the tuned baseline over 6 datasets: QKAN-FWP+ 48× lower (6/6), HQKAN-Δ 135× lower (6/6), QKAN-FWP-O 2.2e5× lower (6/6).

**Min–max scaling fitted on the training part only**

| Dataset | Baseline, paper protocol | Baseline, tuned lr | QKAN-FWP+ | HQKAN-Δ | QKAN-FWP-O |
|---|---|---|---|---|---|
| Bessel J2 | 8.35e-04 | 4.27e-06 | 1.64e-06 | 1.21e-07 | 1.01e-12 |
| Damped SHM | 1.18e-04 | 1.15e-05 | 1.38e-06 | 2.01e-07 | 2.10e-12 |
| NARMA5 | 1.99e-03 | 2.31e-04 | 3.71e-06 | 1.80e-06 | 7.04e-08 |
| NARMA10 | 2.70e-03 | 5.24e-04 | 4.31e-06 | 2.14e-06 | 1.90e-06 |
| Delayed quantum control | 2.04e-03 | 4.63e-04 | 9.03e-06 | 5.92e-06 | 3.30e-08 |
| Jaynes–Cummings | 4.25e-05 | 2.24e-05 | 3.68e-09 | 1.70e-09 | 1.58e-13 |

- vs the tuned baseline over 6 datasets: QKAN-FWP+ 61× lower (6/6), HQKAN-Δ 201× lower (6/6), QKAN-FWP-O 1.9e5× lower (6/6).

| Dataset | N | Baseline, paper protocol | Baseline, tuned lr | QKAN-FWP+ | HQKAN-Δ | QKAN-FWP-O |
|---|---|---|---|---|---|---|
| NARMA5 | 8 | 3.17e-03 | 3.13e-03 | 1.33e-05 | 6.60e-06 | 2.34e-05 |
| NARMA5 | 16 | 3.02e-03 | 2.54e-03 | 1.18e-05 | 5.55e-06 | 3.15e-07 |
| NARMA10 | 8 | 5.29e-03 | 4.79e-03 | 9.90e-06 | 3.90e-06 | 5.20e-06 |
| NARMA10 | 16 | 5.46e-03 | 7.70e-03 | 9.52e-06 | 3.98e-06 | 7.15e-08 |

- **物理的 ⟨Z⟩ 讀出**（取代 `qkan` 預設的 \|a\|−\|b\|）：gated 模型與 HQKAN-Δ 的數字大多變動在 2 倍以內，排序不變。
- **只用訓練段做正規化**：Bessel、SHM、NARMA10、DQC、JC 的數字和原本完全相同，因為這些序列的極值都落在訓練段；
  只有 NARMA5 的最大值在測試段，數字變動不到 3%（QKAN-FWP-O：7.04e-8 對 7.00e-8）。先正規化再切分的洩漏在這組資料上實際沒有作用。
- **NARMA 去掉起始暫態**：正規化後的訊號佔滿整個 [−1, 1]，gated 模型與 HQKAN-Δ 的 MSE 都變大，彼此的排序不變。
  QKAN-FWP-O 在 N = 16 仍比 HQKAN-Δ 低 18 倍與 56 倍；**但在 N = 8 輸給 HQKAN-Δ**（NARMA5：2.3e-5 對 6.6e-6；NARMA10：5.2e-6 對 3.9e-6）。
  N = 8 時它的 token 只有 4 個值（$\min(8, N/2)$ 的規則），看不到 NARMA 需要的延遲；這是讓記憶有完整配對可用所付的代價。

---

## 6. 結果：需要 in-context 辨識的系統族

六個 benchmark 都是單一軌跡，train 與 test 來自同一個系統，所以一個固定的預測器就夠了——這也是線性 AR 贏的原因。
Fast weights 只有在「視窗裡有慢參數存不下來的資訊」時才有意義。這裡每條序列是同一類系統、**不同的物理參數**
（`qkanfwp/families.py`），train／validation／test 用不同的序列，模型必須從 16 步的視窗辨識出系統：

| 族 | 內容 |
|---|---|
| Damped oscillation | $A e^{-\gamma t}\cos(\omega t + \varphi)$，頻率、阻尼、振幅、相位每條序列隨機（每條序列各自滿足一個 AR(2)） |
| Two tones | 兩個阻尼振盪的和（每條序列各自滿足一個 AR(4)） |
| Jaynes–Cummings | 論文的開放 JC 模型，但耦合 $g$、失諧、腔損耗 $\kappa$ 與初始光子振幅每條序列隨機 |
| Hénon map | $x_{t+1} = 1 - a x_t^2 + b x_{t-1}$，$(a,b)$ 隨機；混沌、非線性 |
| Duffing | $\ddot x + d\dot x + ax + bx^3 = 0$，$(d,a,b)$ 隨機 |

「noise 0.02」是加在觀測值上的白雜訊（序列已正規化到約 $[-1,1]$）。每個神經模型都掃同樣的三個 lr
（3e-3、1e-2、3e-2，cosine、40 epochs、batch 32），lr 與 checkpoint 都由 validation 決定。四條參考線不需要訓練，
超參數都由 validation 選：重複上一個值；所有序列共用一個線性 AR(p)；**在每個視窗內各自擬合的 ridge AR(q)**；
以及在每個視窗內對兩個 lag 的二次特徵 $[1, x_t, x_{t-1}, x_t^2, x_tx_{t-1}, x_{t-1}^2]$ 擬合的 ridge
（它用到視窗內全部 14 個配對；對無雜訊的 Hénon map 它就是正確的函數形式）。

### 6.1 和其他架構比

![families](figures/om_family.png)

Mean ± std over 3 seeds at the learning rate chosen on validation (one of 3e-3, 1e-2, 3e-2, cosine); each model is evaluated at its best-validation epoch. References are closed-form.

| Model | Params | Damped oscillation, noise 0 | Two tones, noise 0 | Jaynes–Cummings, noise 0 | Hénon map, noise 0 | Duffing, noise 0 | Damped oscillation, noise 0.02 | Two tones, noise 0.02 | Jaynes–Cummings, noise 0.02 | Hénon map, noise 0.02 | Duffing, noise 0.02 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| *Reference: repeat the last value* | – | *7.48e-02* | *5.13e-02* | *2.74e-02* | *7.07e-01* | *1.12e-02* | *7.61e-02* | *5.24e-02* | *2.79e-02* | *7.09e-01* | *1.20e-02* |
| *Reference: one linear AR(p) for all sequences* | – | *6.95e-08* | *4.63e-08* | *1.34e-08* | *4.60e-02* | *2.25e-06* | *5.86e-03* | *5.11e-03* | *4.55e-03* | *4.66e-02* | *1.18e-03* |
| *Reference: ridge AR(q) fitted inside each window* | – | *6.33e-17* | *1.12e-15* | *1.82e-08* | *5.99e-02* | *1.49e-06* | *7.53e-04* | *2.51e-03* | *4.05e-03* | *6.09e-02* | *9.34e-04* |
| *Reference: ridge on quadratic features of two lags, fitted inside each window* | – | *6.33e-17* | *1.24e-02* | *3.32e-03* | *1.52e-16* | *1.24e-04* | *2.28e-03* | *1.45e-02* | *5.69e-03* | *2.65e-03* | *4.84e-03* |
| GQKAN-QKANFWP (scalar gate) | 152 | 1.64e-02 ± 2.8e-04 | 1.47e-02 ± 6.1e-05 | 6.77e-03 ± 1.3e-04 | 1.70e-03 ± 1.0e-03 | 1.62e-04 ± 8.2e-06 | 1.77e-02 ± 7.8e-05 | 1.60e-02 ± 1.2e-04 | 8.18e-03 ± 2.5e-05 | 3.47e-03 ± 8.6e-04 | 1.51e-03 ± 3.5e-05 |
| CMG (scalar tokens) | 188 | 4.83e-03 ± 2.9e-03 | 1.07e-02 ± 1.6e-03 | 6.27e-03 ± 9.8e-04 | 5.07e-04 ± 5.6e-05 | 3.10e-04 ± 6.9e-05 | 6.25e-03 ± 2.8e-03 | 1.36e-02 ± 7.1e-04 | 7.72e-03 ± 8.5e-04 | 2.33e-03 ± 1.6e-04 | 1.56e-03 ± 6.3e-05 |
| CMG + Δ-tokens + residual | 173 | 4.72e-05 ± 2.8e-06 | 1.04e-04 ± 1.8e-05 | 2.77e-05 ± 1.4e-06 | 6.04e-04 ± 1.4e-04 | 3.40e-06 ± 1.4e-06 | 1.64e-03 ± 3.9e-05 | 5.26e-03 ± 1.2e-04 | 3.68e-03 ± 1.1e-04 | 1.86e-03 ± 9.0e-05 | 9.75e-04 ± 2.7e-05 |
| QKAN-FWP+ | 149 | 4.87e-05 ± 2.1e-05 | 9.73e-05 ± 1.8e-05 | 2.72e-05 ± 4.3e-06 | 9.35e-04 ± 5.5e-04 | 4.23e-06 ± 1.0e-06 | 1.75e-03 ± 2.8e-04 | 4.78e-03 ± 3.6e-04 | 3.58e-03 ± 1.1e-04 | **1.76e-03 ± 1.6e-04** | 1.11e-03 ± 3.2e-05 |
| HQKAN-Δ (static) | 136 | 9.83e-05 ± 1.2e-05 | 1.18e-04 ± 1.6e-05 | 2.78e-05 ± 1.2e-06 | 1.48e-03 ± 1.5e-04 | 3.49e-06 ± 2.7e-06 | 3.38e-03 ± 1.8e-04 | 5.94e-03 ± 2.9e-05 | 4.31e-03 ± 3.8e-05 | 2.86e-03 ± 5.3e-05 | 1.21e-03 ± 2.2e-05 |
| LSTM, same tokens (not QKAN) | 160 | 4.03e-05 ± 5.6e-06 | 7.71e-05 ± 6.4e-06 | 1.89e-05 ± 1.9e-06 | 9.27e-04 ± 3.7e-04 | 2.52e-06 ± 2.9e-07 | 1.91e-03 ± 5.2e-04 | 4.57e-03 ± 1.3e-04 | 3.31e-03 ± 1.5e-05 | 2.80e-03 ± 8.4e-05 | 1.05e-03 ± 3.1e-05 |
| QKAN-FWP-O | 154 | **2.29e-09 ± 2.1e-09** | **4.40e-08 ± 1.4e-08** | **2.00e-07 ± 8.4e-08** | **3.42e-05 ± 4.9e-06** | **1.54e-07 ± 3.5e-08** | **9.05e-04 ± 9.2e-06** | **1.97e-03 ± 2.6e-05** | **2.87e-03 ± 1.7e-05** | 1.79e-03 ± 4.4e-05 | **8.67e-04 ± 3.4e-06** |

| Compared with | Params | Geo-mean test MSE of QKAN-FWP-O | Cells where it is lower | Smallest … largest factor |
|---|---|---|---|---|
| GQKAN-QKANFWP (scalar gate) | 152 | **303× lower** | 10/10 | 1.7× … 7.2e6× |
| CMG (scalar tokens) | 188 | **207× lower** | 10/10 | 1.3× … 2.1e6× |
| CMG + Δ-tokens + residual | 173 | **21× lower** | 10/10 | 1× … 2.1e4× |
| QKAN-FWP+ | 149 | **23× lower** | 9/10 | 0.98× … 2.1e4× |
| HQKAN-Δ (static) | 136 | **30× lower** | 10/10 | 1.4× … 4.3e4× |
| LSTM, same tokens (not QKAN) | 160 | **21× lower** | 10/10 | 1.2× … 1.8e4× |
| *one linear AR(p) for all sequences* | – | **5.8× lower** | 9/10 | 0.067× … 1345× |
| *ridge AR(q) fitted inside each window* | – | 8× higher | 6/10 | 2.5e-08× … 1752× |
| *ridge on quadratic features fitted inside each window* | – | 1.5× higher | 8/10 | 2.9e-11× … 2.8e5× |

- **沒有雜訊時**，QKAN-FWP-O 在五個族都比其他架構低，比其餘最好的架構低 15 倍（Hénon、Duffing）到 2 萬倍（阻尼振盪）。
  其他架構彼此差不多：有記憶的 QKAN-FWP+、CMG、LSTM 和沒有記憶的 HQKAN-Δ 在同一個量級，開迴路的記憶最多帶來 2–3 倍。
- **有雜訊時**差距縮小（不可約的誤差約為雜訊變異數 4e-4）：QKAN-FWP-O 在四個族比其他架構低（比次佳的低 1.1–2.3 倍），
  在 Hénon 上和 QKAN-FWP+ 打平。
- **對封閉形式的參考線**，結果要分開看：
  - 「所有序列共用一個線性 AR」在 10 格中輸 9 格（只在無雜訊的 Jaynes–Cummings 上較好）。
  - 「在視窗內擬合 ridge AR」在無雜訊的線性族上是精確解（到 targets 的捨入誤差），沒有模型能比；無雜訊的 Jaynes–Cummings
    也是它較好。有雜訊時 QKAN-FWP-O 在阻尼振盪上是它的 1.2 倍，在 two tones、Jaynes–Cummings、Duffing 上比它低。
  - 「在視窗內擬合二次特徵」在**無雜訊的 Hénon map 上是精確解（1.5e-16），QKAN-FWP-O 是 3.4e-5**——只要特徵的函數形式對了，
    一個六個係數的最小平方就解掉這個任務。有雜訊時 QKAN-FWP-O 較低（1.8e-3 對 2.6e-3）；在其他族上這條參考線很差
    （two tones 1.2e-2），因為函數形式不對。
  所以 QKAN-FWP-O 的定位是「不需要事先知道函數形式、在各種系統上都接近最好」，而不是在任何一個族上勝過知道函數形式的最小平方。

### 6.2 同一個記憶，換掉特徵

把 Bloch 特徵換成別的特徵，**先驗、gate 與求解完全相同**（`qkanfwp/obsmem.py` 的 `classical` 選項）。最後一欄是對 QKAN-FWP-O 的
幾何平均倍數（小於 1 表示比較好）。

| Variant | Params | Damped oscillation, noise 0 | Two tones, noise 0 | Jaynes–Cummings, noise 0 | Hénon map, noise 0 | Duffing, noise 0 | Damped oscillation, noise 0.02 | Two tones, noise 0.02 | Jaynes–Cummings, noise 0.02 | Hénon map, noise 0.02 | Duffing, noise 0.02 | vs first row |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| *Reference: one linear AR(p) for all sequences* | – | *7.0e-08* | *4.6e-08* | *1.3e-08* | *4.6e-02* | *2.3e-06* | *5.9e-03* | *5.1e-03* | *4.5e-03* | *4.7e-02* | *1.2e-03* | |
| *Reference: ridge AR(q) fitted inside each window* | – | *6.3e-17* | *1.1e-15* | *1.8e-08* | *6.0e-02* | *1.5e-06* | *7.5e-04* | *2.5e-03* | *4.0e-03* | *6.1e-02* | *9.3e-04* | |
| *Reference: ridge on quadratic features of two lags, fitted inside each window* | – | *6.3e-17* | *1.2e-02* | *3.3e-03* | *1.5e-16* | *1.2e-04* | *2.3e-03* | *1.5e-02* | *5.7e-03* | *2.6e-03* | *4.8e-03* | |
| Bloch vectors of 6 circuits, reps = 1 (QKAN-FWP-O) | 154 | 2.3e-09 | 4.4e-08 | 2.0e-07 | 3.4e-05 | 1.5e-07 | 9.1e-04 | 2.0e-03 | 2.9e-03 | 1.8e-03 | 8.7e-04 | – |
| cos u, sin u of the same 6 units (same function space, no circuit) | 112 | 4.1e-09 | 9.1e-08 | 3.1e-07 | 4.2e-05 | 1.3e-07 | 9.0e-04 | **1.9e-03** | 2.9e-03 | 1.8e-03 | 8.8e-04 | 1.2× |
| cos u, sin u of 8 units (same number of features) | 148 | 2.5e-09 | 7.1e-08 | 1.9e-07 | 4.4e-05 | 1.9e-07 | 9.1e-04 | 2.0e-03 | 2.8e-03 | 1.7e-03 | 8.7e-04 | 1.1× |
| cos(w·u + b), 3 per unit, w and b trainable | 166 | 1.0e-08 | 1.1e-06 | 2.3e-07 | 2.3e-05 | 1.8e-07 | 8.8e-04 | 2.0e-03 | **2.8e-03** | **1.6e-03** | 8.6e-04 | 1.6× |
| tanh(w·u + b), 3 per unit | 166 | 2.8e-09 | 3.4e-08 | 1.7e-07 | 3.5e-05 | 1.7e-07 | 1.0e-03 | 2.0e-03 | 2.9e-03 | 1.6e-03 | 9.0e-04 | 1× |
| products u_i·u_j (quadratic polynomial) | 139 | 1.3e-10 | 9.4e-07 | 3.0e-06 | **3.9e-06** | 7.8e-06 | 9.5e-04 | 2.3e-03 | 2.9e-03 | 2.4e-03 | 1.0e-03 | 1.7× |
| 8 tanh units of a second layer (small MLP) | 156 | 1.9e-10 | 6.2e-09 | 5.8e-08 | 3.4e-05 | **2.4e-08** | 8.8e-04 | 2.0e-03 | 2.9e-03 | 1.8e-03 | **8.4e-04** | 0.47× |
| linear term only | 76 | **2.8e-11** | **2.0e-09** | **1.1e-08** | 4.0e-02 | 3.7e-07 | **8.8e-04** | 2.2e-03 | 2.9e-03 | 3.9e-02 | 8.9e-04 | 1.1× |

- **Bloch 特徵就是一次諧波的 Fourier 特徵。** 用同樣 6 個 hidden unit 的 $\cos u, \sin u$（同一個函數空間，112 參數）是 1.2 倍，
  用 8 個 unit（特徵數相同，148 參數）是 1.1 倍，都在 seed 的雜訊之內。
- **tanh 特徵相同（1.0 倍）；可訓練頻率的 cos 特徵 1.6 倍**（差在無雜訊的阻尼振盪與 two tones）。
- **二次多項式整體較差（1.7 倍），但在函數形式吻合時最好**：無雜訊的 Hénon 是 3.9e-6（比 Bloch 好 9 倍）、阻尼振盪好 18 倍；
  two tones、Jaynes–Cummings、Duffing 則差 15–50 倍，有雜訊的 Hénon 也較差（2.4e-3 對 1.8e-3）。
- **小型 MLP 特徵整體最好（0.47 倍，即好 2.1 倍）**：無雜訊的線性族與 Duffing 上好 3–12 倍，Hénon 相同，有雜訊的格子都相同。
- **只留線性項**在 Hénon 上失敗（4e-2）、Duffing 差 2.4 倍；在三個線性的族上反而更好（無雜訊時好 18–80 倍）。

結論：收益來自閉迴路的記憶。非線性系統需要某種非線性特徵，但 Bloch 特徵並不特別——它和同函數空間的 Fourier 特徵等價，
不如一個同樣大小的小型 MLP。這個架構裡的量子電路不是效能的來源。

### 6.3 同樣的特徵，換掉記憶規則

| Variant | Params | Damped oscillation, noise 0 | Two tones, noise 0 | Jaynes–Cummings, noise 0 | Hénon map, noise 0 | Duffing, noise 0 | Damped oscillation, noise 0.02 | Two tones, noise 0.02 | Jaynes–Cummings, noise 0.02 | Hénon map, noise 0.02 | Duffing, noise 0.02 | vs first row |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| *Reference: one linear AR(p) for all sequences* | – | *7.0e-08* | *4.6e-08* | *1.3e-08* | *4.6e-02* | *2.3e-06* | *5.9e-03* | *5.1e-03* | *4.5e-03* | *4.7e-02* | *1.2e-03* | |
| *Reference: ridge AR(q) fitted inside each window* | – | *6.3e-17* | *1.1e-15* | *1.8e-08* | *6.0e-02* | *1.5e-06* | *7.5e-04* | *2.5e-03* | *4.0e-03* | *6.1e-02* | *9.3e-04* | |
| *Reference: ridge on quadratic features of two lags, fitted inside each window* | – | *6.3e-17* | *1.2e-02* | *3.3e-03* | *1.5e-16* | *1.2e-04* | *2.3e-03* | *1.5e-02* | *5.7e-03* | *2.6e-03* | *4.8e-03* | |
| gated least squares, prior in every write (QKAN-FWP-O) | 154 | 2.3e-09 | 4.4e-08 | 2.0e-07 | **3.4e-05** | 1.5e-07 | 9.1e-04 | 2.0e-03 | 2.9e-03 | 1.8e-03 | **8.7e-04** | – |
| exponentially weighted RLS (prior only as the initial condition) | 154 | 9.4e-10 | **2.3e-08** | **3.3e-08** | 3.7e-05 | **1.4e-07** | **9.0e-04** | **1.9e-03** | **2.9e-03** | 1.8e-03 | 8.7e-04 | 0.71× |
| least squares without gate (uniform weights) | 128 | **9.3e-10** | 2.9e-08 | 1.1e-07 | 4.7e-05 | 2.1e-07 | 3.2e-03 | 6.0e-03 | 6.8e-03 | 5.5e-03 | 2.4e-03 | 1.5× |
| normalised delta rule, 4 sweeps over the context | 154 | 6.3e-07 | 6.6e-06 | 1.9e-06 | 1.1e-04 | 4.5e-07 | 9.5e-04 | 2.6e-03 | 3.0e-03 | **1.5e-03** | 8.9e-04 | 4.6× |
| normalised delta rule, 1 sweep | 154 | 2.6e-06 | 2.2e-05 | 4.2e-06 | 1.4e-04 | 6.4e-07 | 1.1e-03 | 3.5e-03 | 3.3e-03 | 1.7e-03 | 9.3e-04 | 7.4× |
| no memory, 9 circuits (same number of parameters) | 154 | 5.8e-05 | 8.9e-05 | 2.3e-05 | 1.7e-03 | 6.5e-07 | 3.1e-03 | 5.7e-03 | 4.4e-03 | 3.2e-03 | 1.2e-03 | 23× |
| no memory, 6 circuits | 103 | 5.9e-05 | 8.6e-05 | 2.3e-05 | 1.7e-03 | 7.8e-07 | 3.4e-03 | 5.9e-03 | 4.3e-03 | 3.1e-03 | 1.2e-03 | 24× |

- **沒有記憶**：參數量相當（9 個電路，154 參數）的靜態模型差 23 倍，和 103 參數的靜態模型（24 倍）一樣。
  差距不是參數量造成的。
- **指數加權 RLS**（先驗只當初始值，$C_t = gC_{t-1} + (1-g)k_tk_t^\top$）是 0.71 倍，略好於每次寫入都重新注入先驗的做法
  （無雜訊的 Jaynes–Cummings 好 6 倍，其餘格子相當）。和論文 benchmark 上的結果一致（5.4 節：平滑序列較好、NARMA 較差）：
  重新注入先驗保證 $C_T \succeq \Lambda_0$，但沒有帶來精度上的好處，而 RLS 還能用 Sherman–Morrison 做 $O(F^2)$ 的遞迴更新。
- **不用 gate**（等權重）：沒有雜訊時相當，有雜訊時差 2.3–3.5 倍。Gate 讓模型調整證據相對於先驗的總權重（$\sum_t\beta_t < 1$）。
- **Delta rule**：掃一次差 7.4 倍，掃四次差 4.6 倍。差距集中在沒有雜訊的線性族（掃一次差 21–1100 倍，掃四次差 10–270 倍）；
  無雜訊的 Hénon 與 Duffing 差 3–4 倍；有雜訊時和最小平方相當（two tones 差 1.3–1.8 倍，有雜訊的 Hénon 上掃四次的 delta rule 反而最低）。
  這只是本報告實作的 normalised delta rule 的結果，不代表所有誤差驅動的遞迴方法。

float32 取代 float64 在系統族上沒有差別：

| Variant | Params | Geo-mean, all cells | Damped oscillation, noise 0 | Two tones, noise 0 | Jaynes–Cummings, noise 0 | Hénon map, noise 0 | Duffing, noise 0 | Damped oscillation, noise 0.02 | Two tones, noise 0.02 | Jaynes–Cummings, noise 0.02 | Hénon map, noise 0.02 | Duffing, noise 0.02 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| float32 instead of float64 (features, statistics and solve) | 154 | **1×** | 1.4× | 1.1× | 0.92× | 1.1× | 0.97× | 0.99× | 1× | 1× | 0.99× | 1× |

---

## 7. 上量子硬體：有限量測次數、數值精度與硬體誤差

QKAN-FWP-O 要解一個由量測值組成的線性方程 $C_T R = b_T$，量測雜訊與捨入誤差都可能被 $C_T^{-1}$ 放大——
這是把它搬上真機前最該先問的問題（7.1、7.2 節）。另一方面，fast weights 是量測算符這件事，在硬體上有兩個角度空間的模型沒有的性質：
query 的量測基底可以由 context 決定（7.3 節），以及 context 與 query 共同的硬體誤差會被最小平方吸收（7.4 節）。
這一節全部是模擬，沒有真機實驗。

### 7.1 Shot 預算的算法

`qkanfwp/daruan.py` 的模擬以「**每個電路、每個輸入**有 $S$ 次量測」為預算：

- 只讀 ⟨Z⟩ 的電路（HQKAN-Δ、QKAN-FWP+ 改用物理讀出的版本）把 $S$ 次全部用在 Z 基底；
- QKAN-FWP-O 需要同一個電路的 ⟨X⟩、⟨Y⟩、⟨Z⟩。三者不對易，不能從同一次量測得到，所以每個基底只有 $\lfloor S/3\rfloor$ 次；
- 每個期望值由對應次數的 ±1 結果估計，結果從精確的 binomial 分布抽樣（不是高斯近似）。

三個模型每次預測要跑的電路數不同（表中的「circuit runs」；N = 16 時 HQKAN-Δ 12、QKAN-FWP-O 54、QKAN-FWP+ 92），
所以每次預測的總量測次數是 circuit runs × $S$。下面的圖與表以 $S$ 為橫軸；要在相同的總量測次數下比較，
可以用這個欄位換算（例如 HQKAN-Δ 在同樣的總預算下可以用 4.5 倍的 $S$）。

每個模型訓練兩次：用精確期望值，以及訓練時就帶著 $S = 10^4$ 的抽樣雜訊（noise-aware）。
系統族的兩個任務所有模型都用 lr 3e-2。QKAN-FWP-O 有三列：預設（所有電路量 X、Y、Z）、query 改沿 context 決定的量測軸讀出（7.3 節），
以及內部用 float32 的版本（7.2 節）。

![shots](figures/om_shots.png)

S shots are available to every circuit for every input it processes. A ⟨Z⟩ read-out spends them in one basis; QKAN-FWP-O splits them over the X, Y and Z bases (⌊S/3⌋ each). Outcomes are binomial. "Circuit runs" is the number of circuit evaluations per prediction, so the total number of shots per prediction is circuit runs × S. Training used exact expectations, or the same finite-shot sampling at S = 10⁴ ("noise-aware").

| Task | Model | Circuit runs per prediction | Trained with | S = 10² | 10³ | 10⁴ | 10⁵ | 10⁶ | exact |
|---|---|---|---|---|---|---|---|---|---|
| Bessel J2 | QKAN-FWP-O | 54 | exact | 5.1e-06 | 6.9e-07 | 9.0e-08 | 1.3e-08 | 1.7e-09 | 1.4e-12 |
| Bessel J2 | QKAN-FWP-O | 54 | S = 10⁴ | 8.7e-11 | 1.4e-11 | 3.1e-12 | 3.0e-13 | 5.8e-14 | 2.7e-14 |
| Bessel J2 | QKAN-FWP-O, query read along the programmed axis | 54 | exact | 2.8e-06 | 4.4e-07 | 5.4e-08 | 1.1e-08 | 1.3e-09 | 1.4e-12 |
| Bessel J2 | QKAN-FWP-O, query read along the programmed axis | 54 | S = 10⁴ | 3.4e-11 | 6.6e-12 | 1.8e-12 | 2.5e-13 | 4.5e-14 | 2.2e-14 |
| Bessel J2 | QKAN-FWP-O, float32 | 54 | exact | 5.4e-06 | 7.0e-07 | 8.7e-08 | 1.3e-08 | 1.7e-09 | 1.4e-12 |
| Bessel J2 | QKAN-FWP-O, float32 | 54 | S = 10⁴ | 7.0e-11 | 1.6e-11 | 3.6e-12 | 4.0e-13 | 6.6e-14 | 3.2e-14 |
| Bessel J2 | HQKAN-Δ, ⟨Z⟩ read-out | 12 | exact | 2.2e-03 | 2.4e-04 | 2.3e-05 | 2.5e-06 | 5.2e-07 | 2.8e-07 |
| Bessel J2 | HQKAN-Δ, ⟨Z⟩ read-out | 12 | S = 10⁴ | 6.8e-04 | 6.7e-05 | 7.8e-06 | 1.4e-06 | 8.9e-07 | 8.1e-07 |
| Bessel J2 | QKAN-FWP+, ⟨Z⟩ read-out | 92 | exact | 3.6e-03 | 3.4e-04 | 3.6e-05 | 4.3e-06 | 1.2e-06 | 8.2e-07 |
| Bessel J2 | QKAN-FWP+, ⟨Z⟩ read-out | 92 | S = 10⁴ | 1.5e-03 | 1.6e-04 | 1.6e-05 | 2.2e-06 | 9.1e-07 | 7.4e-07 |
| NARMA10 | QKAN-FWP-O | 54 | exact | 1.4e-04 | 3.1e-05 | 8.8e-06 | 3.7e-06 | 2.2e-06 | 2.0e-06 |
| NARMA10 | QKAN-FWP-O | 54 | S = 10⁴ | 7.3e-05 | 1.6e-05 | 8.0e-06 | 5.9e-06 | 5.4e-06 | 5.3e-06 |
| NARMA10 | QKAN-FWP-O, query read along the programmed axis | 54 | exact | 1.0e-04 | 2.6e-05 | 8.2e-06 | 3.6e-06 | 2.2e-06 | 2.0e-06 |
| NARMA10 | QKAN-FWP-O, query read along the programmed axis | 54 | S = 10⁴ | 4.1e-05 | 8.6e-06 | 4.0e-06 | 2.8e-06 | 2.5e-06 | 2.4e-06 |
| NARMA10 | QKAN-FWP-O, float32 | 54 | exact | 4.1e-04 | 9.1e-05 | 2.2e-05 | 1.1e-05 | 9.2e-06 | 8.9e-06 |
| NARMA10 | QKAN-FWP-O, float32 | 54 | S = 10⁴ | 1.1e-04 | 2.1e-05 | 6.5e-06 | 3.9e-06 | 3.4e-06 | 3.3e-06 |
| NARMA10 | HQKAN-Δ, ⟨Z⟩ read-out | 12 | exact | 1.4e-03 | 1.4e-04 | 1.7e-05 | 4.3e-06 | 3.0e-06 | 2.9e-06 |
| NARMA10 | HQKAN-Δ, ⟨Z⟩ read-out | 12 | S = 10⁴ | 7.2e-04 | 7.3e-05 | 1.1e-05 | 4.8e-06 | 4.3e-06 | 4.2e-06 |
| NARMA10 | QKAN-FWP+, ⟨Z⟩ read-out | 92 | exact | 2.7e-03 | 2.8e-04 | 3.4e-05 | 1.1e-05 | 8.2e-06 | 8.0e-06 |
| NARMA10 | QKAN-FWP+, ⟨Z⟩ read-out | 92 | S = 10⁴ | 1.7e-03 | 2.1e-04 | 2.9e-05 | 1.3e-05 | 1.1e-05 | 1.1e-05 |
| Delayed quantum control | QKAN-FWP-O | 54 | exact | 7.8e-05 | 1.2e-05 | 2.5e-06 | 5.0e-07 | 1.2e-07 | 3.2e-08 |
| Delayed quantum control | QKAN-FWP-O | 54 | S = 10⁴ | 7.8e-07 | 1.8e-07 | 7.4e-08 | 5.1e-08 | 4.9e-08 | 4.8e-08 |
| Delayed quantum control | QKAN-FWP-O, query read along the programmed axis | 54 | exact | 3.9e-05 | 7.8e-06 | 1.8e-06 | 4.6e-07 | 1.0e-07 | 3.2e-08 |
| Delayed quantum control | QKAN-FWP-O, query read along the programmed axis | 54 | S = 10⁴ | 3.8e-07 | 1.2e-07 | 5.8e-08 | 4.2e-08 | 4.1e-08 | 4.1e-08 |
| Delayed quantum control | QKAN-FWP-O, float32 | 54 | exact | 6.5e-05 | 9.8e-06 | 1.9e-06 | 4.1e-07 | 1.1e-07 | 3.5e-08 |
| Delayed quantum control | QKAN-FWP-O, float32 | 54 | S = 10⁴ | 7.2e-07 | 1.3e-07 | 5.0e-08 | 3.6e-08 | 3.3e-08 | 3.3e-08 |
| Delayed quantum control | HQKAN-Δ, ⟨Z⟩ read-out | 12 | exact | 2.6e-03 | 2.7e-04 | 3.9e-05 | 1.6e-05 | 1.4e-05 | 1.4e-05 |
| Delayed quantum control | HQKAN-Δ, ⟨Z⟩ read-out | 12 | S = 10⁴ | 1.8e-03 | 1.7e-04 | 3.0e-05 | 1.7e-05 | 1.5e-05 | 1.5e-05 |
| Delayed quantum control | QKAN-FWP+, ⟨Z⟩ read-out | 92 | exact | 3.9e-03 | 3.7e-04 | 4.1e-05 | 8.9e-06 | 6.1e-06 | 5.8e-06 |
| Delayed quantum control | QKAN-FWP+, ⟨Z⟩ read-out | 92 | S = 10⁴ | 2.5e-03 | 2.2e-04 | 3.1e-05 | 8.4e-06 | 6.3e-06 | 6.1e-06 |
| Family: damped oscillation, noise 0.02 | QKAN-FWP-O | 54 | exact | 9.4e-04 | 9.1e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 |
| Family: damped oscillation, noise 0.02 | QKAN-FWP-O | 54 | S = 10⁴ | 9.4e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 |
| Family: damped oscillation, noise 0.02 | QKAN-FWP-O, query read along the programmed axis | 54 | exact | 9.2e-04 | 9.1e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 |
| Family: damped oscillation, noise 0.02 | QKAN-FWP-O, query read along the programmed axis | 54 | S = 10⁴ | 9.3e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 |
| Family: damped oscillation, noise 0.02 | QKAN-FWP-O, float32 | 54 | exact | 9.2e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 |
| Family: damped oscillation, noise 0.02 | QKAN-FWP-O, float32 | 54 | S = 10⁴ | 9.4e-04 | 9.1e-04 | 9.1e-04 | 9.1e-04 | 9.1e-04 | 9.1e-04 |
| Family: damped oscillation, noise 0.02 | HQKAN-Δ, ⟨Z⟩ read-out | 12 | exact | 8.7e-03 | 4.0e-03 | 3.5e-03 | 3.4e-03 | 3.4e-03 | 3.4e-03 |
| Family: damped oscillation, noise 0.02 | HQKAN-Δ, ⟨Z⟩ read-out | 12 | S = 10⁴ | 8.5e-03 | 4.0e-03 | 3.5e-03 | 3.4e-03 | 3.4e-03 | 3.4e-03 |
| Family: damped oscillation, noise 0.02 | QKAN-FWP+, ⟨Z⟩ read-out | 92 | exact | 1.5e-02 | 3.3e-03 | 2.2e-03 | 2.1e-03 | 2.1e-03 | 2.1e-03 |
| Family: damped oscillation, noise 0.02 | QKAN-FWP+, ⟨Z⟩ read-out | 92 | S = 10⁴ | 1.0e-02 | 3.0e-03 | 2.3e-03 | 2.2e-03 | 2.2e-03 | 2.2e-03 |
| Family: Hénon map | QKAN-FWP-O | 54 | exact | 1.2e-01 | 1.7e-02 | 2.3e-03 | 3.2e-04 | 6.6e-05 | 3.4e-05 |
| Family: Hénon map | QKAN-FWP-O | 54 | S = 10⁴ | 1.4e-02 | 1.6e-03 | 2.8e-04 | 1.5e-04 | 1.4e-04 | 1.4e-04 |
| Family: Hénon map | QKAN-FWP-O, query read along the programmed axis | 54 | exact | 5.5e-02 | 9.1e-03 | 1.5e-03 | 2.3e-04 | 5.5e-05 | 3.4e-05 |
| Family: Hénon map | QKAN-FWP-O, query read along the programmed axis | 54 | S = 10⁴ | 9.7e-03 | 1.2e-03 | 2.1e-04 | 1.2e-04 | 1.1e-04 | 1.0e-04 |
| Family: Hénon map | QKAN-FWP-O, float32 | 54 | exact | 1.2e-01 | 1.6e-02 | 2.3e-03 | 3.2e-04 | 6.8e-05 | 3.8e-05 |
| Family: Hénon map | QKAN-FWP-O, float32 | 54 | S = 10⁴ | 1.4e-02 | 1.6e-03 | 2.8e-04 | 1.4e-04 | 1.3e-04 | 1.3e-04 |
| Family: Hénon map | HQKAN-Δ, ⟨Z⟩ read-out | 12 | exact | 1.0e-02 | 2.4e-03 | 1.6e-03 | 1.5e-03 | 1.5e-03 | 1.5e-03 |
| Family: Hénon map | HQKAN-Δ, ⟨Z⟩ read-out | 12 | S = 10⁴ | 9.0e-03 | 2.3e-03 | 1.6e-03 | 1.5e-03 | 1.5e-03 | 1.5e-03 |
| Family: Hénon map | QKAN-FWP+, ⟨Z⟩ read-out | 92 | exact | 1.4e-02 | 1.9e-03 | 7.1e-04 | 5.9e-04 | 5.8e-04 | 5.8e-04 |
| Family: Hénon map | QKAN-FWP+, ⟨Z⟩ read-out | 92 | S = 10⁴ | 1.5e-02 | 2.3e-03 | 1.0e-03 | 9.2e-04 | 9.0e-04 | 9.0e-04 |

- **以精確期望值訓練的 QKAN-FWP-O 對量測次數很敏感。** Bessel 從 1.4e-12（精確）退到 9e-8（$S = 10^4$）與 5e-6（$S = 10^2$）；
  Hénon 在 $S \le 10^3$ 時比另外兩個模型差一個數量級。學到的先驗精度很小（7.2 節），量測雜訊被線性求解放大。
- **Noise-aware 訓練大幅改善**，而且在接近線性的任務上（Bessel、DQC、阻尼振盪）幾乎不再受 $S$ 影響：$S = 10^2$ 時 Bessel 是 8.7e-11、
  DQC 是 7.8e-7。但原因要說清楚：模型改為主要依賴 base-activation 的**線性項——它是古典計算的，沒有量測雜訊**——
  而把帶雜訊的 Bloch 特徵的權重降下來。這等於退回 5.4 節「只留線性項」的對照；在這些任務上非線性特徵本來就幾乎沒有貢獻。
- **真正需要非線性特徵的 Hénon map 才是有意義的測試。** Noise-aware 的 QKAN-FWP-O 在 $S = 10^4$ 是 2.8e-4（HQKAN-Δ 1.6e-3、
  QKAN-FWP+ 1.0e-3），$S = 10^3$ 時三者相當（1.6e-3／2.3e-3／2.3e-3），**$S = 10^2$ 時輸給 HQKAN-Δ**（1.4e-2 對 9.0e-3）。
  Query 改沿 context 決定的量測軸讀出之後是 2.1e-4、1.2e-3、9.7e-3：$S = 10^3$ 時比另外兩個模型低約 2 倍，$S = 10^2$ 時與 HQKAN-Δ 相當。
  但 HQKAN-Δ 每次預測只跑 12 個電路，QKAN-FWP-O 是 54 個：以相同的總量測次數比較，QKAN-FWP-O 在 Hénon 上要到每次預測
  約 $10^5$ 次量測以上才有明顯的優勢。
- **NARMA10**：兩種訓練方式下 QKAN-FWP-O 在 $S \le 10^4$ 都低於另外兩個模型（$S = 10^2$ 時 7e-5 ～ 1.4e-4 對 7e-4 ～ 2.7e-3），
  $S$ 更大時三者同一個量級。
- 另外兩個模型同樣受量測雜訊影響：$S \le 10^3$ 時它們的誤差由量測雜訊主導、大致與 $1/S$ 成正比。
- 第 6 節用古典特徵的對照（同一個記憶配上 Fourier、tanh 或 MLP 特徵）完全不需要量測，所以沒有這一節討論的任何退化。
  在本報告測過的任務上，它們在精確期望值下已經和 QKAN-FWP-O 一樣好或更好；有限量測次數只會讓量子電路的版本更差。
- 這一小節只有統計（shot）雜訊；靜態的硬體誤差見 7.4 節。沒有真機實驗。

### 7.2 Gram 矩陣的條件數與單精度

$C_T \succeq \Lambda_0$，所以條件數不超過 $(\lambda_{\max}(\Lambda_0) + \sum_t\beta_t\|k_t\|^2)/\lambda_{\min}(\Lambda_0)$；
學到的先驗精度越小，求解越病態。下表是訓練好的模型在 test window 上 $C_T$ 的條件數（中位數）：

| Task | Model | Trained with | S = 10² | 10³ | 10⁴ | 10⁵ | 10⁶ | exact |
|---|---|---|---|---|---|---|---|---|
| Bessel J2 | QKAN-FWP-O | exact | 9e+05 | 9e+05 | 9e+05 | 9e+05 | 9e+05 | 9e+05 |
| Bessel J2 | QKAN-FWP-O | S = 10⁴ | 1e+06 | 1e+06 | 1e+06 | 1e+06 | 1e+06 | 1e+06 |
| Bessel J2 | QKAN-FWP-O, query read along the programmed axis | exact | 9e+05 | 9e+05 | 9e+05 | 9e+05 | 9e+05 | 9e+05 |
| Bessel J2 | QKAN-FWP-O, query read along the programmed axis | S = 10⁴ | 1e+06 | 1e+06 | 1e+06 | 1e+06 | 1e+06 | 1e+06 |
| Bessel J2 | QKAN-FWP-O, float32 | exact | 9e+05 | 9e+05 | 9e+05 | 9e+05 | 9e+05 | 9e+05 |
| Bessel J2 | QKAN-FWP-O, float32 | S = 10⁴ | 1e+06 | 1e+06 | 1e+06 | 1e+06 | 1e+06 | 1e+06 |
| NARMA10 | QKAN-FWP-O | exact | 2e+06 | 2e+06 | 2e+06 | 2e+06 | 2e+06 | 2e+06 |
| NARMA10 | QKAN-FWP-O | S = 10⁴ | 1e+05 | 1e+05 | 1e+05 | 1e+05 | 1e+05 | 1e+05 |
| NARMA10 | QKAN-FWP-O, query read along the programmed axis | exact | 2e+06 | 2e+06 | 2e+06 | 2e+06 | 2e+06 | 2e+06 |
| NARMA10 | QKAN-FWP-O, query read along the programmed axis | S = 10⁴ | 7e+05 | 6e+05 | 5e+05 | 5e+05 | 5e+05 | 5e+05 |
| NARMA10 | QKAN-FWP-O, float32 | exact | 1e+06 | 1e+06 | 1e+06 | 1e+06 | 1e+06 | 1e+06 |
| NARMA10 | QKAN-FWP-O, float32 | S = 10⁴ | 8e+04 | 8e+04 | 8e+04 | 8e+04 | 8e+04 | 8e+04 |
| Delayed quantum control | QKAN-FWP-O | exact | 1e+06 | 1e+06 | 1e+06 | 1e+06 | 1e+06 | 1e+06 |
| Delayed quantum control | QKAN-FWP-O | S = 10⁴ | 3e+05 | 3e+05 | 3e+05 | 3e+05 | 3e+05 | 3e+05 |
| Delayed quantum control | QKAN-FWP-O, query read along the programmed axis | exact | 1e+06 | 1e+06 | 1e+06 | 1e+06 | 1e+06 | 1e+06 |
| Delayed quantum control | QKAN-FWP-O, query read along the programmed axis | S = 10⁴ | 5e+05 | 4e+05 | 4e+05 | 4e+05 | 4e+05 | 4e+05 |
| Delayed quantum control | QKAN-FWP-O, float32 | exact | 1e+06 | 1e+06 | 1e+06 | 1e+06 | 1e+06 | 1e+06 |
| Delayed quantum control | QKAN-FWP-O, float32 | S = 10⁴ | 6e+05 | 6e+05 | 6e+05 | 6e+05 | 6e+05 | 6e+05 |
| Family: damped oscillation, noise 0.02 | QKAN-FWP-O | exact | 2e+02 | 2e+02 | 2e+02 | 2e+02 | 2e+02 | 2e+02 |
| Family: damped oscillation, noise 0.02 | QKAN-FWP-O | S = 10⁴ | 2e+02 | 2e+02 | 2e+02 | 2e+02 | 2e+02 | 2e+02 |
| Family: damped oscillation, noise 0.02 | QKAN-FWP-O, query read along the programmed axis | exact | 2e+02 | 2e+02 | 2e+02 | 2e+02 | 2e+02 | 2e+02 |
| Family: damped oscillation, noise 0.02 | QKAN-FWP-O, query read along the programmed axis | S = 10⁴ | 4e+02 | 3e+02 | 3e+02 | 3e+02 | 3e+02 | 3e+02 |
| Family: damped oscillation, noise 0.02 | QKAN-FWP-O, float32 | exact | 2e+02 | 2e+02 | 2e+02 | 2e+02 | 2e+02 | 2e+02 |
| Family: damped oscillation, noise 0.02 | QKAN-FWP-O, float32 | S = 10⁴ | 1e+02 | 1e+02 | 1e+02 | 1e+02 | 1e+02 | 1e+02 |
| Family: Hénon map | QKAN-FWP-O | exact | 1e+05 | 1e+05 | 1e+05 | 2e+05 | 2e+05 | 2e+05 |
| Family: Hénon map | QKAN-FWP-O | S = 10⁴ | 2e+04 | 2e+04 | 2e+04 | 2e+04 | 2e+04 | 2e+04 |
| Family: Hénon map | QKAN-FWP-O, query read along the programmed axis | exact | 1e+05 | 1e+05 | 1e+05 | 2e+05 | 2e+05 | 2e+05 |
| Family: Hénon map | QKAN-FWP-O, query read along the programmed axis | S = 10⁴ | 4e+03 | 4e+03 | 4e+03 | 4e+03 | 4e+03 | 4e+03 |
| Family: Hénon map | QKAN-FWP-O, float32 | exact | 1e+05 | 1e+05 | 1e+05 | 1e+05 | 2e+05 | 2e+05 |
| Family: Hénon map | QKAN-FWP-O, float32 | S = 10⁴ | 3e+03 | 3e+03 | 3e+03 | 3e+03 | 3e+03 | 3e+03 |

- 條件數的中位數在論文的 benchmark 上約為 $10^5$–$10^6$：先驗精度的初值 $10^{-5}$ 是在 validation 上選的，在這些乾淨的序列上
  訓練後大致停在那裡（5.4 節的記憶權重表）。在有雜訊的系統族上模型把先驗精度學大，條件數約為 $10^2$；noise-aware 訓練也會學到較大的
  先驗精度，條件數在 NARMA10、DQC 與 Hénon 上降 3–20 倍（Bessel 與有雜訊的阻尼振盪不變）。
  量測次數本身幾乎不改變條件數：它由先驗精度與特徵的尺度決定。
- **單精度。** 其他模型都在 float32 下訓練，QKAN-FWP-O 預設用 float64，這是不對稱的。把特徵、統計量與求解全部改成 float32
  （`precision='float32'`；token 與增量仍和其他模型一樣先用 float64 形成）之後，上表五個任務的 MSE 與 float64 幾乎相同，
  Bessel 仍是 1.4e-12。條件數 $10^6$ 乘上 float32 的 $6\times10^{-8}$ 表示 $R_T$ 的各個分量只有一到兩位有效數字，
  但預測需要的是殘差被擬合的程度，而線性求解對殘差是穩定的；加上模型預測的是增量 $x_{T+1}-x_T$，1e-12 的 MSE（RMS 誤差 $10^{-6}$）
  並不需要雙精度。論文 benchmark 全部 24 格的 float32 結果在 5.4 節「其他設計選擇」的表（整體 1.2 倍；Bessel、SHM 與 JC 不變），系統族上是 1.0 倍（第 6 節）。

### 7.3 由 context 決定 query 的量測基底

讀出 $k_T\cdot R_T$ 對記憶是線性的，而 $R_T$ 在量 query 之前就已經由 context 算出來。對電路 $i$，$R_T$ 裡屬於它的三個 Bloch 係數
$\mathbf R_i$ 定義了一個量測算符 $\mathbf R_i\cdot\boldsymbol\sigma = |\mathbf R_i|\,(\hat{\mathbf r}_i\cdot\boldsymbol\sigma)$。
所以 query 的電路不必量 X、Y、Z 三個基底再組合：在量測前加一個由 $R_T$ 決定的單 qubit 旋轉，把量測軸轉到 $\hat{\mathbf r}_i$，
一個設定就直接估計 $\hat{\mathbf r}_i\cdot\mathbf n_i$，$S$ 次量測全部用在這個設定上（`query_readout='axis'`）。
換句話說，**fast weights 在硬體上的實現就是 query 電路的量測基底**——記憶寫入的是「下一次要量什麼」。
Context 的電路仍然要量三個基底（統計量 $k_tk_t^\top$ 需要完整的 Bloch vector）；古典的常數項與線性項沒有量測雜訊。

Query 讀出造成的 shot 變異數有封閉形式，而且在量 query 之前就能算出來（`ObservableMemoryFWP.query_shot_variance`）：

$$\mathrm{Var}_{\text{axis}} = \frac{s_y^2}{S}\sum_i |\mathbf R_i|^2\,(1-\cos_i^2),\quad \cos_i = \hat{\mathbf r}_i\cdot\mathbf n_i;\qquad
\mathrm{Var}_{XYZ} = \frac{s_y^2}{\lfloor S/3\rfloor}\sum_i\sum_{a\in\{x,y,z\}} R_{ia}^2\,(1-n_{ia}^2).$$

下表把 shot 雜訊的來源分開（`experiments/shot_noise.py --decompose`）：同一個訓練好的模型，只對 query 的電路抽樣、只對 context 的電路抽樣，
或全部抽樣；query 用三個基底或用 context 決定的量測軸。

The same trained model; only the listed circuit runs are sampled, the others use exact expectations. "Programmed axis": each query circuit is measured in the single basis given by the fast observable R_T (all S shots in one setting) instead of X, Y and Z (⌊S/3⌋ each).

| Task | Trained with | Sampled circuits | S = 10² | 10³ | 10⁴ | 10⁵ | 10⁶ | exact |
|---|---|---|---|---|---|---|---|---|
| Bessel J2 | exact | query circuits only, X/Y/Z | 6.1e-06 | 5.8e-07 | 6.7e-08 | 6.5e-09 | 6.7e-10 | 1.4e-12 |
| Bessel J2 | exact | query circuits only, programmed axis | 2.6e-06 | 2.6e-07 | 2.6e-08 | 2.5e-09 | 2.5e-10 | 1.4e-12 |
| Bessel J2 | exact | context circuits only | 1.3e-06 | 2.6e-07 | 4.0e-08 | 6.8e-09 | 1.2e-09 | 1.4e-12 |
| Bessel J2 | exact | all circuits, query in X/Y/Z | 5.2e-06 | 6.8e-07 | 8.6e-08 | 1.2e-08 | 1.7e-09 | 1.4e-12 |
| Bessel J2 | exact | all circuits, query along the programmed axis | 2.6e-06 | 4.2e-07 | 6.5e-08 | 9.5e-09 | 1.5e-09 | 1.4e-12 |
| Bessel J2 | S = 10⁴ | query circuits only, X/Y/Z | 7.0e-11 | 6.5e-12 | 6.5e-13 | 9.7e-14 | 3.5e-14 | 2.7e-14 |
| Bessel J2 | S = 10⁴ | query circuits only, programmed axis | 2.2e-11 | 2.2e-12 | 2.4e-13 | 5.2e-14 | 3.0e-14 | 2.7e-14 |
| Bessel J2 | S = 10⁴ | context circuits only | 5.2e-11 | 9.7e-12 | 2.4e-12 | 2.6e-13 | 5.0e-14 | 2.7e-14 |
| Bessel J2 | S = 10⁴ | all circuits, query in X/Y/Z | 9.0e-11 | 1.5e-11 | 2.9e-12 | 3.1e-13 | 5.7e-14 | 2.7e-14 |
| Bessel J2 | S = 10⁴ | all circuits, query along the programmed axis | 6.3e-11 | 1.2e-11 | 2.5e-12 | 2.9e-13 | 5.6e-14 | 2.7e-14 |
| NARMA10 | exact | query circuits only, X/Y/Z | 1.3e-04 | 1.6e-05 | 3.5e-06 | 2.1e-06 | 2.0e-06 | 2.0e-06 |
| NARMA10 | exact | query circuits only, programmed axis | 5.2e-05 | 6.9e-06 | 2.5e-06 | 2.1e-06 | 2.0e-06 | 2.0e-06 |
| NARMA10 | exact | context circuits only | 7.5e-05 | 2.4e-05 | 7.8e-06 | 3.7e-06 | 2.2e-06 | 2.0e-06 |
| NARMA10 | exact | all circuits, query in X/Y/Z | 1.4e-04 | 3.2e-05 | 8.7e-06 | 3.9e-06 | 2.3e-06 | 2.0e-06 |
| NARMA10 | exact | all circuits, query along the programmed axis | 8.7e-05 | 2.4e-05 | 7.8e-06 | 3.7e-06 | 2.3e-06 | 2.0e-06 |
| NARMA10 | S = 10⁴ | query circuits only, X/Y/Z | 7.9e-05 | 1.1e-05 | 5.9e-06 | 5.4e-06 | 5.3e-06 | 5.3e-06 |
| NARMA10 | S = 10⁴ | query circuits only, programmed axis | 2.8e-05 | 8.0e-06 | 5.7e-06 | 5.3e-06 | 5.3e-06 | 5.3e-06 |
| NARMA10 | S = 10⁴ | context circuits only | 3.4e-05 | 1.2e-05 | 7.0e-06 | 5.7e-06 | 5.4e-06 | 5.3e-06 |
| NARMA10 | S = 10⁴ | all circuits, query in X/Y/Z | 7.3e-05 | 1.7e-05 | 7.8e-06 | 5.8e-06 | 5.4e-06 | 5.3e-06 |
| NARMA10 | S = 10⁴ | all circuits, query along the programmed axis | 4.8e-05 | 1.4e-05 | 7.6e-06 | 5.8e-06 | 5.4e-06 | 5.3e-06 |
| Delayed quantum control | exact | query circuits only, X/Y/Z | 9.1e-05 | 8.4e-06 | 8.5e-07 | 1.1e-07 | 4.0e-08 | 3.2e-08 |
| Delayed quantum control | exact | query circuits only, programmed axis | 2.2e-05 | 2.3e-06 | 2.5e-07 | 5.5e-08 | 3.4e-08 | 3.2e-08 |
| Delayed quantum control | exact | context circuits only | 2.5e-05 | 6.6e-06 | 1.7e-06 | 3.8e-07 | 9.2e-08 | 3.2e-08 |
| Delayed quantum control | exact | all circuits, query in X/Y/Z | 8.3e-05 | 1.2e-05 | 2.1e-06 | 5.3e-07 | 1.2e-07 | 3.2e-08 |
| Delayed quantum control | exact | all circuits, query along the programmed axis | 3.9e-05 | 8.4e-06 | 1.9e-06 | 3.9e-07 | 1.1e-07 | 3.2e-08 |
| Delayed quantum control | S = 10⁴ | query circuits only, X/Y/Z | 4.8e-07 | 9.2e-08 | 5.1e-08 | 4.9e-08 | 4.8e-08 | 4.8e-08 |
| Delayed quantum control | S = 10⁴ | query circuits only, programmed axis | 1.4e-07 | 6.3e-08 | 4.9e-08 | 4.9e-08 | 4.9e-08 | 4.8e-08 |
| Delayed quantum control | S = 10⁴ | context circuits only | 3.5e-07 | 1.5e-07 | 6.6e-08 | 5.1e-08 | 4.9e-08 | 4.8e-08 |
| Delayed quantum control | S = 10⁴ | all circuits, query in X/Y/Z | 7.8e-07 | 1.8e-07 | 7.2e-08 | 5.1e-08 | 4.9e-08 | 4.8e-08 |
| Delayed quantum control | S = 10⁴ | all circuits, query along the programmed axis | 4.5e-07 | 1.5e-07 | 6.8e-08 | 5.2e-08 | 4.9e-08 | 4.8e-08 |
| Family: damped oscillation, noise 0.02 | exact | query circuits only, X/Y/Z | 9.3e-04 | 9.1e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 |
| Family: damped oscillation, noise 0.02 | exact | query circuits only, programmed axis | 9.1e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 |
| Family: damped oscillation, noise 0.02 | exact | context circuits only | 9.2e-04 | 9.1e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 |
| Family: damped oscillation, noise 0.02 | exact | all circuits, query in X/Y/Z | 9.4e-04 | 9.1e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 |
| Family: damped oscillation, noise 0.02 | exact | all circuits, query along the programmed axis | 9.2e-04 | 9.1e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 |
| Family: damped oscillation, noise 0.02 | S = 10⁴ | query circuits only, X/Y/Z | 9.2e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 |
| Family: damped oscillation, noise 0.02 | S = 10⁴ | query circuits only, programmed axis | 9.1e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 |
| Family: damped oscillation, noise 0.02 | S = 10⁴ | context circuits only | 9.2e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 |
| Family: damped oscillation, noise 0.02 | S = 10⁴ | all circuits, query in X/Y/Z | 9.4e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 |
| Family: damped oscillation, noise 0.02 | S = 10⁴ | all circuits, query along the programmed axis | 9.2e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 |
| Family: Hénon map | exact | query circuits only, X/Y/Z | 1.1e-01 | 1.1e-02 | 1.1e-03 | 1.4e-04 | 4.5e-05 | 3.4e-05 |
| Family: Hénon map | exact | query circuits only, programmed axis | 1.8e-02 | 1.8e-03 | 2.1e-04 | 5.2e-05 | 3.6e-05 | 3.4e-05 |
| Family: Hénon map | exact | context circuits only | 3.6e-02 | 7.3e-03 | 1.3e-03 | 2.1e-04 | 5.4e-05 | 3.4e-05 |
| Family: Hénon map | exact | all circuits, query in X/Y/Z | 1.2e-01 | 1.7e-02 | 2.3e-03 | 3.2e-04 | 6.5e-05 | 3.4e-05 |
| Family: Hénon map | exact | all circuits, query along the programmed axis | 5.6e-02 | 9.3e-03 | 1.5e-03 | 2.4e-04 | 5.6e-05 | 3.4e-05 |
| Family: Hénon map | S = 10⁴ | query circuits only, X/Y/Z | 8.5e-03 | 9.8e-04 | 2.2e-04 | 1.5e-04 | 1.4e-04 | 1.4e-04 |
| Family: Hénon map | S = 10⁴ | query circuits only, programmed axis | 3.0e-03 | 4.2e-04 | 1.7e-04 | 1.4e-04 | 1.4e-04 | 1.4e-04 |
| Family: Hénon map | S = 10⁴ | context circuits only | 4.8e-03 | 7.2e-04 | 2.0e-04 | 1.4e-04 | 1.4e-04 | 1.4e-04 |
| Family: Hénon map | S = 10⁴ | all circuits, query in X/Y/Z | 1.4e-02 | 1.6e-03 | 2.8e-04 | 1.5e-04 | 1.4e-04 | 1.4e-04 |
| Family: Hénon map | S = 10⁴ | all circuits, query along the programmed axis | 7.9e-03 | 1.0e-03 | 2.2e-04 | 1.4e-04 | 1.4e-04 | 1.4e-04 |

Excess = test MSE with only the query circuits sampled − test MSE with exact expectations. Closed form: y_scale² Σ_i Σ_a R_ia² (1 − n_ia²) / ⌊S/3⌋ for X/Y/Z and y_scale² Σ_i |R_i|² (1 − cos_i²) / S for the programmed axis.

| Task | Excess, X/Y/Z | Closed form, X/Y/Z | Excess, programmed axis | Closed form, programmed axis | Variance X/Y/Z ÷ programmed axis (closed form) |
|---|---|---|---|---|---|
| Bessel J2 | 5.78e-07 | 6.15e-07 | 2.61e-07 | 2.52e-07 | 2.4× |
| NARMA10 | 1.42e-05 | 1.35e-05 | 4.89e-06 | 5.20e-06 | 2.6× |
| Delayed quantum control | 8.41e-06 | 8.39e-06 | 2.26e-06 | 2.19e-06 | 3.8× |
| Family: damped oscillation, noise 0.02 | 1.79e-06 | 1.98e-06 | 8.50e-07 | 6.45e-07 | 3.1× |
| Family: Hénon map | 1.12e-02 | 1.10e-02 | 1.80e-03 | 1.75e-03 | 6.3× |

- **封閉形式與模擬一致。** 只對 query 的電路抽樣時多出來的 MSE，和封閉形式算出的變異數在 Bessel、NARMA10、DQC 與 Hénon 上相差 5% 以內
  （有雜訊的阻尼振盪是兩個幾乎相等的數相減，誤差較大）。也就是說，一次預測的 shot 誤差可以在量 query 之前由 $R_T$ 估計出來。
- **沿 context 決定的量測軸讀出，query 的 shot 變異數降 2.4–6.3 倍**（Bessel 2.4、NARMA10 2.6、阻尼振盪 3.1、DQC 3.8、Hénon 6.3）。
  三個基底平分預算本身就損失 3 倍，其餘的差別來自 $\mathbf R_i$ 與 $\mathbf n_i$ 的相對方向。
- **剩下的瓶頸是 context 的電路。** 以精確期望值訓練的模型在 $S = 10^4$：Bessel 上 query（量測軸）貢獻 2.6e-8、context 貢獻 4.0e-8；
  Hénon 上是 2.1e-4 對 1.3e-3。所以全部電路都抽樣時，整體的 MSE 只降 1.1–2.1 倍（$S = 10^2$：Bessel 5.2e-6 → 2.6e-6，Hénon 0.12 → 0.056）。
  Context 的統計量 $k_tk_t^\top$ 需要完整的 Bloch vector，這裡沒有對應的省法；noise-aware 訓練之後的排序相同。
- 這個讀出需要在 context 的量測結果出來之後才決定 query 的量測基底，所以一次預測要分兩輪執行電路（先 context、後 query）；
  三個基底的讀出則可以一輪做完。

### 7.4 靜態的硬體誤差：context 內的校正

真機上除了統計雜訊還有系統性的誤差：讀出誤差、去極化、閘的校正誤差。它們在一段時間內大致固定，但會隨校正狀態漂移，
訓練時（模擬器，或某一天的硬體）並不知道。這裡測試的情境是：**所有模型都用理想電路訓練，測試時在每一個電路打開同一個靜態誤差，
不重新訓練、不做 error mitigation**（`experiments/device_noise.py`；期望值是精確的，沒有 shot 雜訊；baseline 用物理的 ⟨Z⟩ 讀出）：

- 讀出誤差 $e$：$P(\text{讀成 }1\mid 0) = e$、$P(\text{讀成 }0\mid 1) = 2e$，每個量到的期望值 $v$ 變成 $(1-3e)\,v + e$；
- 去極化 $p$：$v \to (1-p)\,v$；
- 過旋轉 $\varepsilon$：每個旋轉閘（可訓練的與編碼輸入的）實際轉了 $(1+\varepsilon)$ 倍的角度。

**為什麼預期 QKAN-FWP-O 受的影響小。** 任何固定的單 qubit 雜訊通道對 Bloch vector 的作用都是仿射的；reps = 1 時輸入只經過一次編碼閘，
所以即使雜訊夾在閘與閘之間，帶誤差的特徵仍是 $\{1,\cos u,\sin u\}$ 的線性組合，可以寫成 $k' = Ak$（$A$ 固定，偏移由常數特徵吸收）。
Context 的配對與 query 是在**同一台裝置**上量的，所以最小平方解跟著變成 $R' = A^{-\top}R$，預測 $k'\cdot R' = k\cdot R$ 不變。
配對數多於特徵數、先驗趨近於零時這嚴格成立（`tests/test_obsmem.py` 有這個測試）；實際的模型配對數（N = 16 時 9 個）少於特徵數（25 個），
先驗有作用，所以只是近似。過旋轉不是特徵的仿射變換（它改變 $\cos$、$\sin$ 的頻率），但同樣同時作用在 context 與 query 上。
角度空間的模型沒有對應的機制：慢參數是對理想電路訓練的，讀出的權重固定。

![device errors](figures/om_device.png)

五個任務的幾何平均（帶誤差的 test MSE ÷ 理想裝置的 test MSE）：

| Model | read-out 0.5 % | read-out 1 % | read-out 2 % | read-out 5 % | depolarising 1 % | depolarising 5 % | over-rotation 1 % | over-rotation 5 % |
|---|---|---|---|---|---|---|---|---|
| QKAN-FWP-O | 1× | 1× | 1.1× | 1.6× | 1× | 1.1× | 1× | 1.1× |
| QKAN-FWP-O with the RLS memory | 1× | 1× | 1.1× | 1.5× | 1× | 1.1× | 1× | 1.2× |
| QKAN-FWP-O features without memory (9 circuits) | 1× | 1.2× | 1.9× | 4.7× | 1.1× | 2.1× | 1× | 1.2× |
| QKAN-FWP-O features without memory (6 circuits) | 0.92× | 0.92× | 1.3× | 3.4× | 0.97× | 0.99× | 1.1× | 1.4× |
| HQKAN-Δ, ⟨Z⟩ read-out | 8.5× | 20× | 58× | 289× | 2.2× | 11× | 2.7× | 21× |
| QKAN-FWP+, ⟨Z⟩ read-out | 5.4× | 13× | 38× | 192× | 2.4× | 19× | 2.4× | 21× |

Read-out error e: every measured expectation v becomes (1 − 3e)·v + e (P(read 1 | 0) = e, P(read 0 | 1) = 2e). Depolarising p: v becomes (1 − p)·v. Over-rotation ε: every rotation angle is executed as (1 + ε)·angle. The error is the same in every circuit run of a window.

| Task | Model | Ideal device | read-out 0.5 % | read-out 1 % | read-out 2 % | read-out 5 % | depolarising 1 % | depolarising 5 % | over-rotation 1 % | over-rotation 5 % |
|---|---|---|---|---|---|---|---|---|---|---|
| Bessel J2 | QKAN-FWP-O | 1.4e-12 | 1.5e-12 | 1.6e-12 | 2.0e-12 | 4.5e-12 | 1.4e-12 | 1.6e-12 | 1.4e-12 | 1.5e-12 |
| Bessel J2 | QKAN-FWP-O with the RLS memory | 9.4e-13 | 1.0e-12 | 1.1e-12 | 1.2e-12 | 1.7e-12 | 1.0e-12 | 1.2e-12 | 9.7e-13 | 1.1e-12 |
| Bessel J2 | QKAN-FWP-O features without memory (9 circuits) | 1.8e-08 | 1.5e-08 | 2.3e-08 | 7.3e-08 | 4.9e-07 | 2.0e-08 | 1.3e-07 | 2.3e-08 | 5.6e-08 |
| Bessel J2 | QKAN-FWP-O features without memory (6 circuits) | 2.4e-08 | 1.4e-08 | 1.1e-08 | 2.8e-08 | 2.6e-07 | 1.8e-08 | 9.6e-09 | 3.2e-08 | 8.0e-08 |
| Bessel J2 | HQKAN-Δ, ⟨Z⟩ read-out | 2.8e-07 | 8.3e-05 | 3.3e-04 | 1.3e-03 | 8.1e-03 | 4.2e-06 | 9.7e-05 | 7.5e-06 | 1.9e-04 |
| Bessel J2 | QKAN-FWP+, ⟨Z⟩ read-out | 8.2e-07 | 4.1e-05 | 1.6e-04 | 5.9e-04 | 3.1e-03 | 6.6e-06 | 1.5e-04 | 9.3e-06 | 2.4e-04 |
| NARMA10 | QKAN-FWP-O | 2.0e-06 | 2.0e-06 | 2.0e-06 | 2.0e-06 | 2.0e-06 | 2.0e-06 | 2.0e-06 | 2.0e-06 | 2.0e-06 |
| NARMA10 | QKAN-FWP-O with the RLS memory | 1.9e-06 | 1.9e-06 | 1.9e-06 | 1.8e-06 | 1.8e-06 | 1.9e-06 | 1.9e-06 | 1.9e-06 | 2.0e-06 |
| NARMA10 | QKAN-FWP-O features without memory (9 circuits) | 2.7e-06 | 2.9e-06 | 3.2e-06 | 3.9e-06 | 7.8e-06 | 2.8e-06 | 3.4e-06 | 2.7e-06 | 2.7e-06 |
| NARMA10 | QKAN-FWP-O features without memory (6 circuits) | 3.2e-06 | 3.5e-06 | 3.9e-06 | 4.8e-06 | 9.5e-06 | 3.3e-06 | 4.2e-06 | 3.1e-06 | 3.1e-06 |
| NARMA10 | HQKAN-Δ, ⟨Z⟩ read-out | 2.9e-06 | 5.0e-05 | 2.0e-04 | 7.9e-04 | 5.0e-03 | 5.4e-06 | 7.3e-05 | 9.0e-06 | 1.5e-04 |
| NARMA10 | QKAN-FWP+, ⟨Z⟩ read-out | 8.0e-06 | 8.6e-05 | 3.3e-04 | 1.3e-03 | 8.5e-03 | 2.0e-05 | 4.0e-04 | 1.9e-05 | 2.6e-04 |
| Delayed quantum control | QKAN-FWP-O | 3.2e-08 | 3.3e-08 | 3.4e-08 | 3.6e-08 | 4.3e-08 | 3.3e-08 | 3.5e-08 | 3.1e-08 | 2.7e-08 |
| Delayed quantum control | QKAN-FWP-O with the RLS memory | 1.1e-08 | 1.2e-08 | 1.2e-08 | 1.4e-08 | 2.0e-08 | 1.2e-08 | 1.4e-08 | 1.1e-08 | 1.2e-08 |
| Delayed quantum control | QKAN-FWP-O features without memory (9 circuits) | 6.2e-07 | 8.6e-07 | 1.2e-06 | 2.1e-06 | 7.2e-06 | 8.0e-07 | 2.5e-06 | 5.4e-07 | 4.3e-07 |
| Delayed quantum control | QKAN-FWP-O features without memory (6 circuits) | 6.4e-07 | 6.7e-07 | 7.3e-07 | 9.1e-07 | 2.0e-06 | 7.0e-07 | 1.0e-06 | 6.0e-07 | 6.4e-07 |
| Delayed quantum control | HQKAN-Δ, ⟨Z⟩ read-out | 1.4e-05 | 9.2e-05 | 3.0e-04 | 1.1e-03 | 6.5e-03 | 2.2e-05 | 1.0e-04 | 2.0e-05 | 3.5e-04 |
| Delayed quantum control | QKAN-FWP+, ⟨Z⟩ read-out | 5.8e-06 | 3.9e-05 | 1.3e-04 | 4.6e-04 | 2.7e-03 | 2.1e-05 | 3.2e-04 | 1.3e-05 | 1.2e-04 |
| Family: damped oscillation, noise 0.02 | QKAN-FWP-O | 9.0e-04 | 9.0e-04 | 9.0e-04 | 9.1e-04 | 9.4e-04 | 9.0e-04 | 9.1e-04 | 9.0e-04 | 9.1e-04 |
| Family: damped oscillation, noise 0.02 | QKAN-FWP-O with the RLS memory | 9.0e-04 | 9.0e-04 | 9.0e-04 | 9.1e-04 | 9.6e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 |
| Family: damped oscillation, noise 0.02 | QKAN-FWP-O features without memory (9 circuits) | 3.1e-03 | 3.1e-03 | 3.1e-03 | 3.2e-03 | 3.6e-03 | 3.1e-03 | 3.2e-03 | 3.1e-03 | 3.1e-03 |
| Family: damped oscillation, noise 0.02 | QKAN-FWP-O features without memory (6 circuits) | 3.4e-03 | 3.4e-03 | 3.4e-03 | 3.5e-03 | 4.2e-03 | 3.4e-03 | 3.4e-03 | 3.4e-03 | 3.4e-03 |
| Family: damped oscillation, noise 0.02 | HQKAN-Δ, ⟨Z⟩ read-out | 3.4e-03 | 3.6e-03 | 3.9e-03 | 5.2e-03 | 1.4e-02 | 3.4e-03 | 3.7e-03 | 3.5e-03 | 4.9e-03 |
| Family: damped oscillation, noise 0.02 | QKAN-FWP+, ⟨Z⟩ read-out | 2.1e-03 | 2.2e-03 | 2.5e-03 | 3.6e-03 | 1.1e-02 | 2.1e-03 | 2.5e-03 | 2.2e-03 | 4.6e-03 |
| Family: Hénon map | QKAN-FWP-O | 3.4e-05 | 3.4e-05 | 3.4e-05 | 3.8e-05 | 7.0e-05 | 3.4e-05 | 3.6e-05 | 3.7e-05 | 6.2e-05 |
| Family: Hénon map | QKAN-FWP-O with the RLS memory | 3.7e-05 | 3.7e-05 | 3.7e-05 | 4.2e-05 | 8.4e-05 | 3.7e-05 | 3.9e-05 | 4.0e-05 | 6.7e-05 |
| Family: Hénon map | QKAN-FWP-O features without memory (9 circuits) | 1.7e-03 | 1.7e-03 | 1.8e-03 | 2.0e-03 | 3.7e-03 | 1.7e-03 | 2.0e-03 | 1.8e-03 | 2.3e-03 |
| Family: Hénon map | QKAN-FWP-O features without memory (6 circuits) | 1.7e-03 | 1.7e-03 | 1.8e-03 | 2.4e-03 | 6.3e-03 | 1.7e-03 | 1.9e-03 | 1.7e-03 | 2.7e-03 |
| Family: Hénon map | HQKAN-Δ, ⟨Z⟩ read-out | 1.5e-03 | 1.8e-03 | 2.7e-03 | 6.4e-03 | 3.2e-02 | 1.6e-03 | 3.3e-03 | 1.7e-03 | 5.2e-03 |
| Family: Hénon map | QKAN-FWP+, ⟨Z⟩ read-out | 5.8e-04 | 7.2e-04 | 1.1e-03 | 2.9e-03 | 1.6e-02 | 6.6e-04 | 2.6e-03 | 7.8e-04 | 5.0e-03 |

- **QKAN-FWP-O 幾乎不受影響**：1% 的讀出誤差、去極化或過旋轉下 MSE 不變（1.0 倍），5% 時是 1.1–1.6 倍；
  Bessel 在 5% 的讀出誤差下仍是 4.5e-12。把記憶換成 RLS 的版本行為相同。
- **HQKAN-Δ 與 QKAN-FWP+ 在 1% 的讀出誤差下差 20 倍與 13 倍，5% 時差約 290 倍與 190 倍**；去極化與過旋轉 5% 時差 11–21 倍。
  在 Bessel、NARMA10 與 DQC 上，0.5% 的讀出誤差就讓它們的 MSE 上升 7–300 倍。
- **這個穩健性有兩個來源，要分開看。**
  1. *古典的線性項。* 同樣的特徵但沒有記憶的版本（表中的「without memory」）在 1% 時也幾乎不變，5% 的讀出誤差下差 3–5 倍：
     預測的主要部分由 base-activation 的線性項承擔，它是古典計算的，沒有硬體誤差。HQKAN-Δ 與 QKAN-FWP+ 的輸出則全部經過電路。
  2. *記憶的校正。* 下表把同一個誤差只放在 query 的電路、或只放在 context 的電路（等於誤差在視窗內改變了）。
     1% 的讀出誤差下，Bessel 從 1.6e-12 變成 1.3e-7（8 萬倍），Hénon 從 3.4e-5 變成 1.7e-3（50 倍），DQC 差 22 倍。
     也就是說 Bloch 特徵在讀出中的權重並不小；誤差之所以不影響預測，是因為它同時出現在 context 與 query，被最小平方吸收。
     NARMA10 與有雜訊的阻尼振盪幾乎不靠 Bloch 特徵，所以沒有差別。

| Task | Error | Ideal device | All circuits | Query circuits only | Context circuits only | Query only ÷ all |
|---|---|---|---|---|---|---|
| Bessel J2 | read-out 1 % | 1.4e-12 | 1.6e-12 | 1.3e-07 | 1.4e-07 | 8.1e4× |
| Bessel J2 | depolarising 1 % | 1.4e-12 | 1.4e-12 | 5.9e-09 | 6.0e-09 | 4137× |
| Bessel J2 | over-rotation 1 % | 1.4e-12 | 1.4e-12 | 1.0e-08 | 1.0e-08 | 7344× |
| NARMA10 | read-out 1 % | 2.0e-06 | 2.0e-06 | 3.3e-06 | 2.9e-06 | 1.7× |
| NARMA10 | depolarising 1 % | 2.0e-06 | 2.0e-06 | 2.2e-06 | 2.0e-06 | 1.1× |
| NARMA10 | over-rotation 1 % | 2.0e-06 | 2.0e-06 | 2.1e-06 | 2.1e-06 | 1.1× |
| Delayed quantum control | read-out 1 % | 3.2e-08 | 3.4e-08 | 7.6e-07 | 9.3e-07 | 22× |
| Delayed quantum control | depolarising 1 % | 3.2e-08 | 3.3e-08 | 1.1e-07 | 1.5e-07 | 3.3× |
| Delayed quantum control | over-rotation 1 % | 3.2e-08 | 3.1e-08 | 1.1e-07 | 1.1e-07 | 3.5× |
| Family: damped oscillation, noise 0.02 | read-out 1 % | 9.0e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 | 1× |
| Family: damped oscillation, noise 0.02 | depolarising 1 % | 9.0e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 | 1× |
| Family: damped oscillation, noise 0.02 | over-rotation 1 % | 9.0e-04 | 9.0e-04 | 9.0e-04 | 9.0e-04 | 1× |
| Family: Hénon map | read-out 1 % | 3.4e-05 | 3.4e-05 | 1.7e-03 | 1.8e-03 | 50× |
| Family: Hénon map | depolarising 1 % | 3.4e-05 | 3.4e-05 | 3.5e-04 | 3.4e-04 | 10× |
| Family: Hénon map | over-rotation 1 % | 3.4e-05 | 3.7e-05 | 2.2e-04 | 2.1e-04 | 5.9× |

- **適用範圍。** (i) 誤差必須在一個視窗（N 步的電路執行）之內不變；如果在視窗內漂移，就是上表「只放在 query」的情形，
  此時 QKAN-FWP-O 並不比沒有記憶的版本好。(ii) 只測了三種簡單的誤差模型，沒有 crosstalk、與時間相關的雜訊或真機實驗，
  也沒有和 shot 雜訊同時模擬。(iii) Baseline 沒有做任何補救：讀出誤差可以用標準的 readout mitigation 校正，
  輸出的偏移也可以用少量有標籤的資料重新校正，但這些需要額外的校正電路或資料；QKAN-FWP-O 是每個視窗自動完成。
  (iv) 用古典特徵的對照組（第 6 節）不需要量子硬體，沒有這個問題；這一節比較的是同樣要在量子硬體上執行的模型。

---

## 8. 結果：太陽黑子週期預測

528 個月 → 132 個月的 direct multi-step 預測，論文的協定（peak-aware loss、100 epochs、batch 32、取 validation loss
最低的 checkpoint、lr 由 validation 從論文的 grid 選）。指標：scaled MSE、峰值振幅誤差 PAE（黑子數）、峰值時間誤差 PTE（月）。

### 8.1 切分方式：對 window 的索引切分會讓 targets 重疊

論文的敘述是對 sliding window 做 chronological 80/10/10 切分。每個 window 的 target 長 132 個月，所以相鄰 split 的 targets
重疊 131 個月：validation 最後的 targets 落在第一個 test 預測的歷史截止點之後，用 validation loss 選 checkpoint 等於偷看了
當時還沒發生的資料；training 最後的 targets 也落在 validation 期間內。三種切分比例都有這個問題：

| 切分 | 方式 | Training targets 結束 | Validation targets | 第一個 test 預測的歷史截止點 | Test targets |
|---|---|---|---|---|---|
| 80/10/10 | window 索引（論文） | 1981/09 | 1970/11 – 2003/11 | 1992/12 | 1993/01 – 2026/02 |
| 80/10/10 | 依 target 時間 | 1970/10 | 1970/11 – 1992/12 | 1992/12 | 1993/01 – 2026/02 |
| 60/20/20 | window 索引 | 1937/03 | 1926/05 – 1981/09 | 1970/10 | 1970/11 – 2026/02 |
| 60/20/20 | 依 target 時間 | 1926/04 | 1926/05 – 1970/10 | 1970/10 | 1970/11 – 2026/02 |
| 70/15/15 | window 索引 | 1959/06 | 1948/08 – 1992/10 | 1981/11 | 1981/12 – 2026/02 |
| 70/15/15 | 依 target 時間 | 1948/07 | 1948/08 – 1981/11 | 1981/11 | 1981/12 – 2026/02 |

「依 target 時間」的做法（`run_solar.py --purge`）是把 training 與 validation 各自最後 131 個 window 拿掉，
使每個 split 的 targets 都結束在下一個 split 第一個預測起點之前；test windows 不變，所以兩種切法的 test 指標可以直接對照。
**下面以依 target 時間切分的結果為準**；論文切法的結果只用來和論文印出的數字對照。

### 8.2 依 target 時間切分的結果

For every model the learning rate is the one with the lowest validation loss among those run (the paper's grid); test metrics are mean ± std over seeds. The test windows are the same as in the window-index split.

#### paper split 80/10/10

| Model | Params | lr (by validation) | Seeds | Val. loss | Scaled MSE ↓ | PAE ↓ | PTE ↓ |
|---|---|---|---|---|---|---|---|
| GQKAN-QKANFWP (re-implemented baseline) | 12,423 | 0.0025 | 5 | 2.98 | 0.0208 ± 0.0015 | 43.9 ± 2.1 | 29.8 ± 3.5 |
| QKAN-FWP+ | 11,732 | 0.001 | 5 | 2.94 | 0.0163 ± 0.0009 | 36.3 ± 0.8 | 20.1 ± 2.0 |
| QKAN-FWP-O without fast weights (static observable) | 496 | 0.0025 | 5 | 2.87 | 0.0150 ± 0.0011 | 34.5 ± 1.3 | 19.0 ± 1.1 |
| QKAN-FWP-O | 547 | 0.001 | 5 | 3.50 | 0.0173 ± 0.0003 | 41.7 ± 2.2 | 36.6 ± 3.8 |
| *Reference: repeat the last cycle, 13-month smoothed (no training)* | 0 | – | – | – | 0.0156 | 35.9 | 16.2 |

#### 60/20/20 (test targets 1971–2026)

| Model | Params | lr (by validation) | Seeds | Val. loss | Scaled MSE ↓ | PAE ↓ | PTE ↓ |
|---|---|---|---|---|---|---|---|
| GQKAN-QKANFWP (re-implemented baseline) | 12,423 | 0.0025 | 5 | 4.72 | 0.0177 ± 0.0006 | 73.0 ± 4.7 | 28.1 ± 1.0 |
| QKAN-FWP+ | 11,732 | 0.0025 | 5 | 4.58 | 0.0206 ± 0.0037 | 70.2 ± 4.3 | 29.5 ± 3.1 |
| QKAN-FWP-O without fast weights (static observable) | 496 | 0.0025 | 5 | 4.20 | 0.0165 ± 0.0001 | 54.7 ± 0.6 | 19.1 ± 0.8 |
| QKAN-FWP-O | 547 | 0.0025 | 5 | 3.50 | 0.0184 ± 0.0002 | 59.0 ± 0.8 | 28.7 ± 1.0 |
| *Reference: repeat the last cycle, 13-month smoothed (no training)* | 0 | – | – | – | 0.0166 | 53.1 | 18.7 |

#### 70/15/15 (test targets 1982–2026)

| Model | Params | lr (by validation) | Seeds | Val. loss | Scaled MSE ↓ | PAE ↓ | PTE ↓ |
|---|---|---|---|---|---|---|---|
| GQKAN-QKANFWP (re-implemented baseline) | 12,423 | 0.0025 | 3 | 4.57 | 0.0155 ± 0.0002 | 64.5 ± 4.3 | 27.3 ± 0.7 |
| QKAN-FWP+ | 11,732 | 0.0025 | 3 | 4.70 | 0.0154 ± 0.0007 | 46.5 ± 3.5 | 24.6 ± 1.1 |
| QKAN-FWP-O without fast weights (static observable) | 496 | 0.0025 | 3 | 3.77 | 0.0120 ± 0.0001 | 47.9 ± 0.6 | 21.1 ± 0.2 |
| QKAN-FWP-O | 547 | 0.0025 | 3 | 3.75 | 0.0125 ± 0.0004 | 47.3 ± 1.8 | 22.2 ± 0.9 |
| *Reference: repeat the last cycle, 13-month smoothed (no training)* | 0 | – | – | – | 0.0168 | 38.5 | 18.8 |

「相對 baseline」是對重新實作的 GQKAN-QKANFWP 的 MSE 變化：

| 切分 | QKAN-FWP+ | QKAN-FWP-O 靜態版本 | QKAN-FWP-O | 重複上一個週期（零參數） |
|---|---|---|---|---|
| 80/10/10 | −22% | −28% | −17% | −25% |
| 60/20/20 | +16% | −7% | +4% | −6% |
| 70/15/15 | −1% | −23% | −19% | +8% |

- **沒有模型穩定贏過零參數的「重複上一個週期」。** MSE：QKAN-FWP-O 的靜態版本（496 個參數）在 80/10/10 與 60/20/20 和它相同
  （0.0150 對 0.0156、0.0165 對 0.0166，差距在一個標準差之內），只有 70/15/15 明顯較低（0.0120 對 0.0168）；其餘模型都在至少一種切分上
  比它差。峰值時間誤差 PTE 三種切分都是參考線最好；峰值振幅誤差 PAE 只有 80/10/10 的靜態版本略低（34.5 對 35.9）。
- **相對於重新實作的 baseline**：QKAN-FWP-O 的靜態版本在三種切分都較低（−28%、−7%、−23%），參數量是它的 4%。
  QKAN-FWP+ 不穩定（−22%、+16%、−1%）。
- **In-context 記憶在這個任務上沒有幫助。** 有記憶的 QKAN-FWP-O 在三種切分都比它自己的靜態版本差
  （0.0173／0.0184／0.0125 對 0.0150／0.0165／0.0120），80/10/10 的 PTE 差很多（36.6 對 19.0 個月）。

### 8.3 論文的切法（window 索引）

For every model the learning rate is the one with the lowest validation loss among those run (the paper's grid); test metrics are mean ± std over seeds.

#### paper split 80/10/10

| Model | Params | lr (by validation) | Seeds | Val. loss | Scaled MSE ↓ | PAE ↓ | PTE ↓ |
|---|---|---|---|---|---|---|---|
| GQKAN-QKANFWP (re-implemented baseline) | 12,423 | 0.001 | 5 | 2.51 | 0.0177 ± 0.0010 | 45.8 ± 2.8 | 26.1 ± 2.2 |
| QKAN-FWP+ | 11,732 | 0.001 | 5 | 3.29 | 0.0146 ± 0.0010 | 36.0 ± 0.4 | 18.6 ± 1.7 |
| QKAN-FWP-O without fast weights (static observable) | 496 | 0.0025 | 5 | 2.37 | 0.0144 ± 0.0002 | 35.6 ± 1.1 | 21.3 ± 1.5 |
| QKAN-FWP-O | 547 | 0.0025 | 5 | 2.61 | 0.0134 ± 0.0005 | 33.1 ± 1.4 | 23.7 ± 1.1 |
| *Reference: repeat the last cycle, 13-month smoothed (no training)* | 0 | – | – | – | 0.0156 | 35.9 | 16.2 |
| *Printed in arXiv:2605.06734 for GQKAN-QKANFWP* | 12,474 | – | 5 | – | 0.0168 ± 0.0016 | 39.59 ± 2.82 | 21.89 ± 1.57 |

#### 60/20/20 (test targets 1971–2026)

| Model | Params | lr (by validation) | Seeds | Val. loss | Scaled MSE ↓ | PAE ↓ | PTE ↓ |
|---|---|---|---|---|---|---|---|
| GQKAN-QKANFWP (re-implemented baseline) | 12,423 | 0.0025 | 5 | 4.04 | 0.0175 ± 0.0006 | 76.2 ± 6.6 | 29.1 ± 2.0 |
| QKAN-FWP+ | 11,732 | 0.0025 | 5 | 4.17 | 0.0184 ± 0.0012 | 65.9 ± 4.2 | 27.2 ± 1.5 |
| QKAN-FWP-O without fast weights (static observable) | 496 | 0.0025 | 5 | 3.77 | 0.0137 ± 0.0001 | 67.1 ± 0.4 | 29.4 ± 0.9 |
| QKAN-FWP-O | 547 | 0.0025 | 5 | 3.67 | 0.0140 ± 0.0004 | 63.7 ± 2.7 | 27.5 ± 3.0 |
| *Reference: repeat the last cycle, 13-month smoothed (no training)* | 0 | – | – | – | 0.0166 | 53.1 | 18.7 |

#### 70/15/15 (test targets 1982–2026)

| Model | Params | lr (by validation) | Seeds | Val. loss | Scaled MSE ↓ | PAE ↓ | PTE ↓ |
|---|---|---|---|---|---|---|---|
| GQKAN-QKANFWP (re-implemented baseline) | 12,423 | 0.0025 | 3 | 3.85 | 0.0168 ± 0.0005 | 56.1 ± 5.1 | 26.5 ± 2.0 |
| QKAN-FWP+ | 11,732 | 0.0025 | 3 | 4.60 | 0.0156 ± 0.0004 | 44.8 ± 3.3 | 24.1 ± 0.7 |
| QKAN-FWP-O without fast weights (static observable) | 496 | 0.0025 | 3 | 3.41 | 0.0126 ± 0.0003 | 47.4 ± 3.0 | 20.1 ± 1.5 |
| QKAN-FWP-O | 547 | 0.0025 | 3 | 3.97 | 0.0139 ± 0.0007 | 45.1 ± 0.4 | 28.6 ± 0.6 |
| *Reference: repeat the last cycle, 13-month smoothed (no training)* | 0 | – | – | – | 0.0168 | 38.5 | 18.8 |

在論文的切法下，QKAN-FWP-O 的兩個版本在三種比例都比重新實作的 baseline 低 17–25%，有記憶的版本在 80/10/10 還是最低的（0.0134）。
**這些數字不能當成預測優勢的證據**：validation 的 targets 延伸到 test 期間，checkpoint 與 lr 的選擇看得到當時還沒發生的資料。
改成依 target 時間切分之後（8.2 節），有記憶的版本在 80/10/10 從 0.0134 變成 0.0173，baseline 從 0.0177 變成 0.0208，
它相對 baseline 的差距在三種切分變成 −17%、+4%、−19%。這一節的表只用來和論文印出的數字（同樣的切法）對照：
重新實作的 baseline 是 0.0177，論文印的是 0.0168。

QKAN-FWP+ 的兩個部分（同樣是論文的切法，lr 2.5e-3；下面的圖也是這個切法下的預測）：

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

![solar forecast](figures/solar_forecast.png)

分組 gate 降 MSE（0.0139，PAE／PTE 只小幅改善），last-cycle 讀出改善峰值指標（PAE 34.2、PTE 19.6，但 MSE 沒變）。

![error by start](figures/solar_error_by_start.png)
![error by start, 60/20/20](figures/solar_error_by_start_split622.png)

### 8.4 判斷

- 這個任務只有約 24 個太陽週期的資料，test 期間只含 3–5 個週期。評估的雜訊很大，切分方式本身就足以改變模型的排名。
- 以依 target 時間切分的結果為準：(i) 沒有模型在 MSE 與峰值指標上穩定贏過「重複上一個週期」；
  (ii) QKAN-FWP-O 的參數化（6 個電路、約 500 個參數）在三種切分上都不比 12,000 個參數的模型差，靜態版本的 MSE 低 7–28%——
  這是參數效率的結果，不是預測能力的突破；(iii) in-context 記憶沒有幫助；(iv) QKAN-FWP+ 的優勢不穩定。
- 因此太陽黑子的結果在本報告中只支持一個有限的結論：把 fast weights 放在量測算符的參數化，可以用很少的電路與參數處理多輸出的任務
  （每個輸出只是同一批量測結果上的另一個量測算符）。它不支持「記憶機制改善了太陽週期的預測」。

---

## 9. 沒有效果、或要小心的地方

| 想法 | 結果 | 說明 |
|---|---|---|
| 分組 gate（QKAN-FWP+，time-series） | 0.0036 對 scalar gate 的 0.0031（5.5 節） | Token 夠長之後，這些序列不需要多個記憶時間尺度 |
| Float64（精確）差分（QKAN-FWP+） | 無差別 | 高階差分在平滑序列上被 token 的 scale 縮到接近 0，rounding 雜訊也跟著被縮掉 |
| 原始 lag patch（不做差分），長度 3–10 | validation MSE 是 Δ-token 的 5–20 倍 | 相鄰值幾乎相同，斜率資訊量級太小，50 epochs 內學不出來 |
| 先寫後讀（QKAN-FWP+ write-first） | 整體幾乎沒差（test 0.94 倍），N = 8 時 0.77 倍 | 讓最新 token 經過 slow programmer，只在 window 很短時有用 |
| 從 lr 1e-3 開始的 cosine decay | validation MSE 變 2 倍 | 本來就訓練不足；要搭配更大的初始 lr |
| 固定大 lr（3e-2）不 decay | 比 cosine 差 13 倍 | 後期在最小值附近震盪 |
| QKAN-FWP-O：normalised delta rule 取代最小平方求解 | 論文 benchmark 上掃一次差 62 倍、掃四次差 59 倍；系統族上 7.4 倍與 4.6 倍，有雜訊時相當（5.4、6.3 節） | 只代表本報告實作的這一種 delta rule |
| QKAN-FWP-O：用補值的 token 寫入（不遮罩、或把未知的差分階數補 0） | validation 上都比只寫完整 token 差 | 視窗開頭的 token 和查詢 token 不是同一個分布 |
| QKAN-FWP-O：把先驗只放在遞迴的初始值、沒有下限 | NARMA10 上 3 個 seed 有 2 個發散 | 加上 $10^{-12}$ 的下限後不發散，而且整體比主模型略好（5.4、6.3 節） |
| QKAN-FWP-O：Bloch 特徵相對於古典特徵 | 論文 benchmark 上所有特徵都在 ±20% 之內；系統族上小型 MLP 好 2.1 倍 | 特徵映射不是收益來源（5.4、6.2 節） |
| 太陽黑子：單獨的 chrono 初始化（scalar gate） | 0.0185 對 0.0184 | 一個 gate 只有一個時間尺度 |
| 太陽黑子：平滑的輸出基底（QKAN-FWP+） | validation 與 test 都沒有改善 | 省 2,000 個參數，但不降誤差 |
| 太陽黑子：QKAN-FWP-O 的 in-context 記憶 | 依 target 時間切分後，有記憶的版本在三種切分的 test MSE 都比靜態版本差（8.2 節） | 這個任務上有用的是精簡的參數化，不是記憶 |
| 太陽黑子：論文的 window 索引切分 | 相鄰 split 的 targets 重疊 131 個月。這個切法下 QKAN-FWP-O 比 baseline 低 17–24%；依 target 時間切分後是 −17%、+4%、−19%（8.2、8.3 節） | Validation 看得到 test 期間的資料 |
| QKAN-FWP-O：切線特徵 $u\,\partial\mathbf n/\partial u$（可用 parameter-shift 量得，讓 context 對電路頻率做一階調整） | 論文 benchmark 的 validation 上，4 個電路＋切線特徵（140 參數）不如 6 個電路（154 參數）：幾何平均 6.3e-9 對 3.3e-9。和同為 4 個電路的版本比（單一 seed），無雜訊的 Duffing 好 5.6 倍、Hénon 好約 10%，有雜訊的 Duffing 沒有改善 | 對非線性系統有幫助，但同樣的參數用在更多電路效果相當或更好；程式保留為選項（`tangent`） |

兩個資料上的注意事項：

- **NARMA 的起始暫態**：M = 300 的序列從 0 起跳；N = 8 時暫態樣本會進入訓練集並主導 loss。
- **Δ-token 在 window 開頭的 padding**（QKAN-FWP+）：前 7 個位置的差分是用 replicate padding 算的，並不是真正的差分，
  卻仍然被寫進 fast-weight 記憶。QKAN-FWP-O 只寫入完整的 token，沒有這個問題。

---

## 10. 限制與尚未完成的部分

- 這是**獨立的重新實作**，不是官方程式，而且**沒有重現論文印出的 baseline 數字**（5.3 節）；層的大小、取樣點數等論文
  未給的細節是在這裡選的（3.1、4.5 節），所以 time-series 的絕對 MSE 與論文表格的比較只能參考。CMG 也是依論文敘述重新實作的。
- 六個 time-series benchmark 幾乎是線性問題（5.2 節）。在它們上面，MSE 排名主要反映「誰把一個接近線性的映射擬合得比較準」。
- **特徵映射不是收益的來源，也不主張量子優勢。** reps = 1 的 Bloch 特徵等於一次諧波的 Fourier 特徵；把它換成古典的 Fourier、tanh
  或小型 MLP 特徵而記憶不變，結果相當或更好，二次多項式在函數形式吻合的 Hénon map 上更好（5.4、6.2 節）。整個模型可以古典模擬。
  本報告沒有找到量子電路特徵帶來好處的任務；QKAN 的表述帶來的是第 7 節那些和硬體執行有關的性質，而古典特徵的版本根本不需要硬體。
- QKAN-FWP-O 的 in-context 最小平方本身是既有的做法（3.3 節）。
- **NARMA 的任務定義照論文**：讀 $y$ 的歷史、預測下一個 $y$。Reservoir computing 文獻裡標準的 NARMA 任務是讀輸入 $u$、輸出 $y$；
  那個版本需要多通道的輸入，本報告沒有做，所以這裡的 NARMA 數字不能和那類文獻的數字比較。
- **記憶規則的比較只涵蓋本報告實作的幾種**：每次寫入都帶先驗的 gated 最小平方、先驗只當初始值的指數加權 RLS、不用 gate 的最小平方、
  掃一次與掃四次的 normalised delta rule。其他誤差驅動或遞迴最小平方的方法（不同的步長、動量、Kalman 形式的更新）沒有測。
- **硬體相關的結果都是模擬**（第 7 節）：有限量測次數只有統計雜訊；硬體誤差只有靜態的讀出誤差、去極化與過旋轉，
  沒有 crosstalk、與時間相關的雜訊，也沒有和 shot 雜訊同時模擬；沒有真機實驗。In-context 校正只對視窗內不變的誤差成立。
  在需要非線性特徵的任務上，QKAN-FWP-O 對靜態模型的優勢需要每個電路約 $10^4$ 次以上的量測。
- 論文以多 qubit VQC 為 fast programmer 的三個模型（QFWP、G-QFWP、GQKAN-QFWP）沒有重新實作。
- MiniGrid 強化學習（論文 Sec. 6.3）沒有做；論文 Table 7 的 classical baselines（LSTM、WaveNet-LSTM、MESN…）也沒有重跑。
- lr 只掃了 cosine schedule 下的少數幾個值；模型設定是在少數候選中用 2–3 個 validation seed 選的，候選之間的差距
  有些在 seed 雜訊之內。
- 太陽黑子的結論受切分方式與評估期間影響很大（第 8 節）。
- 系統族（第 6 節）是本報告自己設計的任務；設計目的是讓 in-context 辨識成為必要，因此對閉迴路的模型有利。
  表中同時列出知道函數形式的封閉形式參考線，以便判斷差距。
- 可以延伸的方向：多 qubit 電路上以局部 Pauli 算符為特徵（同一批量測資料可同時估計多個算符）；把 shot 預算依 $|\mathbf R_i|$
  分配給 query 的各個電路；把開迴路的角度記憶和閉迴路的量測算符記憶疊在一起；需要非交換記憶的任務（2.1 節）。

---

## 11. 重現

```bash
pip install -r requirements.txt
python -m pytest tests -q               # 單元測試
bash experiments/run_all.sh             # 全部實驗（約 35 CPU core-hours；已完成的 job 會自動跳過）
python experiments/make_figures.py      # results/tables_final.md、tables_single_change.md 與 figures/
python experiments/make_om_report.py    # results/tables_om.md 與 figures/om_*.png
python experiments/report/build_report.py   # 由 experiments/report/report_text.py 與上述表格組出 REPORT.md
```

| 模型 | variant 名稱 |
|---|---|
| 重新實作的 GQKAN-QKANFWP（論文協定／調過 lr） | `base`／`base@cos30`（JC：`base@cos10`） |
| CMG | `cmg`、`cmg_plus`（＋Δ-token＋residual），lr 由 `results/dev_cmg.jsonl` 的 validation 決定 |
| QKAN-FWP+ | `pmx_diff8_edge_h3l2@cos30`（太陽黑子：`mtg_cyc_pm`） |
| HQKAN-Δ | `ar_hqkan8@cos30` |
| QKAN-FWP-O | `om_c0h6r1_p5@cos30`（太陽黑子：`om`；靜態版本 `om_static`） |
| 同一個記憶、不同特徵 | `om_c0h6r1_p5_fourier1`、`om_c0h8r1_p5_fourier1`、`_fourier`、`_tanh`、`_poly2`、`_mlp`、`_classical` |
| 同樣的特徵、不同記憶規則 | `_rls`、`_gnone`、`_delta`、`_delta4`、`_static`、`om_c0h9r1_p5_static`（參數量相當的靜態模型） |
| 物理的 ⟨Z⟩ 讀出（有限量測次數與硬體誤差的實驗） | variant 名稱加 `+z` |

`@cos30` 表示 cosine schedule、初始 lr 30e-3；`results/README.md` 說明每個結果檔的內容。
環境：Python 3.13、PyTorch 2.15（CPU）、`qkan` 0.2.3（只用於測試對照）。

---

## 附錄 A：在 baseline 上一次只改一項

這裡的模型不受「參數量不超過論文」的限制（多數是 152–190 個參數），目的是看第 2 節的每一項改動單獨有多少效果。
5 個 300 點序列 × N ∈ {16, 64}；數字是「該模型的 seed-mean test MSE ÷ 論文協定 baseline」的幾何平均（越小越好）。
表中的「Extended」指 residual 讀出 ＋ 3 維 Δ-token。

![single changes](figures/single_change_ablation.png)

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

- **Gate 是必要的。** 拿掉 gate（論文的 ungated FWP）MSE 變 4 倍，和論文「gated > ungated」的結論一致。
- **學習率（A1）**：0.079，是單一最大的因素。把 baseline 加大到 193 個參數幾乎沒差（0.074），所以其他增益不是來自參數變多。
- **Δ-token（A3）** 單獨是 0.019，**residual 讀出（A2）** 單獨是 0.062；兩者合起來 0.0042，遠好於各自——
  residual 把「上一個值」交給 skip path，Δ-token 提供斜率與曲率，fast programmer 只需要學增量。
- **分組 gate ＋ chrono 初始化（B1、B2）**：在論文協定下有 0.53；調好 lr 後單獨加是 0.71 倍（0.079 → 0.056），
  疊在 Extended 上是 0.75 倍（0.0042 → 0.0031）。Token 加長到 8 維之後這個增益消失（5.5 節）。
- **在論文協定（lr 1e-3）下**，Extended 也有 0.035，所以表徵與讀出的改進不依賴調 lr。
- **沒有 fast weights 的對照組**在這張表裡就已經和 gated 模型同一個水準（0.0078 對 0.0042），LSTM 加上同樣的 token 與
  residual 是 0.0034。

---

## 參考文獻

- Gated QKAN-FWP — arXiv:2605.06734；後續應用：traffic-matrix forecasting — arXiv:2606.27821
- 同一團隊關於更新規則的後續工作：Self-Modulating QFWP — arXiv:2606.24933；bounded memory gates — arXiv:2607.02363；
  Complementary Matrix-Gated QKAN-FWP（CMG）— arXiv:2607.27945
- QKAN / DARUAN — arXiv:2509.14026；QKAN-LSTM — arXiv:2512.05049；QFWP — arXiv:2402.17760；
  由網路產生的量測算符 — arXiv:2505.13525
- FWP 與 linear transformer：arXiv:2102.11174、2106.06295、review 2508.08435
- 誤差驅動／最小平方的記憶：DeltaNet 2406.06484、Gated DeltaNet 2412.06464、Titans 2501.00663、MesaNet 2506.05233、
  mesa-layer 2309.05858、test-time regression 2501.12352、ALPaCA 1807.08912、R2D2 1805.08136
- 線性遞迴模型的狀態追蹤與非交換轉移：Grazzi et al.（ICLR 2025）、arXiv:2508.07395、2605.07755、CSP 2608.03425、
  Selective RoPE 2511.17388、DeltaProduct 2502.10297、HyperSSM 2611.17162
- Gate 與初始化：Gated Linear Attention 2312.06635、RWKV-7 2503.14456、Fast Weight Attention 2608.27763、Longhorn 2407.14207、
  chrono init 1804.11188、UR-LSTM 1910.09890、HGRN 2311.04823、LRU 2303.06349、Mamba 2312.00752、xLSTM 2405.04517
- Time-series 表徵：PatchTST 2211.14730、DLinear/NLinear 2205.13504
- 資料：SILSO World Data Center, Royal Observatory of Belgium（monthly mean total sunspot number V2.0）
