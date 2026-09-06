---
title: "Hooks | ChatGPT Learn"
kind: web
source: "https://learn.chatgpt.com/docs/hooks"
via: jina
retrieved_at: 2026-09-06T15:51:22+09:00
retrieved_by: unknown
summary: "Codex CLI の hooks。PreToolUse の updatedInput で引数を書き換えられる。hosted の WebSearch には発火しない"
---
# Hooks | ChatGPT Learn

## 引用した記述（原文のまま。要約しない）
- To rewrite a supported tool call without blocking, return `permissionDecision: "allow"` with `updatedInput`:
- | Hosted tools, such as `WebSearch` | No | No | These don't use the local function-tool hook path. |

## このタスクでの使いどころ（使わなかったなら理由）
#5（読み替え）の根拠。Codex の PreToolUse も updatedInput で引数を書き換えられる（今回は Claude の Read だけに使い、shell は deny＋理由）。

## 原文（改変しない）
原文: [20260906_1551_Hooks_ChatGPT_Learn.orig.md](20260906_1551_Hooks_ChatGPT_Learn.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
