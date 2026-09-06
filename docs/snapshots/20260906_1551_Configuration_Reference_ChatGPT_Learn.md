---
title: "Configuration Reference | ChatGPT Learn"
kind: web
source: "https://learn.chatgpt.com/docs/config-file/config-reference"
via: jina
retrieved_at: 2026-09-06T15:51:19+09:00
retrieved_by: unknown
summary: "Codex CLI の設定一覧。compact_prompt は要約指示の全文上書き、tool_output_token_limit、agents の既定モデル"
---
# Configuration Reference | ChatGPT Learn

## 引用した記述（原文のまま。要約しない）
- | `compact_prompt` | `string` | Inline override for the history compaction prompt. |
- | `model_auto_compact_token_limit` | `number` | Token threshold that triggers automatic history compaction (unset uses model defaults). |
- | `tool_output_token_limit` | `number` | Token budget for storing individual tool/function outputs in history. |

## このタスクでの使いどころ（使わなかったなら理由）
採らなかった案の根拠。compact_prompt は要約プロンプトの全文上書きなので、AGENTS.md の節で両ツール共通にした。
（第 6 弾）README「セッションの切り方」の Codex 側の調整ノブ（自動 compact のしきい値・tool 出力の予算）。agent-ws は既定を変えない。

## 原文（改変しない）
原文: [20260906_1551_Configuration_Reference_ChatGPT_Learn.orig.md](20260906_1551_Configuration_Reference_ChatGPT_Learn.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
