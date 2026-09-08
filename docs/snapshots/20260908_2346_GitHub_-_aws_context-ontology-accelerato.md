---
title: "GitHub - aws/context-ontology-accelerator: An open-source, ontology-based semantic context accelerator that enables AI agents to make more accurate, consistent, and explainable decisions."
kind: web
source: "https://github.com/aws/context-ontology-accelerator"
via: jina
retrieved_at: 2026-09-08T23:46:56+09:00
retrieved_by: unknown
summary: "AWS の Scan→Model→Serve 型オントロジー基盤（Python・Apache-2.0）。Neptune+OpenSearch でアイドル約930ドル/月"
---
# GitHub - aws/context-ontology-accelerator: An open-source, ontology-based semantic context accelerator that enables AI agents to make more accurate, consistent, and explainable decisions.

## 引用した記述（原文のまま。要約しない）
- "An open-source semantic context layer for AWS that combines knowledge graphs, formal ontologies, and rule-based systems with modern AI — enabling agents to retrieve context, validate it against business logic, and determine correct actions."
- "The system follows a **Scan → Model → Serve** workflow:"
- "**Scan** — Connect data sources, discover schemas, enrich metadata, ingest unstructured documents"
- "**Model** — Induce and manage ontologies, define metrics, build a unified semantic graph"
- "**Serve** — Query via SPARQL federation (VKG), traverse the knowledge graph, serve context to AI agents via MCP"
- "Python 3.12, Node.js 22+, Docker" / "Java 17+ and Gradle (for Smithy codegen)"

## このタスクでの使いどころ（使わなかったなら理由）
ADR 0014 の「捨てた案」。本番向け基盤（Neptune・OIDC・Smithy）で、1 人の案件フォルダには過大だと判定した根拠。記事にあるコスト警告（アイドルで約 930 ドル/月）はこの README には無く、記事の引用に依っている。

## 原文（改変しない）
原文: [20260908_2346_GitHub_-_aws_context-ontology-accelerato.orig.md](20260908_2346_GitHub_-_aws_context-ontology-accelerato.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
