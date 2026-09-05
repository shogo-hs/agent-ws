# agent-ws

AI エージェント（Claude Code / OpenAI Codex CLI）に仕事の案件を任せるための作業スペースです。
案件ごと・タスクごとにフォルダを切り、エージェントが読む範囲を「今のタスク」と「その案件のナレッジ」だけに絞ります。
集めた情報はタスクのフォルダに残るので、別のセッションで再開しても同じ調べ物をやり直しません。

人がやるのは、最初の導入と、日本語で頼むことだけです。フォルダを切る・情報源を記録する・用語集で文字起こしを直す、といった作業はエージェントが同梱のスクリプトで行います。

## 何が変わるか

- 読む範囲が狭いので、トークンが減り、Sonnet 級のモデルでも結果が安定する
- 「どこから・いつ・原文は何か」が残るので、次のセッションが再収集しない
- 会議の文字起こしの誤変換を、案件の用語集で機械的に直してから読ませられる
- Claude Code と Codex CLI で同じ指示・同じスキル・同じ hooks が効く

## 導入（初回だけ）

1. このリポジトリを自分の場所に置きます（GitHub なら「Use this template」→ clone）。
2. `python3` が使えることを確認します（3.9 以上。追加パッケージは不要）。
3. 実行権限が落ちていたら `chmod +x scripts/ws` を実行します。
4. リポジトリの**ルートで** `claude` または `codex` を起動します。
   - Claude Code: 初回にフォルダを信頼するか聞かれます。信頼すると `.claude/settings.json` の hooks が有効になります。
   - Codex CLI: `/hooks` を開き、`.codex/hooks.json` の 2 つの hook を確認して trust します。

`projects/_example/` はサンプル案件です（内容はすべて架空）。自分の案件を作ったら消して構いません。

## 日々の使い方

エージェントに日本語で頼みます。頼み方と、エージェントが裏で実行することの対応は次のとおりです。

| 人が頼むこと | エージェントがやること（裏で動くもの） |
|---|---|
| 「ACME 社の案件を作って。Kubernetes 移行の支援」 | `scripts/ws project new acme` で案件フォルダを作り、`projects/acme/index.md` の「概要」を書く |
| 「acme の見積タスクを始めて」 | task-start スキル。`scripts/ws task new acme estimate` でタスクフォルダを作って「現在のタスク」にし、`index.md` の「目的」と「進め方」を書く |
| 「続きをやって」 | task-resume スキル。起動時に hook が差し込んだ現在のタスクの `index.md` を読み、「次の一手」から再開する |
| 「kickoff のタスクに切り替えて」 | `scripts/ws task use projects/acme/tasks/<フォルダ名>`。そのあと `/clear`（Claude Code）か新しいセッション（Codex）を促す |
| 「この URL を調べて」「この資料を読んで」 | 読んだあと ref-add スキル。`scripts/ws ref add <URL|ファイル> --summary "…"` で出所・取得日時・原文を `references/` に残す |
| 「この文字起こしをまとめて」 | transcript-ingest スキル。原文を `ref add` → `scripts/ws transcript normalize` で用語集の誤変換を直す → 正規化版だけを読んで決定事項・宿題を抜き出す → 意味の取れない語は「未確定の用語」に残す |
| 「これはナレッジにして」 | knowledge-promote スキル。`scripts/ws know new acme "移行方針"` で `knowledges/` に雛形を作り、事実と出所を書く |
| 「クバネティスは Kubernetes の誤変換」 | `scripts/ws glossary add acme "Kubernetes" --alias "クバネティス"` で用語集に足す |
| 「このタスクは終わり」 | `scripts/ws task done`。状態を done にし、「現在のタスク」を外す |

質問に答えるだけ・数分で終わる作業にはタスクを切る必要はありません。ファイルを作る、調べた情報を残す、日をまたぐ、のどれかに当てはまるときにタスクにします。

### セッションの切り方

1 タスク = 1 セッションにします。新しいタスクは新しいセッションで始め、別のタスクに移るときは切り替えを頼んだあと、Claude Code なら `/clear`、Codex CLI なら新しいセッションを開きます。
hook は起動のたび（`/clear` や compact のあとも）に現在のタスクを差し込むので、切り替え忘れが起きにくくなっています。
長い調べ物は、結論と出所だけを持ち帰るようサブエージェントに分けると、本線のコンテキストが汚れません。

### 人が直接コマンドを叩きたいとき

同じコマンドは端末からも使えます。エージェントを起動する前にタスクだけ切っておく、といった使い方ができます。

```
scripts/ws --help
scripts/ws project new acme
scripts/ws task new acme kickoff --title "キックオフ準備"
scripts/ws task current
scripts/ws doctor            # index.md や frontmatter の欠落を報告する
```

## 構成

```
agent-ws/
├── AGENTS.md              エージェント向けの作業規約（Codex CLI が読む正本）
├── CLAUDE.md              「@AGENTS.md」の1行（Claude Code はこれ経由で同じ規約を読む）
├── .claude/settings.json  Claude Code の hooks 登録
├── .claude/skills -> ../.agents/skills
├── .codex/hooks.json      Codex CLI の hooks 登録（中身は同じスクリプトを呼ぶ）
├── .agents/skills/        スキル（両ツール共通の SKILL.md）
│   ├── task-start/        新しいタスクを切って着手する
│   ├── task-resume/       既存タスクを index.md から再開する
│   ├── ref-add/           情報源を references/ に記録する
│   ├── transcript-ingest/ 文字起こしを用語集で直してナレッジ化する
│   └── knowledge-promote/ タスクで得た知見を knowledges/ に昇格する
├── scripts/ws             エージェントが呼ぶ CLI（python3 の標準ライブラリだけで動く）
├── templates/             案件・タスク・ナレッジ・情報源・用語集の雛形
├── projects/
│   ├── index.md           案件一覧
│   └── <案件>/
│       ├── index.md       案件の概要と決まりごと
│       ├── knowledges/    ナレッジの正本（index.md / glossary.md / NNN_*.md）
│       └── tasks/
│           ├── index.md   タスク一覧
│           └── <yyyymmdd_slug>/
│               ├── index.md      目的・進め方・現在地・次の一手・未確定の用語・情報源の一覧
│               └── references/   集めた情報（出所・取得日時・原文）
├── tests/test_ws.py       scripts/ws の自己チェック
└── .ws/current            （git 管理外）いま着手中のタスクのパス
```

## 仕組み

### エージェントが読む順番

1. `AGENTS.md`（60 行以内の規約。起動時に自動で読まれる）
2. hook が差し込む「現在のタスク」と、その `index.md` の「次の一手」
3. タスクの `index.md`（目的・進め方・現在地・情報源の一覧）
4. 案件の `knowledges/index.md`。必要なナレッジと用語集だけを開く

### hooks が止めるもの

`scripts/ws hook pre-tool-use` が、ツールの入力（読むパス・grep の対象・シェルのコマンド）に「現在のタスク以外の `projects/*/tasks/*/`」が含まれていたら拒否し、理由として `knowledges/` を案内します。
`tasks/index.md`（一覧）と `scripts/ws` 自身の実行は通します。
Claude Code は `.claude/settings.json`、Codex CLI は `.codex/hooks.json` から同じスクリプトを呼びます。

「`mkdir` ではなく `scripts/ws task new` を使う」は規約とスキルで指示しているだけで、hook では止めていません。エージェントが手でフォルダを作ってしまう事故が実際に起きたら、`projects/*/tasks/` 配下への直接の `mkdir` を hook で止める形に足せます。

### index.md

各フォルダの `index.md` が入口です。`<!-- ws:index -->` と `<!-- /ws:index -->` の間は `scripts/ws` が自動で書き換え、その外側は手書きのまま残ります。
タスクの `index.md` には `references/` の中身が直接並ぶので、情報源を探すのに 1 回で済みます。

### 用語集

`knowledges/glossary.md` は Markdown の表（正式表記 / 読み / 誤変換・別表記 / 説明）です。
人が GitHub や Obsidian でそのまま読め、`scripts/ws transcript normalize` も同じ表を読みます。
置換は表に書いた文字列と一致した箇所だけで、読みが近い語を推測して置き換えることはしません。1〜2 文字の語や一般語は誤爆するので書かないでください。

## 制約と注意

- **ルートで起動してください。** サブディレクトリで起動すると、ルートの `.claude/settings.json` の hooks が読まれません（Claude Code 2.1.261 で確認）。
- `.ws/current` は git 管理外です。人ごと・マシンごとに「現在のタスク」は違います。同時に複数のタスクを別セッションで進めたい場合は、clone を分けてください。
- Windows では `.claude/skills` の symlink を作るのに開発者モードか管理者権限が要ります。`python3` が `py -3` の環境では `.claude/settings.json` と `.codex/hooks.json` のコマンドを書き換えてください。
- Codex CLI のプロジェクト hooks は、初回に `/hooks` で trust しないと動きません。

## 開発

```
python3 -m unittest tests/test_ws.py
```

案件作成 → タスク作成 → hook の拒否と許可 → 情報源の保存 → 用語集と正規化 → ナレッジ昇格 → 完了、を一時ディレクトリで通します。

## ライセンス

MIT（[LICENSE](LICENSE)）。
