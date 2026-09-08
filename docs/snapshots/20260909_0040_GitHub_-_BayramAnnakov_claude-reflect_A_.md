---
title: "GitHub - BayramAnnakov/claude-reflect: A self-learning system for Claude Code that captures corrections, positive feedback, and preferences — then syncs them to CLAUDE.md and AGENTS.md."
kind: web
source: "https://github.com/BayramAnnakov/claude-reflect"
via: jina
retrieved_at: 2026-09-09T00:40:34+09:00
retrieved_by: unknown
summary: "claude-reflect: hook で修正発言を検出しキューに溜め、/reflect で CLAUDE.md/AGENTS.md に同期する自己学習システム"
---
# GitHub - BayramAnnakov/claude-reflect: A self-learning system for Claude Code that captures corrections, positive feedback, and preferences — then syncs them to CLAUDE.md and AGENTS.md.

## 引用した記述（原文のまま。要約しない）
- "**Stage 1: Capture (Automatic)** Hooks run automatically to detect and queue corrections:" — `session_start_reminder.py` (Session start) / `capture_learning.py` (Every prompt: "Detects correction patterns and queues them") / `check_learnings.py` (Before compaction: "Backs up queue and informs user") / `post_commit_reminder.py` (After git commit)
- "**Stage 2: Process (Manual)** Run `/reflect` to review and apply queued learnings to CLAUDE.md."
- "**1. Regex patterns (real-time capture)** ... **Corrections**: `"no, use X"` / `"don't use Y"` / `"actually..."` / `"that's wrong"`"
- "**2. Semantic AI validation (during /reflect)** When you run `/reflect`, an AI-powered semantic filter:"
- "Each captured learning has a **confidence score** (0.60-0.95). The final score is the higher of regex and semantic confidence."
- "Approved learnings are synced to:" `~/.claude/CLAUDE.md` / `./CLAUDE.md` / `./**/CLAUDE.md` / "`AGENTS.md` (if exists - works with Codex, Cursor, Aider, Jules, Zed, Factory)"
- "**Skills get smarter** - When you correct Claude during a skill, that correction can be routed back to the skill file itself via `/reflect`"
- "Over time, CLAUDE.md can accumulate similar entries. Run `/reflect --dedupe` to:"

## このタスクでの使いどころ（使わなかったなら理由）
Stop/SessionEnd ではなく UserPromptSubmit で修正発言を regex 捕捉→キュー→手動 /reflect で LLM 検証して CLAUDE.md/AGENTS.md/skill に書き戻す先行例。confidence 0.60-0.95 と dedupe を持つ。効果測定（トークン・手戻り）は無し。

## 原文（改変しない）
原文: [20260909_0040_GitHub_-_BayramAnnakov_claude-reflect_A_.orig.md](20260909_0040_GitHub_-_BayramAnnakov_claude-reflect_A_.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
