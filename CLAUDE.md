# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 儲存庫現況

本儲存庫目前處於**研究提案階段**。截至最新 commit，僅包含一份繁體中文的研究提案 `research_benign_outliers_twinkle.md`，**尚無任何原始碼、建置系統、測試套件或依賴管理檔案**。實作工作尚未開始，README 的角色由該提案本身扮演。

當使用者詢問建置 / lint / 測試指令而這些指令尚不存在時，**請直接告知尚未建立**，不要憑空捏造。等到實作正式啟動後，再回頭把真正的工具鏈更新到本檔案中。

## 研究主題

本提案研究 **benign outlier 攻擊**（出自 *Benign Samples Matter*, 2024）能否破壞 [`twinkle-ai/gemma-3-4B-T1-it`](https://huggingface.co/twinkle-ai/gemma-3-4B-T1-it) 的安全對齊。該模型以 Gemma-3-4B 指令微調版為基底，由 Twinkle AI 額外進行安全對齊。攻擊威脅模型為 **anchor-free**：少量表面無害、但梯度方向有害的樣本（取自常見指令資料集 Dolly、Alpaca），即足以摧毀模型的安全防線。

規劃三條實驗主軸：

1. **脆弱性（Vulnerability）** — 以 Self-Inf-N 篩出 Top-N（50/100/200）outliers 微調目標模型；以 HEx-PHI + GPT-4o judge 量測 HS / ASR，以 MT-bench 量測 utility。
2. **連續學習持久性（Continual-Learning Persistence）** — 測試 (a) 後續正常微調是否能恢復安全性，(b) 1% outlier 摻入 99% 良性資料是否仍能毒化，(c) 多輪任務微調下的累積傷害。
3. **防禦評估（Defenses）** — 評估 **SafeGrad**（在梯度空間保護 safety-critical 參數）與 **AsFT**（保留對齊的 KL 正則化，λ ∈ {0.01, 0.1, 0.5, 1.0}），分別與組合使用兩種設定下的防禦效果。

## 方法層面的關鍵細節（容易記錯的點）

以下是提案中容易在憑記憶實作時出錯的細節：

- **必須使用 Self-Inf-N，不要使用原始 Self-Inf。** 原始 self-influence score `∇L(z)ᵀ H⁻¹ ∇L(z)` 會嚴重偏向挑選極短回答的樣本，導致挑出的 outliers 攻擊力弱、輸出過短。修正後分數為：

  ```
  Self-Inf-N(z) = log(Self-Inf(z) + 1) + log(len(answer) + 1)
  ```

  實作篩選器時務必加上長度項，否則挑出的 outliers 無法重現論文記載的攻擊強度。

- **使用一階梯度近似（first-order approximation）** 處理 Hessian-vector 項，不要嘗試計算精確的 `H⁻¹`。

- **提案中的預設攻擊超參數**：100 筆 outliers、5 epochs、batch size 20、LR 2e-5。**全參數微調（full-parameter）與 LoRA 兩種方式都在實驗一的範圍內**，兩者比較本身就是研究內容的一部分。

- **假說 H1** 將攻擊成功門檻訂為 HEx-PHI（1–5 分制、330 prompts、11 類別）上 ΔHS > 1.5。**未經使用者確認，不要更動此門檻。**

## 規劃中的技術棧（依提案，尚未安裝）

- HuggingFace `transformers` + `peft`（用於 LoRA）、PyTorch。
- 評估：HEx-PHI benchmark、MT-bench、以 GPT-4o 作為 judge。
- 良性資料集：`databricks/databricks-dolly-15k`、`tatsu-lab/alpaca`。
- 比較基準：`Llama-2-7B-Chat`、原版（未經 Twinkle 對齊）`Gemma-3-4B-it`。

## 工作語言

提案以及未來預期新增的研究文件皆使用**繁體中文**；編輯或擴充研究文件時請維持繁體中文。原始碼、識別字（變數 / 函式名稱）、commit message 仍以英文撰寫。
