---
title: ナレッジ
summary: この案件のナレッジの正本。タスクで得た知見はここに昇格する
---
# ナレッジ（beta）

このフォルダが案件のナレッジの正本。tasks/ の中に知見を溜めない。
用語集は glossary.md。文字起こしを読む前に `scripts/ws transcript normalize` が参照する。

<!-- ws:index -->
- [001_基盤構成.md](001_基盤構成.md) [complete] — Redshift ra3.xlplus × 4 ノード（仮）、S3、dbt、Airflow。レイヤーは raw / staging / mart
- [002_関係者.md](002_関係者.md) [complete] — 高橋（責任者）、伊藤・渡辺（データ担当）、田中（自社）
- [glossary.md](glossary.md) — この案件の固有名詞・略語・表記ゆれ・文字起こしの誤変換。scripts/ws transcript normalize が置換に使う
<!-- /ws:index -->
