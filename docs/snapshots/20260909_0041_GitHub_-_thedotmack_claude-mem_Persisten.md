---
title: "GitHub - thedotmack/claude-mem: Persistent Context Across Sessions for Every Agent –  Captures everything your agent does during sessions, compresses it with AI, and injects relevant context back into future sessions. Works with Claude Code, OpenClaw, Codex, Gemini, Hermes, Copilot, OpenCode + More"
kind: web
source: "https://github.com/thedotmack/claude-mem"
via: jina
retrieved_at: 2026-09-09T00:41:23+09:00
retrieved_by: unknown
summary: "claude-mem: SessionStart/PostToolUse/Stop/SessionEnd hook で観測を圧縮・保存し次セッションに注入する永続メモリ"
---
# GitHub - thedotmack/claude-mem: Persistent Context Across Sessions for Every Agent –  Captures everything your agent does during sessions, compresses it with AI, and injects relevant context back into future sessions. Works with Claude Code, OpenClaw, Codex, Gemini, Hermes, Copilot, OpenCode + More

## 引用した記述（原文のまま。要約しない）
- "Captures everything your agent does during sessions, compresses it with AI, and injects relevant context back into future sessions. Works with Claude Code, OpenClaw, Codex, Gemini, Hermes, Copilot, OpenC..."
- "1. **5 Lifecycle Hooks** - SessionStart, UserPromptSubmit, PostToolUse, Stop, SessionEnd (6 hook scripts)"
- "3. **Worker Service** - Local HTTP API with web viewer UI and search endpoints, managed by Bun 4. **SQLite Database** - Stores sessions, observations, summaries"
- "1. **`search`** - Get compact index with IDs (~50-100 tokens/result) ... 3. **`get_observations`** - Fetch full details ONLY for filtered IDs (~500-1,000 tokens/result)"
- "**~10x token savings** by filtering before fetching details"
- "Signing in provisions a memory key for your account and unlocks the **claude-mem observer**: memory that runs off-plan, free for your first 30 days"

## このタスクでの使いどころ（使わなかったなら理由）
5 hook 全部（PostToolUse まで）で観測を集めて Worker+SQLite+Chroma に貯める重量級。CLAUDE.md には書かず MCP 検索で返す。「~10x token savings」は検索の段階的開示の話で、レトロの効果測定ではない。有料の hosted 版（CMEM）へ誘導する利害がある。

## 原文（改変しない）
原文: [20260909_0041_GitHub_-_thedotmack_claude-mem_Persisten.orig.md](20260909_0041_GitHub_-_thedotmack_claude-mem_Persisten.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
