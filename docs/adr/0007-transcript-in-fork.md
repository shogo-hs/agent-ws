# 0007. 文字起こしは fork した調査係の中で処理し、本線に本文を入れない
- 状態: 採用 / 日付: 2026-09-06

## 状況
1 時間の会議の文字起こしは 1 万字を超える。本線で読むとコンテキストを占め、auto-compact のスラッシングを起こす。初版は「時刻の区切りで範囲を分けて読む」と促すだけだった。
## 決定
transcript-ingest スキルの frontmatter に `context: fork` / `agent: researcher` / `background: false` を置き、Claude Code では調査係（haiku）の中で保存・正規化・抽出（決定事項・宿題・論点・固有名詞・未確定の用語）まで行って `<stem>.summary.md` に残す。本線は要点だけ受け取り、ナレッジ昇格の判断と `index.md` の更新を行う。正規化版がある原文を読もうとしたら PreToolUse が読み先を差し替える（Read/Grep は `updatedInput`、シェルは deny＋理由）。
## 理由
`context: fork` のスキルは会話履歴を持たず、`agent` の model が fork 先に効く（公式 skills 文書）。実機（Claude Code 2.1.263・7,900 字の架空の文字起こし）では本線の transcript に本文が 0 回、8 ターン 0.156 USD。n=1 なので効果の測定ではなく、動くことの確認。
## 捨てた案
- Codex の `compact_prompt` に残すものを書く: 既定の要約プロンプトを全文置き換えるので要約の質ごと自分で持つことになる。AGENTS.md の「compact するときに残すもの」節なら両ツールで効く
- シェルの `cat` も `updatedInput` で書き換える: コマンド書き換えは `allow` を伴い、混ざった他のコマンドまで承認なしで通す
## 影響
Codex は fork しない（未知の frontmatter は無視され、同じ SKILL.md が一覧に載ることは 0.153.4 で確認）。Codex では規約と `[agents]` の既定モデル（gpt-5.4-mini）で代替する。SKILL.md は fork 先が質問で返さないよう命令形で書く。

根拠: `docs/sources/token-saving.md` #3・#6
