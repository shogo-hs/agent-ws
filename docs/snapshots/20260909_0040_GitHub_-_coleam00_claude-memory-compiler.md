---
title: "GitHub - coleam00/claude-memory-compiler: Give Claude Code a memory that evolves with your codebase. Hooks automatically capture sessions, the Claude Agent SDK extracts key decisions and lessons, and an LLM compiler organizes everything into structured, cross-referenced knowledge articles - inspired by Karpathy's LLM Knowledge Base architecture."
kind: web
source: "https://github.com/coleam00/claude-memory-compiler"
via: jina
retrieved_at: 2026-09-09T00:40:40+09:00
retrieved_by: unknown
summary: "claude-memory-compiler: hook でセッションを捕捉し Agent SDK で決定・教訓を抽出、LLM コンパイラで知識記事に整理"
---
# GitHub - coleam00/claude-memory-compiler: Give Claude Code a memory that evolves with your codebase. Hooks automatically capture sessions, the Claude Agent SDK extracts key decisions and lessons, and an LLM compiler organizes everything into structured, cross-referenced knowledge articles - inspired by Karpathy's LLM Knowledge Base architecture.

## 引用した記述（原文のまま。要約しない）
- "When a session ends (or auto-compacts mid-session), Claude Code hooks capture the conversation transcript and spawn a background process that uses the Claude Agent SDK to extract the important stuff - decisions, lessons learned, patterns, gotchas - and appends it to a daily log."
- "Conversation -> SessionEnd/PreCompact hooks -> flush.py extracts knowledge -> daily/YYYY-MM-DD.md -> compile.py -> knowledge/concepts/, connections/, qa/ -> SessionStart hook injects index into next session -> cycle repeats"
- "**flush.py** calls the Claude Agent SDK to decide what's worth saving, and after 6 PM triggers end-of-day compilation automatically"
- "Karpathy's insight: at personal scale (50-500 articles), the LLM reading a structured `index.md` outperforms vector similarity."

## このタスクでの使いどころ（使わなかったなら理由）
SessionEnd + PreCompact で transcript を退避→背景プロセスで LLM 抽出→日次ログ→コンパイル→SessionStart で index 注入、という往復の全体像。CLAUDE.md ではなく独自 knowledge/ に書く。効果測定は無く、コストのみ AGENTS.md に記載。

## 原文（改変しない）
原文: [20260909_0040_GitHub_-_coleam00_claude-memory-compiler.orig.md](20260909_0040_GitHub_-_coleam00_claude-memory-compiler.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
