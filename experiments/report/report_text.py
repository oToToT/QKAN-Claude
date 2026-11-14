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
| 太陽黑子：QKAN-FWP-O 的 in-context 記憶 | 三種 split 中 validation 有兩種偏向沒有記憶的版本（8.2 節） | 收益來自參數化，不是記憶 |
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

# ---------------------------------------------------------------------------
RESULTS_TS = r'''## 5. 結果：論文的六個 time-series benchmark

論文協定的 split（80/20）、seeds 0–4、最後一個 epoch 的 test MSE。QKAN-FWP-O 整張表只有一組設定（3.3 節）。

### 5.1 主結果

![paper benchmarks](figures/om_timeseries.png)

每個資料集對四個 window 取幾何平均（粗體是訓練出來的模型中最低的；最右欄是不需要訓練的線性參考線）：

<<ts_summary>>

三個模型對每個參考對象的幾何平均倍數，括號內是勝出的格數：

<<ts_matrix>>

- **QKAN-FWP-O** 比重新實作的 GQKAN-QKANFWP（調過 lr）低四個數量級以上，比 CMG 與另外兩個論文變體也是；
  它比同樣 token 與讀出的 QKAN-FWP+ 低三個數量級，比沒有記憶的 HQKAN-Δ 低兩個數量級以上（只有 NARMA5 的 N = 8 那一格略遜）。
- **CMG**：照 CMG 論文的設定（純量 token、188 參數）在調過 lr 之後和 scalar gate 的 baseline 同一個水準（Bessel 與 SHM 較好，
  NARMA 與 DQC 沒有改善）。給它相同的 Δ-token 與 residual 讀出之後，它比 QKAN-FWP+ 好 1.6 倍——逐權重的 gate 與先寫後讀
  有小幅幫助——但仍然輸給沒有記憶的 HQKAN-Δ。
- **HQKAN-Δ 在每一格都比 QKAN-FWP+ 好**，也在幾乎每一格比 CMG 好：在這些 benchmark 上，「由 slow programmer 產生旋轉角」
  這種型態的記憶沒有幫助，把同樣的參數放進靜態網路反而更好。因為這個結論重要，QKAN-FWP+ 與 HQKAN-Δ 另外各加跑 10 個 seed
  （`results/extra_seeds.jsonl`，5 個序列 × N ∈ {16, 64}）：15 個 seed 合計 HQKAN-Δ 好 2.5 倍，10 格中贏 9 格。
- QKAN-FWP-O 相對 HQKAN-Δ 的差距因此不是「加了記憶就會好」，而是**記憶的型態**：開迴路的角度記憶沒有用，
  閉迴路的量測算符記憶有用（5.4 節的消融）。

完整的表：

<<ts_cells>>

### 5.2 線性參考線：這組 benchmark 有多難

最簡單的參考模型是線性自迴歸 `x̂_t = w·(x_{t−p}, …, x_{t−1}) + c`，用最小平方法在**同樣的訓練 window** 上解出來
（`experiments/reference_baselines.py`），不需要梯度訓練，參數量是 p + 1。

<<ts_linear>>

- 六個序列的一步預測幾乎是線性問題。**9 個參數的線性 AR(8) 在大多數格子贏過兩篇論文印出的最佳數字**，也贏過
  QKAN-FWP+ 與 HQKAN-Δ。Jaynes–Cummings 是「衰減的常數項＋衰減的餘弦」，嚴格滿足三階線性遞迴，AR(3) 就到機器精度。
- QKAN-FWP-O 在 NARMA 與 DQC（不是嚴格線性遞迴的序列）上低於線性 AR(8)；在 Bessel、Damped SHM、Jaynes–Cummings
  這些嚴格（或幾乎）線性的序列上，float64 的最小平方解到了 1e-13 ～ 1e-31，沒有任何以梯度訓練的模型追得上。
- 因此在這六個序列上比較 MSE，比的主要是「誰把一個接近線性的映射擬合得比較準」。QKAN-FWP-O 之所以大幅領先其他
  神經模型，正是因為它在 context 內直接解最小平方，繞過了「用 SGD 把線性映射逼近到很多位有效數字」這件事。
  要檢驗記憶機制本身，需要第 6 節那種固定預測器不夠用的任務。

### 5.3 和論文印出的數字比較：重現缺口

5.1 節的表把論文印出的數字直接並列，但**這個比較只能參考**：論文沒有給 Bessel / SHM / DQC 的取樣點數，
而且重新實作的 GQKAN-QKANFWP 在論文協定下得到的數字和論文印的並不相同：

<<gap>>

- 在論文協定下，重新實作的 GQKAN-QKANFWP 在 5 個 300 點序列上比論文印出的數字差 21 倍（幾何平均），
  Jaynes–Cummings 則反過來好 4–7 倍。
- **讀寫順序不是原因。** CMG 論文寫的是先寫後讀；先寫後讀的 baseline 更差（43 倍）。
- **主要是訓練效率。** 同一個模型把 lr 調好之後，和論文印出的數字只差 1.9 倍（20 格幾何平均，個別格子 0.2–14 倍）。
  也就是說「lr 1e-3、50 epochs」在這份實作裡收斂得比論文慢；可能是初始化、optimizer 細節或層的配置不同，無法從論文確定。
- **NARMA 的尺度。** 把 [−1, 1] 正規化資料上的 MSE 換算回原始尺度，NARMA5 / NARMA10 的 baseline 是 2.3e-5 / 3.6e-5，
  和論文印的 2.8e-5 / 5.2e-5 很接近；但直接在原始尺度上訓練得到的是 1.1e-4，並不吻合。這個解釋無法證實。
- 所以本報告所有「相對 baseline 低幾倍」的數字，都應解讀為**同一個 pipeline 內**的相對比較。

### 5.4 消融：QKAN-FWP-O

數字是「該變體的 test MSE ÷ 完整模型」的幾何平均（大於 1 表示完整模型較好）。

<<om_ablation_ts>>

- **記憶是主要來源。** 拿掉 fast weights（只留靜態的量測算符 $R_0$；同樣的特徵、同樣是 float64）差兩個數量級，
  在 Bessel 與 Damped SHM 上差三到四個數量級。
- **封閉形式的最小平方求解是必要的。** 換成逐步的 delta rule（一次通過的 normalised LMS，不需要矩陣求解）
  幾乎退回到沒有記憶的水準。
- **Gate 的貢獻集中在 NARMA10。** 不用 gate（等權重的統計量）或用常數 gate，整體只差 1.4–1.7 倍，但 NARMA10 差 4–5 倍：
  輸入相依的 gate 讓模型不把起始暫態寫進記憶。先驗精度逐特徵或共用一個，沒有差別。
- **線性（base-activation）項很重要**（拿掉差 4.7 倍），因為這些序列接近線性。
- **Bloch 特徵的貢獻有限**：只留線性項的古典對照組整體只差 1.5 倍，在 Bessel 上甚至更好；差距較明顯的是 Damped SHM
  （這裡的 SHM 是有 sin 項的阻尼擺）與 DQC。也就是說，在論文的 benchmark 上，新架構的收益幾乎全部來自閉迴路的寫入，
  而不是量子電路的特徵；量子特徵真正有用的地方見第 6 節的 Hénon map。

### 5.5 消融：QKAN-FWP+ 的輸入表徵與讀出

5 個 300 點序列 × N ∈ {16, 64}；數字是 seed-mean test MSE ÷ 論文協定 baseline 的幾何平均（越小越好）。

![QKAN-FWP+ ablation](figures/timeseries_ablation.png)

<<fwp_ablation>>

- **Residual 讀出**：拿掉後變差 8 倍（0.0036 → 0.029）。
- **Δ-token**：拿掉（回到純量輸入）變差 18 倍（→ 0.064）。8 維比 3 維整體好 1.3 倍：NARMA 與 DQC 好 2–10 倍，
  Bessel 與 SHM 反而差 2–5 倍。
- **分組 gate**：換回論文的 scalar gate 是 0.0031，略好於分組 gate 的 0.0036——token 夠長之後，gate 的粒度在這組
  benchmark 上沒有差別（單獨加在 baseline 上時有 0.53–0.75 倍的增益，見附錄 A）。
- **Fast weights 本身**：拿掉整個機制（HQKAN-Δ）是 0.00091，比 QKAN-FWP+ 好 4 倍（加到 15 個 seed 是 2.5 倍，5.1 節）。
- **對照（非 QKAN）**：160 參數的 LSTM 用同樣的 token 與 residual 是 0.00093，和 HQKAN-Δ 打平。

### 5.6 穩健性：三個實作選擇會不會改變結論

N = 16、5 seeds。QKAN-FWP-O 量的本來就是物理的 ⟨X⟩、⟨Y⟩、⟨Z⟩，所以第二個條件下它的數字和預設相同。

<<robust>>

<<burnin>>

- **物理的 ⟨Z⟩ 讀出**（取代 `qkan` 預設的 \|a\|−\|b\|）：gated 模型與 HQKAN-Δ 的數字大多變動在 2 倍以內，排序不變。
- **只用訓練段做正規化**：Bessel、SHM、NARMA10、DQC、JC 的數字和原本完全相同，因為這些序列的極值都落在訓練段；
  只有 NARMA5 的最大值在測試段，數字變動很小。先正規化再切分的洩漏在這組資料上實際沒有作用。
- **NARMA 去掉起始暫態**：正規化後的訊號佔滿整個 [−1, 1]，所有模型的 MSE 都變大，但排序不變；N = 8 不再特別差。

---

'''

RESULTS_FAMILY = r'''## 6. 結果：需要 in-context 辨識的系統族

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
（3e-3、1e-2、3e-2，cosine、40 epochs、batch 32），lr 與 checkpoint 都由 validation 決定。三條參考線不需要訓練：
重複上一個值、所有序列共用一個線性 AR(p)、以及**在每個視窗內各自擬合的 ridge AR(q)**
（階數、ridge 強度與是否含截距由 validation 選；它知道系統是線性的，是線性族上很強的 oracle）。

![families](figures/om_family.png)

<<fam_main>>

<<fam_vs>>

- **沒有雜訊時**，QKAN-FWP-O 在五個族都是最低的神經模型，比其餘最好的模型低 15 倍（Hénon、Duffing）到 2 萬倍（阻尼振盪）。
  其他模型彼此差不多：有記憶的 QKAN-FWP+、CMG、LSTM 和沒有記憶的 HQKAN-Δ 在同一個量級，開迴路的記憶最多帶來 2–3 倍。
- **有雜訊時**差距縮小（不可約的誤差約為雜訊變異數 4e-4）：QKAN-FWP-O 在四個族最低（比次佳的模型低 1.1–2.3 倍），
  在 Hénon 上和 QKAN-FWP+ 打平。
- **對線性參考線**：
  - 「所有序列共用一個線性 AR」在 10 格中輸 9 格（只在無雜訊的 Jaynes–Cummings 上較好）。
  - 「在視窗內擬合 ridge AR」在無雜訊的線性族上是精確解（1e-15 ～ 1e-26），沒有模型能比；無雜訊的 Jaynes–Cummings 也是它較好。
    有雜訊時 QKAN-FWP-O 在阻尼振盪上是它的 1.2 倍，在 two tones、Jaynes–Cummings、Duffing 上比它低（1.97e-3 對 2.51e-3、
    2.87e-3 對 4.05e-3、8.67e-4 對 9.34e-4）——學到的先驗與特徵比現場選階數的 ridge 更有效率。
  - 在非線性的 Hénon map 上兩條線性參考線都失效（約 5e-2），QKAN-FWP-O 是 3.4e-5（無雜訊）與 1.8e-3（有雜訊）。

消融（test MSE ÷ 完整模型）：

<<om_ablation_fam>>

- **拿掉 fast weights**：無雜訊時差 5 倍到 2.6 萬倍，有雜訊時差 1.4–3.8 倍。
- **Delta rule 取代最小平方求解**：無雜訊時差 4–1100 倍；有雜訊時幾乎沒有差別（0.93–1.8 倍）。封閉形式求解的價值在高精度的情形；
  當誤差由雜訊主導時，一次通過的誤差驅動更新就夠了——重點是寫入要看誤差。
- **不用 gate**：無雜訊時反而略好（線性族 0.4–0.7 倍），有雜訊時差 2.4–3.5 倍。Gate 在這裡的作用是調整證據相對於先驗的總權重
  （$\sum_t\beta_t < 1$）以及各個 token 的權重；沒有 gate 時只剩先驗精度 $\Lambda_0$ 可以調節。
- **拿掉 Bloch 特徵（古典對照組）**：線性族上無雜訊時反而好 20–80 倍（純線性特徵可以精確表示 AR 遞迴）、有雜訊時相同；
  **Hénon 上差 1164 倍（無雜訊）與 22 倍（有雜訊），Duffing 無雜訊時差 2.4 倍**。量子電路的特徵正是讓非線性系統能在 context 內被辨識的部分；
  在線性系統上它不需要，還會稍微降低精度。

---

'''

RESULTS_SHOTS = r'''## 7. 有限量測次數

QKAN-FWP-O 要解一個由量測值組成的線性方程，量測雜訊可能被 $C_T^{-1}$ 放大——這是把它搬上真機前最該先問的問題。
這裡在測試時對每個量測到的期望值 $v$ 加上 $S$ 次量測的統計雜訊（變異數 $(1-v^2)/S$；`experiments/shot_noise.py`），
並比較兩種訓練方式：用精確期望值訓練，以及訓練時就帶著 $10^4$ shots 的雜訊。為了比較，QKAN-FWP+ 與 HQKAN-Δ
改用物理的 ⟨Z⟩ 讀出；QKAN-FWP-O 的雜訊加在每個 token、每個電路的 ⟨X⟩、⟨Y⟩、⟨Z⟩ 上。
系統族的兩個任務三個模型都用 lr 3e-2。

![shots](figures/om_shots.png)

<<shots>>

---

'''

RESULTS_SOLAR = r'''## 8. 結果：太陽黑子週期預測

528 個月 → 132 個月的 direct multi-step 預測，論文的協定（peak-aware loss、100 epochs、batch 32、取 validation loss
最低的 checkpoint、lr 由 validation 從論文的 grid 選）。指標：scaled MSE、峰值振幅誤差 PAE（黑子數）、峰值時間誤差 PTE（月）。

### 8.1 所有模型、三種 split

除了論文的 80/10/10，另外用兩種 chronological split 檢查結論是否依賴評估期間。

<<solar_all>>

- **論文的 split**：QKAN-FWP+（11,732 參數）與 QKAN-FWP-O（約 500 參數）的 MSE 與 PAE 都明顯低於重新實作的 baseline，
  也低於論文印出的數字。
- **換 split 之後**，QKAN-FWP+ 的 MSE 優勢不穩定（60/20/20 上比 baseline 高 5%，70/15/15 上低 7%）。
  QKAN-FWP-O 的靜態版本在三種 split 上的 test MSE 都比 baseline 低 19–25%（0.0144／0.0137／0.0126 對 0.0177／0.0175／0.0168），
  也低於「重複上一個週期」的參考線；它的 validation loss 在三種 split 上同樣低於 baseline，seed 間的標準差很小。
- **峰值指標沒有模型穩定贏過零參數的參考線**：PTE 在三種 split 上都是參考線最好或接近最好；PAE 只有在論文的 split 上有模型略好。
- **零參數的「重複上一個週期」本身就優於論文印出的模型**（0.0156 / 35.9 / 16.2 對 0.0168 / 39.59 / 21.89）。

### 8.2 QKAN-FWP-O：記憶在這裡有沒有用

沒有證據顯示有用。在論文的 split 上，validation loss 選的是沒有記憶的靜態版本（2.37 對 2.61），test MSE 卻是有記憶的版本較低
（0.0134 對 0.0144）；60/20/20 上 validation 略偏向有記憶的版本、test 打平；70/15/15 上兩者都是靜態版本較好。
設定掃描（`results/dev_solar_om.jsonl`）裡所有帶記憶的變體 validation loss 都比靜態版本高。
所以這個資料集上的收益來自精簡的參數化——年平均 token、16 個 cosine mode 的輸出、last-cycle anchor、
量測算符可訓練的 6 個電路——而不是來自記憶：約 500 個參數（論文模型的 4%）就得到更低的 MSE。

### 8.3 QKAN-FWP+ 的兩個部分

論文的 split、lr 2.5e-3：

<<solar_parts>>

![solar forecast](figures/solar_forecast.png)

分組 gate 降 MSE（0.0139，PAE／PTE 只小幅改善），last-cycle 讀出改善峰值指標（PAE 34.2、PTE 19.6，但 MSE 沒變），
兩者合起來三個指標都好。論文的做法是從 {1, 2, 2.5}×1e-3 中用 validation loss 選 lr：

<<solar_grid>>

但 validation 與 test 的排序相反：上表的 Val. loss 欄，QKAN-FWP+ 是 3.3–3.8，baseline 是 2.5。Validation 期間
（目標 1971–2004，含 SC21–23 等強週期）QKAN-FWP+ 明顯較差，test 期間（1993–2026，含偏弱的 SC24）則明顯較好；
被選中的 checkpoint 多半在前幾個 epoch，表示訓練主要是在微調「重複上一個週期」這個起點。

![error by start](figures/solar_error_by_start.png)
![error by start, 60/20/20](figures/solar_error_by_start_split622.png)

### 8.4 判斷

- 這個 benchmark 的 test 只涵蓋兩到五個太陽週期，不同期間的排序會翻轉，而且零參數的 seasonal-naive 就在同一個水準。
  它**不足以**證明哪個模型的預測能力真的比較好——這個保留同樣適用於論文 Table 7 中各模型之間 10–30% 的差距。
- 在這個前提下，三種 split、validation 與 test 都一致的只有：QKAN-FWP-O 的靜態版本以約 500 個參數得到比 12,423 參數的
  baseline 更低的 MSE。峰值指標與記憶機制的效果都沒有穩定的結論。
- 若要把太陽黑子的結果寫進論文，建議至少：加入 seasonal-naive 當 baseline、用多個 rolling-origin split 取平均、
  並同時報 validation 期間的指標。

---

'''

# ---------------------------------------------------------------------------
SUMMARY = r'''## 摘要

### 模型

| 模型 | 是什麼 | 參數量（論文的 GQKAN-QKANFWP：159） |
|---|---|---|
| 重新實作的 GQKAN-QKANFWP、CMG | Baseline：論文的 scalar gate，以及後續論文的逐座標互補 gate（arXiv:2607.27945） | 152、188 |
| **QKAN-FWP+** | 論文的 gated fast-weight 架構 ＋ Δ-token ＋ residual 讀出 ＋ 每個電路一個 gate | 149 |
| **HQKAN-Δ** | 同樣的 token 與讀出，但沒有 fast weights 的靜態 HQKAN（對照組） | 136 |
| **QKAN-FWP-O** | Fast weights 是 DARUAN 電路的**量測算符**；context 以 gated 最小平方寫入（閉迴路），封閉形式沿用論文的 gated 遞迴 | 130–154 |

### 主要結果

論文的六個 benchmark（test MSE，對四個 window 取幾何平均，5 seeds）：

<<ts_summary>>

1. **QKAN-FWP-O 在論文的 benchmark 上比其他所有訓練出來的模型低兩到五個數量級**（5.1 節），參數量不超過論文。
   消融顯示收益來自閉迴路的記憶：拿掉 fast weights 差兩個數量級，把封閉形式的最小平方換成逐步的 delta rule 也差不多退回原點（5.4 節）。
2. **論文型態的記憶（由 slow programmer 產生旋轉角）在這些 benchmark 上沒有幫助**：沒有 fast weights 的 HQKAN-Δ
   在每一格都比 QKAN-FWP+ 好（15 個 seed 合計 2.5 倍），也比給了相同 token 的 CMG 好。有用的是記憶的型態，不是有沒有記憶。
3. **在每條序列物理參數都不同的系統族上**（第 6 節：模型必須從 16 步的視窗辨識系統），QKAN-FWP-O 在 10 格中的 9 格最低、
   1 格打平：沒有雜訊時比其他神經模型低 15 倍到 2 萬倍，有雜訊時低 1.1–2.3 倍；在非線性的 Hénon map 上比兩條線性參考線低
   30–1300 倍，在有雜訊的線性族上與「在視窗內擬合 ridge AR」的 oracle 相當或更好。
4. **太陽黑子**（第 8 節）：QKAN-FWP-O 的參數化以約 500 個參數（論文模型的 4%）在三種 split 上都得到比 baseline 低 19–25% 的 MSE
   （validation 與 test 一致）；這個收益不是來自記憶。

### 解讀這些數字時必須知道的事

1. **六個 benchmark 幾乎是線性問題。** 一個 9 參數的線性 AR(8)（最小平方，不需要訓練）在大多數格子贏過兩篇論文印出的
   最佳數字，也贏過 QKAN-FWP+ 與 HQKAN-Δ；QKAN-FWP-O 只在 NARMA 與 DQC 上低於它（5.2 節）。QKAN-FWP-O 對其他神經模型的
   巨大差距，主要是「在 context 內直接解最小平方」對「用 SGD 逼近線性映射」的差距。
2. **量子電路的特徵只在非線性系統上有貢獻。** 在論文的 benchmark 與線性的系統族上，只留線性項的古典對照組和完整模型差不多
   （無雜訊的線性族上甚至更準）；在 Hénon map 上拿掉 Bloch 特徵則差 22–1164 倍（5.4、6 節）。整個模型可以古典模擬，不主張量子優勢。
3. **沒有重現論文印出的 baseline 數字。** 重新實作的 GQKAN-QKANFWP 在論文協定下比論文印出的數字差 21 倍（幾何平均），
   調過 lr 後差 1.9 倍；原因沒有找到（5.3 節）。所有「低幾倍」的結論都是同一個 pipeline 內的比較。
4. **In-context 最小平方不是新方法**（ALPaCA、R2D2、mesa-layer、delta rule）。本報告的貢獻是指出 QKAN 層對量測算符是線性的，
   因此 QKAN-FWP 可以有封閉形式的閉迴路寫入，而且它的充分統計量服從論文的 gated 遞迴（3.3 節）。
5. **有限量測次數會被線性求解放大**（第 7 節）；真機沒有測。
6. **太陽黑子**：零參數的「重複上一個週期」就優於論文印出的模型，峰值指標沒有模型穩定贏過它；QKAN-FWP+ 的優勢會隨評估期間改變；
   沒有證據顯示記憶在這個任務上有用（第 8 節）。

沒有做的部分（MiniGrid RL、真機實驗、以多 qubit VQC 為 fast programmer 的模型）列在第 10 節。

---

'''
