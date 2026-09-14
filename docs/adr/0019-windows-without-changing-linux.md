# 0019. Windows（Claude Code / Codex CLI）から同じ hooks と CLI で使えるようにする。Linux 側の挙動は変えない
- 状態: 採用 / 日付: 2026-09-14
## 状況
hooks は Linux 前提だった（shell 形式の `python3 "$CLAUDE_PROJECT_DIR/scripts/ws"`）。Windows では Git Bash が無いと PowerShell に渡って変数が展開されず、`python3` は python.org の installer に無い。ツール入力のパスはバックスラッシュで届き（Git Bash 下でも同じ）、`projects/<案件>/tasks/<タスク>` を `/` で見る拒否判定が黙って素通りする。日本語 Windows は stdin/stdout が cp932。Windows では PowerShell ツールが主シェルになる（根拠 #1）。核の `scripts/ws` は標準ライブラリだけで、bash スクリプト・symlink 生成・chmod は使っていない。

## 決定
- Claude Code の hooks は exec 形式（`command` + `args`、`${CLAUDE_PROJECT_DIR}` 置換、シェル無し）にし、実行ファイル名は両 OS 共通の `python`。statusLine は exec 形式が無いので shell 形式のまま `python`
- Codex は `commandWindows` で Windows だけ別コマンド（#2）。Linux 側の `command` は触らない
- `scripts/ws` の Windows 対応（`\` → `/` の正規化、UTF-8 化、PowerShell の検知語）は `os.name == "nt"` と `tool == "PowerShell"` の下にだけ置く。Linux では no-op
- エージェント向けの `scripts/ws …` の表記（AGENTS.md・skills・拒否の理由文）は置換しない。Windows では最初の 1 回の失敗から `python scripts/ws` に読み替える

## 理由
exec 形式は Linux でも同じ意味（シェルを介さなくなるだけ）で、1 本の settings.json が両 OS で動く。表記を `python scripts/ws` に置換すると、利用者の settings で `Bash(python *)` が deny のとき Linux 側の手打ちが止まる（deny は具体的な allow より優先）。手打ちの読み替えは 1 ターンの損で済む。

## 捨てた案
`python scripts/ws` に置換して `Bash(python scripts/ws *)` を allow（deny に負ける）。`uv run python scripts/ws` に置換（Windows にも uv を要求し、標準ライブラリだけの前提を崩す）。`.claude/skills` の symlink を消して `.agents/skills` 一本にする（一時ディレクトリに両方置いて headless で列挙させると Claude Code 2.1.26x は `.claude/skills` 側しか読まなかった。symlink は残し、Windows は開発者モードで `core.symlinks=true`）。shell 形式のまま `py -3`（Linux に無い）。

## 影響
Linux は `python` が PATH に要る（Debian 系は `python-is-python3`）。Codex は hooks.json のハッシュが変わるので `/hooks` で trust し直す。Windows 実機での発火確認は利用者側で行う。`.gitattributes` で改行を LF に揃える（Windows の `Path.write_text` は CRLF を書く）。
根拠: #1 `docs/snapshots/20260906_1731_Hooks_reference_-_Claude_Code_Docs.orig.md`（exec 形式・Git Bash / PowerShell・バックスラッシュのパス・PowerShell ツール）、#2 `docs/snapshots/20260909_0041_Hooks_ChatGPT_Learn.orig.md`（`commandWindows`）、`tests/test_ws.py` の PowerShell と正規化のテスト
