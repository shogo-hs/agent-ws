---
title: "Getting the most out of Opus 5.5 in Claude and Claude Code"
kind: web
source: "https://claude.dev/blog/getting-the-most-out-of-opus-5-5/"
via: jina
retrieved_at: 2026-10-03T08:11:23+09:00
retrieved_by: unknown
summary: "Opus 5.5 を Claude と Claude Code で使いこなすための公式ブログ（2026-09-22）"
---
# Getting the most out of Opus 5.5 in Claude and Claude Code

## 引用した記述（原文のまま。要約しない）
- Audit every service in services/ for the retry bug in the linked issue. Give each service to its own subagent. When a subagent reports back, check its evidence before you accept it. Finish with one table: service, affected yes or no, and the evidence.
- A long run fills the context window, and Claude Code then summarizes older turns. A list in a file survives that, and it shows you at a glance what’s done and what’s left.
- When a step doesn't need my input, keep going. Put status notes in the same message as your next action. Stop and ask only when you can't continue without me, or before anything destructive: deleting data, force-pushing, or changing anything outside this repository.
- To change the summary’s format, say so in CLAUDE.md, for example, “End every run with three headings: Blocked on me, Changed, Found.”
- Review the diff on this branch against main. List only problems you'd block the merge for. For each one, give the file and line, why it's wrong, and how to show it fails.

## このタスクでの使いどころ（使わなかったなら理由）
（この記述をどう使ったか、使わなかったならその理由）

## 原文（改変しない）
原文: [20261003_0811_Getting_the_most_out_of_Opus_5.5_in_Clau.orig.md](20261003_0811_Getting_the_most_out_of_Opus_5.5_in_Clau.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
