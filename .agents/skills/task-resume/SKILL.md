---
name: task-resume
description: 既存のタスクを別セッションで続けるとき。現在のタスクの index.md を読み、「進め方」の未完了と「次の一手」から再開する。「続きをやって」「再開して」「さっきの続き」で使う。新規なら task-start。
---
# task-resume

ゴール: `index.md` の「現在地」と「次の一手」だけを頼りに、情報を取り直さずに作業を続けられている状態。

## 既定の進め方
1. `scripts/ws task current` で現在のタスクを確認する。別のタスクを続けるなら `scripts/ws task use projects/<project>/tasks/<dir>` のあと、Claude Code なら `/clear`。
2. そのタスクの `index.md` を読む。「進め方」の未完了の段階と「次の一手」に従う。
3. 情報源は `index.md` 末尾の一覧（references/）から必要なものだけ開く。同じ情報を Web や資料から取り直さない。
4. 終える前に「進め方」のチェックと「現在地」「次の一手」を更新する。完了なら `scripts/ws task done`。

## つまずきどころ
- `tasks/` を `ls` して他のタスクを眺めない。一覧が要るなら `tasks/index.md` だけ。
- 「現在地」を更新せずに終わると、次のセッションが同じ作業を繰り返す。質問に答えただけのセッションでも、作業が進んだなら更新する。
- `index.md` の記述と実際のファイルが食い違うとき（一覧に無い情報源が本文に書かれている等）は、ファイルのほうを信じて `index.md` を直す。`scripts/ws index` で一覧は作り直せる。
