"""Prose of REPORT.md.

``build_report.py`` concatenates the blocks below in order and replaces every
``<<name>>`` placeholder by a table taken from results/tables_*.md.  Numbers
quoted in the prose are copied from those tables.
"""

HEADER = r'''# Gated QKAN-FWP：重現、分析與改進

對象論文：*Gated QKAN-FWP: Scalable Quantum-inspired Sequence Learning*（arXiv:2605.06734）。

這份報告包含四件事：

1. 論文機制的整理，以及一份獨立的重新實作（論文沒有公開 fast-weight programmer 的程式）；
2. 兩個在輸入表徵與讀出上改進的模型：**QKAN-FWP+**（保留論文的 gated fast-weight 架構）與 **HQKAN-Δ**（沒有 fast weights 的對照組）；
3. 一個新的架構 **QKAN-FWP-O**：把 fast weights 從「電路的旋轉角」換成「電路的量測算符」，讓記憶可以用 context 內的預測誤差
   以封閉形式寫入；
4. 對 benchmark 本身的檢查：線性參考線、與論文印出數字的可比性、以及幾個實作選擇的影響。

所有模型都是 QKAN-based，參數量不超過論文的 159 個（太陽黑子：不超過 12,474 個）。
所有數字皆由本 repo 的程式產生（`results/*.jsonl`），重現方式見第 11 節。

'''

# ---------------------------------------------------------------------------
BACKGROUND = r'''## 1. 論文在做什麼

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
| B3 | 更新是實數、逐元素的 `Θ_t = A_t⊙Θ_{t−1} + B_t`，`A_t ≥ 0` | 逐元素相乘可交換，記不住順序；每個座標只是一條指數移動平均 | 複數／旋轉／非交換的轉移 | Grazzi et al.（ICLR 2025）、DeltaProduct（2502.10297）、AUSSM、HyperSSM（2611.17162） | 未實作，理由見 2.1 節 |
| B4 | `ΔW_t`、`g_t` 與 fast network 的預測誤差無關（**開迴路**） | 記憶是「每個 token 各猜一次再加權平均」；預測從未和下一個觀測值比較 | 誤差驅動的寫入：delta rule、in-context 最小平方 | Schlag et al.（2102.11174）、DeltaNet（2406.06484）、Titans（2501.00663）、MesaNet（2506.05233）、ALPaCA（1807.08912） | **QKAN-FWP-O**（3.3 節） |
| C1 | 只有最後一步有 loss | 每個 window 只有一個監督訊號 | Context 內每一步都是一個監督配對 | — | QKAN-FWP-O（配對用在寫入，不是 loss） |
| C2 | Slow decoder 直接輸出所有 fast weights | 太陽黑子模型 12.5k 參數中約 8.8k 在這個線性層 | Low-rank／outer-product hypernetwork；或讓 fast weights 不需要由網路產生 | QFWP 的 `L ⊗ Q`（2402.17760） | QKAN-FWP-O（太陽黑子約 500 個參數） |
| D1 | Sec. 6.1 沒有 classical baseline、沒有列出各層大小 | 無法判斷 benchmark 是否真的需要記憶機制 | 加入無記憶的對照組、同參數量的 LSTM、線性 AR | — | HQKAN-Δ、LSTM、線性 AR（5.2 節） |

### 2.1 一個考慮過但沒有實作的方向：旋轉（SU(2)）gate

原論文、Self-Modulating 與 CMG 的 `A_t` 都是實數、逐元素的。fast programmer 的每個電路本來就是 SU(2) 的元素，
所以針對 B3 最自然的推廣是讓 gate 也是旋轉（單位四元數）：$q_t = g_t\,p_t \otimes q_{t-1} + (1-g_t)\,d_t$，
CMG 是 $p_t = 1$ 的特例，有界性與 prefix scan 都還在。這個方向在線性遞迴模型的文獻裡已經被完整處理：

| 文獻 | 內容 |
|---|---|
| Grazzi et al., ICLR 2025 | 對角線性 RNN 做 parity 需要負的特徵值，mod-m 計數需要複數特徵值 |
| arXiv:2508.07395、AUSSM、arXiv:2605.07755、CSP（2608.03425）、Selective RoPE（2511.17388） | 輸入相依的複數／單位模轉移；旋轉與衰減都需要 |
| HyperSSM（arXiv:2611.17162） | 每個通道是結合代數（ℝ、ℂ、ℍ）上的 affine 遞迴 $x_k = a(u_k)x_{k-1} + \bar B(u_k)u_k$；證明能追蹤非交換群的最小通道是四元數；實驗包含「一串 qubit gate 之後的 Bloch vector」 |

也就是說，四元數 gate（衰減＋旋轉＋輸入項＋prefix scan）在 QFWP 上雖然沒有人做，但只是把既有結果搬過來；
而且一步預測並不需要非交換的記憶。本報告因此沒有實作它，而是處理另一個缺口 B4。

---

'''

# ---------------------------------------------------------------------------
MODELS = r'''## 3. 模型

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
| 有界性 | $\Theta_T$ 在 proposal 的凸包內 | $C_T$ 在 $\{\Lambda_0 + k_tk_t^\top\}$ 的凸包內，且 $C_T \succeq \Lambda_0 \succ 0$，求解恆為良態 |
| 量子電路是否依賴記憶 | 是（fast 角度逐樣本不同） | 否：所有 token 跑同一組固定電路、量 X／Y／Z 三個基底，記憶只出現在古典後處理 |
| 電路深度與 $T$ | 無關 | 無關 |

兩個實作細節，不做會出問題：

- **每次寫入都要帶著先驗**（上式的 $\Lambda_0$ 出現在 proposal 裡）。若寫成 $C_t = gC_{t-1} + (1-g)k_tk_t^\top$，
  只要有一個 gate 關到 0，先驗就和舊證據一起被忘掉，求解變成秩不足；NARMA10 的起始暫態會讓 3 個 seed 裡 2 個發散。
- **只寫入完整的 token**。用補值的 token（視窗開頭）寫入，在五個資料集的 validation 上都比較差。因此 token 長度取
  $\min(8, N/2)$，保證視窗至少有一半能形成完整配對。

最終設定：6 個電路、reps = 1；N = 8 時 130 個參數，N ≥ 16 時 154 個（token 長度不同）。訓練同 3.2 節，另加梯度範數裁剪（1.0）。

**定位。**

- *不新*：在學到的特徵上做 in-context 最小平方／Bayesian 線性回歸——ALPaCA（Harrison et al., 2018）、R2D2
  （Bertinetto et al., 2019）、mesa-layer（von Oswald et al., 2023）；誤差驅動的 fast-weight 寫入——delta rule
  （Schlag et al., 2021）、DeltaNet、Titans；可訓練或由網路產生的量測算符——arXiv:2505.13525（開迴路）。
- *本報告的貢獻*（以文獻搜尋所及為限）：(i) 指出 QKAN 層對量測算符是線性的，所以 QKAN-FWP 的 fast weights 可以有封閉形式的
  最佳寫入；(ii) 這個寫入的充分統計量恰好服從論文的 gated 遞迴，因此 Eq. 4、凸包有界與 prefix scan 都保留；
  (iii) QFWP 這一系列模型中第一個閉迴路的寫入規則。
- *不主張量子優勢*：reps = 1 時每個電路的三個特徵就是 $u$ 的一次諧波，整個模型可以古典模擬。
  QKAN 特徵在哪裡有用、哪裡沒用，5.4 與 6 節的消融有直接的答案。

### 3.4 太陽黑子用的模型

**QKAN-FWP+（11,732 參數）。** 在重新實作的 baseline（slow HQKAN 1 → 10 → 10，fast HQKAN 1 → 10 → 20 → 132，200 個 DARUAN 電路）上改三處：

- 分組 gate：fast QKAN 的 20 個輸出節點各一個 gate，chrono 初始化成對數等距的記憶長度 τ ∈ [2, 528] 個月；
- Last-cycle residual 讀出：`ŷ = smooth₁₃(最近 132 個月) + 網路輸出`，decoder 初始化為 0，所以未訓練的模型就是「重複上一個週期」；
- Slow latent 10 → 9，把多出來的 gate 參數抵掉。

**QKAN-FWP-O（547 參數）。** Token 是最近 11 個年平均；寫入的配對是（第 $t$ 個月的 token，之後 132 個月減去到 $t$ 為止的
last-cycle anchor），取視窗內後繼 132 個月都已知的每第三個月（89 個配對）；回歸目標是 132 個月在 16 個 cosine mode 上的係數。
6 個電路、reps = 1。拿掉記憶的靜態版本是 496 個參數。

---

'''

# ---------------------------------------------------------------------------
SETUP = r'''## 4. 實驗設定

### 4.1 資料

`qkanfwp/data.py`：方程式與參數照論文。論文沒寫 Bessel / SHM / DQC 的取樣點數，這裡統一用 300 點
（NARMA 的 M = 300 與 JC 的 3000 點是論文給的）。因此 **time-series 的 MSE 絕對值不能直接和論文 Table 3–6 比**（5.3 節）。
太陽黑子用的是同一份 SILSO V2.0 月資料前 3,326 筆，絕對值可以和論文 Table 7 比。

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
  | CMG（188）、CMG＋Δ-token＋residual（173） | 3e-2（沿用上面兩類模型選出的值） | 1e-2／3e-2 |
  | QKAN-FWP+、HQKAN-Δ、QKAN-FWP-O | 3e-2 | 3e-2 |

### 4.3 模型選擇只用 validation

所有設計決定（baseline 配置、token 長度、gate 分組、寬度、lr）都只用 70/10/20 split 的 validation 部分
（`results/dev_*.jsonl`）。最終數字用論文的 80/20 split、seeds 0–4，這些 run 沒有參與任何決定。

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
| 數值精度 | QKAN-FWP-O 全程 float64；其餘模型 float32（token 的差分用 float64 計算） | — | 5.4 節：拿掉記憶的 float64 靜態版本仍差兩個數量級以上，精度不是差距的來源 |

---

'''

# ---------------------------------------------------------------------------
NEGATIVE = r'''## 9. 沒有效果、或要小心的地方

| 想法 | 結果 | 說明 |
|---|---|---|
| 分組 gate（QKAN-FWP+，time-series） | 0.0036 對 scalar gate 的 0.0031（5.5 節） | Token 夠長之後，這些序列不需要多個記憶時間尺度 |
| Float64（精確）差分（QKAN-FWP+） | 無差別 | 高階差分在平滑序列上被 token 的 scale 縮到接近 0，rounding 雜訊也跟著被縮掉 |
| 原始 lag patch（不做差分），長度 3–10 | validation MSE 是 Δ-token 的 5–20 倍 | 相鄰值幾乎相同，斜率資訊量級太小，50 epochs 內學不出來 |
| 先寫後讀（QKAN-FWP+ write-first） | 整體幾乎沒差（test 0.94 倍），N = 8 時 0.77 倍 | 讓最新 token 經過 slow programmer，只在 window 很短時有用 |
| 從 lr 1e-3 開始的 cosine decay | validation MSE 變 2 倍 | 本來就訓練不足；要搭配更大的初始 lr |
| 固定大 lr（3e-2）不 decay | 比 cosine 差 13 倍 | 後期在最小值附近震盪 |
| QKAN-FWP-O：逐步的 delta rule 取代最小平方求解 | 差一到兩個數量級（5.4 節） | 一次通過的 normalised LMS 離最小平方解還很遠 |
| QKAN-FWP-O：用補值的 token 寫入（不遮罩、或把未知的差分階數補 0） | validation 上都比只寫完整 token 差 | 視窗開頭的 token 和查詢 token 不是同一個分布 |
| QKAN-FWP-O：把先驗只放在遞迴的初始值 | NARMA10 上 3 個 seed 有 2 個發散 | 3.3 節 |
| 太陽黑子：單獨的 chrono 初始化（scalar gate） | 0.0185 對 0.0184 | 一個 gate 只有一個時間尺度 |
| 太陽黑子：平滑的輸出基底（QKAN-FWP+） | validation 與 test 都沒有改善 | 省 2,000 個參數，但不降誤差 |
| 太陽黑子：QKAN-FWP-O 的 in-context 記憶 | validation 較差、test 較好（8.2 節） | 排序隨評估期間翻轉，無法下結論 |

兩個資料上的注意事項：

- **NARMA 的起始暫態**：M = 300 的序列從 0 起跳；N = 8 時暫態樣本會進入訓練集並主導 loss。
- **Δ-token 在 window 開頭的 padding**（QKAN-FWP+）：前 7 個位置的差分是用 replicate padding 算的，並不是真正的差分，
  卻仍然被寫進 fast-weight 記憶。QKAN-FWP-O 只寫入完整的 token，沒有這個問題。

---

## 10. 限制與尚未完成的部分

- 這是**獨立的重新實作**，不是官方程式，而且**沒有重現論文印出的 baseline 數字**（5.3 節）；層的大小、取樣點數等論文
  未給的細節是在這裡選的（3.1、4.5 節），所以 time-series 的絕對 MSE 與論文表格的比較只能參考。CMG 也是依論文敘述重新實作的。
- 六個 time-series benchmark 幾乎是線性問題（5.2 節）。在它們上面，MSE 排名主要反映「誰把一個接近線性的映射擬合得比較準」。
- QKAN-FWP-O 的 in-context 最小平方本身是既有的做法（3.3 節）；它的量子部分可以古典模擬，在線性系統上
  Bloch 特徵沒有貢獻（5.4、6 節）。
- 有限量測次數的影響只做了模擬（第 7 節），沒有真機實驗；沒有硬體雜訊模型。
- 論文以多 qubit VQC 為 fast programmer 的三個模型（QFWP、G-QFWP、GQKAN-QFWP）沒有重新實作。
- MiniGrid 強化學習（論文 Sec. 6.3）沒有做；論文 Table 7 的 classical baselines（LSTM、WaveNet-LSTM、MESN…）也沒有重跑。
- lr 只掃了 cosine schedule 下的少數幾個值；模型設定是在少數候選中用 2–3 個 validation seed 選的，候選之間的差距
  有些在 seed 雜訊之內。
- 太陽黑子的結論受評估期間影響很大（第 8 節）。
- 系統族（第 6 節）是本報告自己設計的任務；設計目的是讓 in-context 辨識成為必要，因此對閉迴路的模型有利。
  表中同時列出知道系統為線性的 oracle，以便判斷差距。
- 可以延伸的方向：把開迴路的角度記憶（CMG）和閉迴路的量測算符記憶疊在一起；多 qubit 電路上以局部 Pauli 算符為特徵
  （同一批量測資料可同時估計多個算符）；需要非交換記憶的任務（2.1 節）。

---

## 11. 重現

```bash
pip install -r requirements.txt
python -m pytest tests -q               # 單元測試
bash experiments/run_all.sh             # 全部實驗（約 25 CPU core-hours；已完成的 job 會自動跳過）
python experiments/make_figures.py      # results/tables_final.md、tables_single_change.md 與 figures/
python experiments/make_om_report.py    # results/tables_om.md 與 figures/om_*.png
python experiments/report/build_report.py   # 由 experiments/report/report_text.py 與上述表格組出 REPORT.md
```

| 模型 | variant 名稱 |
|---|---|
| 重新實作的 GQKAN-QKANFWP（論文協定／調過 lr） | `base`／`base@cos30`（JC：`base@cos10`） |
| CMG | `cmg`、`cmg@cos10`、`cmg@cos30`、`cmg_plus@cos30` |
| QKAN-FWP+ | `pmx_diff8_edge_h3l2@cos30`（太陽黑子：`mtg_cyc_pm`） |
| HQKAN-Δ | `ar_hqkan8@cos30` |
| QKAN-FWP-O | `om_c0h6r1_p5@cos30`（太陽黑子：`om`；靜態版本 `om_static`） |

`@cos30` 表示 cosine schedule、初始 lr 30e-3；`results/README.md` 說明每個結果檔的內容。
環境：Python 3.13、PyTorch 2.15（CPU）、`qkan` 0.2.3（只用於測試對照）。

---

'''

APPENDIX = r'''## 附錄 A：在 baseline 上一次只改一項

這裡的模型不受「參數量不超過論文」的限制（多數是 152–190 個參數），目的是看第 2 節的每一項改動單獨有多少效果。
5 個 300 點序列 × N ∈ {16, 64}；數字是「該模型的 seed-mean test MSE ÷ 論文協定 baseline」的幾何平均（越小越好）。
表中的「Extended」指 residual 讀出 ＋ 3 維 Δ-token。

![single changes](figures/single_change_ablation.png)

<<single_change>>

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

'''

REFERENCES = r'''## 參考文獻

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
'''
