# セッション終了時の自動レトロスペクティブを入れるかの調査の根拠

`docs/adr/0016`（自動レトロスペクティブは LLM に振り返らせず、数えられる指標の記録と人の指摘の取りこぼし検知に留める）の根拠にした出典。
発端は「作業終了時に hook で transcript を振り返り、うまくいった／いかなかったことを AGENTS.md・hooks・skills に書き戻せば
トークン効率と遂行の滑らかさが上がるのでは」という提案（2026-09-09）。

判断の物差しは 3 つ。①hook の仕様上どこで何秒動かせるか（一次情報）、②振り返りで文脈を育てる手法が
**正解や報酬が無い環境**で効くと測られているか、ルールが増えたときの副作用は何か（研究）、③1 セッションあたりの追加コスト（自分の実測）。

各行のファイルに取得日時・引用・原文（`.orig.md`）がある。ページは書き換わるので、規則を見直すときは再取得して差分を見る。

## 一次情報（Anthropic / OpenAI）

| # | 出典（題名と URL） | 取得日時 | ファイル | 何の根拠か |
|---|---|---|---|---|
| 1 | Hooks reference — https://code.claude.com/docs/en/hooks | 2026-09-09T00:38:05+09:00 | [snapshots/20260909_0038_Hooks_reference_-_Claude_Code_Docs.md](../snapshots/20260909_0038_Hooks_reference_-_Claude_Code_Docs.md) | SessionEnd は「once per session」だが決定権なし・既定 1.5 秒（設定で最大 60 秒）・prompt/agent 型 hook 不可。Stop は「once per turn」で `stop_hook_active`・8 回連続で強制終了。transcript は非同期書き込みで発火時に最新ターンが欠けうる。`async: true` は command 型のみ、`-p` では teardown で kill |
| 2 | How Claude remembers your project — https://code.claude.com/docs/en/memory | 2026-09-09T00:40:22+09:00 | [snapshots/20260909_0040_How_Claude_remembers_your_project_-_Clau.md](../snapshots/20260909_0040_How_Claude_remembers_your_project_-_Clau.md) | Claude Code 自身の auto memory の仕様（何を・いつ・どこに書くか）。同じことを二重に作らないための比較対象 |
| 3 | Effective context engineering for AI agents — https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents | 2026-09-09T00:40:26+09:00 | [snapshots/20260909_0040_Effective_context_engineering_for_AI_age.md](../snapshots/20260909_0040_Effective_context_engineering_for_AI_age.md) | 文脈は有限資源で「最小の高信号トークン」に絞るという Anthropic の指針。ルールを溜め込む設計への一次情報側の歯止め |
| 4 | Hooks（Codex CLI） — https://developers.openai.com/codex/hooks | 2026-09-09T00:41:45+09:00 | [snapshots/20260909_0041_Hooks_ChatGPT_Learn.md](../snapshots/20260909_0041_Hooks_ChatGPT_Learn.md) | Codex の SessionEnd は同期のみ・既定 1 秒・最大 3 秒。`transcript_path` はあるが「stable interface ではない」。両ハーネスで同じ形にするなら hook の中では何もできない |

## 研究（振り返りで文脈を育てる手法と、その前提・副作用）

| # | 出典（題名と URL） | 取得日時 | ファイル | 何の根拠か |
|---|---|---|---|---|
| 5 | ACE: Agentic Context Engineering（arXiv 2510.04618） — https://arxiv.org/html/2510.04618 | 2026-09-09T00:40:15+09:00 | [snapshots/20260909_0040_Agentic_Context_Engineering_Evolving_Con.md](../snapshots/20260909_0040_Agentic_Context_Engineering_Evolving_Con.md) | AppWorld で ReAct 42.4 → 59.4（正解あり）／57.2（正解なし・実行結果あり）。**context collapse**: LLM に全文を書き直させると 18,282 → 122 トークンに潰れ精度 66.7 → 57.1（素の 63.7 より下）。対策は Generator/Reflector/Curator の分離と bullet 単位の delta 追記。「信頼できる信号が無いと ACE も DC も劣化しうる」と自ら明記 |
| 6 | Reflexion（arXiv 2303.11366） — https://arxiv.org/html/2303.11366 | 2026-09-09T00:40:24+09:00 | [snapshots/20260909_0040_Language_Agents_with_Verbal_Reinforcemen.md](../snapshots/20260909_0040_Language_Agents_with_Verbal_Reinforcemen.md) | HumanEval pass@1 91%（素 80%）。全実験が二値／スカラー報酬（テスト成否・exact match）を前提。メモリは最大 3 件。WebShop では有用な反省文が出ず 4 試行で打ち切り |
| 7 | Dynamic Cheatsheet（arXiv 2504.07952） — https://arxiv.org/html/2504.07952 | 2026-09-09T00:40:32+09:00 | [snapshots/20260909_0040_Dynamic_Cheatsheet_Test-Time_Learning_wi.md](../snapshots/20260909_0040_Dynamic_Cheatsheet_Test-Time_Learning_wi.md) | 正解ラベル無しで自己判定する設定（個人環境に最も近い）。Game of 24 で 10% → 99%。ただし**全履歴を溜める**対照（FH）は 20.0% → 6.7% に劣化。弱いモデルでは「誤った試行が主に溜まる」 |
| 8 | ExpeL（arXiv 2308.10144） — https://arxiv.org/html/2308.10144 | 2026-09-09T00:40:38+09:00 | [snapshots/20260909_0040_ExpeL_LLM_Agents_Are_Experiential_Learne.md](../snapshots/20260909_0040_ExpeL_LLM_Agents_Are_Experiential_Learne.md) | 経験から抽出した insight に ADD/EDIT/UPVOTE/DOWNVOTE と importance（初期 2、0 で削除）を持たせる＝**増え続けないルール台帳**の設計例。反省文を insight 抽出に混ぜると性能が下がった |
| 9 | Mem0（arXiv 2504.19413） — https://arxiv.org/html/2504.19413 | 2026-09-09T00:40:41+09:00 | [snapshots/20260909_0040_Mem0_Building_Production-Ready_AI_Agents.md](../snapshots/20260909_0040_Mem0_Building_Production-Ready_AI_Agents.md) | 会話の事実記憶で 26,031 → 1,764 トークン、p95 17.1 → 1.44 秒。ただし精度は全文脈のほうが上（J 72.90 → 66.88）。ルール学習ではなく事実記憶の話 |

## 副作用・限界（ルールが増える／自己判定させると何が起きるか）

| # | 出典（題名と URL） | 取得日時 | ファイル | 何の根拠か |
|---|---|---|---|---|
| 10 | How Many Instructions Can LLMs Follow at Once?（IFScale・arXiv 2507.11538） — https://arxiv.org/html/2507.11538 | 2026-09-09T00:40:48+09:00 | [snapshots/20260909_0040_How_Many_Instructions_Can_LLMs_Follow_at.md](../snapshots/20260909_0040_How_Many_Instructions_Can_LLMs_Follow_at.md) | 指示 10〜500 本で遵守率を測定。最良でも 500 本で 68%。claude-opus-4 44.6%・sonnet-4 42.9%。失敗は「黙って落とす」omission。ADR 0005 の「20 行上限」の裏付け |
| 11 | Context Rot（Chroma） — https://research.trychroma.com/context-rot | 2026-09-09T00:40:44+09:00 | [snapshots/20260909_0040_Context_Rot_How_Increasing_Input_Tokens_.md](../snapshots/20260909_0040_Context_Rot_How_Increasing_Input_Tokens_.md) | 18 モデルで入力長が増えるほど性能が落ちる。distractor の害は長さで増幅。Claude 系は曖昧さで棄権しやすい。起動時に差し込む文を増やす設計への歯止め |
| 12 | Large Language Models Cannot Self-Correct Reasoning Yet（arXiv 2310.01798） — https://arxiv.org/html/2310.01798 | 2026-09-09T00:40:51+09:00 | [snapshots/20260909_0040_Large_Language_Models_Cannot_Self-Correc.md](../snapshots/20260909_0040_Large_Language_Models_Cannot_Self-Correc.md) | 正解ラベル無しの自己修正で「全モデル・全ベンチで精度が下がる」。Reflexion 系は oracle ラベルで導いていると指摘。「人の指摘無しに失敗を自己判定させる」設計そのものの反証 |

## 先行実装（Claude Code / Codex の hook でセッションを振り返るもの）

効果（トークン・ターン・手戻り）を測った出典は **13 本中 0 本**。共通形は「hook 本体は transcript のコピーだけで即終了し、LLM 抽出は detach した背景プロセスに逃がす」「書き戻しは confidence 付きで人の承認を挟む」。

| # | 出典（題名と URL） | 取得日時 | ファイル | 何の根拠か |
|---|---|---|---|---|
| 13 | ECC continuous-learning SKILL.md — https://github.com/affaan-m/everything-claude-code/blob/main/skills/continuous-learning/SKILL.md | 2026-09-09T00:41:43+09:00 | [snapshots/20260909_0041_ECC_skills_continuous-learning_SKILL.md_.md](../snapshots/20260909_0041_ECC_skills_continuous-learning_SKILL.md_.md) | Stop hook で 10 メッセージ以上なら transcript から corrections 等を抽出し `skills/learned/` へ（`auto_approve: false`）。**v1 は 2026-04-28 に作者が deprecate** し、常時観測＋confidence 方式へ移行。測定なし |
| 14 | claude-memory-compiler — https://github.com/coleam00/claude-memory-compiler | 2026-09-09T00:40:40+09:00 | [snapshots/20260909_0040_GitHub_-_coleam00_claude-memory-compiler.md](../snapshots/20260909_0040_GitHub_-_coleam00_claude-memory-compiler.md) | SessionEnd + PreCompact（timeout 10 秒）が transcript をコピーして detach した `flush.py` を起動し Agent SDK で決定・教訓を抽出、SessionStart で index 注入。再帰ガード `CLAUDE_INVOKED_BY`。コストのみ「Memory flush (per session) ~$0.02-0.05」「Compile one daily log $0.45-0.65」。効果は測定なし |
| 15 | claude-memory-compiler AGENTS.md — https://github.com/coleam00/claude-memory-compiler/blob/main/AGENTS.md | 2026-09-09T00:43:05+09:00 | [snapshots/20260909_0043_claude-memory-compiler_AGENTS.md_at_main.md](../snapshots/20260909_0043_claude-memory-compiler_AGENTS.md_at_main.md) | 同上の内部設計（`allowed_tools=[]`・`max_turns=2`・60 秒 dedupe） |
| 16 | claude-reflect — https://github.com/BayramAnnakov/claude-reflect | 2026-09-09T00:40:34+09:00 | [snapshots/20260909_0040_GitHub_-_BayramAnnakov_claude-reflect_A_.md](../snapshots/20260909_0040_GitHub_-_BayramAnnakov_claude-reflect_A_.md) | Stop ではなく UserPromptSubmit で「no, use X」等を regex 捕捉してキューに積み、**手動の `/reflect`** で LLM が検証して CLAUDE.md / AGENTS.md / skill へ書き戻す。confidence 0.60-0.95。測定なし |
| 17 | Self-Improving Skills — https://www.developersdigest.tech/blog/self-improving-skills-claude-code | 2026-09-09T00:40:51+09:00 | [snapshots/20260909_0040_Self-Improving_Skills_Claude_Code_That_L.md](../snapshots/20260909_0040_Self-Improving_Skills_Claude_Code_That_L.md) | `/reflect [skill]` が会話から corrections/approvals を抽出し SKILL.md へ confidence 付き diff。stop hook で `reflect --auto` を回す案も書かれている。測定なし |
| 18 | clerk — https://dev.to/vulcan_shen_acdbffa0285d2/clerk-auto-summarize-your-claude-code-sessions-4m87 | 2026-09-09T00:41:11+09:00 | [snapshots/20260909_0041_clerk_Auto-Summarize_Your_Claude_Code_Se.md](../snapshots/20260909_0041_clerk_Auto-Summarize_Your_Claude_Code_Se.md) | SessionEnd → 背景で `claude -p` → 日付別の要約ファイル。CLAUDE.md には書かない。「one API call per session」以外の数字なし。自作ツールの宣伝 |
| 19 | I added one hook to Claude Code（XDA） — https://www.xda-developers.com/added-one-hook-claude-code-stopped-same-mistake-twice/ | 2026-09-09T00:41:16+09:00 | [snapshots/20260909_0041_I_added_one_hook_to_Claude_Code,_and_it_.md](../snapshots/20260909_0041_I_added_one_hook_to_Claude_Code,_and_it_.md) | Stop hook が 1 回目を block して `mistakes.md` を読ませ再点検、`stop_hook_active` で 2 回目は通す。書き戻しは人手。「additional turn eats into credits」と副作用を自認。体験談 |
| 20 | claude-mem — https://github.com/thedotmack/claude-mem | 2026-09-09T00:41:23+09:00 | [snapshots/20260909_0041_GitHub_-_thedotmack_claude-mem_Persisten.md](../snapshots/20260909_0041_GitHub_-_thedotmack_claude-mem_Persisten.md) | 5 つの hook で観測を AI 圧縮して SQLite + Chroma に保存し次セッションへ注入。「~10x token savings」は検索の段階的開示の話でレトロの効果ではない。有料 hosted 版への誘導あり |
| 21 | Continual Learning in Claude Code — https://www.developersdigest.tech/blog/continual-learning-claude-code | 2026-09-09T00:41:01+09:00 | [snapshots/20260909_0041_Continual_Learning_in_Claude_Code_Memory.md](../snapshots/20260909_0041_Continual_Learning_in_Claude_Code_Memory.md) | hook 不使用の概念記事。「Set up a retrospective at the end of your coding session」。測定なし |
| 22 | claude-skill-session-retrospective — https://github.com/accidentalrebel/claude-skill-session-retrospective | 2026-09-09T00:41:07+09:00 | [snapshots/20260909_0041_GitHub_-_accidentalrebel_claude-skill-se.md](../snapshots/20260909_0041_GitHub_-_accidentalrebel_claude-skill-se.md) | 手動スキル。自分の JSONL を読んで lessons を console に出すだけで書き戻し先なし。JSONL の `is_error: true` で拒否を拾う記述は流用できる。測定なし |

## 自分の実測

| # | 何を | ファイル | 結果 |
|---|---|---|---|
| M1 | 実セッション 185 本（agent-ws 12・workspace 173）の transcript から、振り返りに渡す入力量を 3 案で集計 | `bench/retro_cost.csv`・`bench/measure_retro_cost.py` | 丸ごと: workspace 中央値 178,832・p90 517,746（43% が 20 万超で haiku に入らない）。text だけ: 1,266・5,819。user だけ: 82・670。agent-ws は 38,959／21／21 |
| M2 | `claude -p --model haiku` を空ディレクトリで 1 回呼ぶだけで固定で乗る分 | `bench/retro_floor.json` | input 10・cache_creation 7,036・cache_read 13,615・output 58。0.0157 USD・API 1.4 秒・壁時計 3.35 秒。**text だけ／user だけの案ではこの固定分が主成分** |
| M3 | 既存の記録の実績 | `LESSONS.md`・auto-memory・`tasks/lessons.md` | agent-ws LESSONS.md 0 行（12 セッション）。auto-memory の feedback 21 件／約 5 か月（週 1〜2 件）。上限なしの `tasks/lessons.md` は 1,421 行・168 見出しで障害記録が主（ADR 0005 の 1,360 行から更に増加） |
