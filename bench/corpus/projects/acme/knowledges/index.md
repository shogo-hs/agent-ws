---
title: ナレッジ
summary: この案件のナレッジの正本。タスクで得た知見はここに昇格する
---
# ナレッジ（acme）

このフォルダが案件のナレッジの正本。tasks/ の中に知見を溜めない。
用語集は glossary.md。文字起こしを読む前に `scripts/ws transcript normalize` が参照する。

<!-- ws:index -->
- [001_移行方針.md](001_移行方針.md) [complete] — 移行先は EKS（東京）。ワーカーノードは 12 台（キックオフ時点の 8 台から PoC の負荷試験の結果で見直し）。m6i.xlarge 相当。期間 6 ヶ月
- [002_関係者.md](002_関係者.md) [complete] — 顧客側 PM 山田太郎、インフラ 佐藤、アプリ 鈴木。自社側は田中
- [003_PoC結果.md](003_PoC結果.md) [complete] — 受注管理 API の負荷試験。8 ノード 820 ms・10 ノード 610 ms は目標未達、12 ノード 430 ms で達成
- [glossary.md](glossary.md) — この案件の固有名詞・略語・表記ゆれ・文字起こしの誤変換。scripts/ws transcript normalize が置換に使う
<!-- /ws:index -->
