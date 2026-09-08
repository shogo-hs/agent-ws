---
title: "Language Agents with Verbal Reinforcement Learning"
kind: web
source: "https://arxiv.org/html/2303.11366"
via: jina
retrieved_at: 2026-09-09T00:40:24+09:00
retrieved_by: unknown
summary: "Reflexion: 言語的な自己反省をエピソード記憶に残して次試行に活かす"
---
# Language Agents with Verbal Reinforcement Learning

## 引用した記述（原文のまま。要約しない）
- (Abstract) "Reflexion agents verbally reflect on task feedback signals, then maintain their own reflective text in an episodic memory buffer to induce better decision-making in subsequent trials." / "Reflexion achieves a 91% pass@1 accuracy on the HumanEval coding benchmark, surpassing the previous state-of-the-art GPT-4 that achieves 80%."
- (§1) "Reflexion converts binary or scalar feedback from the environment into verbal feedback in the form of a textual summary, which is then added as additional context for the LLM agent in the next episode."
- (§3) "Given a sparse reward signal, such as a binary success status (success/fail), the current trajectory, and its persistent memory mem, the self-reflection model generates nuanced and specific feedback."
- (§4.1 AlfWorld, 134 tasks) "ReAct + Reflexion significantly outperforms ReAct by completing 130 out of 134 tasks using the simple heuristic to detect hallucinations and inefficient planning. Further, ReAct + Reflexion learns to solve additional tasks by learning in 12 consecutive trials."
- (§4.2 HotPotQA, 100 questions) "between trials, we use exact match answer grading using the environment to give a binary success signal to the agent. After each trial, the self-reflection loop is employed to amplify the binary signal, similar to the decision-making setup 4.1 in AlfWorld with a memory size of 3 experiences."
- (§4.3) "We acknowledge that self-reflecting code-generation agents are bound to their ability to write diverse, comprehensive tests. Therefore, in the case in which the model generates a flaky test suite, it is possible that all tests pass on an incorrect solution and lead to a false positive label on a code completion"
- (§5 Limitations) "Policy optimization is a powerful approach to improve action choice through experience, but it may still succumb to non-optimal local minima solutions. In this study, we limit long-term memory to a sliding window with maximum capacity"
- (§B.1 WebShop) "after only four trials, we terminate the runs as the agent does not show signs of improvement. Further, the agent does not generate helpful, intuitive self-reflections after failed attempts. We conclude that Reflexion is unable to solve tasks that require a significant amount of diversity and exploration."

## このタスクでの使いどころ（使わなかったなら理由）
「振り返りをテキストで残して次に活かす」の原点。ただし全実験が環境からの二値/スカラー報酬（exact match・ユニットテスト・ヒューリスティック）を前提にしており、反省文はその信号を「増幅」するもの。メモリは最大3件のスライディング窓で、増え続けるルールの問題は扱っていない。WebShop で「役立つ反省が出ず改善しない」失敗例も自分で報告している。

## 原文（改変しない）
原文: [20260909_0040_Language_Agents_with_Verbal_Reinforcemen.orig.md](20260909_0040_Language_Agents_with_Verbal_Reinforcemen.orig.md)（改変しない。文字起こしなら正規化版 *.normalized.md を読む）
