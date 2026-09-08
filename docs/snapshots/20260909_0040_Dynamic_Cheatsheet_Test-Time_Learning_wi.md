---
title: "Dynamic Cheatsheet: Test-Time Learning with Adaptive Memory"
kind: web
source: "https://arxiv.org/html/2504.07952"
via: direct
retrieved_at: 2026-09-09T00:40:32+09:00
retrieved_by: unknown
summary: "Dynamic Cheatsheet: 推論時に再利用可能な戦略・コード片を蓄積する外部メモリ"
---
# Dynamic Cheatsheet: Test-Time Learning with Adaptive Memory

## 引用した記述（原文のまま。要約しない）
- (Abstract/§1) "Dynamic Cheatsheet (DC), a lightweight framework that endows a black-box LM with a persistent, evolving memory." / "On AIME 2024, Claude 3.5 Sonnet jumped from 23% to 50% accuracy, more than doubling its baseline score" / "GPT-4o's baseline performance (10%) increased to 99% under DC" (Game of 24)
- (§1) "Under DC, memory is carefully curated, focusing on succinct, useful, and transferable knowledge over raw transcripts. This prevents ballooning context lengths (Liu et al., 2024a) and helps ensure that repeated retrieval remains tractable."
- (§2.1.2) "Cur does not have access to ground-truth labels; so, it has to assess the correctness and efficiency of the solutions by itself before updating the memory. In our experiments, we instruct a single model to perform this crucial step."
- (§2.1.2) "(ii) refinement or removal of existing memory entries (i.e., if an existing memory entry was incorrect or superseded by a more efficient or versatile strategy, Cur may remove or update it), and (iii) clarity and compactness of the entire memory"
- (§4.3, AIME 2024, n=30) "Sonnet under FH reached 26.7% accuracy in 2024 questions, while DC-based methods hit 50.0%. Similarly, GPT-4o managed a baseline of 20.0% but fell to 6.7% using FH, in direct contrast to 40.0% with DC-RS. Excessive uncurated input-output pairs can not only overwhelm the model's context window, dilute crucial insights and hamper retrieval efficiency, but also significantly increase inference costs over time."
- (§5 (a) Generative competence) "For DC to be effective, the base model must produce correct solutions with sufficient frequency to populate the memory with high-quality, reusable strategies. Smaller models, such as GPT-4o-mini and Claude 3.5 Haiku, generate correct solutions less reliably, leading to a sparse or low-quality memory repository. As a result, iterative refinement stalls because the stored knowledge consists mostly of incorrect or partial attempts."

## このタスクでの使いどころ（使わなかったなら理由）
正解ラベル無しで「モデル自身が正しさを判断してメモリを更新する」設計の代表例で、個人環境の前提に一番近い。効果は「同型の問題が続く」ベンチ（Game of 24 でコード片を再利用）で最大。生履歴の追記（FH）は 20.0→6.7 に落ちる一方、ACE 側でこの手法の全文書き直しが context collapse を起こす事例として名指しされている。弱いモデルでは誤答が溜まって停滞する、と自ら書いている。

## 原文（改変しない）
原文: [20260909_0040_Dynamic_Cheatsheet_Test-Time_Learning_wi.orig.md](20260909_0040_Dynamic_Cheatsheet_Test-Time_Learning_wi.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
