# 0018. done は人が言ったときか doctor の棚卸しで付ける。current は「最後に触ったタスク」
- 状態: 採用 / 日付: 2026-09-10

## 状況
`.ws/current` を外す経路は `task done` だけだが、完了を判断するのは結果を見た人で、エージェントの最後のターンより後に起きる。エージェントは「現在地・次の一手を更新して返す」までしかできず、セッションの終わり（端末を閉じる・`/clear`）に hook は無い。結果 `task done` は呼ばれず、`status: doing` が永久に残り、`tasks/index.md` と `doctor` が進行中だらけになる。`current_task()` は status を見ないので、frontmatter を直接 done にされたタスクも起動時に注入され続けた。
## 決定
- `.ws/current` の意味は「最後に触ったタスク」。再開の出発点に使うだけで、完了の印ではない。鮮度で自動解除はしない
- done は人が「終わった」と言ったときに `task done [path]` で付ける（path 指定で current 以外も閉じられる）。付け忘れは `doctor` が「doing のまま updated が 14 日超」として列挙し、`task done <path>` を案内する
- `current_task()` は `status: done` を未設定扱いにする（注入・statusLine・ref add・hook の全部に 1 ガードで効く）。`task use` は done のタスクを拒否する
- 前提: セッションの中は直列（1 セッション = 1 タスク）、セッションをまたげば並列（ADR 0003 の写し）。上の 3 点はどちらでも成り立つ

## 捨てた案
- エージェントに終了時の `task done` を規約で義務づける: 完了を判断できないので守られないか、中断を閉じてしまう
- 古い current を鮮度で未設定にする: 主用途は再開で、注入が消えると再開のたびに 2〜3 ターン損する。別タスクへ切り替えるときの無駄は 6,000 字以下 × 1 回
- `task new` / `task use` で「前のタスクは終わった?」と出す: 並列セッションで相手が進めている最中のタスクに出て雑音。A と B を行き来する使い方でも毎回出る

## 影響
doing のまま 14 日触らないタスクは doctor に出る（続けるなら現在地を更新、終わりなら閉じる）。done のタスクを続けるには index.md の status を doing に戻す。

根拠: `tests/test_ws.py` の `test_task_done_by_path_stale_doctor_and_done_is_not_current`・ADR 0003（セッションの写し）
