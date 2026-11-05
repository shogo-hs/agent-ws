# 0037. Bash の実行中に変わったファイルも、そのセッションが書いたものとして記録する
- 状態: 0038 で置き換え / 日付: 2026-11-05

## 状況
0036 は Edit・Write・apply_patch と `scripts/ws` の書き込みだけを記録した。Claude Code は Bash の中の Python や `sed` でファイルを直すことが多く、`task done` のコミットからスキル・スクリプト・ナレッジが漏れ、パスを指定して別にコミットし直していた。
## 決定
PreToolUse で Bash の実行前の時刻を `.ws/sessions/<session_id>.bash_start` に置き、PostToolUse（Claude Code の matcher に Bash を足す）で git の変更一覧のうち、その時刻より後に更新されたファイルを `.touched` に足す。
## 理由
hook には書き先が届かないが、実行の前後はわかる。git status は 1 回 0.03 秒（Raspberry Pi 5 で実測）で、Bash のたびに走らせても負担にならない。
## 捨てた案
- 次のツール呼び出しの PreToolUse でまとめて拾う: Codex でも効くが、モデルが考えている間の他のセッションの書き込みまで拾う。
## 影響
同じ clone の他のセッションが同じ時間に書いたファイルも拾う。Codex は PostToolUse を登録していないので、Codex の Bash で書いたファイルは従来どおり残りの一覧に出る。消したファイルは拾わない。
