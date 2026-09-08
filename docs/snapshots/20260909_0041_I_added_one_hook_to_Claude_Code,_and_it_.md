---
title: "I added one hook to Claude Code, and it stopped making the same mistake twice"
kind: web
source: "https://www.xda-developers.com/added-one-hook-claude-code-stopped-same-mistake-twice/"
via: direct
retrieved_at: 2026-09-09T00:41:16+09:00
retrieved_by: unknown
summary: "XDA: hook 1本で Claude Code が同じミスを繰り返さなくなったという体験記"
---
# I added one hook to Claude Code, and it stopped making the same mistake twice

## 引用した記述（原文のまま。要約しない）
- "I have clearly included the instructions in the prompt and updated the CLAUDE.md file, but prompt instructions only work once."
- "For this setup, I'm using a command-based Stop hook, which runs whenever the main Claude agent finishes responding. The hook blocks its first attempt and tells it to read the list of previously recorded mistakes and review the changes again."
- "I keep the previous mistakes in a dedicated mistakes.md file inside the project's rules folder instead of adding everything to CLAUDE.md."
- スクリプト: `STOP_HOOK_ACTIVE=$(printf '%s' "$INPUT" | jq -r '.stop_hook_active // false')` / `MISTAKES_FILE="${CLAUDE_PROJECT_DIR}/.claude/rules/mistakes.md"` / `"Before finishing, review your work against these known mistakes:\n" + $mistakes`
- "On the first stop attempt, the script returns a block decision and Claude continues working with the mistakes list in its context. Claude Code then sets stop_hook_active to true, which the script checks before allowing the second attempt to finish."
- "Since this particular hook blocks the first stop attempt, Claude receives another model turn and revisits the mistakes file even when there are no changes to inspect."
- Published Aug 30, 2026

## このタスクでの使いどころ（使わなかったなら理由）
lessons の「読む側」の先行例。Stop hook で block して mistakes.md を再確認させる（書き戻しは人手）。stop_hook_active でループを止める実装が参考になる。効果は「同じミスをしなくなった」という体験のみで測定なし。

## 原文（改変しない）
原文: [20260909_0041_I_added_one_hook_to_Claude_Code,_and_it_.orig.md](20260909_0041_I_added_one_hook_to_Claude_Code,_and_it_.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
