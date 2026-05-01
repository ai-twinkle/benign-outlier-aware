---
language:
  - zh-Hant
license: cc-by-sa-3.0
task_categories:
  - text-generation
  - question-answering
size_categories:
  - 10K<n<100K
source_datasets:
  - allenlin316/databricks-dolly-15k-no-safety
tags:
  - traditional-chinese
  - taiwan
  - instruction-tuning
  - benign-outliers
---

# tw-databricks-dolly-15k-no-safety

`allenlin316/databricks-dolly-15k-no-safety` 的臺灣繁體中文翻譯版本，用於本研究 [`research_benign_outliers_twinkle.md`](../../research_benign_outliers_twinkle.md) 中的良性微調資料來源。

## 資料來源

- **上游資料集**：[`allenlin316/databricks-dolly-15k-no-safety`](https://huggingface.co/datasets/allenlin316/databricks-dolly-15k-no-safety)
- **原始資料集**：[`databricks/databricks-dolly-15k`](https://huggingface.co/datasets/databricks/databricks-dolly-15k)
- **筆數**：14,624

## 翻譯方法

| 項目 | 設定 |
|------|------|
| 翻譯模型 | `Qwen3.6-27B`（透過 `https://qwen.pangolin.apmic.ai/v1/chat/completions`） |
| 推理模式 | `chat_template_kwargs.enable_thinking=False`（關閉 thinking） |
| 翻譯欄位 | `instruction`、`context`、`response` |
| 保留欄位 | `category`（不翻譯） |
| 採樣參數 | `temperature=0.2`, `max_tokens=4096` |
| 並行度 | 16 |

### 簡體字過濾

對每筆翻譯結果進行字元級偵測，只要任一欄位包含簡體專用字元，即以強化提示重新翻譯，最多重試 3 次。3 次後仍含簡體字的樣本會在輸出加上 `needs_review: true` 標記，方便後續人工檢查。

> 本資料集**不使用 OpenCC** 等簡轉繁轉換工具，避免機械式詞彙替換造成的臺灣用詞偏移。

## 資料欄位

| 欄位 | 型別 | 說明 |
|------|------|------|
| `id` | `int` | 對應上游資料集的 row index（0-based） |
| `instruction` | `string` | 指令（已翻譯） |
| `context` | `string` | 背景資訊，可能為空字串（已翻譯） |
| `response` | `string` | 回答（已翻譯） |
| `category` | `string` | 任務類別（未翻譯，保留英文） |
| `needs_review` | `bool` | 是否在 3 次重譯後仍有簡體字殘留 |

## 載入方式

```python
from datasets import load_dataset

ds = load_dataset(
    "json",
    data_files="datasets/tw-databricks-dolly-15k-no-safety/datasets.jsonl",
    split="train",
)
```

## 已知限制

1. **專有名詞處理**：罕見專有名詞可能採用音譯而非標準譯名（例如鯊魚種類 *Tope* 可能被音譯為「托佩」而非「皺唇鯊」）。
2. **格式保留**：原文中的 Markdown、列表、URL、程式碼會被保留，但段落結構在極長內容下可能略有調整。
3. **`needs_review=True` 的處理**：研究使用前建議過濾或人工複檢這些樣本。

## 授權

延續上游 `databricks/databricks-dolly-15k` 的 [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) 授權。
