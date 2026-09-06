---
title: "The Subagent Tax. Claude Code Fan-Outs Cost Up to 5.9x the Tokens, and Were Never Faster"
kind: web
source: "https://systima.ai/blog/subagent-tax"
via: jina
retrieved_at: 2026-09-06T17:42:28+09:00
retrieved_by: unknown
summary: "Claude Code のサブエージェント fan-out がトークン 5.9 倍になった実測（第三者ブログ）"
---
# The Subagent Tax. Claude Code Fan-Outs Cost Up to 5.9x the Tokens, and Were Never Faster

## 引用した記述（原文のまま。要約しない）
- Claude Code's subagents used 2.6x to 5.9x as many input tokens as doing the same work sequentially, measured across three model families. They were not faster on any task we timed. And in one matched pair, cache misses pushed the price-weighted cost to roughly five times the sequential run.

## このタスクでの使いどころ（使わなかったなら理由）
第三者（Systima）の実測。調査係への委譲を「読む量が多く返すものが短い仕事」に限る既存の 4 条件の補強。bench v3 でも委譲ありは処理した入力が 3% 多かった（254k 対 246k）。

## 原文（改変しない）
原文: [20260906_1742_The_Subagent_Tax._Claude_Code_Fan-Outs_C.orig.md](20260906_1742_The_Subagent_Tax._Claude_Code_Fan-Outs_C.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
