---
title: "How Many Instructions Can LLMs Follow at Once?"
kind: web
source: "https://arxiv.org/html/2507.11538"
via: jina
retrieved_at: 2026-09-09T00:40:48+09:00
retrieved_by: unknown
summary: "IFScale: 同時指示数が増えると遵守率がどう落ちるか（最大500指示）"
---
# How Many Instructions Can LLMs Follow at Once?

## 引用した記述（原文のまま。要約しない）
- (Abstract) "We introduce IFScale, a simple benchmark of 500 keyword-inclusion instructions for a business report writing task to measure how instruction-following performance degrades as instruction density increases. We evaluate 20 state-of-the-art models across seven major providers and find that even the best frontier models only achieve 68% accuracy at the max density of 500 instructions."
- (§3) "For each experiment, we evaluate a grid of instruction densities N∈{10,20,…,500} under five random seeds."
- (§4.4) "Threshold decay: Performance remains stable until a threshold, then transitions to a different (steeper) degradation slope and displays increased variance. The top two models (gemini-2.5-pro, o3) demonstrate this clearly, maintaining near-perfect performance through 150 or more instructions before declining."
- (§4.4) "Linear decay: ... gpt-4.1 and claude-3.7-sonnet exemplify this pattern" / "Exponential decay: ... Models like claude-3.5-haiku and llama-4-scout ... all exponential decay patterns appear to level off around similar accuracy floors (7-15%)"
- (§4.3) "claude-3.7-sonnet outperforms the newer claude-opus-4 and claude-sonnet-4 at max density (52.7% vs. 44.6% and 42.9% respectively)."
- (§4.6 Primacy) "they start low at minimal instruction densities indicating almost no bias for earlier instructions, peak around 150-200 instructions, then level off or decrease at extreme densities." / "while packing more important instructions towards the beginning of a prompt may help, it becomes a less effective strategy once extreme densities are reached."
- (§4.8) "Models overwhelmingly err toward omission errors as instruction density increases." / "At 500 instructions, llama-4-scout exhibits an extreme O:M ratio of 34.88"
- (§7 Limitations) "We focus exclusively on professional report generation with simple keyword-inclusion instructions, which may not generalize to other task types or domains, or more complex instruction types."

## このタスクでの使いどころ（使わなかったなら理由）
「ルールが増え続けると何が起きるか」を指示数の関数として測った唯一の出典。10 本刻みで 500 本まで、5 seed、20 モデル。劣化は「黙って落とす（omission）」形で出て、150〜200 本あたりで前方優先が最大になる。ただし指示は「この単語を含めよ」という単純制約で、CLAUDE.md のような手続き・禁止事項の遵守とは形が違う点を割り引く。

## 原文（改変しない）
原文: [20260909_0040_How_Many_Instructions_Can_LLMs_Follow_at.orig.md](20260909_0040_How_Many_Instructions_Can_LLMs_Follow_at.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
