HEADER = '''# Gated QKAN-FWP：論文分析、改進方向與實驗驗證

對象論文：*Gated QKAN-FWP: Scalable Quantum-inspired Sequence Learning*（arXiv:2605.06734）。
本報告做三件事：(1) 整理論文機制與其限制；(2) 提出可降低 MSE 的改進方向，並對應近期文獻；
(3) 以重現的 baseline 為基準做實驗，驗證哪些改進有效、哪些無效。

> 所有數字皆由本 repo 的程式產生（`results/*.jsonl`），重現指令見第 10 節。
> 第 4–6 節是依「公平比較」規則做的最終結果；較早、參數量較大的第一階段結果保留在附錄 A。

'''

SUMMARY = '''## 摘要

> **修訂說明**：這一版依外部審查意見逐條查證後重寫，結論比前一版保守。逐條回應在第 0 節。

### 現在不能主張的事

1. **架構上的新穎性。**「多時間尺度（分組）gate」已被原論文團隊自己的後續工作涵蓋：arXiv:2607.27945（CMG，
   2026-07-30）提出逐座標的互補矩陣 gate，並推導了同樣的凸組合有界與 prefix-scan 結構。前一版漏引了它，以及
   同系列的 arXiv:2606.24933、2607.02363。Δ-token 與 residual 讀出則是時間序列預測的標準做法。
2. **重現了論文的 baseline。** 我重現的 GQKAN-QKANFWP 在論文協定下，比論文印出的數字差 21 倍
   （5 個 300 點序列共 20 格的幾何平均；NARMA5 N=16 是 69 倍）。原因沒有找到（5.7 節）。
   所以「相對我自己的 baseline 低幾百倍」不等於「相對論文低幾百倍」。
3. **這組 benchmark 上的 MSE 能代表模型能力。** 一個 9 參數的線性 AR(8)（最小平方法，不需要訓練）在 24 格中的
   21 格贏過我們最好的模型，也在 21 格贏過兩篇論文印出的最佳數字（5.6 節）。
4. **太陽黑子上穩健的改進。** 論文的 split 上三個指標都贏，但換 split 後 MSE 的優勢消失（第 6 節）。

### 仍然成立的事

Test MSE，對四個 window 取幾何平均，5 seeds：

{per_dataset}

1. **同一份資料、同一個 pipeline 內**，兩個 QKAN-based、參數量不超過論文的模型在全部 24 格都贏過重現的
   GQKAN-QKANFWP（不論它用論文協定或調過 lr）：HQKAN-Δ（136 參數）低 175 倍，QKAN-FWP+（149 參數）低 45 倍。
   HQKAN-Δ 對另外兩個重現的 QKAN 變體也是 24/24。
2. **直接和論文印出的數字比**（資料細節沒有全部公開，可比性未經驗證）：HQKAN-Δ 在 21/24 格低於兩篇論文
   （2605.06734 與 2607.27945）所有模型的最佳值，幾何平均低 19.5 倍；QKAN-FWP+ 是 18/24 格、低 5 倍。
3. **上面兩點對實作選擇不敏感**：改用物理的 ⟨Z⟩ 讀出、只用訓練段做正規化、NARMA 去掉起始暫態，結論都一樣（5.8 節）。
4. **診斷性的發現**（我認為這才是這份工作真正有用的部分）：
   - 論文協定（lr 1e-3、50 epochs）在我的實作中遠未收斂，光調 lr 就低 8.5 倍；
   - 在這六個序列上 fast-weight 記憶沒有幫助，靜態的 HQKAN-Δ 比 QKAN-FWP+ 好 2.5 倍（15 seeds）；
   - 六個序列的一步預測幾乎是線性問題，任何要用它們的論文都應該放線性 AR 當 baseline；
   - 太陽黑子：零參數的「重複上一個週期」（0.0156 / 35.9 / 16.2）就優於論文印出的模型（0.0168 / 39.59 / 21.89）。

### 模型大小

| | 論文的 GQKAN-QKANFWP | 我重現的 baseline | 我們的模型 |
|---|---|---|---|
| Time-series 參數量 | 159 | 152 | QKAN-FWP+：149　HQKAN-Δ：136 |
| 太陽黑子參數量 | 12,474 | 12,423 | QKAN-FWP+：11,732 |

### 太陽黑子

論文協定（80/10/10、best-validation checkpoint、5 seeds）下的 test 指標：

| 模型 | 參數量 | Scaled MSE | PAE | PTE |
|---|---|---|---|---|
| 重現的 baseline（lr 依論文做法由 validation 選：1e-3） | 12,423 | 0.0177 ± 0.0010 | 45.8 ± 2.8 | 26.1 ± 2.2 |
| QKAN-FWP+（同樣由 validation 選 lr：1e-3） | 11,732 | 0.0146 ± 0.0010 | 36.0 ± 0.4 | 18.6 ± 1.7 |
| 論文印出的數字 | 12,474 | 0.0168 ± 0.0016 | 39.59 ± 2.82 | 21.89 ± 1.57 |
| 參考：直接重複上一個週期（13 個月平滑，不需訓練） | 0 | 0.0156 | 35.9 | 16.2 |

在論文的 split 上我們的模型三個指標都贏過 baseline 與論文印出的數字。但 (a) 零參數的參考線就已經贏過論文印出的模型；
(b) 在 validation 期間我們的模型比 baseline 差；(c) 換成 60/20/20 split 後 MSE 是 +5%（p = 0.23），
70/15/15 是 −7%（p = 0.07），只有 PAE 在三種 split 都較好。

### 沒有做

MiniGrid 強化學習（論文 Sec. 6.3）、真機實驗、論文以多 qubit VQC 為 fast programmer 的三個模型，以及 CMG 本身的重現。
'''

SEC0_REVIEW = '''## 0. 審查意見逐條回應

| # | 審查意見 | 判定 | 查證結果 | 處理 |
|---|---|---|---|---|
| 1 | 多時間尺度 gate 與原團隊的 arXiv:2607.27945（CMG）撞車；漏引 2606.24933、2607.02363 | **成立** | 三篇都存在、都早於本報告。CMG 是 `Θ_t = G_t⊙Θ_{{t−1}} + (1−G_t)⊙Δ_t`，`G_t` 為逐座標 sigmoid gate，並推導了逐座標的凸組合有界與 affine prefix scan。我的分組 gate 是它的粗粒度特例（程式裡的 `gate_groups='param'` 就是不做 low-rank 分解的 CMG）。 | 撤回新穎性主張，補引三篇。和 CMG 的差別只剩 chrono 初始化與分組方式；而且 5.4 節顯示 gate 的粒度在這組 benchmark 上沒有差別。 |
| 2 | Jaynes–Cummings 參數誤設為 w0 = 1、w = 1、g = 0.5，振盪慢了 2π 倍，才會有 1e-9 的 MSE | **不成立**（但 1e-9 確實不代表什麼） | `qkanfwp/data.py` 用的是 ωc = ωq = 2π、g = π、γ = 0.05；repo 裡沒有 `w0`、`g_jc` 這些變數。實測拉比週期 1.0000（每週期 60 個取樣點），與解析解 sin²(πt)·e^(−γt/2) 的最大差 3.7e-4。 | 參數不用改。但查證時發現更根本的問題：JC 是嚴格的線性遞迴訊號，4 個參數的線性 AR(3) 就有 1e-30（5.6 節）。 |
| 3 | NARMA5 N=16 上自建 baseline（1.94e-3）比論文 Table 3（2.8e-5）差 69 倍；「改進 408 倍」的模型（2.84e-5）只是追平論文，還輸給論文的 G-QKANFWP（1.2e-5） | **實質成立** | 數字都對（只有 baseline 是 152 參數而非 163）。2.84e-5 是第一階段、已被取代的 190 參數模型；最終模型在這一格是 3.67e-6（QKAN-FWP+）與 1.79e-6（HQKAN-Δ）。但核心批評成立：我沒有重現論文的 baseline。 | 不再用「相對自建 baseline 的倍數」當結論；5.7 節量化重現缺口並檢驗了兩個假說；摘要同時列出論文印出的數字。 |
| 4 | 「DARUAN 只含整數諧波」不精確；`fast_measure=True` 輸出的 \\|a\\|−\\|b\\| 不是 ⟨Z⟩ | **前半不適用，後半成立** | 報告與程式都沒有寫過「整數諧波」這個說法。後半是對的，而且前一版沒有揭露：所有結果都沿用 `qkan` 套件的預設 `fast_measure=True`，讀出的是 \\|a\\|−\\|b\\| 而不是論文 Eq. 1 的 ⟨Z⟩；data-encoding gate 的 `w_l` 也固定為 1（不可訓練）。 | 3.5 節揭露；5.8 節改用物理的 ⟨Z⟩ 重跑，結論不變。 |
| 5 | 正規化用了整條序列的 min/max（洩漏）；NARMA 前 `order` 步是 0、沒有 burn-in；residual 讀出不是獨立線性層 | **前兩項成立；第三項沒有出入** | 先正規化再切分和兩篇論文的寫法一致，但確實是洩漏，前一版沒有列為限制。Residual 讀出從頭到尾都是無參數的 `ŷ = x_T + 網路輸出`，報告沒有說它是線性層。 | 3.5 節揭露；5.8 節重跑「只用訓練段做正規化」與「NARMA 丟掉 200 步 burn-in」，結論不變。 |
| 6 | 改成 60/20/20 後 solar 的改進不顯著（p = 0.27） | **成立，前一版已經寫了** | 我算到的是：第一階段只加 gate 的模型 −7.4%（Welch p = 0.066），最終模型 +5.1%（p = 0.23）。0.27 我用 Welch、Student、Mann–Whitney、paired 四種檢定都沒有重現，但結論相同：不顯著。 | 摘要把這個保留提前。 |

查證過程中另外發現、審查意見沒有提到的兩件事：

- **線性 AR(8) 在 21/24 格贏過所有模型**（5.6 節）。這比上面任何一點都更影響這份工作的意義。
- **後續論文 2607.27945 寫的是先寫後讀**（「the fast programmer predicts with the updated state」），和原論文的式子
  （先讀後寫）不同。我原本以為這能解釋重現缺口，實測結果是先寫後讀的 baseline 反而再差 2 倍（5.7 節）。
'''

SEC2_NOTE = '''
**關於 B1（分組 gate）的先行工作。** 上表 B1 這一列前一版只引了 RWKV-7、Mamba 等一般文獻，漏掉了最直接相關的三篇，
都出自原論文團隊：Self-Modulating QFWP（arXiv:2606.24933，對新寫入與舊記憶做逐元素調變）、它的有界版本
（arXiv:2607.02363，對舊記憶分支加 tanh），以及 **Complementary Matrix-Gated QKAN-FWP（arXiv:2607.27945）**。
最後一篇的 CMG 就是把 scalar gate 換成逐座標的互補 gate，動機（「所有 fast 參數被迫共用同一個記憶時間尺度」）、
有界性與 prefix-scan 的論證都和 B1 相同，而且做得更完整（low-rank 產生 gate、七個 dataset、五種序列長度）。
因此 B1 **不是本報告的貢獻**。兩者實驗結論的差異值得記下來：CMG 論文報告逐座標 gate 在它的協定下（純量輸入、
lr 1e-3、100 epochs，參數量多 39–63%）帶來一致的改進；本報告在論文協定下也看到分組 gate 有 0.53 倍的增益
（附錄 A），但把 lr 與輸入表徵修好之後，這個增益就消失了（5.4 節）。

**第二輪新增的兩項改動**（依公平比較規則重做時加入）：把 Δ-token 從 3 維加長到 8 維
（`(x_t, Δx_t, …, Δ⁷x_t)`），以及太陽黑子用的「上一個週期」residual 讀出——它是 A2 在 multi-step 預測上的對應版本。
'''

SEC3_RULES = '''
### 3.4 公平比較的規則（最終結果）

- **QKAN-based**：我們的模型只用 HQKAN。LSTM 只作為對照組出現，不是我們的方法。
- **參數量**：time-series ≤ 152（重現的 baseline；論文是 159），太陽黑子 ≤ 12,423（論文 12,474）。
- **Baseline 都調過 lr**：重現的 GQKAN-QKANFWP、GQKAN-FWP、G-QKANFWP 各自在 validation 上選 cosine 的初始 lr
  （候選 1e-2、3e-2、1e-1，必要時再往外一格），Jaynes–Cummings 另外單獨選。選出的結果：

  | 模型 | 5 個 300 點序列 | Jaynes–Cummings |
  |---|---|---|
  | GQKAN-QKANFWP（152） | 3e-2 | 1e-2 |
  | GQKAN-FWP（114） | 1e-1 | 3e-2 |
  | G-QKANFWP（175） | 3e-2 | 1e-2 |
  | 我們的兩個模型 | 3e-2 | 3e-2 |

- **模型選擇只用 validation**：候選的 token 長度、gate 分組、寬度都在 dev protocol（seeds 100–102）上選
  （`results/dev_param_matched.jsonl`），最終數字用 seeds 0–4。
- 論文的 QFWP / G-QFWP / GQKAN-QFWP（fast programmer 是多 qubit VQC）沒有重現，所以不在 baseline 之列。

### 3.5 與論文實作的已知差異

這些是我的重現和論文（或論文沒有寫明的部分）之間的差異，前一版沒有集中列出：

| 項目 | 本 repo 的做法 | 論文 | 影響 |
|---|---|---|---|
| DARUAN 的讀出 | `qkan` 套件預設的 `fast_measure=True`：輸出 \\|a\\|−\\|b\\|，不是物理量 | Eq. 1 寫的是期望值 ⟨Z⟩ = \\|a\\|²−\\|b\\|² | 5.8 節用 ⟨Z⟩ 重跑，相對結論不變 |
| Data-encoding gate | `RZ(x)`，`w_l ≡ 1`、不可訓練（`qkan` 預設），輸入頻率固定 | 未說明；arXiv:2509.14026 允許可訓練的 `w_l x + b_l`，頻率不限於整數倍 | 未測 |
| 讀與寫的順序 | 先讀後寫 `y_t = F(x_t; W_t)`（原論文的式子） | 原論文同左；後續論文 2607.27945 寫的是先寫後讀 | 5.7 節：先寫後讀的 baseline 再差 2 倍 |
| 正規化 | 對整條序列取 min/max，再切 train/test | 相同（兩篇論文都是先正規化再切分） | 有洩漏；5.8 節改成只用訓練段，數字幾乎不變 |
| NARMA | M = 300，從 0 起跳，沒有 burn-in | M = 300，其餘未說明 | 暫態會壓縮正規化後的有效範圍，並在 N = 8 時進入訓練目標；5.8 節 |
| Bessel / SHM / DQC 的取樣點數 | 各 300 點 | 未說明 | 絕對 MSE 不可比 |
| 層的大小 | 在 validation 上從 5 種配置中選（3.1 節） | 只給總參數量 | — |
'''

SEC4_MODELS = '''## 4. 最終模型

### 4.1 Time-series：兩個 QKAN-based 模型

兩個模型共用三樣東西：

- **Δ-token**：每一步的輸入不是純量 `x_t`，而是 `(x_t, Δx_t, Δ²x_t, …, Δ⁷x_t)`（最近 8 個值的 backward
  differences）。各階差分除以它在訓練集上的標準差（對 window 內所有位置計算，包含開頭 replicate padding
  補出來的位置；這使高階差分在平滑序列上被縮得比單位變異小，見 5.4 節的說明）。
- **Residual 讀出**：`ŷ = x_T + 網路輸出`。
- **訓練**：和論文一樣 50 epochs、batch 4、Adam、MSE，只把固定 lr 1e-3 換成 cosine（初始 3e-2）。

| | **QKAN-FWP+**（149 參數） | **HQKAN-Δ**（136 參數） |
|---|---|---|
| 架構 | 論文的 gated fast-weight programmer | 單一 HQKAN，沒有 fast weights、沒有記憶 |
| Slow programmer | HQKAN 8 → 3 → 2（reps 3）→ 16 個 fast 角度 + 2 個 gate | — |
| Fast programmer / 主網路 | HQKAN 8 → 2 → 1（reps 3），2 個 DARUAN 電路（與 baseline 相同） | HQKAN 8 → 4 → 3 → 1（reps 3），12 個 DARUAN 電路，參數固定 |
| 記憶規則 | 論文 Eq. 3，但每個 DARUAN 電路各一個 gate（chrono 初始化） | 無（只看最後一個 token） |
| 參數分配 | slow 27 + 48 + 54，fast 18 + 2 | 36 + 96 + 4 |

**QKAN-FWP+ write-first** 是 QKAN-FWP+ 的一個變體：先寫入再讀出（`y_T = F(x_T; W_{T+1})`），讓最新的 token
也經過 slow programmer。論文是先讀後寫，所以最新的 token 只會經過很小的 fast programmer。

### 4.2 太陽黑子：QKAN-FWP+（11,732 參數）

在重現的 baseline（slow HQKAN 1 → 10 → 10，fast HQKAN 1 → 10 → 20 → 132，200 個 DARUAN 電路）上改三處：

- **多時間尺度 gate**：fast QKAN 的 20 個輸出節點各一個 gate（論文是全部共用一個 scalar gate），
  chrono 初始化成對數等距的記憶長度 τ ∈ [2, 528] 個月。
- **Last-cycle residual 讀出**：`ŷ = smooth₁₃(最近 132 個月) + 網路輸出`，decoder 初始化為 0，
  所以未訓練的模型就是「重複上一個週期」。
- **Slow latent 10 → 9**：把上面多出來的 gate 參數抵掉，總參數量 11,732 < 12,423。

Fast programmer 的 200 個單 qubit 電路與訓練協定（100 epochs、batch 32、peak-aware loss、best-validation
checkpoint）都和論文相同。
'''

SEC5_TS = '''## 5. 結果：time-series（論文 Sec. 6.1 的六個 dataset）

### 5.1 全部 24 格（論文的 80/20 split，seeds 0–4，test MSE，mean ± std）

![time-series main](figures/timeseries_main.png)

{main}

每一列的粗體是該格最好的模型。

### 5.2 對每個 baseline 的勝負

**HQKAN-Δ（136 參數）：**

{vs_static}

**QKAN-FWP+（149 參數）：**

{vs_fwp}

**QKAN-FWP+ write-first（149 參數）：**

{vs_wf}

- HQKAN-Δ 對每個 baseline 都是 24/24，最小的差距也有 3.5 倍；它在 24 格中也都贏過 QKAN-FWP+ 與 write-first 變體。
- QKAN-FWP+ 對論文的主力模型 GQKAN-QKANFWP 是 24/24（調過 lr 的版本最小差距 1.7 倍）。對另外兩個調過 lr
  的變體各輸 1–2 格，都在 Bessel / Damped SHM 的 1e-6 等級、且在 seed 標準差之內
  （例如 Bessel N=32：1.43e-6 ± 4.0e-7 對 1.22e-6 ± 7.7e-7）。
- Write-first 變體和 QKAN-FWP+ 幾乎一樣（24 格的幾何平均是它的 0.94 倍，13 格較好），主要差別在 N = 8（0.77 倍）；
  它讓「低於論文印出的 GQKAN-QKANFWP 數字」從 23/24 變成 24/24。

### 5.3 和論文印出的數字比較

下表把論文 Table 4–6 的數字直接並列。**這個比較只能參考**：論文沒有給 Bessel / SHM / DQC 的取樣點數，
而且我重現的論文模型在同一份資料上得到的數字和論文印的差了 0.3–180 倍（方向不一），表示兩邊的資料或實作
細節並不相同。粗體表示低於論文所有模型在該格的最佳數字。

{paper}

沒過的格子都在 NARMA 的短 window。這兩個序列的 M = 300 點包含從 0 起跳的暫態；N = 8 時暫態會進入訓練目標，
是我們的模型在該格變差的原因（HQKAN-Δ 只看最後 8 個值，N = 16 以上時 NARMA5 是 1.4–2.1e-6，N = 8 卻是 1.4e-5）。

### 5.4 Ablation：QKAN-FWP+ 的每個部分貢獻多少

5 個 300 點序列 × N ∈ {{16, 64}}；數字是 seed-mean test MSE ÷ 論文協定 baseline 的幾何平均（越小越好）。

![ablation](figures/timeseries_ablation.png)

{ablation}

- **Residual 讀出**：拿掉後變差 8 倍（0.0036 → 0.029）。
- **Δ-token**：拿掉（回到純量輸入）變差 18 倍（→ 0.064）。8 維比 3 維整體好 1.3 倍：NARMA 與 DQC 好 2–10 倍，
  Bessel 與 SHM 反而差 2–5 倍。
- **Float64 差分**：沒有可量測的效果（0.0036 對 0.0036）。原因是 4.1 節提到的 scale：高階差分在平滑序列上被縮到
  接近 0，rounding 雜訊也跟著被縮掉。程式保留這個選項，但它不是改進來源。
- **多時間尺度 gate**：在這個最終模型裡沒有幫助——換回論文的 scalar gate 是 0.0031，略好於分組 gate 的 0.0036。
  （第一階段 3 維 token 的模型裡分組 gate 有 0.75 倍的增益，見附錄 A；token 變長後這個增益消失。）
- **Fast weights 本身**：拿掉整個 fast-weight 機制、把參數直接用在一個靜態 HQKAN 上（HQKAN-Δ）是 0.00091，
  在這 5 個 seed 上比 QKAN-FWP+ 好 4 倍。因為這個結論很重要，我對兩者各加跑 10 個 seed
  （`results/extra_seeds.jsonl`）：**15 個 seed 合計 HQKAN-Δ 好 2.5 倍，10 格中贏 9 格**，150 組同 seed 的配對中
  有 105 組較好。QKAN-FWP+ 的 seed 間變異也比較大（同一格內最差與最好 seed 的 MSE 比值，中位數是 37 倍，
  HQKAN-Δ 是 12 倍）。要注意的是，選模型時用的 3 個 dev seed 上 QKAN-FWP+ 反而略好（1.3–1.9 倍），
  所以只看少數 seed 會得到相反的結論。
- **對照（非 QKAN）**：160 參數的 LSTM 用同樣的 token 與 residual 是 0.00093，和 HQKAN-Δ 打平。

### 5.5 第一層解讀

1. 論文 Sec. 6.1 的六個序列本質上是「局部自迴歸」問題：最近 8 個值加上 residual 讀出就足以把 MSE 壓到 1e-6
   甚至 1e-9 等級，不需要跨整個 window 的記憶。
2. 在固定 ~150 個參數的預算下，把參數花在「由 slow programmer 產生 fast programmer 的角度」不如直接訓練一個
   靜態 QKAN。論文的 read-before-write 順序讓最新的 token 只經過 2 個 DARUAN 電路；write-first 變體針對這點，
   但只在 N = 8 有明顯幫助，不足以補上和 HQKAN-Δ 的差距。
3. 因此這組 benchmark 可以證明「QKAN + 好的輸入表徵」很有效，但**不能**用來證明 gated fast-weight 記憶的價值。
   要檢驗記憶機制，需要真正長程相依的任務（太陽黑子的 528 步輸入、或 RL）。

### 5.6 線性參考線：這組 benchmark 到底有多難？

為了回應「1e-9 等級的 MSE 是不是失真」，我把最簡單的參考模型也放進來：線性自迴歸
`x̂_t = w·(x_{{t−p}}, …, x_{{t−1}}) + c`，用最小平方法在**同樣的訓練 window** 上解出來（`experiments/reference_baselines.py`），
不需要梯度訓練，參數量是 p + 1。粗體是該格最低的數字。

{linear}

- **9 個參數的線性 AR(8) 在 21/24 格贏過我們最好的模型，也在 21/24 格贏過兩篇論文印出的最佳數字。**
  HQKAN-Δ 只在 NARMA 的短 window（NARMA5 N=8、NARMA10 N=8 與 16）勝過它。
- Jaynes–Cummings 是「衰減的常數項＋衰減的餘弦」，嚴格滿足三階線性遞迴，所以 AR(3) 就到 1e-30（機器精度）。
  我們的 1e-9 不是參數設錯造成的，但它離真正的解還差二十個數量級；論文的 1e-4 ～ 1e-6 更遠。
- Bessel、Damped SHM、DQC 也幾乎是線性遞迴；連 NARMA 在訓練目標避開起始暫態之後，AR(8) 也很準
  （NARMA5 在 N ≥ 16 時約 3e-7 ～ 5e-7，NARMA10 在 N ≥ 32 時約 5e-8）。
- 結論：**在這六個序列上比較一步預測的 MSE，比的是「誰把一個接近線性的映射擬合得比較準」，不是序列建模能力。**
  這個批評同時適用於本報告與兩篇論文。HQKAN-Δ 的好成績，本質上是「一個 136 參數的 QKAN 近似了線性 AR(8)，
  但還沒有逼近到最小平方解」。

### 5.7 重現缺口：我的 baseline 沒有重現論文印出的數字

{gap}

- 在論文協定下，重現的 GQKAN-QKANFWP 在 5 個 300 點序列上比論文印出的數字差 21 倍（幾何平均），
  Jaynes–Cummings 則反過來好 4–7 倍。
- **假說一：讀寫順序。** 後續論文寫的是先寫後讀。實測先寫後讀的 baseline 更差（43 倍），所以這不是原因。
- **假說二：訓練效率。** 同一個模型把 lr 調好之後，和論文印出的數字只差 1.9 倍（20 格幾何平均，個別格子 0.2–14 倍）。
  也就是說缺口主要來自「lr 1e-3、50 epochs 在我的實作裡收斂得比論文慢」，而不是模型容量；可能是初始化、
  optimizer 細節或層的配置不同，我無法從論文確定。
- **假說三：NARMA 的尺度。** 把我在 [−1, 1] 正規化資料上得到的 MSE 換算回原始尺度，NARMA5 / NARMA10 的 baseline
  是 2.3e-5 / 3.6e-5，和論文印的 2.8e-5 / 5.2e-5 很接近。這與「論文的 NARMA MSE 是在原始尺度上算的」一致，
  但只是巧合也說得通；直接在原始尺度上訓練得到的是 1.1e-4，並不吻合。這個假說無法證實。
- 因此本報告所有「相對 baseline 低幾倍」的數字，都只能解讀為**同一個 pipeline 內**的相對比較。

### 5.8 Robustness：三個實作選擇會不會改變結論？

N = 16、5 seeds。三種條件分別對應第 0 節的第 4、5 點。

{robust}

{burnin}

- **⟨Z⟩ 讀出**：數字大多變動在 2 倍以內，Jaynes–Cummings 上我們的兩個模型變差 3–4 倍；排序不變，
  對 tuned baseline 的幾何平均優勢從 61 / 201 倍變成 48 / 135 倍。
- **只用訓練段做正規化**：Bessel、SHM、NARMA10、DQC、JC 的數字和原本**完全相同**，因為這些序列的極值都落在訓練段
  （衰減訊號的最大振幅在前面）；只有 NARMA5 的最大值在測試段，數字變動不到 3%。所以洩漏在這組資料上實際沒有作用。
- **NARMA 去掉暫態**：正規化後的訊號佔滿整個 [−1, 1]，所有模型的 MSE 都變大，但我們的兩個模型仍比 baseline 低
  兩到三個數量級；N = 8 不再特別差，證實 5.3 節的解釋。
'''

SEC6_SOLAR = '''## 6. 結果：太陽黑子週期預測（論文 Sec. 6.2）

### 6.1 論文的 split 與協定（80/10/10，test 目標期間 1993–2026）

{main}

![solar forecast](figures/solar_forecast.png)

- 在論文選用的 lr 2.5e-3 下，QKAN-FWP+（11,732 參數）三個指標都比重現的 baseline（12,423 參數）好：
  MSE −27%、PAE −16%、PTE −41%，也都優於論文印出的 0.0168 / 39.59 / 21.89。
- 兩個部分的分工很清楚：**多時間尺度 gate 降 MSE**（gates only：0.0139，PAE / PTE 只小幅改善）；
  **last-cycle 讀出改善峰值指標**（read-out only：PAE 34.2、PTE 19.6，但 MSE 沒變）；兩者合起來三個指標都好。
- **零參數的參考線**（重複上一個週期、13 個月平滑）就有 0.0156 / 35.9 / 16.2，已經優於論文印出的模型。
  我們的模型在它之上把 MSE 再降 14%，PAE / PTE 則略遜於它。

論文的做法是從 {{1, 2, 2.5}}×1e-3 中用 validation loss 選 lr。兩個模型的完整結果：

{grid}

不論用哪個 lr，或各自用 validation 選出的 lr（兩者都是 1e-3），我們的模型在三個 test 指標上都比較好。

### 6.2 這個結果有多穩？

**Validation 與 test 的排序相反。** 上表的 Val. loss 欄：我們的模型是 3.3–3.8，baseline 是 2.5。也就是說，在
validation 期間（目標 1971–2004，SC21–23 等強週期）我們的模型明顯較差，在 test 期間（1993–2026，含偏弱的 SC24）
則明顯較好；被選中的 checkpoint 多半在前幾個 epoch（平均第 1–3 個），表示訓練主要是在微調「重複上一個週期」
這個起點。

換兩種 chronological split 再看一次（同樣的協定、lr 2.5e-3）：

**60/20/20（test 目標 1971–2026，五個週期，5 seeds）**

{split622}

**70/15/15（test 目標 1982–2026，四個週期，3 seeds）**

{split715}

![error by start](figures/solar_error_by_start.png)
![error by start, 60/20/20](figures/solar_error_by_start_split622.png)

三種 split 的 test 指標（baseline → 我們的模型）：

| Split | Test 目標期間 | Scaled MSE | PAE | PTE |
|---|---|---|---|---|
| 80/10/10（論文） | 1993–2026 | 0.0184 → 0.0134（−27%，p < 0.001） | −16%（p = 0.002） | −41%（p < 0.001） |
| 70/15/15 | 1982–2026 | 0.0168 → 0.0156（−7%，p = 0.07） | −20%（p = 0.07） | −9%（p = 0.23） |
| 60/20/20 | 1971–2026 | 0.0175 → 0.0184（+5%，p = 0.23） | −14%（p = 0.035） | −6.5%（p = 0.17） |

- **PAE 在三種 split 都比較好**；PTE 方向一致但只有論文的 split 顯著；**MSE 的優勢只在論文的 split 明顯**，
  在 60/20/20 上消失。
- 零參數的參考線在三種 split 的 PAE / PTE 都比兩個模型好，MSE（0.0156 / 0.0168 / 0.0166）也和我們的模型相當。
- 第一階段只加多時間尺度 gate 的 12,632 參數模型，在 60/20/20 上的 MSE 是 0.0162（−7%），但 PAE / PTE 沒有改善
  （上表第三列與附錄 A）。

### 6.3 判斷

- 依論文自己的協定與 split，我們的 QKAN-based、參數更少的模型在 scaled MSE、PAE、PTE 上都勝過重現的 baseline
  與論文印出的數字。這一點成立。
- 但這個 benchmark 的 test 只涵蓋兩個半太陽週期，不同期間的排序會翻轉，而且零參數的 seasonal-naive 就在同一個水準。
  所以它**不足以**證明哪個模型的預測能力真的比較好——這個保留同樣適用於論文 Table 7 中各模型之間 10–30% 的差距。
- 若要把太陽黑子的結果寫進論文，建議至少：加入 seasonal-naive 當 baseline、用多個 rolling-origin split 取平均、
  並同時報 validation 期間的指標。
'''

SEC7_NEGATIVE = '''## 7. 沒有效果、或要小心的地方

| 想法 | 結果 | 說明 |
|---|---|---|
| 多時間尺度 gate（time-series 最終模型） | 0.0036 對 scalar gate 的 0.0031 | Token 夠長之後，這些序列不需要多個記憶時間尺度；它的價值在長輸入（太陽黑子的 MSE） |
| Float64（精確）差分 | 無差別 | 見 5.4 節 |
| 原始 lag patch（不做差分），長度 3–10 | validation MSE 是 Δ-token 的 5–20 倍，NARMA5 甚至比 baseline 差 | 相鄰值幾乎相同，斜率資訊量級太小，50 epochs 內學不出來 |
| Write-first（先寫後讀） | 整體幾乎沒差：validation 0.94 倍、test 0.94 倍；N = 8 時 0.75–0.77 倍 | 讓最新 token 經過 slow programmer，只在 window 很短時有用 |
| 從 lr 1e-3 開始的 cosine decay | validation MSE 變 2 倍 | 本來就訓練不足；要搭配更大的初始 lr |
| 固定大 lr（3e-2）不 decay | 比 cosine 差 13 倍 | 後期在最小值附近震盪 |
| Solar：單獨的 chrono 初始化（scalar gate） | 0.0185 對 0.0184 | 一個 gate 只有一個時間尺度 |
| Solar：平滑的輸出基底（132 個輸出改成 16–40 個 cosine mode） | validation 與 test 都沒有改善 | 省 2,000 個參數，但不降誤差 |
| Solar：年尺度 patch token | validation 略好、test MSE 略差 | 與其他改動一樣，排序隨期間翻轉 |
| Solar：調高 lr（cosine 5e-3 / 1e-2） | validation 變差 | Solar 是 generalization-limited |

另外兩個實作上的注意事項：

- **Δ-token 在 window 開頭的 padding**：前 7 個位置的差分是用 replicate padding 算的，並不是真正的差分，
  卻仍然被寫進 fast-weight 記憶，也影響 scale 的計算。只用完整的 token（並搭配 write-first）是明顯的下一步，尚未測。
- **NARMA 的起始暫態**：M = 300 的序列從 0 起跳；N = 8 時暫態樣本會進入訓練集並主導 loss。
'''

SEC8_TODO = '''## 8. 還沒做、但值得做的方向

1. **MiniGrid RL（論文 Sec. 6.3）。** 這次沒有做。它需要 A3C 與上千萬個環境步數，而且本報告的主要改動
   （residual 讀出、Δ-token、lr）是為了回歸問題設計的；RL 上值得先試的是多時間尺度 gate 與 write-first。
2. **只用完整 token ＋ write-first** 的 QKAN-FWP（第 7 節），預期能縮小它和 HQKAN-Δ 的差距。
3. **需要真正長期記憶的 benchmark。** 第 5.5 節的結論是現有六個序列無法鑑別記憶機制；可以用延遲更長的 NARMA
   （例如 NARMA30 配 N ≥ 64）、copy / adding task，或把 DQC 的脈衝間隔拉長。
4. **太陽黑子的評估方式**：seasonal-naive baseline、rolling-origin 多 split、同時報 validation 指標（6.3 節）。
5. **記憶規則的其他設計**：delta-rule / keyed 寫入（Gated DeltaNet、RWKV-7）、momentum 記憶（Titans）、
   預測誤差回饋（Recurrent FWP）、dense supervision、low-rank proposal。這些在第 2 節的表中標為未實測。
6. **硬體相容性**：所有改動都在古典側（token 進入古典 encoder、residual 是古典加法、gate 作用在角度上）；
   QKAN-FWP+ 的 fast programmer 電路與論文相同，HQKAN-Δ 則是 12 個固定角度的單 qubit 電路。真機沒有實測。

'''

SEC9_LIMITS = '''## 9. 限制

- 這是**獨立重現**，不是官方程式，而且**沒有重現論文印出的 baseline 數字**（5.7 節）；層的大小、取樣點數等論文
  未給的細節是我選的（3.1、3.5 節），所以 time-series 的絕對 MSE 與論文表格的比較只能參考。
- **沒有架構上的新穎性**：分組 gate 已被 arXiv:2607.27945 涵蓋，而且本報告沒有重現 CMG 來直接比較。
- 六個 time-series benchmark 都輸給線性 AR(8)（5.6 節），在它們上面的 MSE 排名不能當作模型優劣的證據。
- 論文以多 qubit VQC 為 fast programmer 的三個模型（QFWP、G-QFWP、GQKAN-QFWP）沒有重現。
- lr 只掃了 cosine schedule 下的少數幾個值；最終模型是在約 20 個參數量相近的候選中用 3 個 dev seed 選的，
  候選之間的差距有些在 seed 雜訊之內。
- 太陽黑子的結論受評估期間影響很大（第 6 節）。
- 沒有做 MiniGrid RL 與真機實驗；論文 Table 7 的 classical baselines（LSTM、WaveNet-LSTM、MESN…）也沒有重跑。

'''

SEC10_REPRO = '''## 10. 重現

```bash
pip install -r requirements.txt
python -m pytest tests -q          # 41 個測試
bash experiments/run_all.sh        # 全部實驗（約 15 CPU core-hours；已完成的 job 會自動跳過）
python experiments/reference_baselines.py  # 線性 AR 參考線（幾秒）
python experiments/make_figures.py # 產生 figures/、results/tables_final.md、results/tables_stage1.md
```

最終模型的 variant 名稱：`pmx_diff8_edge_h3l2@cos30`（QKAN-FWP+）、`pmx_diff8_edge_h3l2_wf@cos30`（write-first）、
`ar_hqkan8@cos30`（HQKAN-Δ）、太陽黑子的 `mtg_cyc_pm`。

環境：Python 3.13、PyTorch 2.15（CPU）、`qkan` 0.2.3（只用於測試對照）。
'''

APPENDIX_INTRO = '''## 附錄 A：第一階段結果（參數量較大的模型）

這一節是加入「參數量不得超過論文」這條規則之前的結果，保留下來是因為其中的 ablation 與對照組仍然有參考價值。
這裡的「Extended」是 3 維 Δ-token ＋ residual（162 參數），「Extended ＋ multi-timescale gates」是 190 參數；
太陽黑子的多時間尺度 gate 模型是 12,632 參數。**最終結果請以第 4–6 節為準。**

閱讀這一節時請注意第 0 節的三點修正：(1) 這裡的「低 N 倍」都是相對於我自己重現的 baseline，而它沒有重現論文印出的
數字（5.7 節）；例如 A.1.1 的「低 408 倍」模型在 NARMA5 N=16 上是 2.84e-5，只和論文印出的 2.8e-5 打平。
(2)「多時間尺度 gate」不是新東西，原團隊的 CMG（arXiv:2607.27945）已經涵蓋。(3) 這些序列上線性 AR(8) 更準（5.6 節）。

'''
