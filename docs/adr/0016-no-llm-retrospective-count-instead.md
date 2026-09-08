# 0016. セッション終了時の自動レトロスペクティブは LLM に振り返らせない。数えられる指標を残し、規約の変更は人が決める
- 状態: 提案 / 日付: 2026-09-09

## 状況
「作業終了時に hook で transcript を振り返り、うまくいった／いかなかったことをまとめて AGENTS.md・hooks・skills を自動で改善すれば、トークン効率と遂行の滑らかさが上がるのでは」という提案を検討した。hook の仕様（一次情報 2 本）、振り返りで文脈を育てる研究 8 本、Claude Code / Codex の先行実装 10 本、実セッション 185 本のコスト実測で判断した。

## 決定
1. **入れない**: Stop / SessionEnd hook から transcript を LLM に読ませて要約し、規約ファイルを自動で書き換える仕組み。
2. **入れる**: `scripts/ws retro` — transcript から**数えられる指標だけ**（ターン数・最終文脈・Read／検索の回数・hook の拒否とその理由・キャッシュ切れの停止・委譲回数・指摘らしき人の発言の有無）を 1 セッション 1 行で `.ws/retro.jsonl` に残す。SessionStart hook が未処理の transcript を処理する（Claude Code・Codex とも。LLM は呼ばない。bench の解析器を流用）。`doctor` が「拒否の多い理由」「指摘らしき発言があるのに LESSONS.md が変わっていないセッション」を**人に**見せる。エージェントの文脈には何も差し込まない。
3. **任意**: `ws retro explain <session>` は人が頼んだときだけ haiku に「人の発言だけ」を読ませ、lesson 候補 1 行を出す。自動では回さない。

## 理由
- **hook の仕様**: SessionEnd は決定権なし・既定 1.5 秒（設定で最大 60 秒）・prompt/agent 型 hook 不可。Codex は 1〜3 秒。Stop は毎ターン発火し「終わり」を知らない。先行実装 10 本はすべて LLM 処理を detach した背景プロセスに逃がしており、**効果を測ったものは 0 本**。Stop 一発型（ECC v1）は作者が deprecate した。
- **信号が無い**: 効いた研究（Reflexion・ACE・ExpeL）は全部テスト成否や exact match の報酬を前提にする。正解無しの自己判定は「全モデル・全ベンチで精度が下がる」（arXiv 2310.01798）。ACE 自身も「信頼できる信号が無いと劣化しうる」と書く。この環境で信頼できる信号は**人の指摘**と**数えられる事象**だけで、前者は既に ADR 0005 が受ける。
- **書き戻すと壊れる**: 上限なしの自動追記は作者の環境で 1,421 行の lessons.md を作った。指示 500 本で遵守率は最良 68%、Claude 4 系 43〜45%（IFScale）。LLM に全文を書き直させると 18,282 → 122 トークンに潰れる（ACE の context collapse）。
- **コスト**: `claude -p` 1 回の下駄が 20.7k トークン・0.016 USD・3.35 秒。transcript を丸ごと読ませると workspace の中央値 179k、43% が 20 万超で haiku に入らない。agent-ws のセッションは中央値で user 1 ターン・text 21 文字で、振り返る中身がそもそも無い。

## 捨てた案
- Stop + prompt 型 hook（Haiku）で毎ターン振り返る: 毎ターン下駄 20.7k が乗る。ターン数を減らす規約（0012）と逆行
- SessionEnd から detach した `claude -p` で LESSONS.md に自動追記: 上の「信号が無い」「書き戻すと壊れる」。20 行上限（0005）と両立しない
- 指摘のキーワード検知をエージェントの文脈に差し込む: 精度 3/22 で、外れの多い注意は無視される（0005 と同じ理由）。人に見せる `doctor` に留める
- PreToolUse/PostToolUse で常時観測して confidence を育てる（ECC v2）: 毎ターンの hook が増える方向で、測定も無い

## 影響
効果は未測定。案件が 3 つ回った時点で `.ws/retro.jsonl` の拒否理由の分布と「指摘らしき発言 − lesson add」の件数を見て、規約を減らす／hook を直す材料にする。`.ws/` は gitignore のまま。README「人からの指摘」と AGENTS.md は変えない。

根拠: `docs/sources/retrospective.md` #1〜#22・M1〜M3・`bench/results/retro_cost.csv`・`bench/results/retro_floor.json`
