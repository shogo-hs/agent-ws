---
title: "Prompt caching | OpenAI API"
kind: web
source: "https://developers.openai.com/api/docs/guides/prompt-caching"
via: jina
retrieved_at: 2026-09-06T15:51:19+09:00
retrieved_by: unknown
summary: "OpenAI のプロンプトキャッシュ。GPT-5.6 以降は prompt_cache_options.ttl=30m が既定かつ唯一値"
---
# Prompt caching | OpenAI API

## 引用した記述（原文のまま。要約しない）
- Use `prompt_cache_options.ttl` to control the minimum cache lifetime. The only supported value, `30m`, is also the default. A cached prefix remains eligible for reuse for 30 minutes after its most recent write or reuse, though OpenAI may retain it longer.

## このタスクでの使いどころ（使わなかったなら理由）
#4（Codex の hook に --ttl 30 を渡す）の根拠。30 分は最小寿命で、それより長く残ることもある。

## 原文（改変しない）
原文: [20260906_1551_Prompt_caching_OpenAI_API.orig.md](20260906_1551_Prompt_caching_OpenAI_API.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
