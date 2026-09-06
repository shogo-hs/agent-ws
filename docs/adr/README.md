# ADR 一覧 — agent-ws の設計判断

規約（AGENTS.md）や hooks を書き換える前に読む場所。**決定と理由だけ**を 1 本 20 行以内で書き、経緯は作者の作業記録へのリンクで済ませる。
案件の仕事では読まなくてよい（現在のタスクがあっても hook は止めない）。

| 番号 | タイトル | 状態 | 要約 |
|---|---|---|---|
| [0001](0001-enforce-with-hooks.md) | 「他タスクを読まない」は hook で止める | 採用 | プロンプトの指示は助言。拒否の理由文で knowledges/ へ誘導する |
| [0002](0002-one-task-one-session-and-cache-guard.md) | 1 タスク = 1 セッション。キャッシュ切れ後の 1 通目は止める | 採用 | TTL は 60 分（Claude サブスク）/ 30 分（Codex）/ 5 分（API キー） |
| [0003](0003-session-scoped-current-task.md) | 「現在のタスク」はセッションごとに持つ | 採用 | `.ws/sessions/<session_id>.current`。同じ clone で並行できる |
| [0004](0004-knowledges-single-source.md) | ナレッジの正本は knowledges/ だけ | 採用 | 他タスクの tasks/ は拒否。新規タスクで他タスクへの立ち入り 0 回 |
| [0005](0005-lessons-on-first-correction.md) | 指摘は 1 回目で LESSONS.md に残す | 採用 | 2 回目を待つ規則は機能しない。20 行超で減らす |
| [0006](0006-reference-summary-and-original-pair.md) | reference は要点と原文の対 | 採用 | compact 後に中身ごと残るのは小さいファイルだけ |
| [0007](0007-transcript-in-fork.md) | 文字起こしは fork の中で処理する | 採用 | 本線に本文を入れない。Codex は規約と既定モデルで代替 |
| [0008](0008-delegation-four-conditions.md) | 調査係へ渡す仕事は 4 条件で決める | 採用 | 1 回でまとめて渡す。効果は bench で未測定 |

## 書き方

```markdown
# NNNN. タイトル
- 状態: 採用 / 日付: YYYY-MM-DD

## 状況
## 決定
## 理由（数字があれば台帳の値をそのまま）
## 捨てた案
## 影響

根拠: docs/sources/<name>.md の行（#N）・kanban T-XXXXX・設計書 D-XXXXX
```

番号は連番。既存の ADR は書き換えず、決めを変えるときは新しい番号で置き換える（元の状態欄を「NNNN で置き換え」にする）。
`T-XXXXX` / `D-XXXXX` は作者の作業記録（kanban と html-hub）の ID で、このリポジトリの外にある。テンプレートから自分の作業スペースを作った人は、自分の記録の ID に読み替えて使う。
