---
title: "Building Effective AI Agents"
kind: web
source: "https://www.anthropic.com/research/building-effective-agents"
via: jina
retrieved_at: 2026-09-17T23:06:06+09:00
retrieved_by: unknown
summary: "ツールの設計（データ照会と行為の分離）、チェックポイントで人のフィードバックを待つ設計"
---
# Building Effective AI Agents

## 引用した記述（原文のまま。要約しない）
- "Tools can be integrated to pull customer data, order history, and knowledge base articles;"
- "Actions such as issuing refunds or updating tickets can be handled programmatically; and"
- "Agents can then pause for human feedback at checkpoints or when encountering blockers."

## このタスクでの使いどころ（使わなかったなら理由）
`scripts/wsonto/README.md` のツールの二分（`query.py`/`show`＝データを引くだけの照会と、`engine.act`＝案件データを変えるアクション）の設計の裏付け。顧客データや注文履歴を「引く」ツールと、返金やチケット更新のような「変える」アクションを区別している記述が、wsonto の照会系（読むだけ）とアクション系（`objects.json` を書き換え、承認要否がある）を分けた設計に対応する。「チェックポイントで人のフィードバックを待つ」は、`engine.act` が `stage`/`stage_if` のときに実行待ちへ積んで人の承認を待つ設計の一般的な裏付け。

## 原文（改変しない）
原文: [20260917_2306_Building_Effective_AI_Agents.orig.md](20260917_2306_Building_Effective_AI_Agents.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
