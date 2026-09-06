# トークン節約 5 点の根拠

AGENTS.md「compact するときに残すもの」、README「セッションの切り方」「1 時間以上空いたあとの 1 通目を止める」、transcript-ingest の fork 化、reference の要点と原文の分離、正規化版への読み替え hook（kanban T-0NG9F）の根拠。
各行のファイルに取得日時・引用・原文（`.orig.md`）がある。ページは書き換わるので、規則を見直すときは再取得して差分を見る。

| # | 出典（題名と URL） | 取得日時 | via | ファイル | 支えている規則 |
|---|---|---|---|---|---|
| 1 | Explore the context window — https://code.claude.com/docs/en/context-window | 2026-09-06T15:51:13+09:00 | jina | [docs/snapshots/20260906_1551_Explore_the_context_window_-_Claude_Code.md](snapshots/20260906_1551_Explore_the_context_window_-_Claude_Code.md) | 要点と原文の分離（compact 後に再読されるのは直近 5 ファイル、5,000 トークン超はパス参照だけ） |
| 2 | Manage costs effectively — https://code.claude.com/docs/en/costs | 2026-09-06T15:51:15+09:00 | jina | [docs/snapshots/20260906_1551_Manage_costs_effectively_-_Claude_Code_D.md](snapshots/20260906_1551_Manage_costs_effectively_-_Claude_Code_D.md) | compact で残すものを CLAUDE.md（@AGENTS.md）に書く／hook で読む先を差し替える |
| 3 | Extend Claude with skills — https://code.claude.com/docs/en/skills | 2026-09-06T15:51:17+09:00 | jina | [docs/snapshots/20260906_1551_Extend_Claude_with_skills_-_Claude_Code_.md](snapshots/20260906_1551_Extend_Claude_with_skills_-_Claude_Code_.md) | transcript-ingest の context: fork / background: false |
| 4 | How Claude Code uses prompt caching — https://code.claude.com/docs/en/prompt-caching | 2026-09-06T15:51:18+09:00 | jina | [docs/snapshots/20260906_1551_How_Claude_Code_uses_prompt_caching_-_Cl.md](snapshots/20260906_1551_How_Claude_Code_uses_prompt_caching_-_Cl.md) | モデルと effort は冒頭で決める／/rewind／promptCacheTtl |
| 5 | Prompt caching (OpenAI API) — https://developers.openai.com/api/docs/guides/prompt-caching | 2026-09-06T15:51:19+09:00 | jina | [docs/snapshots/20260906_1551_Prompt_caching_OpenAI_API.md](snapshots/20260906_1551_Prompt_caching_OpenAI_API.md) | Codex の hook に --ttl 30（GPT-5.6 以降の最小寿命 30 分） |
| 6 | Configuration Reference (Codex) — https://learn.chatgpt.com/docs/config-file/config-reference | 2026-09-06T15:51:19+09:00 | jina | [docs/snapshots/20260906_1551_Configuration_Reference_ChatGPT_Learn.md](snapshots/20260906_1551_Configuration_Reference_ChatGPT_Learn.md) | compact_prompt を使わない理由（要約プロンプトの全文上書き） |
| 7 | Hooks (Codex) — https://learn.chatgpt.com/docs/hooks | 2026-09-06T15:51:22+09:00 | jina | [docs/snapshots/20260906_1551_Hooks_ChatGPT_Learn.md](snapshots/20260906_1551_Hooks_ChatGPT_Learn.md) | PreToolUse の updatedInput（Codex でも同じ形で書き換え可）、hosted の WebSearch に hook が無い |

## 再取得の手順

`WS_ROOT=$PWD uv run python scripts/ws ref add <URL> --dir docs/snapshots --summary "<1文>"` で該当行の URL を撮り直し、上の表のファイル欄を新しいファイル名に差し替える。
