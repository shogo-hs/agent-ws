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

| [0020](0020-codex-researcher-luna-max-read-to-end.md) | Codex の調査係は gpt-5.6-luna・max にし、researcher に「末尾まで読み切る」規則を足す | 採用 | gpt-5.4-mini は 2026-08-31 に Codex（ChatGPT ログイン）から退役。low は読み切らずに書き始め、規則を足しても 8 回中 2 回は決定の 4 割を落とす。max は 7 回とも落とさず、代償は時間 2.4 倍と luna 単価のトークン 3 倍 |
| [0021](0021-deny-unused-eager-tools-and-effort-knob.md) | 使わない常時ロードのツール定義は `permissions.deny` で外す。effort と thinking は既定を変えず調整ノブにする | 採用 | 固定分 35,105 のうち 4,884 が案件の仕事で呼ばれないツールの定義。bench trap で処理入力 −28%・費用 −14%。effort medium は費用 −14% で 5/5 正解だが、正誤が保てると言えるのが trap だけなので既定にしない |
| [0022](0022-operational-ontology.md) | 業務のオントロジーは「業務を動かす層」として入れる。定義は JSON、解釈と強制は scripts 側 | 採用 | 型・つながりと件数・継承・アクション（引数・前提条件・ルール・承認）を JSON に定義し、`scripts/wsonto/` が前提条件を実体の値で判定して理由つきで拒否する。承認は人だけ（発言か端末）。エージェントは実体を直接読み書きできない。定義の変更も lint と承認を通す。W3C の形式に書き出し、pySHACL と同じ判定になることをテストする |
| [0023](0023-ws-init-removes-unchanged-examples.md) | 同梱の見本は scripts/ws init で消す。消すのは同梱時から内容を変えていないファイルだけ | 採用 | `templates/examples.json` の「パス → sha256」と一致するファイルだけ消す。書き換えたファイルと足したファイルは残り、実行結果に名前が出る。消せるファイルが残っている間だけ SessionStart が 1 行案内する |

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
