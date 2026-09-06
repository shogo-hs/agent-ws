---
title: "Explore the context window - Claude Code Docs"
kind: web
source: "https://code.claude.com/docs/en/context-window"
via: jina
retrieved_at: 2026-09-06T15:51:13+09:00
retrieved_by: unknown
summary: "Claude Code の文脈の中身。compact 後に再読されるのは直近 5 ファイルで、5,000 トークン超はパス参照だけになる"
---
# Explore the context window - Claude Code Docs

## 引用した記述（原文のまま。要約しない）
- Right after compaction, Claude Code re-reads up to five of the files Claude has read or edited in the session, choosing the ones modified most recently, and reloads the rules and nested CLAUDE.md files that apply to those files. A file over 5,000 tokens comes back as a path reference without its content, shown as `Referenced file` instead of `Read`.
- | Context that hooks added earlier | Summarized with the rest of the conversation |
- | [SessionStart hooks](https://code.claude.com/docs/en/hooks-guide#re-inject-context-after-compaction) that match the `compact` source | Claude Code runs them and adds their output to the compacted context |

## このタスクでの使いどころ（使わなかったなら理由）
#1（要点と原文の分離）の根拠。要点ファイルは小さいので compact 後の再読で中身ごと戻る。原文は 5,000 トークンを超えるとパス参照だけになるので、分けておけば失うものが無い。
（第 6 弾）hook が足した文脈は compact で要約に溶けるが、SessionStart(compact) は再実行される（scripts/ws は source=compact でも同じ注入を返す）。index.md の全文を SessionStart で注入すれば compact 後も現在地が戻る、の根拠。

## 原文（改変しない）
原文: [20260906_1551_Explore_the_context_window_-_Claude_Code.orig.md](20260906_1551_Explore_the_context_window_-_Claude_Code.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
