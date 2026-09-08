---
title: "clerk: Auto-Summarize Your Claude Code Sessions"
kind: web
source: "https://dev.to/vulcan_shen_acdbffa0285d2/clerk-auto-summarize-your-claude-code-sessions-4m87"
via: jina
retrieved_at: 2026-09-09T00:41:11+09:00
retrieved_by: unknown
summary: "clerk: SessionEnd で transcript を増分要約し Markdown に保存する CLI"
---
# clerk: Auto-Summarize Your Claude Code Sessions

## 引用した記述（原文のまま。要約しない）
- "clerk is a CLI tool that hooks into Claude Code. Every time a session ends, it generates an incremental summary and saves it as a plain markdown file."
- "You could ask Claude to re-read old transcripts, but each time it re-processes the entire raw conversation, burning tokens. Across multiple sessions and projects, that's expensive and slow. clerk does one API call per session at the moment it ends."
- "Session ends → clerk feed (background) → read transcript → call claude -p → save summary + index"
- "Hooks into Claude Code via SessionStart/SessionEnd hooks / Cursor tracking — only processes new messages since last run"
- 保存先: `~/.clerk/summary/<YYYYMMDD>/<project>.md`
- Published Time: 2026-04-17

## このタスクでの使いどころ（使わなかったなら理由）
SessionEnd→背景で `claude -p`→日付/プロジェクト別 md、という最小構成の先行例。CLAUDE.md/lessons への書き戻しはせず要約保存のみ（/clerk-resume で次セッションに渡す）。「1 セッション 1 API call」と言うだけで、トークン・手戻りの測定は無し。

## 原文（改変しない）
原文: [20260909_0041_clerk_Auto-Summarize_Your_Claude_Code_Se.orig.md](20260909_0041_clerk_Auto-Summarize_Your_Claude_Code_Se.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
