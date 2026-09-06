---
title: "Manage costs effectively - Claude Code Docs"
kind: web
source: "https://code.claude.com/docs/en/costs"
via: jina
retrieved_at: 2026-09-06T15:51:15+09:00
retrieved_by: unknown
summary: "Claude Code の費用削減。CLAUDE.md の Compact instructions、hook で前処理して読む量を減らす、サブエージェントへの委譲"
---
# Manage costs effectively - Claude Code Docs

## 引用した記述（原文のまま。要約しない）
- You can also customize compaction behavior in your CLAUDE.md file at the root of your project:
- Custom [hooks](https://code.claude.com/docs/en/hooks) can preprocess data before Claude sees it. Instead of Claude reading a 10,000-line log file to find errors, a hook can grep for `ERROR` and return only matching lines, reducing context from tens of thousands of tokens to hundreds.

## このタスクでの使いどころ（使わなかったなら理由）
#3（compact で残すものを AGENTS.md に書く。CLAUDE.md は @AGENTS.md で読み込む）と #5（hook で読む先を正規化版に差し替える）の根拠。

## 原文（改変しない）
原文: [20260906_1551_Manage_costs_effectively_-_Claude_Code_D.orig.md](20260906_1551_Manage_costs_effectively_-_Claude_Code_D.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
