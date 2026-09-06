---
title: "Tools reference - Claude Code Docs"
kind: web
source: "https://code.claude.com/docs/en/tools-reference"
via: jina
retrieved_at: 2026-09-06T17:41:33+09:00
retrieved_by: unknown
summary: "Claude Code の組み込みツール一覧（Read/Grep/Bash の出力上限など）"
---
# Tools reference - Claude Code Docs

## 引用した記述（原文のまま。要約しない）
- | Valid | Inline up to roughly 30,000 characters by default; past that, the path of a file saved to the session directory and truncated past 64 MiB, plus a short preview from the start, and Claude reads or searches the file when it needs the rest |
- *   **Read-before-edit**: Claude reads the file in the current conversation before editing it, and a read cut short with a [`PARTIAL view` notice](https://code.claude.com/docs/en/tools-reference#read-tool-behavior) doesn’t count. Claude Opus 4.6, Claude Haiku 4.5, and older models always require the read. Newer models can edit an unread file when reading it wouldn’t need a permission prompt and the Read tool is available.

## このタスクでの使いどころ（使わなかったなら理由）
Bash と Read に Claude Code 側の上限が既にあるので、agent-ws では tool 出力の上限 hook を入れなかった（捨てた案の根拠）。

## 原文（改変しない）
原文: [20260906_1741_Tools_reference_-_Claude_Code_Docs.orig.md](20260906_1741_Tools_reference_-_Claude_Code_Docs.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
