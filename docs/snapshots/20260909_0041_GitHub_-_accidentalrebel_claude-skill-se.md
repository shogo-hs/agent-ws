---
title: "GitHub - accidentalrebel/claude-skill-session-retrospective"
kind: web
source: "https://github.com/accidentalrebel/claude-skill-session-retrospective"
via: jina
retrieved_at: 2026-09-09T00:41:07+09:00
retrieved_by: unknown
summary: "claude-skill-session-retrospective: セッション振り返りをスキルとして実行し CLAUDE.md へ学びを書き戻す"
---
# GitHub - accidentalrebel/claude-skill-session-retrospective

## 引用した記述（原文のまま。要約しない）
- "A Claude Code skill that analyzes your current session and generates a summary of lessons learned, suitable for future reference or blog post sharing."
- "Invoke the skill with `/session-retrospective` or use natural triggers like: "what did we learn" / "session summary" / "lessons learned" / "retro""
- "The skill outputs markdown to console for copy/paste."
- "1. `scripts/get-session.sh` retrieves the current session's JSONL history 2. Claude parses messages, tool uses, and corrections 3. Identifies key moments: problems, solutions, mistakes, techniques 4. Generates blog-post-friendly markdown"
- "Claude Code stores sessions as JSONL in `~/.claude/projects/<project>/<session-id>.jsonl`. Each line contains: `type`: "user" or "assistant" / `message.content`: the actual content / `timestamp`: when it occurred / Tool results with `is_error: true` for rejected actions"
- Star 12 / Fork 4 / 2 Commits / Feb 1, 2026

## このタスクでの使いどころ（使わなかったなら理由）
hook ではなく手動スキル。自分の JSONL を読んで「Mistakes made and lessons learned」を出すが、書き戻し先は無く console 出力止まり。transcript の JSONL 形式（is_error で拒否を拾う）の記述だけ使う。効果測定は無し。

## 原文（改変しない）
原文: [20260909_0041_GitHub_-_accidentalrebel_claude-skill-se.orig.md](20260909_0041_GitHub_-_accidentalrebel_claude-skill-se.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
