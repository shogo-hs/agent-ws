# 0021. 使わない常時ロードのツール定義は `permissions.deny` で外す。effort と thinking は既定を変えず調整ノブにする
- 状態: 採用 / 日付: 2026-09-14

## 状況
「scripts/ws と hooks の仕組みで、まだトークンを減らせないか」を調べた。これまでの計測（0009・0012）は処理したトークン数で見ていて、費用の内訳は見ていなかった。bench（`trap / chain / newtask`、A 条件、Sonnet 5、40 セッション）の transcript を単価で分解すると、費用の 40〜55% は **cache 作成**（1 時間 TTL は読みの 20 倍の単価。うちセッション開始時に書く 14,866 トークンが大半）、22〜30% が **出力（thinking 込み）**、cache 読みは 23〜38% だった（`bench/cost_breakdown.py`）。CLI の引数で 1 ターンに畳める連続ターンは 40 セッションで 0 件、途中のキャッシュ miss も 0 件で、ターン構成の側にはもう余地が無い。固定分 35,105 のうち、agent-ws の仕事で使わない常時ロードのツール（ListAgents・ReportFindings・ScheduleWakeup・Workflow）の定義が 4,884 を占めていた（`bench/results/fixed_v3.md`）。

## 決定
- `.claude/settings.json` の `permissions.deny` にその 4 本を書き、ツール定義ごと外す（Agent SDK の文書: deny の裸のツール名はツール定義をリクエストから除く）。Agent（researcher）と Skill（5 本のスキル）は残す
- effort と thinking の既定は変えない。`--effort medium`・`MAX_THINKING_TOKENS=0` の効きは README に数字つきの調整ノブとして書き、選ぶのは利用者。Codex は `.codex/config.toml` の `model_reasoning_effort` が同じ役
- `bench/run.py` に `--effort` と `--env`、`bench/run_fixed.py`（固定分の計測）、`bench/cost_breakdown.py`（費目の分解）を足し、次に同じ問いが来たら測り直せるようにする

## 理由（bench `trap / large / sonnet`、同日同コード、各 n=5、並べ替え検定）
- deny 4 本: 処理入力 232k → 166k（−28%、p=0.048）、最終文脈 41.3k → 35.4k、費用 0.166 → 0.143（−14%、p=0.12）、5/5 正解。機能の損失は無い（4 本とも案件の仕事で呼ばれない）
- `--effort medium`: 処理入力 −19%（p=0.045）、出力 −21%（p=0.048）、費用 −14%（p=0.046）、5/5。`low` は費用 −18%（p=0.048）、`MAX_THINKING_TOKENS=0` は −23%（p=0.12）でいずれも 5/5。両方（deny 4 本 + low）で処理入力 −44%・費用 −24%
- effort を既定で下げないのは、正誤が落ちないと言えるのが trap（答えの決まった見積）だけだから。Sonnet 4.6 以降は過去ターンの thinking を文脈に残して入力として課金する（keep-all）ので、thinking を減らすと出力だけでなく再送も減る。これは利用者が仕事の型で選ぶ量

## 捨てた案
- Agent と Skill も外す（固定分 −12,151・−35%）: researcher への委譲と task-start 等のスキルが呼べなくなる
- `--tools` フラグ: settings に置けず、起動のたびに付けることになる。`permissions.deny` で同じ量が落ちる
- `--disallowedTools ToolSearch`: 遅延ロードが切れて +16,031。TodoWrite 等の task-tracking ツール名を書くと一群が opt-in されて相殺する（−1,037 に留まる）
- CLI に複数ファイルの `ref add` や `task new --purpose` を足す: 畳める連続ターンが 0 件で、効く対象が無い
- researcher に `effort: low`: Claude 側は haiku で effort 非対応。Codex 側は gpt-5.6-luna への切り替え（PR #21）で `max` を選んだ経緯がある
- cache の TTL を 5 分にする（書き込み単価 $4 → $2.5）: 人が間を置いて頼む使い方では 5 分で切れて全文を書き直す。README に「API キーの人は既定が 5 分」とだけ書く

## 影響
ルートで起動した利用者は `/loop`（ScheduleWakeup）・Workflow・ReportFindings・ListAgents が使えない。要るなら settings の該当行を消す。Codex には対応する仕組みが無い（ツール定義は Codex 側が固定）。README「セッションの切り方」の 2 乗則の式に、セッション開始の書き込み（約 15k × 2 倍単価）が乗ることを書き足す。1 タスク = 1 セッションは変えないが、数分で終わる質問にセッションを切らない理由がもう 1 つ増えた。

根拠: `docs/sources/token-saving.md` #17〜#34、`bench/results/fixed_v3.md`・`fixed_v3.jsonl`・`runs_v3.jsonl`
