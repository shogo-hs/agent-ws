---
title: "Environment variables - Claude Code Docs"
kind: web
source: "https://code.claude.com/docs/en/env-vars"
via: jina
retrieved_at: 2026-09-06T17:41:27+09:00
retrieved_by: unknown
summary: "Claude Code の環境変数一覧（トークン上限・出力上限・compact しきい値など）"
---
# Environment variables - Claude Code Docs

## 引用した記述（原文のまま。要約しない）
- `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`Set the percentage (1-100) of the auto-compact window at which auto-compaction triggers. Use lower values like `50` to compact earlier; the variable can’t raise the threshold, so values above the default percentage are ignored. It applies only in sessions that [compact before the model’s context limit](https://code.claude.com/docs/en/model-config#context-window-and-auto-compaction). Applies to both main conversations and subagents
- `BASH_MAX_OUTPUT_LENGTH`Maximum number of characters of bash output that Claude Code reads back into a command’s result (default: 30000; maximum: 150000). If you set the [`bashOutputMaxChars`](https://code.claude.com/docs/en/settings-reference#bashoutputmaxchars) setting, Claude Code ignores this variable. See [Output limits](https://code.claude.com/docs/en/tools-reference#output-limits)
- `CLAUDE_CODE_MAX_OUTPUT_TOKENS`Set the maximum number of output tokens for most requests. Defaults and caps vary by model; see [max output tokens](https://platform.claude.com/docs/en/about-claude/models/overview#latest-models-comparison). Claude Code defaults to 32000 for model IDs it doesn’t recognize, such as gateway-specific names, and lowers values above a model’s cap to the cap. Increasing this value reduces the effective context window available before [auto-compaction](https://code.claude.com/docs/en/costs#reduce-token-usage) triggers

## このタスクでの使いどころ（使わなかったなら理由）
README「セッションの切り方」の従量課金向けの調整（自動 compact を早める）。agent-ws は既定を変えない（効果を測っていない）。BASH_MAX_OUTPUT_LENGTH は Bash の出力に既に上限があることの確認（出力上限 hook を入れなかった理由の一つ）。

## 原文（改変しない）
原文: [20260906_1741_Environment_variables_-_Claude_Code_Docs.orig.md](20260906_1741_Environment_variables_-_Claude_Code_Docs.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
