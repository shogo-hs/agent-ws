---
title: "MCPMark v2: InsForge on Sonnet 4.6"
kind: web
source: "https://insforge.dev/blog/mcpmark-benchmark-results-v2"
via: jina
retrieved_at: 2026-09-08T23:39:21+09:00
retrieved_by: unknown
summary: "MCPMark v2 の Postgres 21 タスク × 4 走で InsForge MCP が Supabase MCP 比 2.4 倍少ないトークン。InsForge 自身が測ったベンダー計測"
---
# MCPMark v2: InsForge on Sonnet 4.6

## 引用した記述（原文のまま。要約しない）
- Same 21 MCPMark Postgres tasks, 4 runs per task, strict Pass⁴ scoring.
- | Tokens Per Run | 7.3M | 17.9M |
- With Sonnet 4.5, InsForge used approximately 30% fewer tokens than Supabase MCP (8.2M vs 11.6M per run). With Sonnet 4.6, the gap has grown to 59% fewer tokens (7.3M vs 17.9M per run).

## このタスクでの使いどころ（使わなかったなら理由）
0013 の「第三者ベンチ」の行。InsForge 自身の計測でバックエンド MCP 同士の比較なので、MCP を持たない agent-ws には当てはまらないと判定した

## 原文（改変しない）
原文: [20260908_2339_MCPMark_v2_InsForge_on_Sonnet_4.6.orig.md](20260908_2339_MCPMark_v2_InsForge_on_Sonnet_4.6.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
