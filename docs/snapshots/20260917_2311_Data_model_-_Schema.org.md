---
title: "Data model - Schema.org"
kind: web
source: "https://schema.org/docs/datamodel.html"
via: jina
retrieved_at: 2026-09-17T23:11:02+09:00
retrieved_by: unknown
summary: "schema.org のデータモデル。プロパティに複数の domain / range を許した理由（実用上の判断。単一だと人工的な型が増える）"
---
# Data model - Schema.org

## 引用した記述（原文のまま。要約しない）
> each property may have one or more types as its domains. The property may be used for instances of any of these types.
> each property may have one or more types as its ranges. The value(s) of the property should be instances of at least one of these types.
> The decision to allow multiple domains and ranges was purely pragmatic. While the computational properties of systems with a single domain and range are easier to understand, in practice, this forces the creation of a lot of artificial types, which are there purely to act as the domain/range of some properties.

## このタスクでの使いどころ（使わなかったなら理由）
`scripts/wsonto/README.md` の `export.py`（語彙の両端を `schema:domainIncludes` / `schema:rangeIncludes` で書く）の根拠のうち、schema.org 側の事情。schema.org が複数の domain / range を許したのは「実用上の判断」で、単一の domain / range だと人工的な型が増えるから、と書いている。**「RDFS の推論を避けるため」とは書いていない。** 推論つきの検査で `rdfs:range` が `sh:class` を無効にすることは、このリポジトリの `tests/test_onto_w3c.py` で実測したことで、この出典の主張ではない。

## 原文（改変しない）
原文: [20260917_2311_Data_model_-_Schema.org.orig.md](20260917_2311_Data_model_-_Schema.org.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
