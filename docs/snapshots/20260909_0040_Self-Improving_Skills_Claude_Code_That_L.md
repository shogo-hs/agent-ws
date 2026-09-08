---
title: "Self-Improving Skills: Claude Code That Learns From Every Session"
kind: web
source: "https://www.developersdigest.tech/blog/self-improving-skills-claude-code"
via: jina
retrieved_at: 2026-09-09T00:40:51+09:00
retrieved_by: unknown
summary: "Developers Digest: セッションを分析して修正を抽出し、スキル自身を更新する self-improving skills"
---
# Self-Improving Skills: Claude Code That Learns From Every Session

## 引用した記述（原文のまま。要約しない）
- "The `/reflect` command analyzes your conversation in real-time. It scans for: **Corrections** you made ("use this button, not that one") / **Approvals** you confirmed (signals that something worked) / **Patterns** that succeeded"
- "Claude shows a diff with confidence levels: **High confidence:** "never do X" or "always do Y" statements / **Medium confidence:** patterns that worked well / **Low confidence:** observations to review later"
- "For maximal learning, bind the reflect mechanism to a **stop hook** - a command that runs when your Claude Code session ends. Now every session automatically: 1. Analyzes for corrections and patterns 2. Updates the skill file 3. Commits to Git"
- "For automatic reflection after every session, add a stop hook in `.claude/hooks/stop.sh` that runs `reflect --auto`. Start with manual reflection to build confidence in the learnings before automating."
- "The reflection runs after the session ends (on the stop hook), not during your work. The analysis happens in the background and typically takes a few seconds."
- "**Reversible.** Bad learnings roll back in one command."
- Published Time: 2026-01-05

## このタスクでの使いどころ（使わなかったなら理由）
Stop hook で /reflect 相当を回し、CLAUDE.md ではなく SKILL.md 側へ confidence 付きで書き戻し、Git commit で可逆にする案。効果測定は無し（「a few seconds」の体感のみ）。同サイトの continual-learning 記事（2025-12-30）は「セッション末尾にレトロを CLAUDE.md かスラッシュコマンドで自動化」と概念だけ。

## 原文（改変しない）
原文: [20260909_0040_Self-Improving_Skills_Claude_Code_That_L.orig.md](20260909_0040_Self-Improving_Skills_Claude_Code_That_L.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
