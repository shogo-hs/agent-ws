---
title: "Using GPT-6 | OpenAI API"
kind: web
source: "https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6"
via: jina
retrieved_at: 2026-10-03T08:25:31+09:00
retrieved_by: unknown
summary: "GPT-5.6 のモデルガイダンス（effort・verbosity・簡潔さ）"
---
# Using GPT-6 | OpenAI API

## 引用した記述（原文のまま。要約しない）
- In a sample of internal coding-agent eval runs, configurations with leaner system prompts improved evaluation scores by roughly 10–15% while reducing total tokens by 41–66% and cost by 33–67%.
- State each instruction once.
- GPT-5.6 tends to be more concise by default than GPT-5.5.
- Use `medium` as a balanced starting point and `low` for latency-sensitive workloads.
- test the same setting and one level lower on representative tasks

## このタスクでの使いどころ（使わなかったなら理由）
AGENTS.md を削って測る採用候補の根拠。effort は既存の調整ノブ（ADR 0021）を裏づける。URL は prompt-guidance-gpt-5p6 だがページ題名は Using GPT-6。

## 原文（改変しない）
原文: [20261003_0825_Using_GPT-6_OpenAI_API.orig.md](20261003_0825_Using_GPT-6_OpenAI_API.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
