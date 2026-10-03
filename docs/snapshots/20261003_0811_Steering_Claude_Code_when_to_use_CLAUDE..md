---
title: "Steering Claude Code: when to use CLAUDE.md, skills, hooks, and subagents"
kind: web
source: "https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more"
via: jina
retrieved_at: 2026-10-03T08:11:15+09:00
retrieved_by: unknown
summary: "Anthropic公式ブログ: Claude Codeへの指示の出し方7種と、それぞれのcompact時の扱いの比較"
---
# Steering Claude Code: when to use CLAUDE.md, skills, hooks, and subagents

## 引用した記述（原文のまま。要約しない）
jina の .orig.md は導入と比較表と CLAUDE.md の節を落としている。表と導入は同じ時刻に curl した HTML から本文を抜いた `20261003_0811_Steering_Claude_Code_when_to_use_CLAUDE..html-text.orig.md` にある（引用はそちらで grep 済み）。
- "There are seven methods for instructing Claude's behavior: CLAUDE.md files, rules, skills, subagents, hooks, output styles, and appending the system prompt."
- CLAUDE.md (root): "Memoized. Read once and cached for the session; cache cleared and re-read after compaction"
- CLAUDE.md (subdirectory): "Lost until that subdirectory is touched again"
- "It shares the compaction behavior of path-scoped rules: gone until that subdirectory is touched again."
- "Unscoped rules behave like CLAUDE.md in that they are always loaded at session start and get re-injected on compaction."
- Skills: "Invoked skills re-injected up to a shared budget; oldest dropped first"
- Subagents: "Only the final message (summary plus metadata) returns to the main session"
- Hooks: "Bypass compaction entirely"
- Output styles: "Never compacted" / Appending the system prompt: "Never compacted; applies only to that invocation"
- "If you backed up your chat history into another file for later reference before compaction using the `PreCompact` event, Claude wouldn't know which file had the chat history saved."

## このタスクでの使いどころ（使わなかったなら理由）
X 記事の「長い作業では残る層と消える層がある」章と「指示の出し方は 7 つ」の裏取り（2026-10-03）。agent-ws の SessionStart(compact) 注入・CLAUDE.md→@AGENTS.md・Skill 6 本の構成と食い違いが無いかの確認に使った。

## 原文（改変しない）
原文: [20261003_0811_Steering_Claude_Code_when_to_use_CLAUDE..orig.md](20261003_0811_Steering_Claude_Code_when_to_use_CLAUDE..orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
