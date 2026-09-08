---
title: "Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models"
kind: web
source: "https://arxiv.org/html/2510.04618"
via: jina
retrieved_at: 2026-09-09T00:40:15+09:00
retrieved_by: unknown
summary: "ACE: 進化するコンテキストで context collapse / brevity bias を回避する手法"
---
# Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models

## 引用した記述（原文のまま。要約しない）
- (§1) "Second, context collapse: methods that rely on monolithic rewriting by an LLM often degrade into shorter, less informative summaries over time, causing sharp performance declines (Figure 2)."
- (§2.2 Brevity Bias) "A recurring limitation of context adaptation methods is brevity bias: the tendency of optimization to collapse toward short, generic prompts. Gao et al. (2025) document this effect in prompt optimization for test generation, where iterative methods repeatedly produced near-identical instructions (e.g., 'Create unit tests to ensure methods behave as expected'), sacrificing diversity and omitting domain-specific detail."
- (§2.2 Context Collapse) "For instance, at step 60 the context contained 18,282 tokens and achieved an accuracy of 66.7, but at the very next step it collapsed to just 122 tokens, with accuracy dropping to 57.1—worse than the baseline accuracy of 63.7 without adaptation. While we highlight this through Dynamic Cheatsheet (Suzgun et al., 2025), the issue is not specific to that method; rather, it reflects a fundamental risk of end-to-end context rewriting with LLMs, where accumulated knowledge can be abruptly erased instead of preserved."
- (§3) "ACE adopts an agentic architecture with three specialized components: a Generator, a Reflector, and a Curator." / "Rather than regenerating contexts in full, ACE incrementally produces compact delta contexts: small sets of candidate bullets distilled by the Reflector and integrated by the Curator."
- (§3.2) "In grow-and-refine, bullets with new identifiers are appended, while existing bullets are updated in place (e.g., incrementing counters). A de-duplication step then prunes redundancy by comparing bullets via semantic embeddings."
- (Table 1, AppWorld, DeepSeek-V3.1) ReAct 42.4 (avg) → ReAct + ACE (offline, GT labels ✓) 59.4 (+17.0) / ReAct + ACE (offline, GT labels ✗) 57.2 (+14.8) / ReAct + ACE (online, ✗) 59.5 (+17.1)
- (§4.3) "ACE remains effective even without access to ground-truth labels during adaptation: ReAct + ACE achieves an average improvement of 14.8% over the ReAct baseline in this setting. This robustness arises because ACE leverages signals naturally available during execution (e.g., code execution success or failure)"
- (§4.4) "when ground-truth supervision or reliable execution signals are absent, both ACE and DC may degrade in performance. In such cases, the constructed context can be polluted by spurious or misleading signals, highlighting a potential limitation of inference-time adaptation without reliable feedback."
- (§4.6) "ACE is robust to reflection quality: it remains effective with a much weaker Reflector and shows only modest additional gains from stronger reflectors, and it degrades gracefully under noisy/harmful reflections, staying above the base model except under fully adversarial updates every iteration."
- (§4.7) "ACE achieves 82.3% reduction in adaptation latency and 75.1% reduction in the number of rollouts as compared to GEPA" / "reducing adaptation latency by 86.9% on average"
- (§5 Limitations) "A limitation of ACE is its reliance on a reasonably strong Reflector: if the Reflector fails to extract meaningful insights from generated traces or outcomes, the constructed context may become noisy or even harmful." / "We also note that not all applications require rich or detailed contexts. Tasks like HotPotQA often benefit more from concise, high-level instructions"
- (§A.5) "We find that incremental updates are critical: by preserving useful information that would otherwise be lost to context collapse, they account for a large share of ACE's gains."

## このタスクでの使いどころ（使わなかったなら理由）
「セッション末に規約ファイルを LLM に全文書き直させる」設計の最大リスク（context collapse: 18,282→122 トークン、精度がベースライン以下へ）と、その回避策（差分追記＋カウンタ更新＋埋め込み de-dup、生成/反省/整理の役割分離）の一次資料。ラベル無しでも実行フィードバック（コード実行の成否）があれば +14.8 だが、「信頼できる信号が無いと文脈が汚染されて劣化しうる」と自ら限界を書いているので、個人環境で「人の指摘」以外の信号が無い場面はこの限界側に当たる。

## 原文（改変しない）
原文: [20260909_0040_Agentic_Context_Engineering_Evolving_Con.orig.md](20260909_0040_Agentic_Context_Engineering_Evolving_Con.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
