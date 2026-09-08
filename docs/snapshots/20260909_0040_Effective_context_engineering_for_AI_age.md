---
title: "Effective context engineering for AI agents"
kind: web
source: "https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents"
via: jina
retrieved_at: 2026-09-09T00:40:26+09:00
retrieved_by: unknown
summary: "Anthropic engineering: コンテキストエンジニアリング。構造化メモ・compaction・長期タスクでの記憶の外部化"
---
# Effective context engineering for AI agents

## 引用した記述（原文のまま。要約しない）
- "Structured note-taking, or agentic memory, is a technique where the agent regularly writes notes persisted to memory outside of the context window. These notes get pulled back into the context window at later times."
- "Like Claude Code creating a to-do list, or your custom agent maintaining a NOTES.md file, this simple pattern allows the agent to track progress across complex tasks, maintaining critical context and dependencies that would otherwise be lost across dozens of tool calls."
- "After context resets, the agent reads its own notes and continues multi-hour training sequences or dungeon explorations."
- "In Claude Code, for example, we implement this by passing the message history to the model to summarize and compress the most critical details. The model preserves architectural decisions, unresolved bugs, and implementation details while discarding redundant tool outputs or messages."
- "Start by maximizing recall to ensure your compaction prompt captures every relevant piece of information from the trace, then iterate to improve precision by eliminating superfluous content."
- "Each subagent might explore extensively, using tens of thousands of tokens or more, but returns only a condensed, distilled summary of its work (often 1,000-2,000 tokens)."

## このタスクでの使いどころ（使わなかったなら理由）
公式が「メモの外部化（structured note-taking）」と「compaction はまず recall 最大化→precision」を推奨している根拠。セッション末尾の自動振り返りそのものには触れていない。数字はサブエージェント要約の 1,000-2,000 tokens のみで、レトロの効果測定ではない。

## 原文（改変しない）
原文: [20260909_0040_Effective_context_engineering_for_AI_age.orig.md](20260909_0040_Effective_context_engineering_for_AI_age.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
