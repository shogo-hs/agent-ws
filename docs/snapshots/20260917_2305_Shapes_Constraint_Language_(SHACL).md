---
title: "Shapes Constraint Language (SHACL)"
kind: web
source: "https://www.w3.org/TR/shacl/"
via: jina
retrieved_at: 2026-09-17T23:05:50+09:00
retrieved_by: unknown
summary: "SHACL 仕様。sh:closed・sh:class・sh:minCount/maxCount・sh:in・sh:inversePath・sh:targetClass の定義"
---
# Shapes Constraint Language (SHACL)

## 引用した記述（原文のまま。要約しない）
- "The SHACL Core language includes a property called `sh:closed` that can be used to specify the condition that each value node has [values](https://www.w3.org/TR/shacl/#dfn-value) only for those properties that have been explicitly enumerated via the [property shapes](https://www.w3.org/TR/shacl/#dfn-property-shape) specified for the shape via `sh:property`."
- "The condition specified by `sh:class` is that each [value node](https://www.w3.org/TR/shacl/#dfn-value-nodes) is a [SHACL instance](https://www.w3.org/TR/shacl/#dfn-shacl-instance) of a given type."
- "A [node](https://www.w3.org/TR/shacl/#dfn-node)`n` in an [RDF graph](https://www.w3.org/TR/shacl/#dfn-rdf-graph)`G` is a SHACL instance of a [SHACL class](https://www.w3.org/TR/shacl/#dfn-shacl-class)`C` in `G` if one of the [SHACL types](https://www.w3.org/TR/shacl/#dfn-shacl-types) of `n` in `G` is `C`." （SPARQL では `$value rdf:type/rdfs:subClassOf* $class .`）
- "`sh:minCount` specifies the minimum number of [value nodes](https://www.w3.org/TR/shacl/#dfn-value-nodes) that satisfy the condition."

## このタスクでの使いどころ（使わなかったなら理由）
`scripts/wsonto/README.md` の `validate.py`（SHACL Core の部分集合、閉世界）と `export.py` の Turtle 書き出しの直接の仕様根拠。`CLOSED`（`sh:closed`）・`CLASS`（`sh:class`）・`MIN_COUNT`/`MAX_COUNT`（`sh:minCount`/`sh:maxCount`）・`IN`（`sh:in`）の各 code は、この仕様の該当コンポーネントに 1 対 1 で対応する。「SHACL instance は `rdf:type` とその SHACL superclass（`rdfs:subClassOf*` で辿る）で決まる」という定義が、`sh:targetClass` が下位の型の実体にも当たること、および `to_turtle` の `sh:targetClass` の ignoredProperties を上位の型の形に足す設計の根拠になっている。

## 原文（改変しない）
原文: [20260917_2305_Shapes_Constraint_Language_(SHACL).orig.md](20260917_2305_Shapes_Constraint_Language_(SHACL).orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
