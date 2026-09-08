---
title: "How Claude remembers your project - Claude Code Docs"
kind: web
source: "https://code.claude.com/docs/en/memory"
via: jina
retrieved_at: 2026-09-09T00:40:22+09:00
retrieved_by: unknown
summary: "Claude Code 公式: CLAUDE.md と auto memory の仕組み。Claude が自分で書くメモの保存先と更新タイミング"
---
# How Claude remembers your project - Claude Code Docs

## 引用した記述（原文のまま。要約しない）
- "Auto memory lets Claude accumulate knowledge across sessions without you writing anything. As it works, Claude saves four kinds of notes for itself. Claude records the kind as a `type` field in the memory file's frontmatter:" — `user` / `feedback` / `project` / `reference`
- "Claude skips anything it can derive from the codebase, such as architecture, file paths, or debugging fixes. It also skips anything your CLAUDE.md files already say.Claude doesn't save something every session. It decides what's worth remembering based on whether the information would be useful in a future conversation."
- "Claude reads and writes files in this directory throughout your session, using `MEMORY.md` to keep track of what's stored where."
- "The first 200 lines of `MEMORY.md`, or the first 25KB, whichever comes first, are loaded at the start of every conversation."
- "After Claude writes to `MEMORY.md`, Claude Code measures the file against the 200-line and 25KB read limits. If the file is near a limit, Claude Code reminds Claude to shorten it"
- "Claude Code has two complementary memory systems. Both are loaded at the start of every conversation. Claude treats them as context, not enforced configuration."
- "If the instruction is something that must run at a specific point, such as before every commit or after each file edit, write it as a hook instead."

## このタスクでの使いどころ（使わなかったなら理由）
公式の auto memory は「セッション中に随時」書く方式で、セッション末尾の一括振り返り（Stop/SessionEnd hook）は公式には無い。書き戻し先（~/.claude/projects/<project>/memory/）と読み込み上限（200行/25KB）が、自作レトロの設計制約になる。効果の測定は公式にも無い。

## 原文（改変しない）
原文: [20260909_0040_How_Claude_remembers_your_project_-_Clau.orig.md](20260909_0040_How_Claude_remembers_your_project_-_Clau.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
