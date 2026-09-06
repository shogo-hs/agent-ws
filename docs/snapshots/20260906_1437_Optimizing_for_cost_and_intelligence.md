---
title: "Optimizing for cost and intelligence"
kind: web
source: "https://platform.claude.com/docs/en/about-claude/models/optimizing-for-cost-and-intelligence"
via: jina
retrieved_at: 2026-09-06T14:37:38+09:00
retrieved_by: unknown
summary: "コストと知性の最適化ガイド。オーケストレータが大量の定型作業を安いモデルに渡す設計指針"
---
# Optimizing for cost and intelligence

## 引用した記述（原文のまま。要約しない）
- "An orchestrator buys something only when there is bulk to hand off: many independent pieces, ideally too many for one context window."
- "Delegation paid on the routine, normally solvable share of the work, the opposite of the intuition that workers are for hard problems."

## このタスクでの使いどころ（使わなかったなら理由）
AGENTS.md「安いモデルの調査係に渡す仕事」の条件②（読む量が多く返すものが短い＝独立した大量の断片がある）の根拠。委譲が効くのは定型・分割可能な作業であり、難しい判断は本線に残す、という線引きの出所。

## 原文（改変しない）
原文: [20260906_1437_Optimizing_for_cost_and_intelligence.orig.md](20260906_1437_Optimizing_for_cost_and_intelligence.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）

