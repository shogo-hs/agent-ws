---
title: "Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory"
kind: web
source: "https://arxiv.org/html/2504.19413"
via: jina
retrieved_at: 2026-09-09T00:40:41+09:00
retrieved_by: unknown
summary: "Mem0: 本番向けの長期メモリ。full-context 比でレイテンシ・トークンを削減と主張"
---
# Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory

## 引用した記述（原文のまま。要約しない）
- (Abstract) "Through comprehensive evaluations on the LOCOMO benchmark, we systematically compare our approaches against six baseline categories" / "Mem0 achieves 26% relative improvements in the LLM-as-a-Judge metric over OpenAI" / "Mem0 attains a 91% lower p95 latency and saves more than 90% token cost"
- (§3.1) "The LOCOMO dataset ... comprises 10 extended conversations, each containing approximately 600 dialogues and 26000 tokens on average, distributed across multiple sessions."
- (§2.2) "In our experimental evaluation, we configured the system with 'm' = 10 previous messages for contextual reference and 's' = 10 similar memories for comparative analysis. All language model operations utilized GPT-4o-mini as the inference engine."
- (Table 2) Full-context: memory tokens 26031, total p50 9.870s / p95 17.117s, Overall J 72.90% ／ Mem0: 1764 tokens, search p50 0.148s / p95 0.200s, total p50 0.708s / p95 1.440s, J 66.88% ／ Mem0^g: 3616 tokens, total p95 2.590s, J 68.44%
- (§4.3) "a full-context method that ingests a chunk of roughly 26,000 tokens still achieves the highest J score (approximately 73%). However ... it also incurs a very high total p95 latency—around 17 seconds ... Mem0 and Mem0^g significantly reduce token usage and thus achieve lower p95 latencies of around 1.44 seconds (a 92% reduction) and 2.6 seconds (a 85% reduction), respectively over full-context approach."
- (§4.5) "Mem0 encodes complete dialogue turns in a natural language representation and therefore occupies only 7k tokens per conversation on an average." / "Zep's memory graph consumes in excess of 600k tokens."

## このタスクでの使いどころ（使わなかったなら理由）
「メモリを圧縮すると何を失って何を得るか」の実測値として使う: 全文脈 J 72.90 に対し Mem0 66.88（-6 pt）で p95 17.1s→1.44s、プロンプトに載せるトークン 26k→1.8k。会話メモリ（事実の記憶）の話であって、ルール/規約の学習ではない点と、評価が GPT-4o-mini の LLM-as-a-Judge である点は前提として押さえる。

## 原文（改変しない）
原文: [20260909_0040_Mem0_Building_Production-Ready_AI_Agents.orig.md](20260909_0040_Mem0_Building_Production-Ready_AI_Agents.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
