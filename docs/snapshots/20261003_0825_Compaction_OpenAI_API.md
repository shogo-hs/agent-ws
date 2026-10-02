---
title: "Compaction | OpenAI API"
kind: web
source: "https://developers.openai.com/api/docs/guides/compaction"
via: jina
retrieved_at: 2026-10-03T08:25:29+09:00
retrieved_by: unknown
summary: "Responses API の compaction（サーバー側と /responses/compact）"
---
# Compaction | OpenAI API

## 引用した記述（原文のまま。要約しない）
- The returned compaction item carries forward key prior state and reasoning into the next run using fewer tokens.

## このタスクでの使いどころ（使わなかったなら理由）
API 側の仕組み。Codex CLI は内部で compaction を行い、agent-ws から触れるのは model_auto_compact_token_limit だけ。

## 原文（改変しない）
原文: [20261003_0825_Compaction_OpenAI_API.orig.md](20261003_0825_Compaction_OpenAI_API.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
