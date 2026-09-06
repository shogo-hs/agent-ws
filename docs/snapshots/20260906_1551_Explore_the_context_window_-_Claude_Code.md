---
title: "Explore the context window - Claude Code Docs"
kind: web
source: "https://code.claude.com/docs/en/context-window"
via: jina
retrieved_at: 2026-09-06T15:51:13+09:00
retrieved_by: unknown
summary: "Claude Code の文脈の中身。compact 後に再読されるのは直近 5 ファイル・5,000 トークン超はパス参照だけ・スキル一覧は再注入されない"
---
# Explore the context window - Claude Code Docs

## 引用した記述（原文のまま。要約しない）
- Right after compaction, Claude Code re-reads up to five of the files Claude has read or edited in the session, choosing the ones modified most recently, and reloads the rules and nested CLAUDE.md files that apply to those files. A file over 5,000 tokens comes back as a path reference without its content, shown as `Referenced file` instead of `Read`.

## このタスクでの使いどころ（使わなかったなら理由）
#1（要点と原文の分離）の根拠。要点ファイルは小さいので compact 後の再読で中身ごと戻る。原文は 5,000 トークンを超えるとパス参照だけになるので、分けておけば失うものが無い。

## 原文（改変しない）
原文: [20260906_1551_Explore_the_context_window_-_Claude_Code.orig.md](20260906_1551_Explore_the_context_window_-_Claude_Code.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
