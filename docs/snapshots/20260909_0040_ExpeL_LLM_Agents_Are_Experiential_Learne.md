---
title: "ExpeL: LLM Agents Are Experiential Learners"
kind: web
source: "https://arxiv.org/html/2308.10144"
via: jina
retrieved_at: 2026-09-09T00:40:38+09:00
retrieved_by: unknown
summary: "ExpeL: 成功/失敗の経験から自然言語の insight を抽出して蓄積する"
---
# ExpeL: LLM Agents Are Experiential Learners

## 引用した記述（原文のまま。要約しない）
- (§4.2) "The operations the LLM can perform are: ADD a new insight, EDIT the content of an existing insight, DOWNVOTE to disagree with an existing insight, or UPVOTE to agree with an existing insight. A newly added insight will have an initial importance count of two associated with it, and the count will increment if subsequent operators UPVOTE or EDIT are applied to it and will decrement when DOWNVOTE is applied to it. If an insight's importance count reaches zero, it will be removed. This particular design choice robustifies the process since even successful trajectories can be suboptimal and mislead the generated insights."
- (§4.2) "We empirically found that gpt-4-0613 is better than gpt-3.5-turbo-0613 at following instructions on how to use the insight extraction operators and hallucinated less."
- (§4.3) "the task specifications will be augmented with the concatenation of the full list of extracted insights"
- (§5.2) "When restricting the ExpeL agent to only one mode of learning (insights-only or retrieval-only), HotpotQA and ALFWorld environments demonstrate contrasting quantitative distinctions (36%/31% and 50%/55% for HotpotQA and ALFWorld, respectively)."
- (§5.2) "ExpeL matches Reflexion's performance (40% at R3 vs. 39%) for HotpotQA and even outperforms it for ALFWorld (54% at R3 vs. 59%) without repeated attempts."
- (§5.4 Ablation) "(1) learned insights by the agent are more advantageous than hand-crafted ones; (2) using reflections in addition to success/failure pairs and lists of successes is disadvantageous, possibly due to reflections sometimes outputting hallucinations, therefore misleading the insight extraction stage; and (3) a better LLM is more advantageous"
- (Table 3 caption) "Hand-crafted insights enjoyed a performance boost over ReAct but were less effective than LLM-generated ones. Furthermore, adding reflections to the insight-generating process hurt performance."
- (§D.2) "We employ four-fold validation for all experiments. We train on one half of the dataset and evaluate on the other half" / HotpotQA は 100 validation tasks

## このタスクでの使いどころ（使わなかったなら理由）
「経験からルール（insight）を抽出して規約に足す」を最も直接やっている論文。ルールに importance count を持たせ、DOWNVOTE で 0 になったら消す、という「増え続けない」仕組みが個人のハーネスにそのまま移せる。ただし成功/失敗の判定は環境報酬（HotpotQA の正誤・ALFWorld の完了）に依存し、さらに「Reflexion の反省文を insight 抽出に混ぜると幻覚で劣化した」と自己反省ベースの入力に否定的な結果を出している。

## 原文（改変しない）
原文: [20260909_0040_ExpeL_LLM_Agents_Are_Experiential_Learne.orig.md](20260909_0040_ExpeL_LLM_Agents_Are_Experiential_Learne.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
