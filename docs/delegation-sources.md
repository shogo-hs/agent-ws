# 委譲規則の根拠

AGENTS.md の「安いモデルの調査係に渡す仕事」の根拠。各行のファイルに取得日時・引用・原文がある。
ページは書き換わるので、規則を見直すときは再取得して差分を見る。

| # | 出典（題名と URL） | 取得日時 | via | ファイル | 支えている規則 |
|---|---|---|---|---|---|
| 1 | Introducing GPT-5.4 mini and nano — https://openai.com/index/introducing-gpt-5-4-mini-and-nano/ | 2026-09-06T14:36:44+09:00 | jina | [docs/snapshots/20260906_1436_Introducing_GPT-5.4_mini_and_nano.md](snapshots/20260906_1436_Introducing_GPT-5.4_mini_and_nano.md) | 条件①②、渡し方（本線＝計画・調整・最終判断／調査係＝コード探索・大きなファイルの通読・付随資料の処理） |
| 2 | GPT-5.4 Mini Model \| OpenAI API — https://developers.openai.com/api/docs/models/gpt-5.4-mini | 2026-09-06T14:37:22+09:00 | jina | [docs/snapshots/20260906_1437_GPT-5.4_Mini_Model_OpenAI_API.md](snapshots/20260906_1437_GPT-5.4_Mini_Model_OpenAI_API.md) | Codex researcher の既定モデル gpt-5.4-mini の選定根拠 |
| 3 | GPT-5.4 nano Model \| OpenAI API — https://developers.openai.com/api/docs/models/gpt-5.4-nano | 2026-09-06T14:37:26+09:00 | jina | [docs/snapshots/20260906_1437_GPT-5.4_nano_Model_OpenAI_API.md](snapshots/20260906_1437_GPT-5.4_nano_Model_OpenAI_API.md) | 条件①②（nano は不採用の比較対象として引用） |
| 4 | Subagents \| ChatGPT Learn — https://learn.chatgpt.com/docs/agent-configuration/subagents | 2026-09-06T14:37:30+09:00 | jina | [docs/snapshots/20260906_1437_Subagents_ChatGPT_Learn.md](snapshots/20260906_1437_Subagents_ChatGPT_Learn.md) | 条件③④、該当するもの（通読・要約・該当箇所探し） |
| 5 | Choosing the right model — https://platform.claude.com/docs/en/about-claude/models/choosing-a-model | 2026-09-06T14:37:37+09:00 | jina | [docs/snapshots/20260906_1437_Choosing_the_right_model.md](snapshots/20260906_1437_Choosing_the_right_model.md) | Claude Code researcher の既定モデル haiku の選定根拠 |
| 6 | Optimizing for cost and intelligence — https://platform.claude.com/docs/en/about-claude/models/optimizing-for-cost-and-intelligence | 2026-09-06T14:37:38+09:00 | jina | [docs/snapshots/20260906_1437_Optimizing_for_cost_and_intelligence.md](snapshots/20260906_1437_Optimizing_for_cost_and_intelligence.md) | 条件②、委譲は定型・分割可能な作業に限る／難しい判断は本線に残す線引き |
| 7 | Building Effective AI Agents — https://www.anthropic.com/engineering/building-effective-agents | 2026-09-06T14:37:39+09:00 | jina | [docs/snapshots/20260906_1437_Building_Effective_AI_Agents.md](snapshots/20260906_1437_Building_Effective_AI_Agents.md) | 該当するもの（複数情報源の横断調査）、易しい仕事を安いモデルへ振る委譲基準 |
| 8 | Create custom subagents - Claude Code Docs — https://code.claude.com/docs/en/sub-agents | 2026-09-06T14:37:40+09:00 | jina | [docs/snapshots/20260906_1437_Create_custom_subagents_-_Claude_Code_Do.md](snapshots/20260906_1437_Create_custom_subagents_-_Claude_Code_Do.md) | Claude Code researcher に haiku を選んだコスト根拠、description を短く保つ制約 |

## 再取得の手順

`WS_ROOT=$PWD uv run python scripts/ws ref add <URL> --dir docs/snapshots --summary "<1文>"` で該当行の URL を撮り直し、上の表のファイル欄を新しいファイル名に差し替える。
