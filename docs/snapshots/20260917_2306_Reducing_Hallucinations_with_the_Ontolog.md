---
title: "Reducing Hallucinations with the Ontology in Palantir AIP (Engineering Responsible AI , #1)"
kind: web
source: "https://blog.palantir.com/reducing-hallucinations-with-the-ontology-in-palantir-aip-288552477383"
via: jina
retrieved_at: 2026-09-17T23:06:14+09:00
retrieved_by: unknown
summary: "ハルシネーション対策の3段（データで接地・不得手な計算は関数へ・提案は承認待ちに積む）"
---
# Reducing Hallucinations with the Ontology in Palantir AIP (Engineering Responsible AI , #1)

## 引用した記述（原文のまま。要約しない）
- "In practice, this means allowing the model to request data directly from the Ontology to add to the information in the original prompt."
- "it’s not always the right tool for more complex tasks like solving equations, forecasting, or running simulations, which are better handled with purpose-built models or functions."
- "Instead of directly taking the suggested reallocation or substitution action and writing that back to an external system, AIP Logic can instead _queue up_ a suggested reallocation proposal for approval."
- "These three approaches — building on the data, logic, and actions of your Ontology — can reduce the likelihood and impact of hallucinations"

## このタスクでの使いどころ（使わなかったなら理由）
`scripts/wsonto/README.md` 全体の設計思想（データで接地する `query`/`show`、計算は `expr.py` の許可リスト式評価に閉じる、書き込みは `engine.act` が実行待ちに積む）の三段構えの根拠。データで接地・不得手な計算は関数（wsonto では許可された式のみ評価する `expr.py`）へ・提案は承認待ちに積む、の 3 段がそのまま wsonto の照会・式評価・アクション実行待ちの 3 つの層に対応する。

## 原文（改変しない）
原文: [20260917_2306_Reducing_Hallucinations_with_the_Ontolog.orig.md](20260917_2306_Reducing_Hallucinations_with_the_Ontolog.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
