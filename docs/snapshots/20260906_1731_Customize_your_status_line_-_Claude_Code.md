---
title: "Customize your status line - Claude Code Docs"
kind: web
source: "https://code.claude.com/docs/en/statusline"
via: jina
retrieved_at: 2026-09-06T17:31:46+09:00
retrieved_by: unknown
summary: "Claude Code の status line 設定と渡される JSON の項目"
---
# Customize your status line - Claude Code Docs

## 引用した記述（原文のまま。要約しない）
- Add a `statusLine` field to your user settings (`~/.claude/settings.json`, where `~` is your home directory) or [project settings](https://code.claude.com/docs/en/settings#where-settings-live). Set `type` to `"command"` and point `command` to a script path or an inline shell command. For a full walkthrough of creating a script, see [Build a status line step by step](https://code.claude.com/docs/en/statusline#build-a-status-line-step-by-step).
- | `cost.total_cost_usd` | Estimated session cost in USD, computed client-side at list price unless a [`modelPricing`](https://code.claude.com/docs/en/settings-reference#modelpricing) table is in effect. May differ from your actual bill. Resets to $0 when `/clear` starts a new session. Before v2.1.211, the total carried over after `/clear` |
- | `context_window.used_percentage` | Pre-calculated percentage of context window used |
- | `session_id` | Unique session identifier |

## このタスクでの使いどころ（使わなかったなら理由）
scripts/ws statusline が読む項目の名前と意味。project の settings.json に置けること（settings reference の Scope: Any file と合わせて）。費用と使用率は Claude Code が計算した値をそのまま出す。

## 原文（改変しない）
原文: [20260906_1731_Customize_your_status_line_-_Claude_Code.orig.md](20260906_1731_Customize_your_status_line_-_Claude_Code.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
