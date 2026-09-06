---
title: "Hooks reference - Claude Code Docs"
kind: web
source: "https://code.claude.com/docs/en/hooks"
via: jina
retrieved_at: 2026-09-06T17:31:32+09:00
retrieved_by: unknown
summary: "Claude Code の hooks リファレンス（イベント・入出力 JSON・設定）"
---
# Hooks reference - Claude Code Docs

## 引用した記述（原文のまま。要約しない）
- Hook output strings, including additionalContext, systemMessage, and plain stdout, are capped at 10,000 characters. Output that exceeds this limit is saved to a file and replaced with a preview and file path, the same way a large valid Bash result is handled under Output limits.
- SessionStart, SubagentStart, PostModelSwitch	Context only	hookSpecificOutput.additionalContext adds context for Claude. SessionStart also accepts initialUserMessage, watchPaths, sessionTitle, and reloadSkills. No blocking or decision control
- updatedToolOutput	Replaces the tool’s output with the provided value before it is sent to Claude. The value must match the tool’s output shape
- Runs once after every tool call in a batch has resolved, before Claude Code sends the next request to the model. PostToolUse fires once per tool, which means it fires concurrently when Claude makes parallel tool calls. PostToolBatch fires exactly once with the full batch, so it is the right place to inject context that depends on the set of tools that ran rather than on any single tool. There is no matcher for this event.

## このタスクでの使いどころ（使わなかったなら理由）
（第 6 弾）SessionStart の注入上限 INJECT_MAX=6,000 字の根拠（10,000 字で切られてファイル参照に化ける）。PostToolUse の updatedToolOutput で tool の結果を差し替えられることを確認したが、transcript の集計で tool の結果は処理トークンの 5〜7% しか無いので使わなかった。

## 原文（改変しない）
原文: [20260906_1731_Hooks_reference_-_Claude_Code_Docs.orig.md](20260906_1731_Hooks_reference_-_Claude_Code_Docs.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
