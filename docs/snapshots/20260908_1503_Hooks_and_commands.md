---
title: "Hooks and commands"
kind: web
source: "https://microsoft.github.io/apm/producer/author-primitives/hooks-and-commands/"
via: jina
retrieved_at: 2026-09-08T15:03:17+09:00
retrieved_by: unknown
summary: "APM の hooks は移植性を装わないプリミティブで、主要な配布経路にするなと明記。出力先はハーネス別"
---
# Hooks and commands

## 引用した記述（原文のまま。要約しない）
- Hooks and slash commands are the two APM primitives that do not pretend to be portable. Unlike skills or instructions, they ship to a strict subset of harnesses, never get folded into `AGENTS.md`, and rely on each target’s own format.
- Neither generalizes: nothing reaches `AGENTS.md`, nothing routes to harnesses that lack the concept. Unsupported targets are silently skipped, not errors. Treat both as opt-in surface, not as your primary distribution path.
- The `${PLUGIN_ROOT}`, `${CLAUDE_PLUGIN_ROOT}`, and `${CURSOR_PLUGIN_ROOT}` tokens resolve to the installed package root and are rewritten per target.

## このタスクでの使いどころ（使わなかったなら理由）
APM 移管の可否判定（kanban T-6PJJT）で「移管しない」と結論づけた根拠の1つ。
hook が呼ぶスクリプトを `${PLUGIN_ROOT}` で同梱して配れること自体は確認できたので、
`scripts/ws` の配布は技術的に可能。ただし APM 自身が hooks を「主要な配布経路にするな」と
書いており、hook が仕組みの中心にある agent-ws（ADR 0001）とは前提が合わない。

## 原文（改変しない）
原文: [20260908_1503_Hooks_and_commands.orig.md](20260908_1503_Hooks_and_commands.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
