---
title: "GitHub - gura105/operational-ontology: A minimal, readable reference implementation of the Operational Ontology pattern. Palantir Foundry is one implementation; this is the concept, minimized."
kind: web
source: "https://github.com/gura105/operational-ontology"
via: jina
retrieved_at: 2026-09-08T23:46:01+09:00
retrieved_by: unknown
summary: "Palantir 型（オブジェクト・リンク・アクション）のミニ実装。Zod+SQLite+MCP、フォークして使う前提"
---
# GitHub - gura105/operational-ontology: A minimal, readable reference implementation of the Operational Ontology pattern. Palantir Foundry is one implementation; this is the concept, minimized.

## 引用した記述（原文のまま。要約しない）
- "It exists to make the definition precise and runnable; it is not a framework. Fork it and reuse the ideas."
- "**Semantic objects and links.** Business entities and their relationships are modeled explicitly, on top of physical data that existed first and that other systems own."
- "**Action-gated writes.** A business decision changes state only through a named action. There is no generic update path — not for a user, not for an application, not for an agent."
- "**Business rules live in the ontology, not in the prompt.**"
- "**The same preconditions that gate humans gate agents.**"
- "**Why not OWL/RDF?** Those model what things _are_ (semantic). Half of this pattern is what you can _do_ (kinetic): actions, preconditions, audit, write-back. A reasoner cannot cancel an order."
- "**No npm package.** Fork it; don't depend on it."
- "Built and verified with Node 24, better-sqlite3, zod 4, MCP SDK 1.29."

## このタスクでの使いどころ（使わなかったなら理由）
ADR 0014 の「理由」と「捨てた案」。このパターンの前提が「他システムが持つ統合済みの物理データ」と「名前の付いた書き込みアクション」であることの根拠。agent-ws のエージェントは案件データへ書き込むアクションを持たず、書くのは文書なので、precondition が止める対象が無いと判定した。導入するなら Node・pnpm・SQLite を足すことになる点も同じ出典。

## 原文（改変しない）
原文: [20260908_2346_GitHub_-_gura105_operational-ontology_A_.orig.md](20260908_2346_GitHub_-_gura105_operational-ontology_A_.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
