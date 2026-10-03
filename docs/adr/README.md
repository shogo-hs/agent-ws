# ADR 一覧 — agent-ws の設計判断

規約（AGENTS.md）や hooks を書き換える前に読む場所。**決定と理由だけ**を 1 本 20 行以内で書き、経緯は作者の作業記録へのリンクで済ませる。
案件の仕事では読まなくてよい（現在のタスクがあっても hook は止めない）。

| 番号 | タイトル | 状態 | 要約 |
|---|---|---|---|
| [0001](0001-enforce-with-hooks.md) | 「他タスクを読まない」は hook で止める | 採用 | プロンプトの指示は助言。拒否の理由文で knowledges/ へ誘導する |
| [0002](0002-one-task-one-session-and-cache-guard.md) | 1 タスク = 1 セッション。キャッシュ切れ後の 1 通目は止める | 採用 | TTL は 60 分（Claude サブスク）/ 30 分（Codex）/ 5 分（API キー） |
| [0003](0003-session-scoped-current-task.md) | 「現在のタスク」はセッションごとに持つ | 採用 | `.ws/sessions/<session_id>.current`。同じ clone で並行できる |
| [0004](0004-knowledges-single-source.md) | ナレッジの正本は knowledges/ だけ | 採用（横断の置き場は 0015 で置き換え） | 他タスクの tasks/ は拒否。新規タスクで他タスクへの立ち入り 0 回 |
| [0005](0005-lessons-on-first-correction.md) | 指摘は 1 回目で LESSONS.md に残す | 採用 | 2 回目を待つ規則は機能しない。20 行超で減らす |
| [0006](0006-reference-summary-and-original-pair.md) | reference は要点と原文の対 | 採用 | compact 後に中身ごと残るのは小さいファイルだけ |
| [0007](0007-transcript-in-fork.md) | 文字起こしは fork の中で処理する | 採用 | 本線に本文を入れない。Codex は規約と既定モデルで代替 |
| [0008](0008-delegation-four-conditions.md) | 調査係へ渡す仕事は 4 条件で決める | 採用（Codex 側の受け皿は 0020 で置き換え） | 1 回でまとめて渡す。効果は bench で未測定 |
| [0009](0009-inject-index-at-session-start.md) | SessionStart で index.md 全文とナレッジ一覧を注入する | 採用 | 消費の 93〜95% はターンごとの再送。Read のターンを省く。効果は bench で未測定 |
| [0010](0010-deny-cross-task-scans.md) | projects/ を横断する一覧・検索は hook で拒否する | 採用 | find projects や path 無しの Grep は他タスクの本文を返す |
| [0011](0011-no-apm-distribution.md) | 配布に Microsoft APM を使わない | 採用 | 逐語の重複は researcher の 4 行だけ。移すと単一正本がハーネスごとのコピーに戻る |
| [0012](0012-token-levers-are-session-length-not-tools.md) | 索引・グラフ・出力圧縮のツールは入れない | 採用 | 消費はセッション長の 2 乗。tool search が既定オンで MCP の削減余地は無い |
| [0013](0013-no-backend-context-engineering-port.md) | InsForge 型の backend context engineering は取り込まない | 採用 | 狭い skills・CLI・1 回の状態注入・拒否文は同等物が既にある。bench で拒否は 45 本中 3 回 |
| [0014](0014-no-ontology-layer.md) | 重いオントロジー（グラフ DB・MCP・precondition）は入れない。軽い関係層は実務で判断する | 0022 で置き換え | 前提の注入・用語集・hook が同等物。関係の欄は任意で足し、手戻りの 3 型を LESSONS に数えて 3 案件後に決める |
| [0016](0016-no-llm-retrospective-count-instead.md) | セッション終了時の自動レトロスペクティブは LLM に振り返らせない。数えられる指標を残し、規約の変更は人が決める | 提案 | SessionEnd は LLM 型 hook 不可・最大 60 秒。先行実装 10 本に効果の測定なし。正解の無い自己判定は精度を下げ、自動追記は 1,421 行に育つ。`ws retro` で拒否・ターン・文脈を数え、doctor が人に見せる |
| [0015](0015-common-knowledges-for-cross-project-facts.md) | 案件をまたぐ自社の事実は repo 直下の knowledges/（共通）に置く | 採用 | 組織図・決裁範囲・社内システム・標準手順・共通用語。3 ヶ月変わらないものだけ、案件側が勝つ、1 ファイル 1 担当で 90 日で doctor が警告。注入の増分は 274 字 |
| [0017](0017-disable-claude-code-advisor.md) | Claude Code の Advisor（相談役モデル）はリポジトリの settings で外す | 採用 | 正誤に効かず（5/5 対 5/5）相談が起きた本だけ 3.4〜3.7 倍。相談 1 回で Opus が 44k を非キャッシュで読む。`env` の `CLAUDE_CODE_DISABLE_ADVISOR_TOOL=1`。戻すなら行を消す |
| [0018](0018-done-by-human-or-doctor.md) | done は人が言ったときか doctor の棚卸しで付ける。current は「最後に触ったタスク」 | 採用 | エージェントは完了を判断できない。`task done [path]`、doing 14 日放置を doctor が列挙、done は current 扱いしない。セッション内直列・セッション間並列のどちらでも成り立つ |
| [0019](0019-windows-without-changing-linux.md) | Windows から同じ hooks と CLI で使えるようにする。Linux 側の挙動は変えない | 採用 | Claude Code は exec 形式で `python` を直接起動、Codex は `commandWindows`。`\` → `/` の正規化・UTF-8 化・PowerShell の検知は `os.name == "nt"` / `tool == "PowerShell"` の下だけ。手打ち表記は置換しない |

| [0020](0020-codex-researcher-luna-max-read-to-end.md) | Codex の調査係は gpt-5.6-luna・max にし、researcher に「末尾まで読み切る」規則を足す | 0025 で置き換え | gpt-5.4-mini は 2026-08-31 に Codex（ChatGPT ログイン）から退役。low は読み切らずに書き始め、規則を足しても 8 回中 2 回は決定の 4 割を落とす。max は 7 回とも落とさず、代償は時間 2.4 倍と luna 単価のトークン 3 倍 |
| [0021](0021-deny-unused-eager-tools-and-effort-knob.md) | 使わない常時ロードのツール定義は `permissions.deny` で外す。effort と thinking は既定を変えず調整ノブにする | 採用 | 固定分 35,105 のうち 4,884 が案件の仕事で呼ばれないツールの定義。bench trap で処理入力 −28%・費用 −14%。effort medium は費用 −14% で 5/5 正解だが、正誤が保てると言えるのが trap だけなので既定にしない |
| [0022](0022-operational-ontology.md) | 業務のオントロジーは「業務を動かす層」として入れる。定義は JSON、解釈と強制は scripts 側 | 採用 | 型・つながりと件数・継承・アクション（引数・前提条件・ルール・承認）を JSON に定義し、`scripts/wsonto/` が前提条件を実体の値で判定して理由つきで拒否する。承認は人だけ（発言か端末）。エージェントは実体を直接読み書きできない。定義の変更も lint と承認を通す。W3C の形式に書き出し、pySHACL と同じ判定になることをテストする |
| [0023](0023-ws-init-removes-unchanged-examples.md) | 同梱の見本は scripts/ws init で消す。消すのは同梱時から内容を変えていないファイルだけ | 採用 | `templates/examples.json` の「パス → sha256」と一致するファイルだけ消す。書き換えたファイルと足したファイルは残り、実行結果に名前が出る。消せるファイルが残っている間だけ SessionStart が 1 行案内する |
| [0024](0024-researcher-omit-claude-md-and-opus55-tips.md) | researcher は CLAUDE.md を読まずに起動する。途中経過の報告だけで返事を終えない。`/goal` は README で案内するだけにする | 採用 | researcher.md に `omitClaudeMd: true`（1 リクエスト目の入力 −31%、正答率は落ちない）。AGENTS.md に途中報告で返事を終えない 1 文。Skill の effort・Stop hook の自動継続・Agent Teams などは採らない |
| [0025](0025-codex-researcher-gpt6-luna-high.md) | Codex の調査係は gpt-6-luna・high にする（0020 を置き換え） | 採用 | 同じ抽出で gpt-5.6-luna・max と同じく 5/5 全問正解、クレジット −74%・時間 −55%。gpt-6-luna・max は高く遅く、決定を落とす回があった。Codex CLI 0.156.1 以上が要る |
| [0026](0026-wrap-originals-in-random-id-tags.md) | ref add の原文を同じランダム ID の開始タグと終了タグで囲み、タグの中の指示は人の依頼が求めるときだけ従う | 採用 | 公式の多層防御のひとつ。3 モデル 60 回の bench では両条件とも従わず、効果は測れなかった（床効果）。Haiku はタグがあると指示に触れる回が減るので、researcher に「知らせる」を書いた |
| [0027](0027-state-each-fixed-instruction-once.md) | 毎ターン送る固定の指示は 1 か所にだけ書き、オントロジーの使い方は定義があるときだけ注入する | 採用 | 固定分は Claude −5.1%・Codex −4.5%。trap・newtask × Claude・Codex の 80 回で正誤は落ちず、費用の差が有意だったのは Claude の newtask（−6%）だけ。OpenAI の −41〜66% は、変えられるのが固定分の約 3 割なので再現しない |
| [0028](0028-check-quotes-against-original-on-promote.md) | 「引用した記述」が原文にあるかを know new と doctor が機械で照合する（AGENTS.md は変えない） | 採用 | 調査係の引用 12 か所が原文とずれたまま通った（issue #36）。固定分と追加のターンは 0、合っていれば出力も増えない。効果は未測定 |
| [0029](0029-quote-check-precision-on-real-data.md) | 引用の照合は原文と引用の両方から Markdown の記号を除き、括弧の中だけを見る | 採用 | 実データ 1,084 行で「原文に無い」が 227 → 45。0028 のままだと適合率 約 16%。PR #40 で `<` の扱いを直して 16（本物 約 9・誤検知 約 7。当初の「本物 約 37」は誤り） |
| [0030](0030-check-deliverable-quotes-against-cited-source.md) | タスクの成果物の「出所: … 引用: 「…」」を、出所が指すファイルと照合する | 採用 | issue #36 の事故 12 か所のうち 6 か所を誤検知 0 で拾う（0028・0029 は 0）。実際の成果物の引用 410 件で誤検知 0 |
| [0031](0031-arxiv-html-instead-of-pdf.md) | arXiv の論文は PDF ではなく HTML 版を本文にし、版で固定して保存する | 採用 | 実際の台帳の引用 64 件で一字一句の一致は HTML 版 49・PDF（段組なし）45・PDF（`-layout`）0。数式・表は LaTeX ソースで補う。r.jina.ai は arXiv の HTML 版に 331 バイトしか返さないので直接取る |
| [0032](0032-local-only-clone-and-template-update.md) | テンプレートを clone したまま使う運用（ローカル運用）を受け入れ、push を 3 段（宛先・pre-push・hook）で止める。更新の取り込みは `scripts/ws update` | 採用 | 古い版の clone に未コミットの作業 3 つを加えて `git pull --autostash` で最新に上げ、3 つとも残った。宛先だけだと URL の直書きで 1 行で回り込める |

## 書き方

```markdown
# NNNN. タイトル
- 状態: 採用 / 日付: YYYY-MM-DD

## 状況
## 決定
## 理由（数字があれば台帳の値をそのまま）
## 捨てた案
## 影響

根拠: docs/sources/<name>.md の行（#N）・bench/results/ のファイル・GitHub の issue / PR
```

番号は連番。既存の ADR は書き換えず、決めを変えるときは新しい番号で置き換える（元の状態欄を「NNNN で置き換え」にする）。
根拠には**このリポジトリの中か GitHub で辿れるものだけ**を書く（`docs/sources/` の行番号・`bench/results/` のファイル・issue / PR 番号）。
手元のチケット管理やドキュメント管理システムの ID は書かない。読む人が辿れないため。
