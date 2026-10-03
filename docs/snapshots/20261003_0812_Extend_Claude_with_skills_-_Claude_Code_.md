---
title: "Extend Claude with skills - Claude Code Docs"
kind: web
source: "https://code.claude.com/docs/en/skills"
via: jina
retrieved_at: 2026-10-03T08:12:02+09:00
retrieved_by: unknown
summary: "Claude Code公式ドキュメント: compact時の各指示の扱いの確認用（2026-10-03撮り直し）"
---
# Extend Claude with skills - Claude Code Docs

## 引用した記述（原文のまま。要約しない）
- "Claude Code re-attaches the most recent invocation of each skill after the summary, keeping the first 5,000 tokens of each. Re-attached skills share a combined budget of 25,000 tokens. Claude Code fills this budget starting from the most recently invoked skill, so older skills can be dropped entirely after compaction if you have invoked many in one session."
- Overrides the session effort level. Default: inherits from session.

## このタスクでの使いどころ（使わなかったなら理由）
X 記事の「長い作業では残る層と消える層がある」章と「指示の出し方は 7 つ」の裏取り（2026-10-03）。agent-ws の SessionStart(compact) 注入・CLAUDE.md→@AGENTS.md・Skill 6 本の構成と食い違いが無いかの確認に使った。

## 原文（改変しない）
原文: [20261003_0812_Extend_Claude_with_skills_-_Claude_Code_.orig.md](20261003_0812_Extend_Claude_with_skills_-_Claude_Code_.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
