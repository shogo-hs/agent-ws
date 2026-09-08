---
title: "Hooks | ChatGPT Learn"
kind: web
source: "https://developers.openai.com/codex/hooks"
via: jina
retrieved_at: 2026-09-09T00:41:45+09:00
retrieved_by: unknown
summary: "OpenAI 公式: Codex CLI の hooks（SessionStart〜Stop/SessionEnd のライフサイクルイベント）"
---
# Hooks | ChatGPT Learn

## 引用した記述（原文のまま。要約しない）
- "Hooks are an extensibility framework for Codex. They let you run scripts or MCP tools during the agentic loop, enabling features such as: ... Summarize chats to create persistent memories automatically"
- "| When the main thread ends | `SessionEnd` (doesn't run for subagents) |"
- "`SessionEnd` and `Interrupt` use `1` second by default and support up to `3` seconds."
- "`SessionEnd` lets you run a command when a session ends, such as saving final notes or cleaning up files. It runs for the main thread when you archive or delete a conversation that's still open, when Codex closes normally, or after a conversation has been idle and isn't open in any connected client for 30 minutes."
- "`SessionEnd` hooks always run synchronously, even when `async` is `true`. They are advisory, so their output won't steer Codex or keep the thread open."
- "`transcript_path` points to a chat transcript for convenience, but the transcript format isn't a stable interface for hooks and may change over time."
- Stop: "`stop_hook_active` | `boolean` | Whether this turn was already continued by `Stop`" / "`last_assistant_message`" / "For this event, `decision: "block"` doesn't reject the turn. Instead, it tells Codex to continue and automatically creates a new continuation prompt"
- Published Time: Tue, 08 Sep 2026

## このタスクでの使いどころ（使わなかったなら理由）
Codex 側で同じ仕組みを組むときの制約: SessionEnd は同期・最大3秒なので LLM 呼び出しは detach 必須。transcript_path は非安定インターフェース。公式が用途例として「Summarize chats to create persistent memories automatically」を挙げているが実装や測定は無い。

## 原文（改変しない）
原文: [20260909_0041_Hooks_ChatGPT_Learn.orig.md](20260909_0041_Hooks_ChatGPT_Learn.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
