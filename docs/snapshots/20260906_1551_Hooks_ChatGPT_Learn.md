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
- By default, Codex limits each model-visible hook-output message to roughly 2,500 tokens. If a hook returns more, Codex saves the full text under `<temp_dir>/hook_outputs/<session_id>/<uuid>.txt` and gives the model a head-and-tail preview with the saved-file path. This behavior is called **spilling**: Codex stores oversized output on disk and replaces it with a shorter, model-visible preview. If the file can't be written, the model still receives a truncated preview.
- "additionalContextLimit": 5000

## このタスクでの使いどころ（使わなかったなら理由）
#5（読み替え）の根拠。Codex の PreToolUse も updatedInput で引数を書き換えられる（今回は Claude の Read だけに使い、shell は deny＋理由）。
（第 6 弾）Codex は hook の注入が約 2,500 トークンで切られるので、.codex/hooks.json の session-start に additionalContextLimit: 8000 を付けた根拠。

## 原文（改変しない）
原文: [20260906_1551_Hooks_ChatGPT_Learn.orig.md](20260906_1551_Hooks_ChatGPT_Learn.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
