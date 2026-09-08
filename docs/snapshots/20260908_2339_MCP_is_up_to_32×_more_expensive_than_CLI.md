---
title: "MCP is up to 32× more expensive than CLI. Here’s why we still use it."
kind: web
source: "https://www.scalekit.com/blog/mcp-vs-cli-use"
via: jina
retrieved_at: 2026-09-08T23:39:28+09:00
retrieved_by: unknown
summary: "Scalekit の GitHub タスク 75 走。MCP は CLI の 4〜32 倍のトークン。原因はツール定義（43 ツール）の毎回注入"
---
# MCP is up to 32× more expensive than CLI. Here’s why we still use it.

## 引用した記述（原文のまま。要約しない）
- We ran 75 benchmark runs comparing CLI and MCP for AI agent tasks. CLI won on every efficiency metric — 10 to 32× cheaper, 100% reliable versus MCP’s 72%.
- Same model (Claude Sonnet 4). Same tasks. Same prompts. Only the tool interface changes.
- GitHub’s Copilot MCP server exposes 43 tools.
- A skill-augmented CLI — just an 800-token document of gh tips — reduces tool calls by a third and latency by a third versus naive CLI.

## このタスクでの使いどころ（使わなかったなら理由）
0013 の②。差の原因はツール定義の毎ターン注入で、MCP 0 本の agent-ws には減らす対象が無い（0012 と同じ結論）

## 原文（改変しない）
原文: [20260908_2339_MCP_is_up_to_32×_more_expensive_than_CLI.orig.md](20260908_2339_MCP_is_up_to_32×_more_expensive_than_CLI.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
