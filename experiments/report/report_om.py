"""Prose of part A of REPORT.md (third round: the observable-memory FWP).

``METHOD`` has no numbers.  ``RESULTS`` is a format string filled by
build_report.py with tables from results/tables_om.md; the numbers quoted in
its prose are copied from those tables.
"""

METHOD = r'''## A. 第三輪：新架構 QKAN-FWP-O（把 fast weights 從「旋轉角」換成「量測算符」）

> 這一部分是最新的一輪。第 0–10 節是前兩輪的內容，保留原樣；它們的結論（重現缺口、線性 AR 參考線、
> 太陽黑子的保留）仍然有效，而且是這一輪設計實驗時的前提。

### A.1 這一輪給自己的三個條件

前一輪的教訓是：我提的「分組 gate」早就被原團隊的 CMG 涵蓋，而且六個 benchmark 上一個 9 參數的線性 AR 就贏過所有模型。
所以這一輪：

1. 新設計不能只是 CMG 的變形，**動手之前先把文獻查完**；
2. 必須在**線性 AR 解不了、而且真的需要記憶**的任務上驗證，並且把線性參考線和每個模型放在同一張表；
3. 仍然是 QKAN-based，參數量不超過論文的 159。

### A.2 先被文獻否決的想法：旋轉（SU(2)）gate

原論文、Self-Modulating、CMG 的更新規則都可以寫成同一個形式

$$\Theta_t = A_t \odot \Theta_{t-1} + B_t ,\qquad (A_t, B_t) = \text{只由 } x_t \text{ 決定},$$

其中 $A_t$ 是**實數、逐元素**的（scalar gate 與 CMG：$[0,1]$；tanh 版本：$[-1,1]$）。逐元素相乘可交換，所以記憶記不住「順序」；
$A_t \ge 0$ 時每個座標只是一條指數移動平均。fast programmer 的每個電路本來就是 SU(2) 的元素，所以最自然的推廣是讓
gate 也是旋轉（四元數）：$q_t = g_t\,p_t \otimes q_{t-1} + (1-g_t)\,d_t$，CMG 是 $p_t = 1$ 的特例，有界性與 prefix scan 都還在。

查文獻的結果是這條路**已經有人走完了**，只是不在 QFWP 這條線上：

| 文獻 | 內容 | 和這個想法的關係 |
|---|---|---|
| Grazzi et al., ICLR 2025 | 對角線性 RNN 要做 parity 需要負的特徵值，mod-m 計數需要複數特徵值 | 說明了「非負對角」的極限 |
| arXiv:2508.07395、AUSSM、arXiv:2605.07755、CSP（arXiv:2608.03425）、Selective RoPE（arXiv:2511.17388） | 輸入相依的複數／單位模轉移；旋轉與衰減都需要 | 交換的旋轉（複數通道）已被涵蓋 |
| **HyperSSM，arXiv:2611.17162（2026-11）** | 每個通道是一個結合代數（ℝ、ℂ、ℍ）上的 affine 遞迴 $x_k = a(u_k)x_{k-1} + \bar B(u_k)u_k$，$a = e^{\Delta(-\alpha + v(u_k))}$；證明能追蹤非交換群的最小通道就是四元數；實驗包含「一串 qubit gate 之後的 Bloch vector」 | 就是上面的四元數 gate（衰減＋旋轉＋輸入項＋prefix scan），而且理論更完整 |

所以「把 gate 換成 SU(2)」在 QFWP 上雖然沒有人做，但只是把一個月前剛發表的結果搬過來；而且一步預測並不需要非交換的記憶。
這個方向我**沒有實作**，只留在這裡當作相關工作。

### A.3 真正的缺口：整個家族的寫入都是「開迴路」

把上面的遞迴展開就是論文的 Eq. 4：$\Theta_T = \sum_k \beta_k\,\Delta(x_k)$。也就是說，記憶是
「每個 token 各自猜一次該寫什麼，再做加權平均」。**fast programmer 的預測從來沒有和下一個觀測值比較過**——
slow programmer 看不到 $\Theta_{t-1}$，也看不到預測誤差。古典的 FWP 文獻在 2021 年就指出這一點並改用 delta rule
（Schlag et al.；後來的 DeltaNet、Titans 都是誤差驅動的寫入）；QFWP 的四篇論文（2605.06734、2606.24933、2607.02363、
2607.27945）全部是開迴路，我在搜尋中也沒有找到任何閉迴路的 QFWP。

對時間序列預測，這特別可惜：context 裡的每一步都**自帶答案**（token $t$ 之後實際出現的 $x_{t+1}$）。

### A.4 關鍵觀察：QKAN 對「量測算符」是線性的

DARUAN 的 activation 是 $\phi(u) = \langle 0|U^\dagger(u)\,O\,U(u)|0\rangle$。論文把 $U$ 裡的旋轉角當 fast weights，
$\phi$ 對它們是高度非線性的，所以「給定 context，最好的 fast weights 是什麼」沒有封閉解，只能讓 slow programmer 去猜。
但如果把單 qubit 的量測算符寫成 $O = r_0 I + \mathbf r\cdot\boldsymbol\sigma$，則

$$\phi(u) = r_0 + \mathbf r\cdot\mathbf n(u),\qquad \mathbf n(u) = (\langle X\rangle,\langle Y\rangle,\langle Z\rangle)\ \text{是電路輸出的 Bloch vector}.$$

**同一個電路、同一組角度，activation 對 $(r_0,\mathbf r)$ 是線性的**；整個 QKAN 層（各 edge 相加）也是。
於是把 fast weights 從旋轉角換成量測算符之後，「給定 context 的最佳 fast weights」就是一個加權最小平方問題。

**架構（QKAN-FWP-O）。** 令 $\tau_t$ 為第 $t$ 步的 token（和前一輪相同的 Δ-token），

- 特徵：$u_t = E\tau_t + e$（HQKAN 的古典 encoder），$k_t = \big[1,\ u_t,\ \mathbf n_1(u_{t,1}),\dots,\mathbf n_h(u_{t,h})\big]$。
  $h$ 個單 qubit DARUAN 電路的角度是**慢參數**（不隨輸入改變）；中間的 $u_t$ 是 QKAN 原本就有的 base-activation 項
  （`qkan` 套件的 `base_activation`，這裡取恆等函數）。
- context 內的配對：$(k_t,\ y_t)$，$y_t = x_{t+1}-x_t$，$t = 1,\dots,T-1$（只用 token 完整的那些 $t$）。
- 記憶（論文的 scalar-gated 遞迴，作用在充分統計量上）：

$$C_t = g_t\,C_{t-1} + (1-g_t)\,(\Lambda_0 + k_t k_t^\top),\qquad b_t = g_t\,b_{t-1} + (1-g_t)\,(\Lambda_0 R_0 + k_t\,y_t),$$

  $C_0 = \Lambda_0$、$b_0 = \Lambda_0 R_0$；gate $g_t = \sigma(w_g\cdot k_t + c_g)$ 是**同一批電路上的另一個量測算符**。
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
| 遞迴 | $\Theta_t = g\Theta_{t-1} + (1-g)\Delta_t$ | **同一個**遞迴，作用在 $(C, b)$ |
| 封閉形式（Eq. 4）／prefix scan | 有 | 有（對 $(C,b)$；最後多一次 $F\times F$ 的線性求解，$F \le 25$） |
| 有界性 | $\Theta_T$ 在 proposal 的凸包內 | $C_T$ 在 $\{\Lambda_0 + k_tk_t^\top\}$ 的凸包內，且 $C_T \succeq \Lambda_0 \succ 0$，求解恆為良態 |
| 量子電路是否依賴記憶 | 是（fast 角度逐樣本不同） | **否**：所有 token 跑同一組固定電路、量 X／Y／Z 三個基底，記憶只出現在古典後處理 |
| 電路深度與 $T$ | 無關 | 無關 |

兩個實作細節是實驗中發現、不做會出問題的：

- **每次寫入都要帶著先驗**（上式的 $\Lambda_0$ 出現在 proposal 裡）。一開始我寫的是 $C_t = gC_{t-1} + (1-g)k_tk_t^\top$，
  結果只要有一個 gate 關到 0，先驗就和舊證據一起被忘掉，求解變成秩不足；NARMA10 的起始暫態讓 3 個 seed 裡 2 個發散。
- **只寫入完整的 token**。用補值的 token（視窗開頭）寫入，在五個資料集上都比較差。因此 token 長度取
  $\min(8, N/2)$，保證視窗至少有一半能形成完整配對（這條規則是在 validation 上和固定長度比較後選的）。

### A.5 定位：哪些是新的、哪些不是

- **不新**：在學到的特徵上做 in-context 最小平方／Bayesian 線性回歸——ALPaCA（Harrison et al., 2018）、R2D2
  （Bertinetto et al., 2019）、mesa-layer（von Oswald et al., 2023）；誤差驅動的 fast-weight 寫入——delta rule
  （Schlag et al., 2021）、DeltaNet、Titans；可訓練／由網路產生的量測算符——arXiv:2505.13525（開迴路）。
- **我認為是新的**（以這次搜尋的範圍為限）：(i) 指出 QKAN 層對量測算符是線性的，所以 QKAN-FWP 的 fast weights 可以有
  封閉形式的最佳寫入；(ii) 這個寫入的充分統計量恰好服從論文的 gated 遞迴，因此 Eq. 4、凸包有界與 prefix scan 都保留；
  (iii) QFWP 系列第一個閉迴路的寫入規則。
- **不主張量子優勢**：$\text{reps}=1$ 時每個電路的三個特徵就是 $u$ 的一次諧波（$\cos$、$\sin$ 與常數的組合），
  整個模型可以古典模擬。QKAN 特徵在哪裡有用、哪裡沒用，A.8 的消融有直接的答案。
'''

RESULTS = r'''### A.6 結果一：論文的六個 benchmark（論文協定，5 seeds）

所有模型用同一份資料、同一個 pipeline；QKAN-FWP-O 整張表只有一組設定（6 個電路、reps = 1、token 長度 $\min(8, N/2)$，
N = 8 時 {p_small} 個參數、N ≥ 16 時 {p_big} 個；設定在 70/10/20 的 validation 上選定）。CMG 這次有重現
（`gate='cmg'`：rank-one 產生的逐權重互補 gate、先寫後讀），並且另外給了它前一輪最好的 token 與 residual 讀出。

![paper benchmarks](figures/om_timeseries.png)

{ts_summary}

{ts_vs}

完整的 24 格：

{ts_main}

### A.7 結果二：需要 in-context 辨識的系統族

六個 benchmark 都是單一軌跡，train 與 test 來自同一個系統，所以一個固定的預測器就夠了——這也是線性 AR 贏的原因。
fast weights 只有在「視窗裡有慢參數存不下來的資訊」時才有意義。這裡每條序列是同一類系統、**不同的物理參數**
（`qkanfwp/families.py`），train／validation／test 用不同的序列，模型必須從 16 步的視窗辨識出系統：

| 族 | 內容 |
|---|---|
| Damped oscillation | 論文的 damped SHM，但頻率、阻尼、振幅、相位每條序列隨機 |
| Two tones | 兩個阻尼振盪的和 |
| Jaynes–Cummings | 論文的 JC，但耦合 $g$、失諧、腔損耗 $\kappa$ 與初始光子振幅每條序列隨機 |
| Hénon map | $x_{t+1} = 1 - a x_t^2 + b x_{t-1}$，$(a,b)$ 隨機；混沌、非線性 |
| Duffing | $\ddot x + d\dot x + ax + bx^3 = 0$，$(d,a,b)$ 隨機 |

「noise 0.02」是加在觀測值上的白雜訊（序列已正規化到約 $[-1,1]$）。每個神經模型都掃同樣的三個 lr 並由 validation 決定，
checkpoint 也由 validation 選。三條參考線不需要訓練：重複上一個值、所有序列共用一個線性 AR、
以及**在每個視窗內各自擬合的 ridge AR**（它知道系統是線性的，是線性族上很強的 oracle）。

![families](figures/om_family.png)

{fam_main}

{fam_vs}

### A.8 消融：到底是哪一部分在起作用

論文 benchmark：

{ts_ablation}

系統族：

{fam_ablation}

### A.9 有限量測次數（shot noise）

這個架構要解一個由量測值組成的線性方程，量測雜訊可能被 $C_T^{-1}$ 放大——這是把它搬上真機前最該先問的問題。
下面在測試時對每個量測到的期望值加上 $S$ 次量測的統計雜訊（變異數 $(1-v^2)/S$），並比較兩種訓練方式：用精確期望值訓練，
以及訓練時就帶著 $10^4$ shots 的雜訊（noise-aware）。baseline 改用物理的 ⟨Z⟩ 讀出以便比較。

![shots](figures/om_shots.png)

{shots}

{solar_section}
'''
