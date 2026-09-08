# APM 移管を見送った判断の根拠

「agent-ws の規約・スキル・hooks を Microsoft APM（Agent Package Manager）に移管すべきか」を
調べて見送った判断（kanban T-6PJJT、結論は html-hub の D-61CTQ）の根拠。
各行のファイルに取得日時・引用・原文（`.orig.md`）がある。ページは書き換わるので、
判断を見直すときは再取得して差分を見る。

APM は 1〜2 週に 1 マイナーの頻度で更新され、manifest schema は Working Draft のままなので、
**この表の内容は v0.30.0（2026-09-07）時点のもの**として扱うこと。

| # | 出典（題名と URL） | 取得日時 | via | ファイル | 支えている判断 |
|---|---|---|---|---|---|
| 1 | Targets matrix（APM） — https://microsoft.github.io/apm/reference/targets-matrix/ | 2026-09-08T15:03:20+09:00 | jina | [docs/snapshots/20260908_1503_Targets_matrix.md](../snapshots/20260908_1503_Targets_matrix.md) | Codex は instructions / prompts / commands 非対応（`AGENTS.md` 経由でしか届かない）／Claude だけ skills の収束から外れ `.claude/skills/` に実体コピーされる＝いまの symlink の単一正本が崩れる |
| 2 | Hooks and commands（APM） — https://microsoft.github.io/apm/producer/author-primitives/hooks-and-commands/ | 2026-09-08T15:03:15+09:00 | jina | [docs/snapshots/20260908_1503_Hooks_and_commands.md](../snapshots/20260908_1503_Hooks_and_commands.md) | hook と同梱スクリプトは配れる（`${PLUGIN_ROOT}`）が、APM 自身が「主要な配布経路にするな」と書いている。hook が中心の agent-ws（ADR 0001）とは前提が合わない |
| 3 | Claude Code の規律を hook に降ろしたら、Haiku でも壊れなくなった — https://zenn.dev/yui/articles/97597aa13b9802 | 2026-09-08T15:03:11+09:00 | jina | [docs/snapshots/20260908_1503_Claude_Codeの規律をhookに降ろしたら、Haikuでも壊れなくなった.md](../snapshots/20260908_1503_Claude_Codeの規律をhookに降ろしたら、Haikuでも壊れなくなった.md) | `doctor` の検査を `PostToolUse`（Edit/Write）に降ろして exit 2 で返す案の出どころ（第三者の報告。帰属） |

## 出典を読まずに確かめた事実（一次情報はローカルの実装）

APM はこの環境に導入済みで（`/usr/local/bin/apm`）、ソースの clone が
`settings/sh_skill_repository/.reference/apm/` にある。次の判断は Web ページではなく
実装を読んで確かめたもの。

| 確かめたこと | 読んだ場所 |
|---|---|
| hook が呼ぶスクリプトの配置先が `.claude/hooks/<pkg>/` と `.codex/hooks/<pkg>/` に分かれ、ハーネスごとに 1 部ずつコピーされる | `src/apm_cli/integration/hook_integrator.py` の `_rewrite_command_for_target`（L323-402） |
| ハーネス別の hook は `<name>-claude-hooks.json` / `<name>-codex-hooks.json` のファイル名で振り分けられる | 同 `_HOOK_FILE_TARGET_SUFFIXES` / `_filter_hook_files_for_target`（L186-228） |
| statusLine は APM のプリミティブに無く、hooks キーだけがマージされる | `src/apm_cli/integration/targets.py` の各 `TargetProfile` |

## 再取得の手順

`WS_ROOT=$PWD uv run python scripts/ws ref add <URL> --dir docs/snapshots --summary "<1文>"` で
該当行の URL を撮り直し、上の表のファイル欄を新しいファイル名に差し替える。
