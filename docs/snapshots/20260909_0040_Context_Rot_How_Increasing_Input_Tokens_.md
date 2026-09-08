---
title: "Context Rot: How Increasing Input Tokens Impacts LLM Performance"
kind: web
source: "https://research.trychroma.com/context-rot"
via: jina
retrieved_at: 2026-09-09T00:40:44+09:00
retrieved_by: unknown
summary: "Context Rot: 入力トークンが増えるほど性能が劣化する（18モデル実測）"
---
# Context Rot: How Increasing Input Tokens Impacts LLM Performance

## 引用した記述（原文のまま。要約しない）
- "We demonstrate that even under these minimal conditions, model performance degrades as input length increases, often in surprising and non-uniform ways. Real-world applications typically involve much greater complexity, implying that the influence of input length may be even more pronounced in practice."
- "An evaluation across 18 LLMs, including leading closed-source and open-weights models, revealing nonuniform performance with increasing input length."
- (NIAH Extension findings) "Across all experiments, model performance consistently degrades with increasing input length." / "Lower similarity needle-question pairs increases the rate of performance degradation." / "Distractors have non-uniform impact on model performance with regards to how distracting they are relative to each other. We see this impact more prominently as input length increases"
- "The observed performance degradation at longer input lengths is not due to the intrinsic difficulty of the needle-question pairing. By holding the needle-question pair fixed and varying only the amount of irrelevant content, we isolate input size as the primary factor in performance decline."
- (Haystack structure) "Across all 18 models and needle-haystack configurations, we observe a consistent pattern that models perform better on shuffled haystacks than on logically structured ones."
- (LongMemEval) "filtering out 38 prompts to end up with 306 total prompts. These prompts average out to ~113k tokens." / "Focused prompts average to ~300 tokens" / "Across all models, we see significantly higher performance on focused prompts compared to full prompts."
- (LongMemEval, Claude) "The Claude models exhibit the most pronounced gap between focused and full prompt performance. This discrepancy is largely driven by abstentions that arise with ambiguity, leading to model uncertainty ... This behavior is most evident in Claude Opus 4 and Sonnet 4, which appear to be particularly conservative under ambiguity"

## このタスクでの使いどころ（使わなかったなら理由）
「ルールが増える＝コンテキストが伸びる」の副作用の根拠。関係ない文脈（irrelevant content）と紛らわしい文脈（distractor）を区別し、後者の害は長さとともに増幅すると述べる。Claude 系は曖昧さで棄権しやすいと名指しされているので、Claude Code のハーネスに矛盾しかけたルールを溜めることの害はここから推せる。ただし NIAH/会話 QA の測定で、指示遵守そのものは測っていない。

## 原文（改変しない）
原文: [20260909_0040_Context_Rot_How_Increasing_Input_Tokens_.orig.md](20260909_0040_Context_Rot_How_Increasing_Input_Tokens_.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
