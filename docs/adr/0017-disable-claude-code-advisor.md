# 0017. Claude Code の Advisor（相談役モデル）はリポジトリの settings で外す
- 状態: 採用 / 日付: 2026-09-09

## 状況
利用者から「Sonnet にタスクをやらせると Advisor で Opus が呼ばれる」と報告があった。Advisor は実行役（Sonnet）が `advisor()` を呼ぶと会話全文を相談役（Opus）に送る Claude Code の機能で、有効化は `/advisor`・`advisorModel`・`--advisor` の 3 経路、選択はユーザー設定に残り続ける。相談役の読み込みはキャッシュされず、回数の上限設定は無い（docs/sources/advisor.md #1）。

## 決定
`.claude/settings.json` の `env` に `CLAUDE_CODE_DISABLE_ADVISOR_TOOL=1` を置き、ルートで起動した全セッション（サブエージェント含む）で Advisor を外す。README に理由と戻し方（その行を消す）を書く。bench で Advisor を測るときは `run.py --advisor` が組んだ rundir からその行だけ外す。

## 理由（数字があれば台帳の値をそのまま）
- bench `trap / large / sonnet`（2.1.266、同日同時刻、各 n=5）: A（agent-ws）は Advisor なし 0.184 USD・5/5 正解、Advisor あり 0.267 USD・5/5 正解。正誤に効かず、相談が起きた 1 本だけ 0.678 USD（相談なしの中央値の 3.7 倍）。相談 1 回で Opus が 44,384 トークンを読み 0.338 USD、助言を受けた Sonnet 側もターンが 6 → 12 に伸びた。相談は 10 本中 2 本
- B（仕組みなし）＋Advisor は 1/5 正解で、既存の B 単独 1/5 と同じ。正解した 1 本は相談した本で 0.627 USD。規約（A）は 0.18 USD で 5/5 なので、規約のほうが安くて確実
- 公式は「計画するものが少ない短いタスクには効かない」と書く（#1）。agent-ws の仕事は 5〜8 ターンで読む順番も置き場所も規約で決まっており、毎ターン固定で送られる分（約 40k）をキャッシュで安く払う設計なのに、Advisor はその固定分ごと Opus に非キャッシュで読ませる（相談 1 回の 44k の大半がこの固定分）
- `env` で外すと headless でも対話でも効き、`--advisor` を付けても無効になることを debug ログで確認した（D: [AdvisorTool] 行が消え、費用もフラグなしと同額）

## 捨てた案
- README で注意喚起するだけ: `/advisor` の選択はユーザー設定に残り続けるので、一度試した利用者には効き続ける。AGENTS.md で「相談するな」と指示する: Claude Code 自身が「実質的な作業の前に呼べ」と注入するので競合して当てにならない。相談回数に上限を付ける: その設定が無い（#1）

## 影響
ルートで起動した利用者は `/advisor` が使えず、自分で設定した advisorModel も無視される。戻すには settings の 1 行を消す。Codex には Advisor が無いので無関係。相談率はタスクの型で変わるので、資料を書く newtask で測り直すのは任意（結論は変わらない見込み）。

根拠: `docs/sources/advisor.md` #1・#2・#3・#4、`bench/results/runs_advisor_a.jsonl`・`runs_advisor_v.jsonl`
