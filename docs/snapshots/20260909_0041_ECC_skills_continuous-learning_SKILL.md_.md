---
title: "ECC/skills/continuous-learning/SKILL.md at main · affaan-m/ECC"
kind: web
source: "https://github.com/affaan-m/everything-claude-code/blob/main/skills/continuous-learning/SKILL.md"
via: jina
retrieved_at: 2026-09-09T00:41:43+09:00
retrieved_by: unknown
summary: "ECC continuous-learning: Stop hook でセッションを評価しパターンを ~/.claude/skills/learned/ に保存するスキル"
---
# ECC/skills/continuous-learning/SKILL.md at main · affaan-m/ECC

## 引用した記述（原文のまま。要約しない）
- "This skill runs as a **Stop hook** at the end of each session: 1. **Session Evaluation**: Checks if session has enough messages (default: 10+) 2. **Pattern Detection**: Identifies extractable patterns from the session 3. **Skill Extraction**: Saves useful patterns to `~/.claude/skills/learned/`"
- config.json: `"min_session_length": 10, "extraction_threshold": "medium", "auto_approve": false, "learned_skills_path": "~/.claude/skills/learned/", "patterns_to_detect": ["error_resolution","user_corrections","workarounds","debugging_techniques","project_specific"]`
- Hook Setup: `"Stop": [{ "matcher": "*", "hooks": [{ "type": "command", "command": "~/.claude/skills/continuous-learning/evaluate-session.sh" }] }]`
- "**Why Stop Hook?** **Lightweight**: Runs once at session end / **Non-blocking**: Doesn't add latency to every message / **Complete context**: Has access to full session transcript"
- "**DEPRECATED 2026-04-28.** Use `continuous-learning-v2` instead. v2 is a strict superset: stop-hook observation becomes PreToolUse/PostToolUse observation, full skills become atomic instincts with confidence scoring, and global-only storage becomes project-scoped plus global promotion."
- vs Homunculus 表: "Observation | Stop hook (end of session) | PreToolUse/PostToolUse hooks (100% reliable)" / "Analysis | Main context | Background agent (Haiku)" / "Confidence | None | 0.3-0.9 weighted"
- "v1 relied on skills to observe. Skills are probabilistic—they fire ~50-80% of the time. v2 uses hooks for observation (100% reliable) and instincts as the atomic unit of learned behavior."

## このタスクでの使いどころ（使わなかったなら理由）
Stop hook で transcript を評価→~/.claude/skills/learned/ に書く最も直接的な先行例。作者自身が v1 を deprecate し、Stop 一発から PreToolUse/PostToolUse 常時観測＋confidence 付き instinct に移った経緯が設計判断の材料。「~50-80%」はスキル発火率の主張で出典不明、効果測定ではない。

## 原文（改変しない）
原文: [20260909_0041_ECC_skills_continuous-learning_SKILL.md_.orig.md](20260909_0041_ECC_skills_continuous-learning_SKILL.md_.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
