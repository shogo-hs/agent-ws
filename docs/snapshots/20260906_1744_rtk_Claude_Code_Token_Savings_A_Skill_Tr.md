---
title: "rtk Claude Code Token Savings: A Skill Trial Benchmark"
kind: web
source: "https://blog.jetbrains.com/ai/2026/07/rtk-claude-code-token-savings/"
via: jina
retrieved_at: 2026-09-06T17:44:40+09:00
retrieved_by: unknown
summary: "rtk を Claude Code の実タスクで A/B 計測したベンチマーク（JetBrains ブログ・第三者）"
---
# rtk Claude Code Token Savings: A Skill Trial Benchmark

## 引用した記述（原文のまま。要約しない）
- > **TL;DR: rtk advertised saving: 60–90%. Measured on real agent work: +7.6% more expensive at low reasoning effort (p=0.004), ±0% at high effort. Setup: Claude Code 2.1.201 · claude-sonnet-5 low and high efforts · SkillsBench. Task quality: unchanged in both arms, at both effort levels.**
- Only a fifth of what the model reads is even compressible by rtk. Squeeze all of it by 70% and the total saving still tops out around 3% of the bill.

## このタスクでの使いどころ（使わなかったなら理由）
第三者（JetBrains）の実測。Bash 出力を圧縮する hook を agent-ws に入れなかった根拠の一つ（圧縮できるのは読む量の 1/5、低 effort では費用が増えた、と JetBrains は報告している。agent-ws の材料で同じ結果になるかは測っていない）。

## 原文（改変しない）
原文: [20260906_1744_rtk_Claude_Code_Token_Savings_A_Skill_Tr.orig.md](20260906_1744_rtk_Claude_Code_Token_Savings_A_Skill_Tr.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
