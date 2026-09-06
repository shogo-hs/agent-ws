---
title: "Extend Claude with skills - Claude Code Docs"
kind: web
source: "https://code.claude.com/docs/en/skills"
via: jina
retrieved_at: 2026-09-06T15:51:17+09:00
retrieved_by: unknown
summary: "Claude Code のスキル仕様。context: fork は会話履歴を持たず、model/effort は fork 先に効く。一覧の文字数予算"
---
# Extend Claude with skills - Claude Code Docs

## 引用した記述（原文のまま。要約しない）
- Add `context: fork` to your frontmatter when you want a skill to run in isolation. The skill content becomes the prompt that drives the subagent. It won’t have access to your conversation history.
- Set `background: false` in the frontmatter to instead wait for the result in the turn that invoked the skill.

## このタスクでの使いどころ（使わなかったなら理由）
#2（transcript-ingest の fork 化）の根拠。会話履歴が無いので SKILL.md を自己完結の指示として書き、background: false で本線が結果を待つ。

## 原文（改変しない）
原文: [20260906_1551_Extend_Claude_with_skills_-_Claude_Code_.orig.md](20260906_1551_Extend_Claude_with_skills_-_Claude_Code_.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
