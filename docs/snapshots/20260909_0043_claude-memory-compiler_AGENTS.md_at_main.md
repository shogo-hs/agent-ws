---
title: "claude-memory-compiler/AGENTS.md at main · coleam00/claude-memory-compiler"
kind: web
source: "https://github.com/coleam00/claude-memory-compiler/blob/main/AGENTS.md"
via: jina
retrieved_at: 2026-09-09T00:43:05+09:00
retrieved_by: unknown
summary: "claude-memory-compiler の技術リファレンス: hook 構成・flush の内部・コスト"
---
# claude-memory-compiler/AGENTS.md at main · coleam00/claude-memory-compiler

## 引用した記述（原文のまま。要約しない）
- hooks 設定: `"SessionStart": [... "uv run python hooks/session-start.py", "timeout": 15 ]`, `"PreCompact": [... "hooks/pre-compact.py", "timeout": 10 ]`, `"SessionEnd": [... "hooks/session-end.py", "timeout": 10 ]`
- "**`session-end.py`** (SessionEnd) Reads hook input from stdin (JSON with `session_id`, `transcript_path`, `cwd`) / Copies the raw JSONL transcript to a temp file (no parsing in the hook - keeps it fast) / Spawns `flush.py` as a fully detached background process / Recursion guard: exits immediately if `CLAUDE_INVOKED_BY` env var is set"
- "**Why both PreCompact and SessionEnd?** Long-running sessions may trigger multiple auto-compactions before you close the session. Without PreCompact, intermediate context is lost to summarization before SessionEnd ever fires."
- "Skips if context is empty or if same session was flushed within 60 seconds (deduplication)"
- "Calls Claude Agent SDK (`query()` with `allowed_tools=[]`, `max_turns=2`)"
- "Claude decides what's worth saving - returns structured bullet points or `FLUSH_OK`"
- Costs 表: "Memory flush (per session) | ~$0.02-0.05", "Compile one daily log | $0.45-0.65", "Query (no file-back) | ~$0.15-0.25"

## このタスクでの使いどころ（使わなかったなら理由）
hook 内は transcript のコピーだけで LLM 呼び出しは detach した背景プロセスに逃がす、再帰ガード、60秒 dedupe、PreCompact 併用、という実装上の具体策。数字はコスト（1セッション ~$0.02-0.05）のみで、効果（手戻り・トークン削減）の測定は無い。

## 原文（改変しない）
原文: [20260909_0043_claude-memory-compiler_AGENTS.md_at_main.orig.md](20260909_0043_claude-memory-compiler_AGENTS.md_at_main.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
