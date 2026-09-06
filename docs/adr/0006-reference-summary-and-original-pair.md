# 0006. reference は要点 `.md` と原文 `.orig.md` の対で保存する
- 状態: 採用 / 日付: 2026-09-06

## 状況
Web の出典はページ丸ごと残す方針（20 万字の打ち切りを廃止）にしたため、reference 1 ファイルに要点と原文が同居すると、次のセッションが要点を見るだけでページ全体を読む。原文は数十 KB〜200 KB ある。
## 決定
`ref add` は `<name>.md`（frontmatter・引用した記述・使いどころ・原文へのポインタ）と `<name>.orig.md`（本文そのまま）を同じディレクトリに対で保存し、`index.md` の一覧には要点側だけ載せる。`transcript normalize` は原文側を読む。`doctor` が対の欠落を警告し、旧形式（1 ファイル）は通す。旧形式は `ref split` で移行する。
## 理由
Claude Code は compact 後に直近 5 ファイルを再読するが、5,000 トークンを超えるファイルはパス参照だけになる。要点側が小さければ中身ごと生き残る。`docs/snapshots/` の実測は要点 0.9〜1.6 KB に対し原文 8.8〜212 KB。
## 捨てた案
- 原文を `references/orig/` のような別ディレクトリに置く: 隣に `.orig.md` があるかの 1 判定で normalize・doctor・読み替え hook が済むほうが単純（`.normalized.md` と同じ流儀）
- Read の出力上限（`CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS` 等）を下げる: 原文を確かめたい場面の全文まで切れる
- 20 万字の打ち切りを残す: ページ丸ごと残す方針に反する。一覧に載るのは summary だけなので本体が長くても読む量は増えない
## 影響
1 情報源が 2 ファイルになる。情報源そのものが `.orig.md` という名前のときは接尾辞を付け替える。原文を読むのは引用の実在を確かめるときだけ。

根拠: `docs/token-saving-sources.md` #1・kanban T-0NG9F・T-4ZFES・設計書 D-X26K2（2 節の表・採らなかった案）・D-GAD0W（採らなかった案の表）
