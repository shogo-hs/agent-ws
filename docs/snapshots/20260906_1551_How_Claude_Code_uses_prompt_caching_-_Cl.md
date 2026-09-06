---
title: "How Claude Code uses prompt caching - Claude Code Docs"
kind: web
source: "https://code.claude.com/docs/en/prompt-caching"
via: jina
retrieved_at: 2026-09-06T15:51:18+09:00
retrieved_by: unknown
summary: "Claude Code のプロンプトキャッシュ。モデル・effort 変更で全損、TTL は 1 時間（サブスク）/ 5 分、promptCacheTtl、rewind は prefix を再利用"
---
# How Claude Code uses prompt caching - Claude Code Docs

## 引用した記述（原文のまま。要約しない）
- Each model has its own cache. Switching with [`/model`](https://code.claude.com/docs/en/model-config#setting-your-model) means the next request reads the entire conversation history with no cache hits, even though the content is identical.
- [`/rewind`](https://code.claude.com/docs/en/checkpointing) truncates your conversation back to an earlier turn. The remaining history is the same content the cache was built from at that point, and the system prompt and project context layers are unchanged, so the next request hits the earlier cache entry.

## このタスクでの使いどころ（使わなかったなら理由）
README「セッションの切り方」の 2 行（モデルと effort は冒頭で決める／失敗した試行は /rewind）と、API キー利用者向けの promptCacheTtl の根拠。

## 原文（改変しない）
原文: [20260906_1551_How_Claude_Code_uses_prompt_caching_-_Cl.orig.md](20260906_1551_How_Claude_Code_uses_prompt_caching_-_Cl.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
