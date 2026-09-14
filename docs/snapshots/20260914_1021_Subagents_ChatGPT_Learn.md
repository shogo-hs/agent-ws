---
title: "Subagents | ChatGPT Learn"
kind: web
source: "https://learn.chatgpt.com/docs/agent-configuration/subagents"
via: jina
retrieved_at: 2026-09-14T10:21:42+09:00
retrieved_by: unknown
summary: "Codex のサブエージェント（撮り直し。推論量の選び方と既定の解決順）"
---
# Subagents | ChatGPT Learn

## 引用した記述（原文のまま。要約しない）
- "If an explicit spawn request or an `[agents]` default selects a model without an explicit or configured reasoning effort, the subagent uses that model's default reasoning effort."
- "**`gpt-5.6-terra`**: Use for agents that favor speed and efficiency over depth, such as exploration, read-heavy scans, large-file review, or processing supporting documents. It works well for parallel workers that return distilled results to the main agent."
- "**`gpt-5.6-luna`**: Use for fast, narrowly scoped agents handling clear, repeatable, or high-volume work."
- "**`low`**: Use when the task is straightforward and speed matters most."
- "**`max`** and **`xhigh`**: Use for especially demanding reasoning when the selected model supports these levels."
- "Higher reasoning effort increases response time and token usage, but it can improve quality for complex work."

## このタスクでの使いどころ（使わなかったなら理由）
`[agents]` の既定に reasoning effort を明示する根拠（省くと luna の既定 medium になる）。terra が「読む量の多い調査」の推奨、luna が「型の決まった高頻度の仕事」の推奨で、両者を bench で比べた動機。max/xhigh は「特に重い推論」向けという一般論だが、通読して抜く仕事では low が読み切らず、max だけが決定を落とさなかった（ADR 0020）。

## 原文（改変しない）
原文: [20260914_1021_Subagents_ChatGPT_Learn.orig.md](20260914_1021_Subagents_ChatGPT_Learn.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
