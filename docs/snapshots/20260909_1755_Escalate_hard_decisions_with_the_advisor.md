---
title: "Escalate hard decisions with the advisor tool - Claude Code Docs"
kind: web
source: "https://code.claude.com/docs/en/advisor"
via: jina
retrieved_at: 2026-09-09T17:55:06+09:00
retrieved_by: claude-code
summary: "Claude Code の Advisor: 有効化の 3 経路・相談役は会話全文を非キャッシュで読む・回数の上限設定なし・CLAUDE_CODE_DISABLE_ADVISOR_TOOL=1 で無効化"
---
# Escalate hard decisions with the advisor tool - Claude Code Docs

## 引用した記述（原文のまま。要約しない）
- It adds less value on short tasks where there is little to plan, or on work where every turn needs the strongest model.
- Your selection is saved to `advisorModel` in your user settings and persists across sessions.
- There is no setting to cap or force advisor calls; if you want Claude to consult more or less often during a task, say so in your instructions.
- When Claude calls the advisor, the advisor model reads the conversation, so each call consumes tokens at the advisor model’s rates in addition to your main model’s usage.
- The advisor model’s own read of the conversation is not cached. Each advisor call processes the full transcript anew, with no reuse between calls.
- To disable the advisor tool entirely, set `CLAUDE_CODE_DISABLE_ADVISOR_TOOL=1`. The `/advisor` command becomes unavailable and any configured `advisorModel` is ignored. The `--advisor` flag is accepted but has no effect.

## このタスクでの使いどころ（使わなかったなら理由）
Advisor を agent-ws 側で外すと決めた ADR 0017 の根拠。相談役は会話全文を毎回非キャッシュで読む・回数の上限設定が無い・短いタスクには効かないと公式が書いている、の 3 点が「agent-ws の仕事の型とは相性が悪い」の出所。`/advisor` の選択がユーザー設定に残り続けることが「利用者が一度試すと以後ずっと付く」経路の根拠。`CLAUDE_CODE_DISABLE_ADVISOR_TOOL=1` が外す手段の根拠（S1 で project settings の env でも効くことを実測）。

## 原文（改変しない）
原文: [20260909_1755_Escalate_hard_decisions_with_the_advisor.orig.md](20260909_1755_Escalate_hard_decisions_with_the_advisor.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
