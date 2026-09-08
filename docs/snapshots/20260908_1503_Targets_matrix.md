---
title: "Targets matrix"
kind: web
source: "https://microsoft.github.io/apm/reference/targets-matrix/"
via: jina
retrieved_at: 2026-09-08T15:03:20+09:00
retrieved_by: unknown
summary: "APM のプリミティブ×ハーネス対応表。skills だけが全ハーネス native、Codex は instructions/prompts/commands 非対応"
---
# Targets matrix

## 引用した記述（原文のまま。要約しない）
- `| claude | `.claude/` | [x] | [ ] | [x] | [x] | [x] | [x] | [x] |`（列は instructions / prompts / agents / skills / commands / hooks / mcp）
- `| codex | `.codex/` + `.agents/` | [ ] | [ ] | [x] | [x] | [ ] | [x] | [x] |`
- Skills deploy to `.agents/skills/` for Copilot, Cursor, OpenCode, Gemini, Antigravity, Codex, Hermes project scope, and Windsurf by default (...). Claude, Grok Build, Kiro, and Hermes user scope keep target-native skill directories.
- **Compile output.** `AGENTS.md` only. Per-file instructions are not installed for Codex.

## このタスクでの使いどころ（使わなかったなら理由）
APM 移管の可否判定（kanban T-6PJJT）の対応表の根拠。この表から、agent-ws が使う2ハーネスでは
hooks と agents と skills は両方に配れるが、instructions は Codex に配れず `AGENTS.md` 経由でしか
届かないと判定した。また skills の収束から外れる Claude だけが `.claude/skills/` に実体コピーされるため、
いまの「`.agents/skills/` が実体・Claude は symlink」という単一正本が、移管すると両ハーネスに
1部ずつのコピーに変わることが分かった（移管しない理由の1つ）。

## 原文（改変しない）
原文: [20260908_1503_Targets_matrix.orig.md](20260908_1503_Targets_matrix.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
