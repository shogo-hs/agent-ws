# 0003. 「現在のタスク」はセッションごとに持つ
- 状態: 採用 / 日付: 2026-09-06

## 状況
現在のタスクは clone に 1 つの `.ws/current`（git 管理外）で決めていた。同じ clone で 2 セッションを並行させると、後から `task use` した側が先のセッションの現在のタスクを書き換え、先の側は自タスクの読み書きを hook に拒否され `ref add` の保存先も変わった（GitHub issue #1）。
## 決定
hook と CLI は `.ws/sessions/<session_id>.current`（セッションの写し）を先に見て、無ければ `.ws/current` を写してから使う。hook は stdin の `session_id`、CLI は環境変数 `CODEX_THREAD_ID` → `CLAUDE_CODE_SESSION_ID` で見分ける。環境変数の無い端末は従来どおり `.ws/current`。新しいセッションと `/clear` は最後に設定したタスクから始まる。`task done` は写しを消さず空にする。
## 理由
hook の stdin と shell の環境変数が同じ session_id を持つことを両ツールで実測した（Claude Code 2.1.245 / Codex 0.153.4）。hook だけ直しても `ref add` の保存先は直らないので CLI 側にも識別が要る。写しを消すと、完了したセッションが次の解決で他セッションのタスクを拾う。
## 捨てた案
- タスクフォルダに `cd` して起動し cwd で決める: サブディレクトリ起動ではルートの hooks が読まれない（Claude Code 2.1.261）
- clone を分ける（初版の制約）: 人ごと・マシンごとの状態は分かれるが、同じ人の並行作業には重い
## 影響
同じ clone で複数セッションを並行できる。`task use` 直後から次の hook までの数秒は `.ws/current` を見る。端末から叩く `task current` はセッションに紐付かない。

根拠: GitHub issue #1・PR #2・#3
