---
title: beta
summary: "BETA 社のデータ基盤をオンプレ DWH から Redshift + dbt + Airflow に刷新する支援（内容はすべて架空）"
created: 2026-08-18
---
# beta

## 概要
顧客は BETA 社（架空）。オンプレの DWH（240 テーブル・12 TB）を Redshift に移し、変換を dbt、スケジュールを Airflow に置き換える。
責任者は高橋、データ担当は伊藤と渡辺。自社側は田中。期間は 2026-09 から 2027-02。

## この案件での決まりごと
- 定例は隔週木曜 14:00。
- SQL の書き直しは dbt のモデル単位で PR を出す。
- 個人情報を含む列は mart に置かない。

## 中身
<!-- ws:index -->
- [knowledges/](knowledges/index.md) — この案件のナレッジの正本。タスクで得た知見はここに昇格する
- [tasks/](tasks/index.md) — この案件のタスク。作業中は自分のタスクだけを見る
<!-- /ws:index -->
