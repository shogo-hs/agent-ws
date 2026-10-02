---
title: "Reasoning models | OpenAI API"
kind: web
source: "https://developers.openai.com/api/docs/guides/reasoning"
via: jina
retrieved_at: 2026-10-03T08:26:19+09:00
retrieved_by: unknown
summary: "Reasoning models（再取得。reasoning.context・configuration_update）"
---
# Reasoning models | OpenAI API

## 引用した記述（原文のまま。要約しない）
- GPT-5.6 models instead default to rendering available reasoning from earlier turns.
- they still occupy space in the model’s context window and are billed as [output tokens]

## このタスクでの使いどころ（使わなかったなら理由）
GPT-5.6 は過去ターンの reasoning を文脈に残す（Claude の keep-all と同じ形）。effort を下げると再送分も減る根拠。Codex の config に reasoning.context のキーは無い。

## 原文（改変しない）
原文: [20261003_0826_Reasoning_models_OpenAI_API.orig.md](20261003_0826_Reasoning_models_OpenAI_API.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
