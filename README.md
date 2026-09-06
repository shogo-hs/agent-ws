# agent-ws

AI エージェント（Claude Code / OpenAI Codex CLI）に仕事の案件を任せるための作業スペースです。
案件ごと・タスクごとにフォルダを切り、エージェントが読む範囲を「今のタスク」と「その案件のナレッジ」だけに絞ります。
集めた情報はタスクのフォルダに残るので、別のセッションで再開しても同じ調べ物をやり直しません。

人がやるのは、最初の導入と、日本語で頼むことだけです。フォルダを切る・情報源を記録する・用語集で文字起こしを直す、といった作業はエージェントが同梱のスクリプトで行います。

## 何が変わるか

- 「続きをやって」だけで現在のタスクから始まる。仕組みを外すと案件 8 件の状態では 5 回中 4〜5 回「どのタスクの続きか」を聞き返して止まり、Haiku 4.5 ではフォルダを見にも行かない。引き継ぎでは前のセッションが残した記録から再開し、元の資料を読み直さない（処理した入力は仕組みなしの半分。Sonnet・各 5 回。[計測](#計測)）
- 「どこから・いつ・原文は何か」が残るので、次のセッションが再収集しない
- 会議の文字起こしの誤変換を、案件の用語集で機械的に直してから読ませられる
- Claude Code と Codex CLI で同じ指示・同じスキル・同じ hooks が効く

## 導入（初回だけ）

1. このリポジトリを自分の場所に置きます（GitHub なら「Use this template」→ clone）。
2. `python3` が使えることを確認します（3.9 以上。追加パッケージは不要）。
3. 実行権限が落ちていたら `chmod +x scripts/ws` を実行します。
4. リポジトリの**ルートで** `claude` または `codex` を起動します。
   - Claude Code: 初回にフォルダを信頼するか聞かれます。信頼すると `.claude/settings.json` の hooks が有効になります。
   - Codex CLI（0.153 以上）: 初回にフォルダを信頼するか聞かれます。信頼したあと `/hooks` を開き、`.codex/hooks.json` の 4 つの hook を確認して trust します。
     信頼していない hook は警告なしに飛ばされるので、起動時に `[agent-ws] 現在のタスク` の案内が出なければ `/hooks` を見直してください。
     `.codex/config.toml` はフォルダを trusted にしたときだけ読まれます。

`projects/_example/` はサンプル案件です（内容はすべて架空）。自分の案件を作ったら消して構いません。
`docs/snapshots/`（規則の根拠にした Web ページの原文。約 2.2 MB）と `bench/`（計測）も、使うだけなら消して構いません。台帳（`docs/sources/`）は残しておくと、規則の数字の出所が分かります。

## 日々の使い方

エージェントに日本語で頼みます。頼み方と、エージェントが裏で実行することの対応は次のとおりです。

| 人が頼むこと | エージェントがやること（裏で動くもの） |
|---|---|
| 「ACME 社の案件を作って。Kubernetes 移行の支援」 | `scripts/ws project new acme` で案件フォルダを作り、`projects/acme/index.md` の「概要」を書く |
| 「acme の見積タスクを始めて」 | task-start スキル。`scripts/ws task new acme estimate` でタスクフォルダを作って「現在のタスク」にし、`index.md` の「目的」と「進め方」を書く |
| 「続きをやって」 | task-resume スキル。起動時に hook が差し込んだ現在のタスクの `index.md` を読み、「次の一手」から再開する |
| 「kickoff のタスクに切り替えて」 | `scripts/ws task use projects/acme/tasks/<フォルダ名>`。そのあと `/clear`（Claude Code）か新しいセッション（Codex）を促す |
| 「この URL を調べて」「この資料を読んで」 | `scripts/ws ref add <URL>` で本文丸ごとを references/ に残してから読む（WebFetch は hook が止めて ref add に誘導する） |
| 「大量の資料を読んでまとめて」 | researcher（haiku / gpt-5.4-mini）に渡し、結論と出所だけ受け取る |
| 「この文字起こしをまとめて」 | transcript-ingest スキル。原文を `ref add` → `scripts/ws transcript normalize` で用語集の誤変換を直す → 正規化版だけを読んで決定事項・宿題を抜き出す → 意味の取れない語は「未確定の用語」に残す。Claude Code では researcher の中（fork）で走り、本線には要点（`.summary.md`）だけが戻る |
| 「これはナレッジにして」 | knowledge-promote スキル。`scripts/ws know new acme "移行方針"` で `knowledges/` に雛形を作り、事実と出所を書く |
| 「クバネティスは Kubernetes の誤変換」 | `scripts/ws glossary add acme "Kubernetes" --alias "クバネティス"` で用語集に足す |
| 「結論を先に書いて」「その言い方はやめて」 | `scripts/ws lesson add "報告は結論を先に書く（読む人はチャットしか見ない）"` で `LESSONS.md` に 1 行残す。案件固有なら `--project acme` で案件の決まりごとへ |
| 「このタスクは終わり」 | `scripts/ws task done`。状態を done にし、「現在のタスク」を外す |

質問に答えるだけ・数分で終わる作業にはタスクを切る必要はありません。ファイルを作る、調べた情報を残す、日をまたぐ、のどれかに当てはまるときにタスクにします。

### セッションの切り方

1 タスク = 1 セッションにします。新しいタスクは新しいセッションで始め、別のタスクに移るときは切り替えを頼んだあと、Claude Code なら `/clear`、Codex CLI なら新しいセッションを開きます。
hook は起動のたび（`/clear` や compact のあとも）に現在のタスクを差し込むので、切り替え忘れが起きにくくなっています。
Claude Code では `/clear` の前に `/rename <タスク名>` しておくと `/resume` で戻れます。起動直後に `/context` を一度見ると、AGENTS.md と hook の注入がコンテキストをどれだけ使っているか分かります。
長い調べ物は、結論と出所だけを持ち帰るようサブエージェントに分けると、本線のコンテキストが汚れません。
モデルと reasoning effort はセッションの最初に決めます。途中で変えると、そこから会話全体のキャッシュが作り直しになります。
試行が失敗したら訂正で続けず `/rewind`（Esc 2 回）で戻ってから言い直します。戻った先までの会話はキャッシュ済みです。
`/usage` の「Prompt cache (main)」行（Claude Code 2.1.251 以降）で、直近のキャッシュ miss の回数と warm/cold を確認できます。
従量課金で 1 セッションが長くなるなら、自動 compact を早める調整ノブがあります（Claude Code は環境変数 `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`、Codex は `model_auto_compact_token_limit`）。index.md に現在地が残っているので早めの compact に耐えますが、compact 自体の費用との損益分岐は測っていないので agent-ws の既定は変えていません。

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
├── LESSONS.md             人からの指摘（1 行 1 件。hook が起動のたびに全行を差し込む）
├── .claude/settings.json  Claude Code の hooks 登録
├── .claude/skills -> ../.agents/skills
├── .claude/agents/researcher.md  調査係サブエージェント（Claude Code・haiku）
├── .codex/hooks.json      Codex CLI の hooks 登録（中身は同じスクリプトを呼ぶ）
├── .codex/config.toml     Codex CLI のプロジェクト設定（web_search を外す、調査係の既定モデル）
├── .codex/agents/researcher.toml  調査係サブエージェント（Codex CLI・gpt-5.4-mini）
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
│               └── references/   集めた情報（要点 .md と原文 .orig.md の対、文字起こしは正規化版 .normalized.md と要点 .summary.md も）
├── docs/                  agent-ws 自体の設計判断と規則の根拠（案件の仕事では読まない）
│   ├── adr/               設計判断の記録（決定と理由・捨てた案。1 本 20 行以内）
│   ├── sources/           規則の根拠台帳（委譲規則・トークン節約の 5 点。URL・取得日時・支えている規則）
│   └── snapshots/         出典ページの原文（要点 .md と原文 .orig.md の対）
├── tests/test_ws.py       scripts/ws の自己チェック
└── .ws/                   （git 管理外）最後に設定したタスク（current）と、セッションごとの現在のタスクの写し・最終応答時刻
```

## 仕組み

### エージェントが読む順番

1. `AGENTS.md`（60 行以内の規約。起動時に自動で読まれる）
2. hook が差し込む「現在のタスク」、案件の `index.md` の「この案件での決まりごと」、案件の `knowledges/index.md` の一覧、タスクの `index.md` の全文、`LESSONS.md` の全行
3. 必要なナレッジと用語集だけを開く（一覧は 2 で渡されているので `knowledges/index.md` を読み直さない）

### 起動時の注入でターンを減らす

エージェントはターンごと（ツールを 1 回呼ぶごと）に会話全体を入力として送り直します。キャッシュが効いても課金はされ、bench では 1 ターンの入力が 32k トークン前後でした。
一方で tool の結果そのものは 1 セッション合計で 2〜6 万字と小さく、処理した入力の 93〜95% はこの払い直しでした（bench の transcript の集計）。
そこで SessionStart hook は、現在のタスクの `index.md` の全文と案件の `knowledges/index.md` の一覧を最初から文脈に入れます。再開のたびに `scripts/ws task current` → `Read index.md` → `Read knowledges/index.md` と 2〜3 ターン使っていた分が要らなくなります。
注入は合計 6,000 字まで（Claude Code の hook 出力は 10,000 字で切られてファイル参照に化けるため）で、超える `index.md` は従来どおりパスと「次の一手」だけを示します。compact のあとも SessionStart(compact) で同じものが入るので、要約で消えた現在地は index.md から戻ります。
Codex CLI は hook の注入が既定で約 2,500 トークンに切られるため、`.codex/hooks.json` の session-start に `additionalContextLimit: 8000` を付けています。
同じ理由で AGENTS.md には「複数のファイルは 1 ターンでまとめて読む」「返答は結論・数字・置き場所だけ（出力トークンは入力の 5 倍の単価）」を置いています。

### ステータスライン（Claude Code）

`.claude/settings.json` の `statusLine` が `scripts/ws statusline` を呼び、画面の下に「現在のタスク | モデル | 文脈の使用率 | このセッションの費用（定価）」を常時出します。値は Claude Code が渡すもの（`context_window.used_percentage`・`cost.total_cost_usd`）をそのまま表示するだけで、トークンは使いません。
文脈の使用率が上がってきたら `/compact`、タスクの切れ目なら `/clear` の頃合いです。自分の statusLine を使っているなら `.claude/settings.json` の `statusLine` を消してください（project の設定が user の設定より優先されます）。Codex CLI には同等の設定が無いので `/status` で見ます。

### hooks が止めるもの

`scripts/ws hook pre-tool-use` が、ツールの入力（読むパス・grep の対象・シェルのコマンド）に「現在のタスク以外の `projects/*/tasks/*/`」が含まれていたら拒否し、理由として `knowledges/` を案内します。
`tasks/index.md`（一覧）と `scripts/ws` 自身の実行は通します。
`projects/`・案件直下・`tasks/` 直下を対象にした `find` / `ls` / `grep -r` / `rg` / `tree` と、パス指定の無い Grep / Glob も現在のタスクがある間は拒否します（他タスクの本文が結果に混ざり、読む導線としては `projects/index.md` と `tasks/index.md` で足りるため）。現在のタスクが無いとき（agent-ws 自体を直すとき）は止めません。現在のタスクがある間は `bench/` と `docs/snapshots/` も読ませません（案件の仕事に関係なく、grep が当たると数十 KB の原文を丸ごと読んでしまうため）。
Claude Code は `.claude/settings.json`、Codex CLI は `.codex/hooks.json` から同じスクリプトを呼びます。
起動時の案内（SessionStart）は JSON の `additionalContext` で返します。Claude Code は素のテキストでも文脈に足しますが、Codex CLI は JSON でないと文脈に載りません（0.153.4 で確認）。

「`mkdir` ではなく `scripts/ws task new` を使う」は規約とスキルで指示しているだけで、hook では止めていません。エージェントが手でフォルダを作ってしまう事故が実際に起きたら、`projects/*/tasks/` 配下への直接の `mkdir` を hook で止める形に足せます。

正規化版（`.normalized.md`）がある文字起こしの原文を Read や Grep しようとすると、hook が読む先を正規化版に読み替えます（Bash/shell 経由の `cat`/`sed`/`grep` は書き換えずに deny し、正規化版のパスを示します）。

### 1 時間以上空いたあとの 1 通目を止める

Claude のプロンプトキャッシュはサブスクリプションで 1 時間で切れ、切れたあと同じ会話に続きを送ると会話全文を定価で再処理します。
agent-ws は Stop hook で応答が終わった時刻を記録し、次に人がメッセージを送ったとき 60 分以上空いていれば、UserPromptSubmit hook がその 1 通を送らずに止めて `/clear` して index.md から再開するよう案内します。止めた時点では API は呼ばれないので費用はかかりません（実測: 所要 208 ms、使用トークン 0）。
それでも続けたいときは、同じ内容を 10 分以内にもう一度送れば通ります。止めた本文は `.ws/sessions/` に残ります。
しきい値の優先順位は 環境変数 `WS_CACHE_TTL_MIN` → hook 呼び出しの `--ttl` 引数 → 既定 60（分）です。Codex CLI は `.codex/hooks.json` の user-prompt-submit が `--ttl 30` を渡します（GPT-5.6 以降のプロンプトキャッシュは最後の利用から 30 分は再利用できる、が公式の保証で、`prompt_cache_options.ttl` の既定かつ唯一の値が `30m` のため。それより長く残ることはある）。
Claude で API キーを直に叩いていてキャッシュが 5 分で切れる環境なら `WS_CACHE_TTL_MIN=5` にします。逆に切れてほしくない・60 分のままでよいなら `.claude/settings.json` に `"promptCacheTtl": "1h"`（Claude Code 2.1.242 以降）を置くとプロンプトキャッシュ自体を 1 時間に延ばせます（書き込み単価は上がります）。

### index.md

各フォルダの `index.md` が入口です。`<!-- ws:index -->` と `<!-- /ws:index -->` の間は `scripts/ws` が自動で書き換え、その外側は手書きのまま残ります。
タスクの `index.md` には `references/` の中身が直接並ぶので、情報源を探すのに 1 回で済みます。
`ref add` は要点ファイル（`<name>.md`。frontmatter・引用した記述・使いどころ）と原文ファイル（`<name>.orig.md`。本文そのまま）の対で保存し、一覧には要点側だけが載ります。同じ `source` の reference が既にあれば取得せずにそのパスを返します（同じページを 2 回撮って 2 回読まないため。撮り直すなら `--force`）。旧形式（1 ファイル）で残っている reference は `scripts/ws ref split <file>` で新形式に移行できます。

### 用語集

`knowledges/glossary.md` は Markdown の表（正式表記 / 読み / 誤変換・別表記 / 説明）です。
人が GitHub や Obsidian でそのまま読め、`scripts/ws transcript normalize` も同じ表を読みます。
置換は表に書いた文字列と一致した箇所だけで、読みが近い語を推測して置き換えることはしません。1〜2 文字の語や一般語は誤爆するので書かないでください。

### 人からの指摘

「結論を先に」「その言い方はやめて」のような指摘は `scripts/ws lesson add "〜のとき、〜する（理由）"` で `LESSONS.md` に 1 行残し、hook が起動のたびに全行を差し込みます。
1 回目で残します（2 回目を待つ規則は、1 回目を覚えている者がセッションをまたいで居ないので機能しません）。
20 行を超えると `scripts/ws doctor` が報告するので、統合するか AGENTS.md・doctor の検査へ昇格して減らしてください。長いほど守られなくなります。
案件固有の指摘は `--project <案件>` で案件の `index.md` の「この案件での決まりごと」に入ります。
指摘かどうかを機械で見分ける hook は付けていません。指摘らしい語で当てても大半が説明や質問で、外れの多い注意は無視されるようになるからです。

## 制約と注意

- **ルートで起動してください。** サブディレクトリで起動すると、ルートの `.claude/settings.json` の hooks が読まれません（Claude Code 2.1.261 で確認）。
- `.ws/current` は git 管理外です。人ごと・マシンごとに「現在のタスク」は違います。同じ clone で複数のセッションを並行させることはできます。現在のタスクはセッションごとに `.ws/sessions/<session_id>.current` に写して持つので、片方の `task use` がもう片方に影響しません（セッションは Claude Code なら環境変数 `CLAUDE_CODE_SESSION_ID`、Codex CLI なら `CODEX_THREAD_ID` で見分けます）。新しいセッションと `/clear` のあとは、最後に設定したタスク（`.ws/current`）から始まります。端末から直接叩く `scripts/ws task current` はセッションに紐付かないので `.ws/current` を返します。
- Windows では `.claude/skills` の symlink を作るのに開発者モードか管理者権限が要ります。`python3` が `py -3` の環境では `.claude/settings.json` と `.codex/hooks.json` のコマンドを書き換えてください。
- Codex CLI のプロジェクト hooks は、フォルダの信頼に加えて `/hooks` で hook ごとに trust しないと動きません。信頼は hook の定義のハッシュに対して記録されるので、`.codex/hooks.json` を書き換えたら trust し直してください（`scripts/ws` の中身を変えるだけなら不要です）。今回 user-prompt-submit に `--ttl 30` を足したので、更新後は `/hooks` で trust し直してください。

## 計測

同じ材料・同じ依頼文・同じモデルで、agent-ws の仕組みがある場合（A）、同じ `projects/` ツリーだけで規約・hooks・スキル・スクリプトを外した場合（B）、tasks/ 階層も index.md も無い導入前の状態（C。資料の平置き＋作業メモ）を headless の Claude Code で走らせ、処理した入力トークン（毎ターンの新規入力＋キャッシュ作成＋キャッシュ読みの合計）・費用（定価）・読みに行った範囲・答えの正誤を比べました。材料は架空の案件 8 件・189 ファイル・約 700 KB（進行中のタスクが 6 つ）で、依頼メールに「古い数字は使うな」といった警告は入れていません。各条件 5 回、合計 99 セッション。手順・条件・数える値の定義は [bench/README.md](bench/README.md)、1 セッション 1 行の結果は `bench/results/runs.jsonl`、集計は `bench/results/summary.md` にあります。

**「続きをやって」だけで頼む**（現在のタスクは acme の見積。正解は 12 台 × 新単価の 363,400 円/月）

| 材料 | モデル | 条件 | 着手して正解 | 聞き返して終了 | 処理した入力（中央値） | 費用 USD |
|---|---|---|---|---|---|---|
| 案件 3 | Sonnet | agent-ws | 5/5 | 0 | 279k | 0.152 |
| 案件 3 | Sonnet | 同じ構造・仕組みなし | 4/5 | 1 | 319k | 0.193 |
| 案件 3 | Sonnet | 導入前 | 0/5 | 5 | 128k | 0.102 |
| 案件 8 | Sonnet | agent-ws | 5/5 | 0 | 242k | 0.141 |
| 案件 8 | Sonnet | 同じ構造・仕組みなし | 1/5 | 4 | 213k | 0.159 |
| 案件 8 | Sonnet | 導入前 | 0/5 | 5 | 133k | 0.114 |
| 案件 8 | Haiku 4.5 | agent-ws | 5/5 | 0 | 164k | 0.063 |
| 案件 8 | Haiku 4.5 | 同じ構造・仕組みなし | 0/5 | 5 | 22k | 0.018 |
| 案件 8 | Haiku 4.5 | 導入前 | 0/5 | 5 | 22k | 0.018 |

仕組みが無いと「どのタスクの続きか教えてください」と聞き返して止まります。数字を出せなかった回はすべてこれで、別のタスクを進めた回や古い数字を掴んだ回はありません。案件が増えるほど聞き返しが増え、Haiku 4.5 はフォルダを見にも行きません。仕組みなしの費用が安いのは、そこで止まっているからです。

**引き継ぎ**（見積タスクが無い状態から「タスクを始めて、今日は前提の確認まで」→ 新しいセッションで「続きをやって」。案件 8・Sonnet）

| 条件 | 2 セッション目で正解 | 元の資料（inbox/）を読み直した | 元からあった他タスクに立ち入った | 処理した入力（中央値） | 費用 USD |
|---|---|---|---|---|---|
| agent-ws | 5/5 | 0/5 | 0 回 | 329k | 0.161 |
| 同じ構造・仕組みなし | 5/5 | 4/5 | 1〜2 回 | 701k | 0.460 |
| 導入前 | 4/5 | 4/5 | 0〜3 回 | 460k | 0.294 |

agent-ws は 1 セッション目が `scripts/ws` で残した index.md と references/ から再開し、元の資料を読み直しません。仕組みなしは 1 セッション目が手作りした記録があっても inbox/ を読み直し、他の案件に未完了タスクが無いか確かめに行くので、処理した入力が 2 倍になります（5 対 5 の並べ替え検定で p = 0.008）。

**新規タスクを最初から**（「10 月からの移行フェーズの進め方の資料を作って」。ナレッジだけで書ける依頼。案件 8・Sonnet）

| 条件 | ナレッジの事実 8 項目 | 古い数字の混入 | 他タスクの資料に立ち入った | 最終文脈 | 処理した入力（中央値） | 費用 USD |
|---|---|---|---|---|---|---|
| agent-ws | 8/8 × 5 回 | 0 | 0 回 | 42k | 299k | 0.206 |
| 同じ構造・仕組みなし | 8/8 × 5 回 | 0 | 0〜7 回（中央値 7） | 54k | 481k | 0.340 |
| 導入前 | 8/8 × 5 回 | 0 | 2〜8 回 | 70k | 377k | 0.340 |

資料の中身はどの条件でも同じ 8 項目を押さえていて、古い数字を前提に使った例もありません。差は読みに行く範囲で、agent-ws はナレッジ 3 本と現在のタスクだけを読み、仕組みなしは古いタスクの文字起こしまで開くので、処理した入力が 1.3〜1.6 倍、費用が 1.65 倍になります（A/B の p は処理した入力 0.016・費用 0.008）。

**第 6 弾（起動時の注入・ターンを減らす規約・横断検索の拒否）の前後**（案件 8・Sonnet・各 5 回。前 = PR #6 まで、後 = このブランチ。処理した入力は中央値、p は 5 対 5 の並べ替え検定）

| 実験 | 前 | 後 | p |
|---|---|---|---|
| 続きをやって（trap） | 749k・18 ターン | 224k・6 ターン | 0.048 |
| 引き継ぎ 1 本目（新規タスク。注入の対象外） | 475k・12 ターン | 508k・13 ターン | 0.71 |
| 引き継ぎ 2 本目（続きをやって） | 343k・9 ターン | 224k・6 ターン | 0.43（1 回だけ 1,141k・25 ターン。ナレッジ昇格後に `scripts/ws index` の挙動を確かめに scripts/ws を読み始めた） |

「続きをやって」の前の値が上の表（246k）より大きいのは、PR #6 で入れた doctor の「引用した記述が未記入」の警告に従って、旧形式の reference を新形式へ作り替え始めたためです（5 回中 3 回、ターン 18〜23）。第 6 弾で最初期の形式（「## 要点」だけ）は検査しないようにしました。PR #5 時点の値（254k・7 ターン）と比べると 224k・6 ターンで、差は誤差の範囲です（p = 0.38）。正誤はどの条件も 5/5 で変わりません。

**効かなかった場面・測っていないこと**

- タスク名を言って頼む依頼では差が出ません（前回の計測。index.md が同じなら読む範囲も同じ）
- 「Sonnet でも安定する」は、この材料では「古い数字を掴む」形の誤答が 1 回も出なかったので示せていません。仕組みなしの失敗はすべて「聞き返して止まる」でした
- 固定分（1 ターンの下駄）は agent-ws が Sonnet で 32.0k、仕組みなしが 29.2k（AGENTS.md・skills・注入の 2.9k）。Haiku 4.5 は 24.5k と 21.8k
- Codex CLI・Opus・compact 後の再注入・用語集の正規化は測っていません

`bench/` は agent-ws を使うだけなら不要です。`projects/_example/` と同じく消して構いません。

## 開発

```
python3 -m unittest tests/test_ws.py
```

案件作成 → タスク作成 → hook の拒否と許可 → 情報源の保存 → 用語集と正規化 → ナレッジ昇格 → 完了、を一時ディレクトリで通します。

## ライセンス

MIT（[LICENSE](LICENSE)）。
