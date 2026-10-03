---
title: "How Claude remembers your project - Claude Code Docs"
kind: web
source: "https://code.claude.com/docs/en/memory"
via: jina
retrieved_at: 2026-10-03T08:12:00+09:00
retrieved_by: unknown
summary: "Claude Code公式ドキュメント: compact時の各指示の扱いの確認用（2026-10-03撮り直し）"
---
# How Claude remembers your project - Claude Code Docs

## 引用した記述（原文のまま。要約しない）
- "Project-root CLAUDE.md survives compaction: after `/compact`, Claude re-reads it from disk and re-injects it into the session."
- "If an instruction disappeared after compaction, it was given only in conversation, lives in a nested CLAUDE.md that hasn't reloaded yet, or is a path-scoped rule that hasn't matched a file since."
- Claude treats them as context, not enforced configuration.
- To block an action regardless of what Claude decides, use a [PreToolUse hook](/docs/en/hooks-guide) instead.
- target under 200 lines per CLAUDE.md file.
- Auto memory is on by default in local sessions.
- To toggle it, open `/memory` in a session and use the auto memory toggle, which saves `autoMemoryEnabled` to your user settings at `~/.claude/settings.json`.
- The first 200 lines of `MEMORY.md`, or the first 25KB, whichever comes first, are loaded at the start of every conversation.
- These conditional rules only apply when Claude is working with files matching the specified patterns.

## このタスクでの使いどころ（使わなかったなら理由）
X 記事の「長い作業では残る層と消える層がある」章と「指示の出し方は 7 つ」の裏取り（2026-10-03）。agent-ws の SessionStart(compact) 注入・CLAUDE.md→@AGENTS.md・Skill 6 本の構成と食い違いが無いかの確認に使った。

## 原文（改変しない）
原文: [20261003_0812_How_Claude_remembers_your_project_-_Clau.orig.md](20261003_0812_How_Claude_remembers_your_project_-_Clau.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
