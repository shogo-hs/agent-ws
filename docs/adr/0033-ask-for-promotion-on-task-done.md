# 0033. task done は knowledges が変わっていなければ止め、昇格の確認を人に聞かせる。status の直接の done は hook で拒否する
- 状態: 採用 / 日付: 2026-10-12

## 状況
他のタスクは hook が読ませない（0001・0010）ので、完了までに `knowledges/` へ昇格されなかった決定・仕様・手順は、以後どのタスクからも参照できない。昇格は AGENTS.md の「やること」とスキルに書いてあるだけで、`task done` は何も確かめずに閉じていた。完了の経路も `task done` だけではなく、エージェントが index.md の `status:` を書き換えて閉じることもできた（0018 の「frontmatter を直接 done にされたタスク」）。

## 決定
- `task new` が、案件と共通の `knowledges/*.md`（`index.md` を除く。非再帰なので `ontology/` は入らない）の本文のハッシュをまとめた値を、タスクの frontmatter の `knowledges_digest` に残す
- `task done` は同じ値を計算し直し、一致したら（このタスクの間に knowledges が変わっていなければ）完了にせず止める。返す文は「候補を人に見せて、knowledges に残すものはあるかを聞く。あれば know new、無いと人が答えたら `--no-promote "<人の答え>"`」。path 指定で現在のタスク以外を閉じるときは、先に `task use` を案内する（他のタスクは読めないので候補を挙げられない）
- `--no-promote` の理由は空なら拒否し、1 行に潰して frontmatter の `no_promote` に残す。`tasks/index.md` の行に「昇格なし: 理由」として出る
- 完了したら `knowledges_digest` を空にする。`doctor` は「done なのに `knowledges_digest` が残っている」タスクを、`task done` を経ずに閉じたものとして出す
- pre-tool-use hook は、タスクの `index.md` の status を done にする Edit / MultiEdit / Write と Codex の `apply_patch` を拒否する。Edit 系は編集後の内容を組み立てて status を見る（`doing` → `done` の 1 語置換も拾う）。done を doing に戻す編集は止めない
- `knowledges_digest` を持たない既存のタスクは止めない
- hook は `task done` の前にセッションの写し（`.ws/sessions/<id>.current`）を消さない（use / new は従来どおり消す）。止まったあとに別セッションのタスクへ乗り移らず、未設定（空の写し）のセッションの `task done` が別セッションのタスク（`.ws/current`）を閉じることもない。閉じたタスクの写しは done なので未設定として扱われる（0018）

## 理由
- 判定にファイルの mtime を使うと、`git clone`・`checkout`・`ws update`（`--autostash` が退避したファイルを書き戻す）で今日の日付になり、素通りする側に壊れる。気づく手段も無い。frontmatter の `updated` は、Edit での直しや案件側の `glossary add` で変わらず、止めすぎる側に壊れる。本文のハッシュはどちらにも外れない
- 判定は止めるところまでで、昇格するかの判断はしない。正解の無い判断を LLM の自己判定に任せない（0016）ので、返し文で人に聞かせ、人の答えを理由として残す
- 拒否の場所は `task done` の中（Claude Code・Codex・人の手打ちの全部が通る）と、ファイル編集の hook だけにした。シェルでの書き換え（`sed -i`・`python -c`）は追いきれないので、`doctor` が後から拾う
- AGENTS.md には足さない。止まったときに返し文が手順を渡すので、毎ターンの固定分を増やさない（0027・0028）

## 捨てた案
- hook で `scripts/ws task done` のコマンド文字列を見て止める: `task done` の中で止めれば Codex の配線も文字列の解析も要らない
- 確認文を出すだけで閉じる: エージェントは読み流す
- `task done` 時に LLM が tasks/ を読んで昇格候補を自動で書く: 0016 と同じ理由
- 人が端末で打ったときは `input()` で理由を聞く: 人も `--no-promote` で足りる

## 影響
並行する同じ案件のタスクや、他案件が共通の `knowledges/` に昇格したときも値が変わり、確認なしで閉じられる。`know new` で雛形を作っただけでも通る（中身は見ない）。一度 done にして doing に戻したタスクは値が空なので、二度目の `task done` では止まらない。精度が要るようになったら、`know new` に出所のタスクを記録させて、それで判定する。既存のテストの `task done` には `--no-promote` を付けた。

根拠: `tests/test_ws.py` の `test_task_done_asks_for_promotion_and_direct_done_is_denied`
