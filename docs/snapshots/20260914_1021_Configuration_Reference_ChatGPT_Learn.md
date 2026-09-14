---
title: "Configuration Reference | ChatGPT Learn"
kind: web
source: "https://learn.chatgpt.com/docs/config-file/config-reference"
via: jina
retrieved_at: 2026-09-14T10:21:59+09:00
retrieved_by: unknown
summary: "Codex の設定リファレンス（撮り直し。model_reasoning_effort の値）"
---
# Configuration Reference | ChatGPT Learn

## 引用した記述（原文のまま。要約しない）
- "model_reasoning_effort	minimal | low | medium | high | xhigh / Adjust reasoning effort for supported models (Responses API only; xhigh is model-dependent)."
- "agents.default_subagent_model	string / Default model for spawned agents. An explicit spawn model takes precedence."
- "agents.default_subagent_reasoning_effort	string / Default reasoning effort for spawned agents. An explicit spawn effort takes precedence."

## このタスクでの使いどころ（使わなかったなら理由）
設定キーの名前と優先順位（明示の spawn 指定 > `[agents]` の既定）。リファレンスの一覧は xhigh までで max が無いが、0.153.4 の `-c model_reasoning_effort="max"` は luna で受理された（自分の実測）。文書のほうが遅れている。

## 原文（改変しない）
原文: [20260914_1021_Configuration_Reference_ChatGPT_Learn.orig.md](20260914_1021_Configuration_Reference_ChatGPT_Learn.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
