---
title: "The Ultra Mode Trade-Off: When Bigger Reasoning Budgets Backfire in Codex CLI"
kind: web
source: "https://codex.danielvaughan.com/2026/07/24/codex-cli-ultra-mode-trade-off-reasoning-budgets-subagent-cost-task-routing/"
via: jina
retrieved_at: 2026-09-14T10:22:09+09:00
retrieved_by: unknown
summary: "第三者: 推論量を上げるとサブエージェントで逆効果になるという報告"
---
# The Ultra Mode Trade-Off: When Bigger Reasoning Budgets Backfire in Codex CLI

## 引用した記述（原文のまま。要約しない）
- "This contrasts with `max` reasoning effort, which simply extends single-agent chain-of-thought without spawning anything."
- "The `max` reasoning effort is available to all Sol users and frequently produces results comparable to Ultra for tightly coupled problems — without the sub-agent overhead."
- "Variable renames, import additions, test scaffolds with clear patterns — these do not benefit from deeper reasoning at any level."

## このタスクでの使いどころ（使わなかったなら理由）
第三者の整理（帰属）。max は 1 エージェントの思考を長くするだけで、型の決まった仕事には効かないという見立て。agent-ws の実測はこれと逆で、通読して抜く仕事では max だけが落とさなかった（判断には実測を使った）。記事中の相対コスト（low 1.5x・max 8x 等）は著者の見積で、agent-ws の判断には使っていない。一次情報は Models ページと Subagents ページ。

## 原文（改変しない）
原文: [20260914_1022_The_Ultra_Mode_Trade-Off_When_Bigger_Rea.orig.md](20260914_1022_The_Ultra_Mode_Trade-Off_When_Bigger_Rea.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
