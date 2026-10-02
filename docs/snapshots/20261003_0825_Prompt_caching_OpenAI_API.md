---
title: "Prompt caching | OpenAI API"
kind: web
source: "https://developers.openai.com/api/docs/guides/prompt-caching"
via: jina
retrieved_at: 2026-10-03T08:25:30+09:00
retrieved_by: unknown
summary: "OpenAI プロンプトキャッシュの最新仕様（再取得）"
---
# Prompt caching | OpenAI API

## 引用した記述（原文のまま。要約しない）
- For GPT-5.6 and later, cache writes cost 1.25× the standard, uncached input-token rate.
- Use `prompt_cache_options.ttl` to control the minimum cache lifetime. The only supported value, `30m`, is also the default.
- That can change the prefix, so the first request after compaction may reuse less of the previous cache even when the conversation is logically the same.
- On GPT-6 models, append a `configuration_update` input item to change reasoning effort between responses while keeping request-level `reasoning.effort` unchanged.

## このタスクでの使いどころ（使わなかったなら理由）
TTL 30 分は 09-06 から不変（Codex の --ttl 30 はそのまま）。書き込み 1.25 倍は API 課金の話で、Codex のクレジット課金には無い（Pricing – Codex）。configuration_update は GPT-6 の API 向けで、Codex CLI が使うかは確認できない。

## 原文（改変しない）
原文: [20261003_0825_Prompt_caching_OpenAI_API.orig.md](20261003_0825_Prompt_caching_OpenAI_API.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
