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
- *   **Long context**: Claude Code sends your full conversation with every request, and each time Claude uses tools it sends another request carrying that batch of tool results. With [prompt caching](https://code.claude.com/docs/en/prompt-caching), Claude Code re-reads that history at the [cached token rate](https://platform.claude.com/docs/en/about-claude/pricing), so a one-line question in a session that has been open all day still draws usage for the whole conversation. See [Manage context proactively](https://code.claude.com/docs/en/costs#manage-context-proactively) for ways to keep your context small

## このタスクでの使いどころ（使わなかったなら理由）
#3（compact で残すものを AGENTS.md に書く。CLAUDE.md は @AGENTS.md で読み込む）と #5（hook で読む先を正規化版に差し替える）の根拠。
（第 6 弾）「ターンごとに会話全体を払い直す」の根拠。AGENTS.md「ターンを減らす」と README「起動時の注入でターンを減らす」。

## 原文（改変しない）
原文: [20260906_1551_Manage_costs_effectively_-_Claude_Code_D.orig.md](20260906_1551_Manage_costs_effectively_-_Claude_Code_D.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
