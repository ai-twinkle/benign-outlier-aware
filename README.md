# benign-outlier-aware

研究 **Benign Outliers** 對 [Twinkle AI](https://huggingface.co/twinkle-ai) 開源模型 [`twinkle-ai/gemma-3-4B-T1-it`](https://huggingface.co/twinkle-ai/gemma-3-4B-T1-it) 安全對齊的影響，並評估現有梯度約束類防禦方法（SafeGrad、AsFT）的有效性。

> **Benign Outliers**：來自良性微調資料集（如 Dolly、Alpaca）中表面無害、但梯度方向有害的少量樣本。論文 *Benign Samples Matter!* 指出，僅需 100 筆此類樣本即可使已對齊模型的安全防線崩潰，且不依賴外部惡意資料作為錨點（anchor-free）。

完整研究背景、方法論與實驗設計請參閱 [`research_benign_outliers_twinkle.md`](research_benign_outliers_twinkle.md)。

---

## 研究問題

1. **脆弱性** — `twinkle-ai/gemma-3-4B-T1-it` 對 benign outlier 攻擊是否同樣脆弱？
2. **識別性** — 能否以 Self-Inf-N 從良性資料集萃取針對此模型的 benign outliers？
3. **持久性** — 在連續學習場景下，benign outlier 造成的安全降解是否難以被後續微調消除？
4. **防禦性** — SafeGrad 與 AsFT 等梯度約束類防禦方法，能否有效抵擋此類攻擊？

---

## 儲存庫內容

```
benign-outlier-aware/
├── research_benign_outliers_twinkle.md   # 研究提案（中文，主文件）
├── CLAUDE.md                             # Claude Code 工作指引
├── datasets/
│   ├── tw-databricks-dolly-15k-no-safety/  # Dolly 繁中翻譯版（本研究產出）
│   └── GSM8K_zh_tw/                        # GSM8K 繁中版（DoggiAI 提供）
└── scripts/
    └── translate_dolly.py                # Dolly 翻譯腳本（Qwen3.6-27B）
```

---

## 資料集

### `datasets/tw-databricks-dolly-15k-no-safety/`

`allenlin316/databricks-dolly-15k-no-safety` 的臺灣繁體中文翻譯版本，做為本研究之**良性微調資料來源**。

| 項目 | 數值 |
|------|------|
| 筆數 | 14,624 |
| 欄位 | `id`, `instruction`, `context`, `response`, `category`, `needs_review` |
| 翻譯模型 | `Qwen3.6-27B`（自架，no-think 模式） |
| 標記人工檢查 (`needs_review=true`) | 382 筆（2.6%） |

詳見資料卡 [`datasets/tw-databricks-dolly-15k-no-safety/README.md`](datasets/tw-databricks-dolly-15k-no-safety/README.md)。

### `datasets/GSM8K_zh_tw/`

[`DoggiAI/GSM8K_zh_tw`](https://huggingface.co/datasets/DoggiAI/GSM8K_zh_tw) 完整快照，做為本研究**實用性（utility）評估**的數理推理基準之一。

| 切分 | 筆數 |
|------|------|
| train | 7,471 |
| test | 1,319 |
| exception | 2 |

---

## 重現 Dolly 翻譯流程

> 此流程依賴自架的 Qwen API endpoint，外部使用者需替換為自己的 endpoint 後才能完整重現。

```bash
# 1. 建立虛擬環境
python3 -m venv .venv
source .venv/bin/activate

# 2. 安裝相依
pip install datasets dragonmapper tqdm httpx

# 3. （選用）小規模試跑驗證
python scripts/translate_dolly.py --limit 20 --concurrency 8

# 4. 全量翻譯（支援斷點續跑）
python scripts/translate_dolly.py --concurrency 16
```

輸出會持續寫入 `datasets/tw-databricks-dolly-15k-no-safety/datasets.jsonl`，重跑時會自動跳過已完成的 `id`。

**參數摘要：**

| 旗標 | 預設 | 說明 |
|------|------|------|
| `--limit` | 全量 | 只翻前 N 筆（試跑用） |
| `--concurrency` | 16 | 並行請求數 |
| `--max-retries` | 3 | 偵測到簡體字時的重譯次數，超過後標 `needs_review` |

---

## 路線圖

對應研究提案中 Phase 1–6：

- [x] **Phase 0** — 良性資料集準備（Dolly 繁中、GSM8K 繁中）
- [ ] **Phase 1** — 環境建置、模型載入、HEx-PHI 基準測試
- [ ] **Phase 2** — Self-Inf-N 實作與 benign outlier 篩選
- [ ] **Phase 3** — 實驗一：基礎脆弱性分析
- [ ] **Phase 4** — 實驗二：連續學習場景實驗
- [ ] **Phase 5** — 實驗三：SafeGrad、AsFT 防禦評估
- [ ] **Phase 6** — 結果分析與論文撰寫

---

## 引用與參考

- *Benign Samples Matter!* — Benign outlier 識別與安全對齊破壞研究（Self-Inf-N 方法）
- *SafeGrad* — Safety-critical gradient protection for LLM fine-tuning
- *AsFT* — Alignment-Preserving Fine-Tuning via regularization
- *HEx-PHI* — Benchmark for evaluating LLM harmfulness（11 categories, 330 prompts）
- [`twinkle-ai/gemma-3-4B-T1-it`](https://huggingface.co/twinkle-ai/gemma-3-4B-T1-it) — 目標研究模型

---

## 維護者與貢獻者

- **Liang-Hsun Huang** ([@lianghsun](https://github.com/lianghsun)) — 主持人、研究設計、資料集翻譯流程實作
- **allenlin316** ([@allenlin316](https://github.com/allenlin316)) — 研究方向提案、上游資料集 `databricks-dolly-15k-no-safety` 提供者

歡迎開 Issue 或 PR 討論研究方法、提交實驗結果或回報資料集問題。

---

## 授權

研究文件、程式碼以本儲存庫之 LICENSE 為準。資料集授權延續各自上游：

- `tw-databricks-dolly-15k-no-safety` — CC BY-SA 3.0（延續 `databricks-dolly-15k`）
- `GSM8K_zh_tw` — MIT（延續 `DoggiAI/GSM8K_zh_tw`）
