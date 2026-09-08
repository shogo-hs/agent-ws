---
title: "Hooks reference - Claude Code Docs"
kind: web
source: "https://code.claude.com/docs/en/hooks"
via: jina
retrieved_at: 2026-09-09T00:38:05+09:00
retrieved_by: unknown
summary: "Claude Code hooks リファレンス。Stop / SessionEnd の入力 JSON と transcript_path"
---
# Hooks reference - Claude Code Docs

## 引用した記述（原文のまま。要約しない）
- 「once per session: `SessionStart` and `SessionEnd`」「once per turn: `UserPromptSubmit`, `Stop`, and `StopFailure`」
- Stop: 「Runs when the main Claude Code agent has finished responding. Does not run if the stoppage occurred due to a user interrupt.」
- Stop input: 「The `stop_hook_active` field is `true` when Claude Code is already continuing as a result of a stop hook. Check this value or process the transcript to avoid blocking on a condition that will never resolve. Claude Code overrides the hook and ends the turn after 8 consecutive blocks.」
- transcript_path: 「The transcript file is written asynchronously and may lag the in-memory conversation, so it may not yet include the current turn's most recent messages when a hook fires.」
- SessionEnd: 「SessionEnd hooks have no decision control. They can't block session termination but can perform cleanup tasks.」「SessionEnd hooks have a default timeout of 1.5 seconds. This applies to session exit, `/clear`, and switching sessions via interactive `/resume`. ... The overall budget is automatically raised to the highest per-hook timeout configured in settings files, up to 60 seconds.」
- SessionEnd の reason: `clear`, `resume`, `logout`, `prompt_input_exit`, `other`
- prompt / agent hook を受ける event に `Stop` は含まれるが `SessionEnd` と `SessionStart` は含まれない（「Events that support `command`, `http`, and `mcp_tool` hooks but not `prompt` or `agent`: ... `SessionEnd`」）
- prompt hook: 「Send the hook input and your prompt to a Claude model, Haiku by default」「`timeout` ... Default: 30」。agent hook: 「After up to 50 turns, the subagent returns a structured `{ "ok": true/false }` decision」「Default: 60」
- async: 「Add `"async": true` to a command hook's configuration to run it in the background without blocking Claude. This field is only available on `type: "command"` hooks.」「In non-interactive mode with the `-p` flag, Claude Code kills any async hook still running at teardown」「If your hook's work must outlive a `claude -p` session, start a fully detached process from it」

## このタスクでの使いどころ（使わなかったなら理由）
「作業終了時」に当たる event は SessionEnd だが、LLM 系 hook（prompt/agent）は使えず、時間予算は最大 60 秒。Stop は毎ターン発火するので「セッションの終わり」を知らない。transcript を LLM に読ませる振り返りを hook の中で同期に回すのは仕様上も無理があり、やるなら detach したプロセスか、次回 SessionStart／cron での後処理になる。

## 原文（改変しない）
原文: [20260909_0038_Hooks_reference_-_Claude_Code_Docs.orig.md](20260909_0038_Hooks_reference_-_Claude_Code_Docs.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
