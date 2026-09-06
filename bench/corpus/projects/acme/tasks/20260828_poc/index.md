---
title: "PoC 環境の構築と負荷試験"
status: done
project: acme
created: 2026-08-28
updated: 2026-08-29
summary: "Terraform で EKS の PoC 環境を作り、受注管理 API の負荷試験でノード数を確定した（12）"
---
# PoC 環境の構築と負荷試験

## 目的
PoC 環境で負荷試験を行い、本番のノード数を確定する。結果を移行方針としてナレッジに昇格する。

## 進め方
- [x] 手順書に沿って PoC 環境を作る
- [x] 8 / 10 / 12 ノードで負荷試験を行う
- [x] 結果を knowledges/003_PoC結果.md に昇格する
- [x] 移行方針（knowledges/001_移行方針.md）のノード数を 12 に更新する

## 現在地
完了。ノード数 12 で目標達成。移行方針を更新済み。

## 次の一手
（完了）

## 参照したナレッジ
- knowledges/001_移行方針.md
- knowledges/003_PoC結果.md

## 未確定の用語
（なし）

## 情報源（references/）
<!-- ws:index -->
- [references/20260828_0900_PoC手順書.md](references/20260828_0900_PoC手順書.md) — Terraform で EKS を作り、負荷試験を流すまでの手順
- [references/20260829_1700_負荷試験結果.md](references/20260829_1700_負荷試験結果.md) — 8 / 10 / 12 ノードの p95 レイテンシ。12 ノードで目標達成
- [references/20260829_1800_2026-08-29_PoC報告会_文字起こし.md](references/20260829_1800_2026-08-29_PoC報告会_文字起こし.md) — PoC 報告会の文字起こし（架空）。ノード数を 12 に見直すことで合意
- [references/20260829_1800_2026-08-29_PoC報告会_文字起こし.normalized.md](references/20260829_1800_2026-08-29_PoC報告会_文字起こし.normalized.md) — PoC 報告会の文字起こし（用語集で正規化）。ノード数を 12 に見直すことで合意
<!-- /ws:index -->
