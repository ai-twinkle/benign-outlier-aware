# Benign Outliers 對 Twinkle AI 模型安全對齊之影響研究

## 研究背景

大型語言模型（LLMs）經過安全對齊訓練後，往往在後續微調（Fine-tuning）階段面臨安全性降解的風險。現有研究多聚焦於有害數據集對安全對齊的破壞，然而近期研究（Benign Samples Matter, 2024）揭示了一個更隱蔽的威脅：**即使完全使用良性數據進行微調，其中少量的「良性異常樣本（Benign Outliers）」仍能嚴重破壞模型的安全防線**。

本研究以 Twinkle AI 開源模型 [`twinkle-ai/gemma-3-4B-T1-it`](https://huggingface.co/twinkle-ai/gemma-3-4B-T1-it) 為研究對象，探討此模型在 benign outlier 攻擊下的脆弱性，並評估現有防禦方法的有效性。

---

## 研究問題

1. **脆弱性（Vulnerability）**：`twinkle-ai/gemma-3-4B-T1-it` 在面對 benign outlier 攻擊時，安全對齊是否同樣容易被破壞？
2. **識別與還原（Identification）**：能否用 Self-Inf-N 方法從良性數據集中有效萃取出針對此模型的 benign outliers？
3. **連續學習場景（Continual Learning）**：在真實的連續學習（Continual Learning）場景下，benign outlier 的破壞力是否具有持久性且難以被後續微調消除？
4. **防禦有效性（Defense）**：SafeGrad 與 AsFT 等梯度約束防禦方法，能否有效對抗 benign outlier 攻擊？

---

## 目標模型

| 項目 | 說明 |
|------|------|
| 模型名稱 | `twinkle-ai/gemma-3-4B-T1-it` |
| 基底架構 | Google Gemma 3 4B（Instruction-tuned） |
| 來源 | HuggingFace Open Source |
| 特性 | Twinkle AI 在 Gemma 3 基礎上進行安全對齊與指令微調 |

---

## 核心方法論：Benign Samples Matter 論文

> 參考資料來源：NotebookLM Notebook — [Benign Samples Matter 論文](https://notebooklm.google.com/notebook/5d84f1bb-24de-4f7c-9a93-c85e1ecdf717)

### 核心問題定義

良性微調數據集（如 Dolly、Alpaca）中，存在少量表面無害但「梯度方向有害」的樣本。這些樣本在微調時會將模型參數推向有害區域，且不依賴外部有害數據作為錨點（anchor-free），因此難以被傳統毒性檢測工具（Perspective API、OpenAI Moderation）偵測。

### Benign Outlier 識別方法：Self-Inf-N

論文提出 **Self-Inf-N（Normalized Self-Influence Score）** 評分方法：

**Step 1 — 計算自影響力分數（Self-Influence Score）**

$$\text{Self-Inf}(z) = \nabla_\theta \mathcal{L}(z)^\top H^{-1} \nabla_\theta \mathcal{L}(z)$$

使用一階梯度近似（first-order gradient approximation）計算每個樣本 $z$ 對模型自身損失的影響程度，找出梯度模最大的異常值。

**Step 2 — 修正長度偏差（Length Bias Correction）**

原始 Self-Inf 分數存在嚴重偏差，傾向挑選回答極短的樣本，導致：
- 微調後模型效能降低
- 生成的有害內容過於簡短，缺乏實際攻擊威脅

**Step 3 — Self-Inf-N 正規化**

$$\text{Self-Inf-N}(z) = \log(\text{Self-Inf}(z) + 1) + \log(\text{len}(a) + 1)$$

將自影響力分數與回答 token 長度透過對數轉換映射至相近尺度，平衡兩者權重，篩選出更具多樣性且破壞力強的 benign outliers。

### 關鍵發現

| 發現 | 細節 |
|------|------|
| **高破壞力** | 僅需 100 筆 benign outliers 即可使安全對齊嚴重崩潰，效果媲美使用純惡意數據微調 |
| **跨架構遷移性** | 在某模型上篩選的 outliers，能有效攻擊 Qwen、Gemma、Mistral、Llama-3 等不同架構 |
| **連續學習中的持久性** | 1% outliers 混入 99% 良性數據後，有害性大幅提升且後續微調難以消除 |
| **防禦繞過** | 現有毒性檢測工具（Perspective API、OpenAI Moderation）、數據增強防禦、Lisa 雙狀態微調防禦全面失效 |

---

## 實驗一：脆弱性分析

### 目標
驗證 `twinkle-ai/gemma-3-4B-T1-it` 對 benign outlier 攻擊的脆弱程度。

### 實驗設計

```
良性數據集（Dolly / Alpaca）
        ↓
Self-Inf-N 篩選
        ↓
Top-N benign outliers（N = 50 / 100 / 200）
        ↓
Fine-tune twinkle-ai/gemma-3-4B-T1-it
        ↓
安全性評估（HEx-PHI）+ 實用性評估（MT-bench）
```

**基礎訓練設定（參考論文預設值）：**
- Outlier 數量：100 筆
- 訓練 epochs：5
- Batch size：20
- Learning rate：$2 \times 10^{-5}$
- 微調方式：Full-parameter fine-tuning / LoRA（比較兩者差異）

### 評估指標

| 指標 | 說明 | 工具 |
|------|------|------|
| **Harmfulness Score (HS)** | 1–5 分，5 最危險 | HEx-PHI (330 prompts, 11 categories) + GPT-4o judge |
| **Attack Success Rate (ASR)** | 有害回應比例 | HEx-PHI |
| **Utility Score** | 一般對話與任務能力 | MT-bench |
| **Safety Degradation Rate** | 攻擊前後 HS 變化量 | — |

---

## 實驗二：連續學習場景下的持久性

### 研究動機

真實部署場景中，模型往往需要持續接受新任務的微調（Continual Learning / Sequential Fine-tuning）。本實驗探討：
- Benign outlier 造成的安全降解，在後續的正常微調後能否自然恢復？
- 數據中毒（Data Poisoning）情境下，低比例 outlier（1%）的長期影響？

### 實驗設計

**Scenario A — 連續學習持久性**
```
Phase 1: Benign outlier fine-tuning（100 outliers）
       ↓ 測量 HS₁
Phase 2: 正常良性數據再次微調（1000 samples, no outliers）
       ↓ 測量 HS₂
觀察：HS₂ 是否恢復至基線？
```

**Scenario B — 數據中毒**
```
混合數據集 = 1% outliers + 99% 隨機良性樣本
       ↓
Fine-tune twinkle-ai/gemma-3-4B-T1-it
       ↓ 測量 HS
比較：純良性數據微調 vs. 1% 污染數據微調
```

**Scenario C — 跨任務遷移**
```
Task 1 fine-tuning（含 outliers）→ 測量 HS
Task 2 fine-tuning（無 outliers）→ 測量 HS
Task 3 fine-tuning（無 outliers）→ 測量 HS
觀察安全降解是否持續累積
```

---

## 實驗三：防禦方法評估

### 防禦方法 A：SafeGrad

**原理：**
SafeGrad 識別與安全對齊高度相關的「安全關鍵梯度（safety-critical gradients）」，在微調過程中約束這些梯度的更新幅度，防止安全相關參數被有害更新覆蓋。

**核心機制：**
1. 在安全對齊數據上前向傳播，計算安全相關參數的梯度分佈
2. 識別對安全行為貢獻最大的參數子集（safety-critical parameters）
3. 微調時對這些參數施加梯度懲罰或投影約束：

$$\theta_{t+1} = \theta_t - \alpha \cdot \text{Proj}_{\perp S}(\nabla_\theta \mathcal{L}_\text{finetune})$$

其中 $S$ 為安全梯度空間，投影確保微調梯度不破壞安全方向。

**評估問題：** SafeGrad 是否能在保留 utility 的同時，有效阻止 benign outlier 對安全參數的污染？

### 防禦方法 B：AsFT（Alignment-Preserving Fine-Tuning）

**原理：**
AsFT 在微調 loss 中加入對齊保留正則化項，強制模型在學習新任務的同時維持安全輸出分佈：

$$\mathcal{L}_\text{AsFT} = \mathcal{L}_\text{finetune} + \lambda \cdot \mathcal{L}_\text{alignment}$$

其中 $\mathcal{L}_\text{alignment}$ 衡量微調模型與原始對齊模型在安全相關 token 上的 KL 散度或輸出差異。

**超參數搜尋：** $\lambda \in \{0.01, 0.1, 0.5, 1.0\}$，在 harmfulness 與 utility 間尋找 Pareto-optimal 點。

### 防禦比較矩陣

| 防禦方法 | 攻擊場景 | HS（攻擊後） | Utility | 推論開銷 |
|----------|----------|-------------|---------|---------|
| 無防禦（Baseline） | Benign Outlier | TBD | TBD | — |
| Data Augmentation（加入安全樣本） | Benign Outlier | TBD | TBD | 低 |
| Lisa | Benign Outlier | TBD | TBD | 中 |
| **SafeGrad** | Benign Outlier | TBD | TBD | 中 |
| **AsFT** | Benign Outlier | TBD | TBD | 低 |
| SafeGrad + AsFT（組合） | Benign Outlier | TBD | TBD | 中 |

---

## 研究假說

**H1**：`twinkle-ai/gemma-3-4B-T1-it` 雖已進行安全對齊，但面對 Self-Inf-N 篩選的 100 筆 benign outliers 微調後，Harmfulness Score 將顯著上升（$\Delta$HS > 1.5）。

**H2**：Benign outlier 造成的安全降解在連續學習場景中具有持久性，後續正常微調無法完全恢復安全性。

**H3**：SafeGrad 透過保護安全關鍵梯度，能比 AsFT 更有效地抵抗 benign outlier 攻擊，但代價是略微降低 utility。

**H4**：SafeGrad 與 AsFT 組合使用，可達到最佳的 safety-utility trade-off。

---

## 研究時程規劃

| 階段 | 工作項目 | 預計時程 |
|------|----------|---------|
| Phase 1 | 環境建置、模型載入、HEx-PHI 基準測試 | Week 1 |
| Phase 2 | Self-Inf-N 實作與 Benign Outlier 篩選 | Week 1–2 |
| Phase 3 | 實驗一：基礎脆弱性分析 | Week 2–3 |
| Phase 4 | 實驗二：連續學習場景實驗 | Week 3–4 |
| Phase 5 | 實驗三：SafeGrad、AsFT 防禦評估 | Week 4–5 |
| Phase 6 | 結果分析、論文撰寫 | Week 6 |

---

## 技術棧

```yaml
模型:
  - twinkle-ai/gemma-3-4B-T1-it (HuggingFace)
  - 比較基準: Llama-2-7B-Chat, Gemma-3-4B-it (原版)

微調框架:
  - HuggingFace Transformers + PEFT (LoRA)
  - PyTorch

評估:
  - HEx-PHI benchmark (安全性)
  - MT-bench (實用性)
  - GPT-4o as judge

良性數據集:
  - Dolly (databricks/databricks-dolly-15k)
  - Alpaca (tatsu-lab/alpaca)

防禦實作:
  - SafeGrad (自行實作 / 參考原始論文)
  - AsFT (自行實作 / 參考原始論文)
```

---

## 預期貢獻

1. **首次**系統性評估 `twinkle-ai/gemma-3-4B-T1-it` 對 benign outlier 攻擊的脆弱性
2. **驗證**連續學習場景下 benign outlier 安全降解的持久性與不可逆性
3. **評估** SafeGrad 與 AsFT 在對抗 anchor-free benign outlier 攻擊上的實際效果
4. 提供針對 Gemma 3 架構的**防禦建議**，供後續安全對齊研究參考

---

## 參考文獻

- **Benign Samples Matter!** — Benign outlier 識別與安全對齊破壞研究（Self-Inf-N 方法）
- **SafeGrad** — Safety-critical gradient protection for LLM fine-tuning
- **AsFT** — Alignment-Preserving Fine-Tuning via regularization
- **Lisa** — Dual-state fine-tuning defense（本研究中作為 baseline 比較）
- **HEx-PHI** — Benchmark for evaluating LLM harmfulness (11 categories, 330 prompts)
- `twinkle-ai/gemma-3-4B-T1-it` — [HuggingFace Model Card](https://huggingface.co/twinkle-ai/gemma-3-4B-T1-it)
