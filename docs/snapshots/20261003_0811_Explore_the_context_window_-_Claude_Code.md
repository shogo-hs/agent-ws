---
title: "Explore the context window - Claude Code Docs"
kind: web
source: "https://code.claude.com/docs/en/context-window"
via: jina
retrieved_at: 2026-10-03T08:11:59+09:00
retrieved_by: unknown
summary: "Claude Code公式ドキュメント: compact時の各指示の扱いの確認用（2026-10-03撮り直し）"
---
# Explore the context window - Claude Code Docs

## 引用した記述（原文のまま。要約しない）
- "| Invoked skill bodies | Re-injected, capped at 5,000 tokens per skill and 25,000 tokens total; oldest dropped first |"
- "| Context that hooks added earlier | Summarized with the rest of the conversation |"
- "| [SessionStart hooks](https://code.claude.com/docs/en/hooks-guide#re-inject-context-after-compaction) that match the `compact` source | Claude Code runs them and adds their output to the compacted context |"
- "| System prompt and output style | Both still apply |"
- "If a rule must persist across compaction, drop the `paths:` frontmatter or move it to the project-root CLAUDE.md."
- "Truncation keeps the start of the file, so put the most important instructions near the top of `SKILL.md`."

## このタスクでの使いどころ（使わなかったなら理由）
X 記事の「長い作業では残る層と消える層がある」章と「指示の出し方は 7 つ」の裏取り（2026-10-03）。agent-ws の SessionStart(compact) 注入・CLAUDE.md→@AGENTS.md・Skill 6 本の構成と食い違いが無いかの確認に使った。 2026-09-06 版から表に Git status / Background commands の行が増え、output style の行の文言が変わった。

## 原文（改変しない）
原文: [20261003_0811_Explore_the_context_window_-_Claude_Code.orig.md](20261003_0811_Explore_the_context_window_-_Claude_Code.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
