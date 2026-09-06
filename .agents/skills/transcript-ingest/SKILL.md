---
name: transcript-ingest
description: Teams・Zoom などの会議の文字起こし（トランスクリプト）を渡されて、要点やナレッジにするとき。文字起こしには誤変換が多い前提で、案件の用語集で機械的に直してから解釈する。「この文字起こしをまとめて」「議事録にして」「会議の内容をナレッジ化して」で使う。
context: fork
agent: researcher
background: false
---
# transcript-ingest

あなたは、この指示だけで最後まで作業する調査係。本線の会話は見えず、聞き返す相手もいない。**確認や質問をせず、今すぐ下の手順を実行して結果を返す。**

処理する文字起こし: $ARGUMENTS
（上が空なら `scripts/ws task current` で現在のタスクを確かめ、その `references/` で frontmatter `kind: transcript` の要点ファイル（`.orig.md`・`.normalized.md`・`.summary.md` を除く）のうち最新のものを使う。案件が分からないときは `--project <案件>` が付いている）

ゴール: 原文は `references/` に残り、正規化版から決定事項・宿題・論点・固有名詞・未確定の用語が `<stem>.summary.md` に書かれ、同じ内容が返っている状態。

## 手順（順に実行する）
1. `scripts/ws ref add <file> --kind transcript --summary "会議名 日付"`。渡されたファイルが既に `references/` 配下にあるなら飛ばす。
2. `scripts/ws transcript normalize <保存された要点ファイル>` を実行し、出力される置換一覧（何を何回直したか）を確認する。
3. **正規化版（`*.normalized.md`）だけを読む。** 原文（`.orig.md`）は読まない。1 万字を超えると normalize が警告するので、その場合は `sed -n '1,200p' <file>` のように時刻の区切りで範囲を分けて読む。
4. `<stem>.summary.md` を `references/` に書く。frontmatter は `title: "<会議名> の要点"`、`kind: summary`、`source: "<正規化版のパス>"`、`summary: "1 文"`。本文は次の 5 節: 決定事項 / 宿題（誰が・何を・いつまでに）/ 論点 / 出てきた固有名詞 / 未確定の用語。
5. 文脈から確定できた誤変換は `scripts/ws glossary add <project> "正式表記" --alias "誤変換" --desc "説明"` で用語集に足し、normalize をやり直す。確定できない語は推測で埋めず「未確定の用語」に残す。
6. 返答は `<stem>.summary.md` のパスと、決定事項・宿題・未確定の用語の箇条書き。文字起こしの本文は返さない。

ナレッジに昇格するかの判断と `index.md` の更新はこのスキルの外（本線）で行う。

## 誤変換の見分け方
- 同じ人名・製品名が数行おきに違う表記で出る → 用語集の候補。
- 文脈に合わない一般語（「久保ネティス」「修二定例」）→ 音が似た固有名詞を疑う。用語集の「読み」列で探す。

## つまずきどころ
- 正規化前の原文（`.orig.md`）を読もうとすると hook が正規化版に読み替える（Bash の `cat`/`sed` は deny される）。原文を直接開こうとせず、常に正規化版のパスから始める。
- 用語集に 1〜2 文字の語や一般語（「移行」「対応」）を足さない。関係ない箇所まで置換される。固有名詞と略語だけを足す。
- 数字・日付・金額は誤認識が多い。前後を読んで確かめ、確信が無ければ「未確定の用語」に残す。
- **Codex では fork されない。** 本線で走らせるときは、手順 3〜4（読解と抽出）を `researcher`（`spawn_agent`）に渡すか、本線で正規化版を分割して読む。
