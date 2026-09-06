# 0001. 「他タスクを読まない」は規約に書くだけでなく hook で止める
- 状態: 採用 / 日付: 2026-09-05

## 状況
読む範囲を今のタスクと案件のナレッジに絞りたい。AGENTS.md に「他タスクの tasks/ を読まない」と書くだけでは、プロンプトの指示は助言に過ぎず、確実には守られない。
## 決定
`scripts/ws hook pre-tool-use` が、ツールの入力（読むパス・grep の対象・シェルのコマンド）に現在のタスク以外の `projects/*/tasks/*/` が含まれていたら拒否し、理由として `knowledges/` を案内する。Claude Code は `.claude/settings.json`、Codex CLI は `.codex/hooks.json` から同じ 1 本を呼ぶ。hook は python3 の標準ライブラリだけで書く。
## 理由
hooks は決定論的に実行される。拒否の理由文はモデルに届くので、止めるだけでなく正しい参照先へ誘導できる。仕組み全体（規約・hooks・注入）を外した bench の B 条件は、新規タスクで他タスクの資料に中央値 7 回立ち入り、agent-ws は 0 回だった（Sonnet・各 5 回）。ただし「規約だけあって hook が無い」条件は測っていない。
## 捨てた案
- `permissions.deny` に `Read(projects/**/tasks/**)`: 静的なので「今のタスクだけ許す」が書けない
- `claude --agent` でツールを絞った専用エージェント: Claude Code 専用で、起動後のタスク切り替えに追従しない
- bash + jq で書く: jq が無い環境が多い。`scripts/ws` を MCP サーバにする: ツール定義がコンテキストに載り続ける
## 影響
**起動はリポジトリのルートで行う**必要がある（サブディレクトリ起動ではルートの hooks が読まれない。0003 も参照）。hook が拒否するたびに 1 ターン増える。`mkdir` の直打ちなど、まだ規約でしか止めていないものは事故が起きたら hook に足す。

根拠: kanban T-SKSDN・設計書 D-SETHW（採らなかった案の表・ベストプラクティスとの照合）・README「計測」新規タスクの表・`bench/results/summary.md` newtask 行
