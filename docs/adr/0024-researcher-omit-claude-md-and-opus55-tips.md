# 0024. researcher は CLAUDE.md を読まずに起動する。途中経過の報告だけで返事を終えない。`/goal` は README で案内するだけにする
- 状態: 採用 / 日付: 2026-10-03

## 状況
Claude Code のハーネスを 7 層（effort・記憶・手順・道具・分業・安全・完了）で組む個人の記事を手がかりに、主張 31 件を公式の文書で確かめた（28 件一致・3 件一部違い。`docs/sources/harness-tips.md`）。agent-ws と突き合わせると 7 層の大半は既にある。effort は調整ノブ（0021）、規約は文脈で強制は hooks（0001）、手順はスキル、分業は researcher（0008）、完了の印は index.md の「進め方」。新しく効くのは次の 3 つだった。①自作のサブエージェントは既定で CLAUDE.md を読むので、委譲のたびに AGENTS.md の全文が researcher にも入る（#14）。②Opus 5.5 は長い作業の途中経過を伝える返事で、ツールを呼ばずにターンを終えることがある（#3）。③`/goal` で終わりの条件を別のモデルに判定させられる（#19）。

## 決定
- `.claude/agents/researcher.md` に `omitClaudeMd: true`（v2.1.271 以降）。researcher に要る規則は本文に持つ。足りなかった「根拠は一次情報の順」を本文に足した（Codex の `researcher.toml` にも同じ文）。tasks の外・`docs/snapshots/`・`bench/` の拒否は hook が持つので、CLAUDE.md が無くても効く
- AGENTS.md「ターンを減らす」に、途中経過の報告だけで返事を終えない、止まって聞くのは人の判断が要るときと取り消せない操作の前だけ、を足す（#4 の公式の文例）
- README に、`/goal` の書き方（判定役は会話だけを見る、回数の上限を条件に入れる）、`/rewind` で戻らないもの（Bash とサブエージェントが変えたファイル）、Opus 5.5 は medium で始まることを書く

## 理由（`bench/researcher_omit.py`・`bench/results/runs_omit.jsonl`。本線 sonnet が 1,134 行の文字起こしの抽出を researcher に渡す。base と omit を交互に各 n=5、並べ替え検定）
- researcher の 1 リクエスト目の入力は 12,067 → 8,353（−3,714・−31%、p=0.008）、処理した入力の合計は 92,857 → 82,372（−11%、p=0.008）、cache 作成は 35,836 → 31,986（−11%、p=0.008。いずれも中央値）
- 正答率（決定 20・宿題 15・混ぜてはいけない案 12）は base 4/5・omit 5/5 で全問正解。落ちてはいない（差は n=5 では誤差の範囲）
- 実際の利用では利用者の `~/.claude/CLAUDE.md` も外れる。bench は `--setting-sources project` なので、この分は数字に入っていない

## 捨てた案
- Skill に `effort` を書く: 本線の途中で effort が変わる。API では top-level の effort を変えるとキャッシュが無効になる（#3）。Claude Code の内部でも同じかは確かめていないが、cache 作成は最大の費目（0021）なので試さない。researcher は haiku で effort に対応しない（0021）
- Stop hook で、「進め方」が残っていれば自動で続けさせる: 人が見ている使い方では、止まって聞くのが正しいことが多い。公式も自動の継続は 2〜3 回で止めるよう勧めている（#3）。人が離れるときは `/goal` で足りる
- `permissions.deny` に `Read(./.env)` などを書く: agent-ws には `.env` も公開済みのフォルダも無い。deny は Python や Node が自分で開くファイルを止めない（#16）。読む範囲は hook で絞っている
- Notification hook（入力待ちの通知）: 利用者の `~/.claude` の設定で、OS ごとに中身が違う。テンプレートが持つものではない（#17）
- Agent Teams: 実験的で既定オフ。有効にすると、名前を付けて呼んだサブエージェントがチームメイトとして動く（#15）。researcher への委譲の形が変わる
- 経過時間と持ち時間を毎ターン伝える: 並列の多エージェント向けの話。調べ物と確認が少し減る副作用がある（#3）。researcher は 1 本ずつ呼ぶ
- 規約を `.claude/rules/` に paths 付きで分ける: compact のあと、該当ファイルに触るまで消える（#8）。AGENTS.md は 61 行で、分ける理由が無い

## 影響
researcher は AGENTS.md と利用者の `~/.claude/CLAUDE.md` を読まない。researcher に守らせたい規則は `researcher.md` の本文に書く（AGENTS.md に書いても届かない）。2.1.271 より前の Claude Code での挙動は確かめていない。Codex は今までどおり AGENTS.md を読む（同じことをする設定は見つけていない）。AGENTS.md は 1 行が長くなったが、行数は変わらない。

根拠: docs/sources/harness-tips.md #3・#4・#8・#14〜#17・#19、`bench/results/runs_omit.jsonl`
