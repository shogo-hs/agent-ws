# 0011. 配布に Microsoft APM を使わない
- 状態: 採用 / 日付: 2026-09-08

## 状況
Claude Code と Codex の両方に配るため、hooks 登録とサブエージェント定義を `.claude/` と `.codex/` に別形式で置いている。Microsoft APM（Agent Package Manager）は 1 つの宣言から 13 ハーネスへ primitives を配るツールで、この二重管理を肩代わりできる可能性があった。
## 決定
APM パッケージにしない。テンプレートリポジトリのまま配る。実装を読む限り hooks も同梱スクリプトも Codex 向けのサブエージェント TOML も配れるので、技術的な不可ではなく損得の判断。
## 理由
実際に二重管理なのは 3 組で、逐語の重複は `researcher` の指示本文 4 行しかない。スキルは `.claude/skills` を git 追跡の symlink に、規約は `CLAUDE.md` を `@AGENTS.md` 1 行に、hook 実装は `scripts/ws` 1 本に集約して既に単一正本になっている。hooks 登録は Codex だけ `--ttl 30` と `additionalContextLimit`、Claude だけ PostToolUse・matcher・statusLine を持つ非対称で、共通化できる部分が少ない。
## 捨てた案
- 全面移管: `scripts/ws` が `.claude/hooks/agent-ws/` と `.codex/hooks/agent-ws/` へ 2 部コピーされ、Claude だけ skills の収束から外れて `.claude/skills/` に実体コピーされる。いま単一正本のものがハーネスごとのコピーに戻る
- hooks だけ移管: APM 自身が "Treat both as opt-in surface, not as your primary distribution path" と書いている。hook で強制する設計（0001）とは前提が合わない
- `researcher` 定義だけ移管: 4 行のために APM CLI 0.x への依存を利用者に強制する。いまは python3 だけで動く
## 影響
statusLine と `templates/` は APM の primitive に無いので、移管しても管理外が残る事情は変わらない。3 つ目のハーネスに広げる・既存リポジトリへ後付けする・サブエージェントが増える・APM が 1.0 に到達する、のいずれかが起きたら再検討する。

根拠: `docs/sources/apm-migration.md` #1〜#3・kanban T-6PJJT・設計書 D-61CTQ
