---
name: knowledge-promote
description: タスクの中で得た知見を、案件のナレッジ（knowledges/）に昇格するとき。「ナレッジにして」「次も使えるように残して」「他のタスクでも使う」で使う。ナレッジの正本は tasks/ ではなく knowledges/。
---
# knowledge-promote

ゴール: 案件に残る事実が `knowledges/` に 1 か所だけあり、frontmatter の `summary` と出所が付いている状態。

## 既定の進め方
1. `projects/<project>/knowledges/index.md` を見て、同じ内容のナレッジが既にあれば新規に作らずそれを更新する。
2. 無ければ `scripts/ws know new <project> "タイトル"` で雛形を作る。
3. 事実だけを書く。`summary` を 1 文で、`source` に出所（references/ のパス、会議名と日付）を書く。`type` は fact（事実・仕様）/ procedure（手順）/ decision（決定と理由）/ contact（関係者と役割）。
4. 用語なら本文ではなく `scripts/ws glossary add` で用語集に足す。
5. 数値・仕様は references の「引用した記述」と突き合わせてから書く。

## つまずきどころ
- 既存のナレッジと重複して 2 本になる。`knowledges/index.md` を先に見る。
- タスクの経緯（試行錯誤、誰が何を言ったか）を書き込んでしまう。残すのは事実と決定だけで、経緯はタスクの `index.md` に置く。
- `summary` が空だと `scripts/ws doctor` が警告し、`index.md` の一覧にも要約が出ない。出所が無い知見は `status: draft` のままにして人に確認する。
