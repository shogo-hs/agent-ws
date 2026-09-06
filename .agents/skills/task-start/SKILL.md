---
name: task-start
description: 新しいタスクに着手するとき。案件名と短いスラッグでタスクフォルダを作り、現在のタスクに設定し、index.md の「目的」と「進め方」を書く。「〜のタスクを始めて」「新しい作業を切って」「着手して」で使う。既存タスクの続きなら task-resume。
---
# task-start

ゴール: タスクのフォルダができ、「現在のタスク」に設定され、`index.md` の「目的」と「進め方」が書かれている状態。

## 既定の進め方
1. 案件が無ければ `scripts/ws project new <project>` で作り、`projects/<project>/index.md` の「概要」を書く。
2. `scripts/ws task new <project> <slug> --title "タイトル"` を実行する。
3. 出力されたパスの `index.md` を開き、「目的」を 1〜3 文で書く（依頼文を写さず、何を渡せば終わりかを書く）。「進め方」を 3〜6 個の段階に分ける。
4. `projects/<project>/knowledges/index.md` を読み、関係するナレッジがあれば「参照したナレッジ」に列挙する。用語集（glossary.md）は固有名詞が出た時点で開く。
5. 作業に入る。情報を集めたら ref-add で残す。終える前に「現在地」「次の一手」を更新する。
6. 「進め方」に読む量が多い段階（URL の横断調査など）があれば、その段階は researcher に渡す。

## つまずきどころ
- 他のタスクフォルダを「参考に」開こうとして hook に止められる。他タスクの成果は knowledges/ にあるべきもの。無ければ人に聞く。
- slug に日本語や空白を入れるとフォルダ名が読みにくくなる。英数字で短く（例: kickoff, cost-estimate）。タイトルは `--title` に書く。
- `mkdir` や雛形の手コピーでタスクを作ると、現在のタスクにならず `tasks/index.md` の一覧にも載らない。必ず `scripts/ws task new`。
