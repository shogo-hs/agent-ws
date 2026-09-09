# Claude Code の Advisor を agent-ws 側で外すかの判断の根拠

Advisor（Sonnet 実行＋Opus 相談）をリポジトリ側で外すと決めた ADR 0017 の出典。
発端は agent-ws の実利用者からの「Sonnet にタスクをやらせると Advisor で Opus が呼ばれる」という報告（2026-09-09）。

判断の物差しは 3 つ。①Advisor が何を読み・どう課金され・どう外せるか（一次情報）、②Anthropic が「効く」としている条件と agent-ws の仕事の型が合うか（一次情報）、③agent-ws の bench で費用と正誤がどう変わるか（自分の実測。`bench/results/runs_advisor_*.jsonl`、tag `adv1`）。

各行のファイルに取得日時・引用・原文（`.orig.md`）がある。ページは書き換わるので、規則を見直すときは再取得して差分を見る。

## 一次情報（Anthropic）

| # | 出典（題名と URL） | 取得日時 | ファイル | 何の根拠か |
|---|---|---|---|---|
| 1 | Escalate hard decisions with the advisor tool（Claude Code） — https://code.claude.com/docs/en/advisor | 2026-09-09T17:55:06+09:00 | [snapshots/20260909_1755_Escalate_hard_decisions_with_the_advisor.md](../snapshots/20260909_1755_Escalate_hard_decisions_with_the_advisor.md) | 有効化は `/advisor`・`advisorModel`・`--advisor` の 3 経路で、選択はユーザー設定に残り続ける。相談役は会話全文を毎回非キャッシュで読む。回数の上限・強制の設定は無い。短いタスクには効かない。`CLAUDE_CODE_DISABLE_ADVISOR_TOOL=1` で `/advisor` ごと無効化 |
| 2 | Advisor tool（Claude API） — https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool | 2026-09-09T17:55:15+09:00 | [snapshots/20260909_1755_Advisor_tool.md](../snapshots/20260909_1755_Advisor_tool.md) | Advisor 分は上位の `usage` に入らず `usage.iterations` の `advisor_message` にだけ出る（数え方の出所）。出力の典型値 1,400〜1,800 トークン。相談 2 回以下ならキャッシュは元が取れない。コーディングでは 1 タスク 2〜3 回呼ぶよう system prompt で促す |

## 自分の実測

| # | 何を | どこに | 要点 |
|---|---|---|---|
| 3 | `claude -p` で `--advisor opus` の有効化と、project の `.claude/settings.json` の `env` に `CLAUDE_CODE_DISABLE_ADVISOR_TOOL=1` を置いたときの無効化（debug ログの `[AdvisorTool]` 行） | `docs/adr/0017` | 2.1.266。フラグで「Server-side tool enabled with claude-opus-5」、env ありでは行が消え費用もフラグなしと同額 |
| 4 | bench `trap / large / sonnet` を A・A＋Advisor・B＋Advisor で各 n=5 | `bench/results/runs_advisor_a.jsonl`・`runs_advisor_v.jsonl` | 結果と解釈は `docs/adr/0017` |
