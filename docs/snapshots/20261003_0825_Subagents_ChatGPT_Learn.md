---
title: "Subagents | ChatGPT Learn"
kind: web
source: "https://developers.openai.com/codex/subagents"
via: jina
retrieved_at: 2026-10-03T08:25:30+09:00
retrieved_by: unknown
summary: "Codex のサブエージェントの文脈と費用"
---
# Subagents | ChatGPT Learn

## 引用した記述（原文のまま。要約しない）
- Because each subagent does its own model and tool work, subagent workflows consume more tokens than comparable single-agent runs.
- If you don’t configure a subagent model or `model_reasoning_effort`, the subagent inherits the parent agent’s model and reasoning effort.

## このタスクでの使いどころ（使わなかったなら理由）
委譲の 4 条件と [agents] の既定（ADR 0020）で既に対応済み。fork_turns の記述はこのページに無い。

## 原文（改変しない）
原文: [20261003_0825_Subagents_ChatGPT_Learn.orig.md](20261003_0825_Subagents_ChatGPT_Learn.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
