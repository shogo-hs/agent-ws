---
title: "rangeIncludes - Schema.org Property"
kind: web
source: "https://schema.org/rangeIncludes"
via: jina
retrieved_at: 2026-09-17T23:05:56+09:00
retrieved_by: unknown
summary: "schema:rangeIncludes。推論を起こさない意図した範囲の注釈"
---
# rangeIncludes - Schema.org Property

## 引用した記述（原文のまま。要約しない）
- "Relates a property to a class that constitutes (one of) the expected type(s) for values of the property."

## このタスクでの使いどころ（使わなかったなら理由）
`scripts/wsonto/README.md` の `export.py` にある「両端は `rdfs:domain` / `rdfs:range` では書かず、`schema:domainIncludes` / `schema:rangeIncludes`（推論を起こさない注釈）で書く」の根拠のうち rangeIncludes 側。ページの定義文自体は「値として期待される型を示す」という関係の説明にとどまり、「RDFS 推論を起こさない」という設計上の利点はこのページには明記されていない（`tests/test_onto_w3c.py` の実測で確かめた事実）。schema.org は RDFS の `rdfs:range` と違って推論規則ではなく注釈として設計されているという判断は、`rdfs:range` を使っていた頃に RDFS 推論つきの検査で型違いのリンク先に型が付いた実測（下記「このリポジトリで実測したこと」）が直接の根拠で、この一次資料はその代替先として `domainIncludes`/`rangeIncludes` という語彙が存在することの裏付けとして使った。

## 原文（改変しない）
原文: [20260917_2305_rangeIncludes_-_Schema.org_Property.orig.md](20260917_2305_rangeIncludes_-_Schema.org_Property.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
