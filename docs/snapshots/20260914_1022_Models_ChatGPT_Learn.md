---
title: "Models | ChatGPT Learn"
kind: web
source: "https://learn.chatgpt.com/codex/models"
via: jina
retrieved_at: 2026-09-14T10:22:03+09:00
retrieved_by: unknown
summary: "Codex で使えるモデル一覧（ChatGPT アカウントでの提供）"
---
# Models | ChatGPT Learn

## 引用した記述（原文のまま。要約しない）
- "**GPT-5.4 and GPT-5.4 mini retire from Codex on August 31, 2026.**"
- "If you sign in with ChatGPT, replace `gpt-5.4` with `gpt-5.6-terra` and `gpt-5.4-mini` with `gpt-5.6-luna` in saved configurations, custom agents, and scheduled tasks. The OpenAI API and Codex authenticated with your own API key aren't affected."
- "**Luna, for clear, repeatable tasks.** Choose Luna for specific, high-volume tasks when you know what a good result looks like, such as extraction, classification, transformation, and structured summaries."
- "Use the lowest reasoning effort that produces the result you need. Increase it for tasks that need more planning, analysis, or checking."
- "**Max** gives the selected model more time to reason about a single task. Use it for the hardest problems, when depth matters more than speed or usage."
- "Most tasks do not need Max or Ultra."

## このタスクでの使いどころ（使わなかったなら理由）
ADR 0020 の「gpt-5.4-mini → gpt-5.6-luna」の直接の根拠（公式の置き換え指示。ChatGPT ログインだけが対象で API キーは無関係）。推論量は「必要な結果が出る最低」で選ぶという物差し。bench で low は必要な結果（全件の抽出）を出せず、max だけが決定を落とさなかったので、この物差しどおり max を採った。「Max は最難問向け」「ほとんどの仕事に要らない」は一般論として残す。

## 原文（改変しない）
原文: [20260914_1022_Models_ChatGPT_Learn.orig.md](20260914_1022_Models_ChatGPT_Learn.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
