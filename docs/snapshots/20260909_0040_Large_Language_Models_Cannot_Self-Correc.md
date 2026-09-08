---
title: "Large Language Models Cannot Self-Correct Reasoning Yet"
kind: web
source: "https://arxiv.org/html/2310.01798"
via: jina
retrieved_at: 2026-09-09T00:40:51+09:00
retrieved_by: unknown
summary: "LLM は外部フィードバック無しの自己修正で推論性能を上げられない（むしろ下がる）"
---
# Large Language Models Cannot Self-Correct Reasoning Yet

## 引用した記述（原文のまま。要約しない）
- (Abstract) "In the context of reasoning, our research indicates that LLMs struggle to self-correct their responses without external feedback, and at times, their performance even degrades after self-correction."
- (§1) "we first define the concept of intrinsic self-correction, a scenario wherein the model endeavors to rectify its initial responses based solely on its inherent capabilities, without the crutch of external feedback. Such a setting is crucial because high-quality external feedback is often unavailable in many real-world applications."
- (§1) "Kim et al. (2023); Shinn et al. (2023) use oracle labels about the answer correctness to guide the self-correction process" ／ "We demonstrate that existing techniques actually decrease reasoning performance when oracle labels are not used (Section 3)"
- (§3.1) GSM8K test 1,319 問 / CommonSenseQA dev 1,221 問 / HotpotQA 100 問（Shinn et al. と同じセット）。GPT-3.5-Turbo (0613), GPT-4, GPT-4-Turbo (1106), Llama-2-70b-chat
- (§3.2) "we use the correct label to determine when to stop the self-correction loop. ... If the answer is already correct, no (further) self-correction will be performed." / "If we are already in possession of the ground truth, there seems to be little reason to deploy LLMs for problem-solving. Therefore, the results can only be regarded as indicative of an oracle's performance."
- (§3.2) "We observe that, after self-correction, the accuracies of all models drop across all benchmarks."
- (§3.2) "For GSM8K, 74.7% of the time, GPT-3.5 retains its initial answer. Among the remaining instances, the model is more likely to modify a correct answer to an incorrect one than to revise an incorrect answer to a correct one. The fundamental issue is that LLMs cannot properly judge the correctness of their reasoning."
- (§6) "several prior works have already shown that LLM self-correction performance becomes significantly weaker without access to external feedback (Gou et al., 2023; Zhou et al., 2023a) and can be easily biased by misleading feedback (Wang et al., 2023a)"

## このタスクでの使いどころ（使わなかったなら理由）
Reflexion 系の改善が「正解ラベルで止め時を決めている」ことを名指しで指摘した批判。外部フィードバック無しの自己評価は「正→誤」の書き換えのほうが多く、自分の推論の正しさを判定できない、と結論している。個人環境でセッション末に「今回の失敗は何か」を人の指摘無しにモデルに判定させる設計は、まさにこの intrinsic self-correction に当たる。

## 原文（改変しない）
原文: [20260909_0040_Large_Language_Models_Cannot_Self-Correc.orig.md](20260909_0040_Large_Language_Models_Cannot_Self-Correc.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
