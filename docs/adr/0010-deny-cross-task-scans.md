# 0010. projects/ を横断する一覧・検索は hook で拒否する
- 状態: 採用 / 日付: 2026-09-06

## 状況
0001 と 0004 は「他タスクのパスを含むアクセス」を拒否するが、`find projects -maxdepth 3` や path を指定しない Grep / Glob は他タスクのパスを含まないまま全タスクの名前と本文を返す。bench の仕組みなし条件では `find projects` 1 回の結果が 9,000 字だった。
## 決定
現在のタスクがある間、対象が `projects` / `projects/<案件>` / `projects/<案件>/tasks` / ルート（Grep・Glob の path 未指定、`find .` `rg 単価 .` など）の一覧・検索（find / ls / tree / grep -r / rg と Grep / Glob）を拒否し、`projects/index.md`・`tasks/index.md`・`knowledges/`・現在のタスクへ誘導する。`projects/index.md` のようなファイル指定は通す。現在のタスクが無いとき（agent-ws 自体を直すとき）は止めない。
## 理由
一覧は index.md にある（0004）。検索結果に他タスクの本文が混ざると「正本は knowledges/ だけ」が崩れ、読む量も増える。規約だけでは守られない（0001）。
## 捨てた案
- PostToolUse の `updatedToolOutput` で結果から他タスクの行を削る: 結果の形式ごとの整形が要り、Codex は未対応（parsed but not supported yet）
- 規約に書くだけ: 0001 と同じ理由
## 影響
案件をまたぐ検索は `knowledges/` を案件ごとに指定する。`cd <現在のタスク> && find .` は通る（コマンドに現在のタスクのパスがあれば「.」を対象に数えない）。

根拠: `docs/sources/token-saving.md` #7・#8・kanban T-G6KJ5・設計書 D-1GVS1
