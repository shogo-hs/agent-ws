---
title: "domainIncludes - Schema.org Property"
kind: web
source: "https://schema.org/domainIncludes"
via: jina
retrieved_at: 2026-09-17T23:06:01+09:00
retrieved_by: unknown
summary: "schema:domainIncludes。推論を起こさない意図した定義域の注釈"
---
# domainIncludes - Schema.org Property

## 引用した記述（原文のまま。要約しない）
- "Relates a property to a class that is (one of) the type(s) the property is expected to be used on."

## このタスクでの使いどころ（使わなかったなら理由）
`scripts/wsonto/README.md` の `export.py` の同じ設計判断（`schema:domainIncludes` / `schema:rangeIncludes` を使う）の根拠のうち domainIncludes 側。rangeIncludes 側と同様、このページ自体には「推論を起こさない」という利点の明記は無い。schema.org の語彙が rdfs:domain/range の代わりとして存在することの裏付けであり、「推論を起こさない」という結論は `tests/test_onto_w3c.py` の実測（下記）に基づく。

## 原文（改変しない）
原文: [20260917_2306_domainIncludes_-_Schema.org_Property.orig.md](20260917_2306_domainIncludes_-_Schema.org_Property.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
