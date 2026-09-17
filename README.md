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
- 業務の型・つながり・できること（アクション）を JSON で定義すると、前提条件はエージェントの判断ではなくエンジンが実体の値で検査して理由付きで拒否し、金額のような計算もエンジンがする。決裁の要る変更は実行待ちに積まれ、人の承認を経てから反映される（[オントロジー](#オントロジー業務の型つながりできること)）

## 導入（初回だけ）

1. このリポジトリを自分の場所に置きます（GitHub なら「Use this template」→ clone）。
2. `python` が PATH にあることを確認します（3.9 以上。追加パッケージは不要）。hooks はこの名前で起動します（Debian 系で無ければ `python-is-python3`、Windows は python.org の installer で「Add python.exe to PATH」）。
3. 実行権限が落ちていたら `chmod +x scripts/ws` を実行します（Linux / macOS）。Windows は `python scripts/ws …` と前置きして叩きます。
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
| 「大量の資料を読んでまとめて」 | researcher（haiku / gpt-5.6-luna）に渡し、結論と出所だけ受け取る |
| 「この文字起こしをまとめて」 | transcript-ingest スキル。原文を `ref add` → `scripts/ws transcript normalize` で用語集の誤変換を直す → 正規化版だけを読んで決定事項・宿題を抜き出す → 意味の取れない語は「未確定の用語」に残す。Claude Code では researcher の中（fork）で走り、本線には要点（`.summary.md`）だけが戻る |
| 「これはナレッジにして」 | knowledge-promote スキル。`scripts/ws know new acme "移行方針"` で `knowledges/` に雛形を作り、事実と出所を書く |
| 「クバネティスは Kubernetes の誤変換」「IdP 連携の担当は鈴木さん」 | `scripts/ws glossary add acme "Kubernetes" --alias "クバネティス"` / `glossary add acme "IdP 連携" --relation "→担当: 鈴木"` で用語集に足す（「関係」は任意。3 ヶ月変わらないものだけ） |
| 「うちは部長決裁が 500 万円まで」「勤怠システムは KinTai って呼んでる」 | `scripts/ws know new --common "決裁範囲" --owner "経営企画室"` / `glossary add --common "KinTai" --alias "勤怠システム"` で repo 直下の `knowledges/`（共通。案件をまたぐ自社の事実）に書く。3 ヶ月変わらないものだけ。案件側と同じ語・事実があれば案件側が勝つ |
| 「acme の見積を 12 台・12 か月で出して」（型が定義されている案件だけ） | `scripts/ws onto act IssueEstimate title="運用の見積" sizing=SD-2 items=pi-node,pi-monitor months=12 approver=sato`。返るのは拒否（理由文つき）・反映（計算した値つき）・実行待ち（決裁の上限を超えるとき）のいずれか |
| 「IdP 連携の担当は誰？」 | `scripts/ws onto query Person --where "any('IdP' in w.name for w in leads)"` か `show <型:id>` で照会する。型やアクションの一覧・詳細は `types` / `describe` |
| 「承認 P-0001」（人が送る） | UserPromptSubmit hook がその発言を拾い、積んだときの前提ではなく今の状態で検査し直してから実行待ちを反映する。エージェントは何もしない（自分では承認できない） |
| 「うちの業務の型を定義して」 | ontology-define スキル。「答えたい質問」を書くところから始める |
| 「結論を先に書いて」「その言い方はやめて」 | `scripts/ws lesson add "報告は結論を先に書く（読む人はチャットしか見ない）"` で `LESSONS.md` に 1 行残す。案件固有なら `--project acme` で案件の決まりごとへ |
| 「このタスクは終わり」 | `scripts/ws task done`。状態を done にし、「現在のタスク」を外す |

質問に答えるだけ・数分で終わる作業にはタスクを切る必要はありません。ファイルを作る、調べた情報を残す、日をまたぐ、のどれかに当てはまるときにタスクにします。

### セッションの切り方

1 タスク = 1 セッションにします。新しいタスクは新しいセッションで始め、別のタスクに移るときは切り替えを頼んだあと、Claude Code なら `/clear`、Codex CLI なら新しいセッションを開きます。
ただし、セッションを始めるたびに開始時の書き込み（約 15k トークン。cache 作成の単価は読みの 20 倍で、trap の費用の約 4 割）を払うので、質問に答えるだけの用事にセッションを切らないでください。
hook は起動のたび（`/clear` や compact のあとも）に現在のタスクを差し込むので、切り替え忘れが起きにくくなっています。
Claude Code では `/clear` の前に `/rename <タスク名>` しておくと `/resume` で戻れます。起動直後に `/context` を一度見ると、AGENTS.md と hook の注入がコンテキストをどれだけ使っているか分かります。
長い調べ物は、結論と出所だけを持ち帰るようサブエージェントに分けると、本線のコンテキストが汚れません。
モデルと reasoning effort はセッションの最初に決めます。途中で変えると、そこから会話全体のキャッシュが作り直しになります。
試行が失敗したら訂正で続けず `/rewind`（Esc 2 回）で戻ってから言い直します。戻った先までの会話はキャッシュ済みです。
`/usage` の「Prompt cache (main)」行（Claude Code 2.1.251 以降）で、直近のキャッシュ miss の回数と warm/cold を確認できます。
従量課金で 1 セッションが長くなるなら、自動 compact の閾値を下げる調整ノブがあります（Claude Code は `/autocompact <値>` か `autoCompactWindow`、Codex は `model_auto_compact_token_limit`）。index.md に現在地が残っているので早めの compact に耐えますが、**下げすぎは逆効果**です。LangWatch の Rogerio Chaves が 2,451 セッション・287,748 API コールを集計した報告では、コストの最小点は 220,000 トークンで、170k〜316k が 10% 以内、110k を切ると再発見のステップ数が節約を上回るとされています。同じ報告は compact 直後にユーザーの訂正率が 17.7% → 41.9%（2.37 倍）に跳ね、30 ステップ以上続くことも測っています。agent-ws の既定は変えていません（1 タスク = 1 セッションなら、そもそも閾値に届く前にセッションが終わるため）。長寿命のセッションを回すなら 200k 前後にするのが、いまのところ根拠のある設定です。

### 人が直接コマンドを叩きたいとき

同じコマンドは端末からも使えます。エージェントを起動する前にタスクだけ切っておく、といった使い方ができます。

```
scripts/ws --help
scripts/ws project new acme
scripts/ws task new acme kickoff --title "キックオフ準備"
scripts/ws task current
scripts/ws task done projects/acme/tasks/<dir>   # 終わったタスクを閉じる（doctor が 14 日放置の doing を知らせる）
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
├── .codex/agents/researcher.toml  調査係サブエージェント（Codex CLI・gpt-5.6-luna）
├── .agents/skills/        スキル（両ツール共通の SKILL.md）
│   ├── task-start/        新しいタスクを切って着手する
│   ├── task-resume/       既存タスクを index.md から再開する
│   ├── ref-add/           情報源を references/ に記録する
│   ├── transcript-ingest/ 文字起こしを用語集で直してナレッジ化する
│   ├── knowledge-promote/ タスクで得た知見を knowledges/ に昇格する
│   └── ontology-define/   業務の型・つながり・アクションを定義する（定義がある案件だけ関係する）
├── scripts/ws             エージェントが呼ぶ CLI（python3 の標準ライブラリだけで動く）
├── scripts/wsonto/        オントロジーのエンジン（定義の読み込み・照会・実行・承認・書き出し。取り決めは [scripts/wsonto/README.md](scripts/wsonto/README.md)）
├── templates/             案件・タスク・ナレッジ・情報源・用語集・共通ナレッジの雛形
├── knowledges/            案件をまたぐ自社の事実（組織図・決裁範囲・社内システム・標準手順・共通用語）。案件の knowledges/ と同じ形。見本は架空
│   └── ontology/          自社共通の型定義（あれば。ontology.json・実体・記録・実行待ち・index.md）
├── projects/
│   ├── index.md           案件一覧
│   └── <案件>/
│       ├── index.md       案件の概要と決まりごと
│       ├── knowledges/    ナレッジの正本（index.md / glossary.md / NNN_*.md）
│       │   └── ontology/  案件の型定義（あれば。ontology.json・objects.json・log.jsonl・proposals/・questions.json・index.md）
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
├── tests/test_onto_*.py   scripts/wsonto の自己チェック（schema・store・engine・query・export・lint・W3C 突き合わせ）
├── tests/fixtures/onto_case/  オントロジーの適合テストの見本（架空の案件支援。common/ が自社の部署・人・決裁権限、project/ が案件の決定・台数・単価・見積）
└── .ws/                   （git 管理外）最後に触ったタスク（current。完了の印ではない）と、セッションごとの現在のタスクの写し・最終応答時刻
```

## 仕組み

### エージェントが読む順番

1. `AGENTS.md`（60 行以内の規約。起動時に自動で読まれる）
2. hook が差し込む「現在のタスク」、案件の `index.md` の「この案件での決まりごと」、案件の `knowledges/index.md` の一覧、repo 直下 `knowledges/index.md` の一覧（共通。案件をまたぐ自社の事実）、タスクの `index.md` の全文、`LESSONS.md` の全行
3. 必要なナレッジと用語集だけを開く（一覧は 2 で渡されているので `knowledges/index.md` を読み直さない）

### 起動時の注入でターンを減らす

エージェントはターンごと（ツールを 1 回呼ぶごと）に会話全体を入力として送り直します。キャッシュが効いても課金はされ、会話が空でも毎ターン固定で送られる分（システムプロンプト・ツール定義・CLAUDE.md や hook の差し込み。以下「固定分」）は 1 ターン 39k トークン前後でした（Claude Code 2.1.263・Sonnet・2026-09-08 の実測。bench を取った当時は 32k で、ハーネス側が太った分だけ増えています）。
一方で tool の結果そのものは 1 セッション合計で 2〜6 万字と小さく、処理した入力の 93〜95% はこの払い直しでした（bench の transcript の集計）。
払い直しは長さに対して線形ではありません。実セッション 20 本・847 ターンを当てはめると **総トークン ≒ 固定分 × ターン数 + 1,848 × ターン数²**（R² 0.976）で、1 ターンごとに会話が約 3,700 トークン太り、それを以降の全ターンで払い直します。42 ターンを 1 本で走らせると約 4.9M、同じ 42 ターンを 6 ターン × 7 セッションに割ると約 2.1M で、**57% の差**になります。「1 タスク = 1 セッション」はここに効いています。
そこで SessionStart hook は、現在のタスクの `index.md` の全文と案件の `knowledges/index.md` の一覧を最初から文脈に入れます。再開のたびに `scripts/ws task current` → `Read index.md` → `Read knowledges/index.md` と 2〜3 ターン使っていた分が要らなくなります。
注入は合計 6,000 字まで（Claude Code の hook 出力は 10,000 字で切られてファイル参照に化けるため）で、超える `index.md` は従来どおりパスと「次の一手」だけを示します。compact のあとも SessionStart(compact) で同じものが入るので、要約で消えた現在地は index.md から戻ります。
Codex CLI は hook の注入が既定で約 2,500 トークンに切られるため、`.codex/hooks.json` の session-start に `additionalContextLimit: 8000` を付けています。
同じ理由で AGENTS.md には「複数のファイルは 1 ターンでまとめて読む」「返答は結論・数字・置き場所だけ（出力トークンは入力の 5 倍の単価）」を置いています。

### ステータスライン（Claude Code）

`.claude/settings.json` の `statusLine` が `scripts/ws statusline` を呼び、画面の下に「現在のタスク | モデル | 文脈の使用率 | このセッションの費用（定価）」を常時出します。値は Claude Code が渡すもの（`context_window.used_percentage`・`cost.total_cost_usd`）をそのまま表示するだけで、トークンは使いません。
文脈の使用率が上がってきたら `/compact`、タスクの切れ目なら `/clear` の頃合いです。自分の statusLine を使っているなら `.claude/settings.json` の `statusLine` を消してください（project の設定が user の設定より優先されます）。Codex CLI には同等の設定が無いので `/status` で見ます。

### 使わないツールの定義を外す（Claude Code）

`.claude/settings.json` の `permissions.deny` に `ListAgents`・`ReportFindings`・`ScheduleWakeup`・`Workflow` を置いています。deny に裸のツール名を書くと、そのツールの定義がモデルに送るツール一覧から外れます（Agent SDK の permissions 文書）。この 4 本は Claude Code が常時ロードする（tool search で遅延されない）ツールで、案件の仕事では呼ばれません。毎ターン固定で送られる分は 35,105 → 30,221 トークン（−14%。Claude Code 2.1.26x・Sonnet 5・`bench/results/fixed_v3.md`）、bench の trap では処理した入力が 232k → 166k（−28%、各 5 回、p=0.048）で、正誤は変わりません。`/loop`（ScheduleWakeup）や Workflow が要る人は該当行を消してください。Agent（researcher）と Skill（スキル 5 本）は残しています（外すとさらに −12k ですが委譲とスキルが使えなくなります）。deny に `ToolSearch` や TodoWrite 等の task-tracking ツール名を書くと逆に増えるので書かないでください（前者は遅延ロードが切れて +16k、後者は一群が opt-in されて相殺）。Codex にはツール定義を外す設定が無いので Claude Code だけです。

### 出力（thinking）を減らす調整ノブ

1 セッションの費用を単価で分けると、cache 作成が 40〜55%、出力（thinking 込み）が 22〜30%、cache 読みが 23〜38% でした（bench の A 条件 40 セッション。`bench/cost_breakdown.py`）。出力は入力の 5 倍の単価で、Sonnet 4.6 以降は過去ターンの thinking も文脈に残って入力として課金されるので、effort を下げると出力と再送の両方が減ります。bench の trap（各 5 回）では `--effort medium` で費用 −14%（p=0.046）、`--effort low` で −18%（p=0.048）、`MAX_THINKING_TOKENS=0` で −23%（p=0.12）、いずれも 5/5 正解でした。資料を作る newtask（各 5 回）でも medium は必須 8 項目を 5/5 で満たし費用 −10%（p=0.38。誤差の範囲）でした。ただし判断の重い仕事で同じとは言えないので、既定は変えていません。安く回したい仕事では `claude --effort medium` で起動するか、`.claude/settings.json` に `"effortLevel": "medium"` を足してください（Codex は `.codex/config.toml` の `model_reasoning_effort`）。effort をセッションの途中で変えるとキャッシュが作り直しになるので、最初に決めます。

### hooks が止めるもの

`scripts/ws hook pre-tool-use` が、ツールの入力（読むパス・grep の対象・シェルのコマンド）に「現在のタスク以外の `projects/*/tasks/*/`」が含まれていたら拒否し、理由として `knowledges/` を案内します。
`tasks/index.md`（一覧）と `scripts/ws` 自身の実行は通します。
`projects/`・案件直下・`tasks/` 直下を対象にした `find` / `ls` / `grep -r` / `rg` / `tree` と、パス指定の無い Grep / Glob も現在のタスクがある間は拒否します（他タスクの本文が結果に混ざり、読む導線としては `projects/index.md` と `tasks/index.md` で足りるため）。現在のタスクが無いとき（agent-ws 自体を直すとき）は止めません。repo 直下の `knowledges/`（共通）は現在のタスクの有無に関係なく読み書きできます。現在のタスクがある間は `bench/` と `docs/snapshots/` も読ませません（案件の仕事に関係なく、grep が当たると数十 KB の原文を丸ごと読んでしまうため）。
Claude Code は `.claude/settings.json`、Codex CLI は `.codex/hooks.json` から同じスクリプトを呼びます。
起動時の案内（SessionStart）は JSON の `additionalContext` で返します。Claude Code は素のテキストでも文脈に足しますが、Codex CLI は JSON でないと文脈に載りません（0.153.4 で確認）。

「`mkdir` ではなく `scripts/ws task new` を使う」は規約とスキルで指示しているだけで、hook では止めていません。エージェントが手でフォルダを作ってしまう事故が実際に起きたら、`projects/*/tasks/` 配下への直接の `mkdir` を hook で止める形に足せます。

正規化版（`.normalized.md`）がある文字起こしの原文を Read や Grep しようとすると、hook が読む先を正規化版に読み替えます（Bash/shell 経由の `cat`/`sed`/`grep` は書き換えずに deny し、正規化版のパスを示します）。

`knowledges/ontology/` と `projects/*/knowledges/ontology/` の `objects.json`・`log.jsonl`・`proposals/`（実体・記録・実行待ち）は、現在のタスクの有無に関係なく直接の読み書きを拒否します（読むには `scripts/ws onto query / show / log / act` を使います）。`ontology.json`・`index.md`・`questions.json` を含む配下全体への Edit / Write / MultiEdit / NotebookEdit も拒否し（`define apply` に誘導）、`onto approve`/`reject`/`adopt` を含む Bash コマンドや、承認・却下の文面と `claude`/`codex` の起動を同時に含むコマンドも拒否します（承認は人だけ）。保守用の環境変数 `WS_ONTO_MAINT=1` を**hook のプロセス**に立てると実体・記録・実行待ちと定義の直接編集の拒否だけを止められますが、エージェントの Bash からはそのプロセスの環境を変えられません（承認の拒否は常に効きます）。

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
用語集の「関係」列とナレッジの frontmatter `relates_to` / `supersedes` は残っています（任意欄。誰も読まない欄になりがちでした）。関係を書くなら、次のオントロジーの `link_types` に定義するほうを勧めます。

### 共通ナレッジ（案件をまたぐ自社の事実）

自社の組織図・決裁範囲・社内システムの一覧・標準手順・共通用語のように、どの案件でも同じで 3 ヶ月は変わらない事実は、repo 直下の `knowledges/` に置きます（案件の `knowledges/` と同じ形。`scripts/ws know new --common "タイトル" --owner "担当"` と `glossary add --common`）。進捗・数値・案件ごとの決定は案件側に置きます。組織図は 1 行 1 人か 1 部署で、関係は `→所属`・`→上位`・`→決裁` だけを書きます（見本は `knowledges/001_組織図.md`。架空です）。
SessionStart hook が案件のナレッジ一覧と同じ形で一覧行を差し込みます（現在のタスクが無いときも）。見本の組織図 1 枚と用語 3 語での増分は 274 字（現在のタスクあり 1,836 → 2,110 字、無し 136 → 410 字）で、共通側が無ければ 0 です。本文は必要なときだけ読みます。
同じ語・同じ事実が案件側と共通側にあれば案件側が勝ちます（顧客の組織図は案件、自社の組織図は共通）。`scripts/ws transcript normalize` は共通 → 案件の順に用語集を読み、同じ誤変換は案件側で上書きします。
共通側は案件の外で腐るので、1 ファイル 1 担当（frontmatter の `owner`）を持たせます。`owner` が空か `updated` が 90 日を超えると `scripts/ws doctor` が警告するので、担当が中身を確かめて `updated` を直すか消してください。hook は共通 `knowledges/` の読み書きを現在のタスクの有無に関係なく通します（`projects/` 横断とルートの一覧・検索の拒否は変わりません）。設計判断は `docs/adr/0015`。

### オントロジー（業務の型・つながり・できること）

自社共通の `knowledges/ontology/ontology.json` と案件ごとの `projects/<案件>/knowledges/ontology/ontology.json` に、業務の「型・つながり・できること（アクション）・制約」を JSON で書くと、`scripts/wsonto/`（取り決めは [scripts/wsonto/README.md](scripts/wsonto/README.md)）が読み込んで、照会・実行・承認・記録・書き出しを行います。定義を置いていない案件にはこの節は関係なく、起動時の注入（ナレッジの一覧）への増分も 0 字です。置いた場合の増分は、ナレッジの一覧に載る 1 行ぶんです（同梱の見本で実測: 共通だけが見える状態で 410 → 551 字の +141 字、見本の案件のタスクで 2,110 → 2,451 字の +341 字）。ナレッジの一覧に `ontology/` の行があれば、その案件（か自社共通）には型が定義されています。

**何を定義できるか**

| 種類 | 中身 |
|---|---|
| 型とプロパティ | `object_types`。名前・別名・説明・プロパティ（文字列・数値・日付・enum など。必須・一意・既定値・エージェントに見せるか） |
| つながり | `link_types`。from → to の件数の下限・上限と、逆向きの名前（例: `owner` の逆は `action_items`） |
| 型の継承 | `extends`。「すべての A は B か」と言えるときだけ使う（例: 案件の `Stakeholder` は共通の `Person` を extends。共通の型を案件で拡張できる。逆はできない） |
| できること（アクション） | `action_types`。引数・前提条件（`criteria`）・適用するルール・承認の要否（`approval`） |
| 定数 | `constants`。式から名前で参照する値（契約月数の下限など）。引数では上書きできない |

**アクション 1 回の流れ**

`scripts/ws onto act <アクション> 名前=値 …` は次の順で進みます。①引数の型と必須項目を検査する ②前提条件をすべて評価し、満たさないものがあれば理由文を添えて拒否する ③問題なければ実体の写しにルールを適用する ④触った実体を制約（SHACL 相当）で検査し、違反があれば元の実体を変えずに拒否する ⑤承認が要るかを判定する ⑥要らなければ反映して記録し、要れば実行待ちに積んで記録する。**どの段階で落ちても、本物の実体は変わりません。**

**見本の案件（架空の ACME 社移行支援）での具体例** — 見本は共通の `knowledges/ontology/` と `projects/_example/knowledges/ontology/` に同梱してあり（内容はテストの基準 `tests/fixtures/onto_case/` と同じ。消して構いません）、`scripts/ws onto types --project _example` や `scripts/ws onto eval --project _example` でそのまま試せます。

- 置き換え済みの決定（提案時の台数・8 台）を前提にした見積は、現行の決定（PoC の結果で見直した台数・12 台）を示して拒否されます。
- 12 台・12 か月の見積は、月額 410,000 円・総額 4,920,000 円をエンジンが計算して反映されます（営業部長の決裁上限 500 万円の範囲内なので）。
- 同じ内容を 24 か月にすると総額が決裁上限を超えるため、実行待ちに積まれます。
- 有効期限の切れた単価や、見積の決裁権限を持たない人を指定した見積は拒否されます。

**承認のしかた**

決裁の要るアクションと定義の変更は、実行待ち（`proposals/P-0001.json` か `S-0001.json`）に積まれます。承認できるのは人だけです。チャットで「承認 P-0001」と送るか、端末で `scripts/ws onto approve P-0001` を実行します。積んだ時点の前提ではなく、承認したときの今の状態で検査をやり直してから反映します。エージェントが承認・却下を実行しようとすると hook が拒否します。

**定義の変え方**

型・つながり・アクション・定数を変えるときは `ontology.json` を直接編集できません（hook が拒否し、`scripts/ws onto define apply <patch.json>` に誘導します）。`define apply` は patch を今の定義にマージし、メタモデルの検査（名前の規則・参照先の不在・継承の循環など）と lint のアンチパターン検収を行い、今の実体を新しい定義で検査してから実行待ちに積みます。人が承認すると版（`version`）が 1 上がり、`ontology.json` が置き換わります。lint が見るアンチパターン:

| code | 見るもの |
|---|---|
| `MISNOMER` | プロパティ・リンクの名前が `date` `value` `item` のような汎用語 |
| `SET_ACTION` | 名前が `Set`/`Update` で始まり、1 プロパティしか変えないアクション |
| `ACTION_SPRAWL` | 1 つの型を対象にするアクションが 10 を超える |
| `KITCHEN_SINK` | 技術列らしい名前（`etl_` `_hash` など）や、1 つの型に 20 超のプロパティ |
| `GOD_OBJECT` | 実体 10 件以上の型で、埋まっている率が 30% 未満のプロパティが 5 つ以上 |
| `TIME_MACHINE` | 型名が `V2` `Old` `Bak` などで終わる |
| `SILO_NAME` | 別の型と label・別名が重なる |
| `THIN_DESCRIPTION` | アクションの説明が 20 字未満 |

**記録と改ざんの検出**

アクション・承認・却下・定義の変更はすべて `log.jsonl` に 1 行ずつ追記され、拒否も残ります。各行に誰が・何を・結果・変更前後の値・記録のハッシュが入ります。アクションを通さずに `objects.json` を直接書き換えると、`scripts/ws doctor` が最後の記録のハッシュと今のファイルのハッシュの食い違いを見つけます。

**答えたい質問と eval**

型を定義するときは、先に `questions.json` に「答えたい質問」を書きます。`scripts/ws onto eval` はその質問を写しの上で実行し、期待どおりの答えが返るかを確かめます（本物の実体は変えません）。

**書き出し**

`scripts/ws onto export --format jsonschema|turtle|mermaid|markdown` で定義を書き出せます。JSON Schema はアクションの引数と実体の形、Turtle は RDFS/OWL の語彙と SHACL の制約（rdflib / pySHACL で検査できます）、Mermaid は ER 図、markdown は `index.md` に使う人向けの表と図です。

**コマンド**

| コマンド | 中身 |
|---|---|
| `init [--common\|--project X]` | 空の定義を作る（既にあれば何もしない） |
| `types` | 型とアクションの一覧 |
| `describe <型かアクション>` | 型ならプロパティ・つながり、アクションなら引数・前提条件・承認 |
| `query <型> [--where 式] [--select a,b] [--limit N]` | 実体を照会する |
| `show <型:id>` | 1 件の値・つながり・関係する実行待ちを見る |
| `act <アクション> [名前=値 …] [--why 文] [--dry-run]` | アクションを実行する（反映・実行待ち・拒否のいずれかを返す） |
| `define apply <patch.json> [--why 文]` | 定義を変える（検査・lint のあと実行待ちに積む） |
| `approve <P-… か S-…>` / `reject <id> --reason 文` | 人だけ。実行待ちを承認・却下する |
| `proposals [--all]` | 実行待ちの一覧 |
| `validate` / `lint` / `eval` | 制約検査 / 定義の検収 / 答えたい質問の評価 |
| `export --format … [--out path]` | 書き出し |
| `log [--object 型:id] [--action 名前] [--limit N]` | 記録の照会 |
| `adopt --note 文` | 人だけ。手で直した実体を記録に取り込む |

型・つながり・アクションを足す・直すのは `.agents/skills/ontology-define/` スキルです。設計判断は [ADR 0022](docs/adr/0022-operational-ontology.md)。

### 人からの指摘

「結論を先に」「その言い方はやめて」のような指摘は `scripts/ws lesson add "〜のとき、〜する（理由）"` で `LESSONS.md` に 1 行残し、hook が起動のたびに全行を差し込みます。
1 回目で残します（2 回目を待つ規則は、1 回目を覚えている者がセッションをまたいで居ないので機能しません）。
20 行を超えると `scripts/ws doctor` が報告するので、統合するか AGENTS.md・doctor の検査へ昇格して減らしてください。長いほど守られなくなります。
案件固有の指摘は `--project <案件>` で案件の `index.md` の「この案件での決まりごと」に入ります。
指摘かどうかを機械で見分ける hook は付けていません。指摘らしい語で当てても大半が説明や質問で、外れの多い注意は無視されるようになるからです。

## 制約と注意

- **ルートで起動してください。** サブディレクトリで起動すると、ルートの `.claude/settings.json` の hooks が読まれません（Claude Code 2.1.261 で確認）。
- **Claude Code の Advisor（相談役モデル）は外しています**（`.claude/settings.json` の `env` の `CLAUDE_CODE_DISABLE_ADVISOR_TOOL=1`）。Advisor は相談のたびに固定分ごと会話全文を Opus に非キャッシュで読ませます。agent-ws の仕事では正誤に効かず（5/5 対 5/5）、相談が起きた本だけ費用が 3.4〜3.7 倍になりました（[ADR 0017](docs/adr/0017-disable-claude-code-advisor.md)）。戻すならその行を消してください（`/advisor` も使えるようになります）。
- `.ws/current` は git 管理外です。人ごと・マシンごとに「現在のタスク」は違います。同じ clone で複数のセッションを並行させることはできます。現在のタスクはセッションごとに `.ws/sessions/<session_id>.current` に写して持つので、片方の `task use` がもう片方に影響しません（セッションは Claude Code なら環境変数 `CLAUDE_CODE_SESSION_ID`、Codex CLI なら `CODEX_THREAD_ID` で見分けます）。新しいセッションと `/clear` のあとは、最後に設定したタスク（`.ws/current`）から始まります。端末から直接叩く `scripts/ws task current` はセッションに紐付かないので `.ws/current` を返します。
- **Windows でも同じ hooks が動きます**（[ADR 0019](docs/adr/0019-windows-without-changing-linux.md)）。Claude Code の hooks はシェルを介さない exec 形式で `python` を直接起動するので Git Bash は任意です（PowerShell だけでも動きます）。ツール入力がバックスラッシュ区切りで届いても、他タスクの拒否・横断検索の拒否は同じように効きます（PowerShell ツールの `Get-ChildItem -Recurse` / `Select-String` / `Invoke-WebRequest` も止めます）。前提は 2 つ。`python` が PATH にあること、`.claude/skills` の symlink を作るために開発者モードを有効にして `git clone -c core.symlinks=true` すること（symlink が無いと Claude Code からスキルが見えません）。エージェントに `scripts/ws …` を叩かせる文面は Linux と共通なので、Windows では最初の 1 回だけ失敗して `python scripts/ws …` に読み替えます。
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

**2 回目の計測（2026-09-06 夜。PR #8 の agent-ws を A にして A/B/C を取り直し）**

上の表の A は PR #4 時点のコードです。PR #6 で doctor の警告が旧形式の reference の作り替えを誘発して「続きをやって」の処理した入力が 3 倍になる退行があり（749k・18 ターン）、PR #8 で直しました。そのうえで A を 10 回ずつ取り直し、B/C は朝の 5 回に 5 回ずつ足して 10 回にしています（B/C は agent-ws のファイルを含まないので条件は同じ）。処理した入力は中央値、p は A との 5 対 5 以上の並べ替え検定です。

| 場面 | 条件 | 精度 | 処理した入力 | 費用 USD | p（入力 / 費用） |
|---|---|---|---|---|---|
| 続きをやって（Sonnet） | agent-ws | 10/10 | 185k | 0.138 | — |
|  | 同じ構造・仕組みなし | 1/10（9 回は聞き返し） | 170k | 0.147 | 0.69 / 0.63 |
|  | 導入前 | 0/10 | 152k | 0.118 | 0.21 / 0.05 |
| 続きをやって（Haiku 4.5） | agent-ws | 5/5 | 186k | 0.076 | — |
|  | 仕組みなし / 導入前 | 0/5 / 0/5（1 ターンで聞き返し） | 22k | 0.018 | — |
| 新規タスク（必須 8 項目） | agent-ws | 8/8 × 10、他タスクへの立ち入り 0 | 248k | 0.194 | — |
|  | 同じ構造・仕組みなし | 8/8 × 10、立ち入り中央値 6 回 | 501k | 0.333 | 0.001 / 0.001 |
|  | 導入前 | 8/8 × 9（1 回は 0）、立ち入り 6 回 | 403k | 0.363 | 0.005 / 0.004 |
| 引き継ぎ（1 本目 + 2 本目の合計） | agent-ws | 2 本目 10/10 | 691k | 0.372 | — |
|  | 同じ構造・仕組みなし | 9/10 | 1,264k | 0.712 | 0.003 / 0.001 |
|  | 導入前 | 9/10 | 999k | 0.598 | 0.007 / 0.003 |

引き継ぎの 1 本目（新規に着手する側）だけを見ると、agent-ws は導入前より処理した入力が多く（508k 対 420k。タスク作成と `ref add` の分）、費用は安い（0.258 対 0.307）という混ざった結果です。効くのは 2 本目（167k 対 512k）で、合計では 31〜45% 少なくなります。新規タスクの「古い数字」の機械ヒット（A 10・B 13・C 17 箇所）はすべて目視し、どれも「8・10 台は未達で 12 台に確定」という経緯の記述で、古い数字を前提に使った例はありませんでした。

**PR #8 の中身の効果**（退行を除いた土台 = PR #6 + doctor の修正、に対して。「続きをやって」・Sonnet・案件 8）

| 条件 | n | 処理した入力 | 費用 USD | ターン | 正誤 | p（対 土台） |
|---|---|---|---|---|---|---|
| 土台 | 20 | 296k | 0.172 | 8 | 20/20 | — |
| 起動時の注入だけ | 10 | 246k | 0.166 | 6 | 10/10 | 0.34 |
| AGENTS.md「ターンを減らす」だけ | 10 | 239k | 0.166 | 6 | 10/10 | 0.078 |
| PR #8 全部 | 20 | 183k | 0.141 | 5 | 20/20 | < 0.001 |

注入と規約はそれぞれ −17〜19% で単独では有意に届かず、両方で −38%・費用 −18%・ターン 8 → 5 になります。新規タスク（注入の対象外）では差が出ません。行は `bench/results/runs_ts7.jsonl`（部品分解）と `runs_ts8.jsonl`（A/B/C）にあります。

**効かなかった場面・測っていないこと**

- タスク名を言って頼む依頼では差が出ません（前回の計測。index.md が同じなら読む範囲も同じ）
- 「Sonnet でも安定する」は、この材料では「古い数字を掴む」形の誤答が 1 回も出なかったので示せていません。仕組みなしの失敗はすべて「聞き返して止まる」でした
- 毎ターン固定で送られる分は agent-ws が Sonnet で 32.0k、仕組みなしが 29.2k（AGENTS.md・skills・注入の 2.9k）。Haiku 4.5 は 24.5k と 21.8k
- Codex CLI・Opus・compact 後の再注入・用語集の正規化は測っていません
- オントロジーがエージェントの正確さとトークンに与える効果は未計測です。照会（`query`/`show`）と実行（`act`）はそれぞれ 1 ターンなので、1 タスクあたりのトークンは増える見込みで、減るとすれば防げた手戻りの分だけです

`bench/` は agent-ws を使うだけなら不要です。`projects/_example/` と同じく消して構いません。

## 開発

```
python3 -m unittest discover -s tests
```

案件作成 → タスク作成 → hook の拒否と許可 → 情報源の保存 → 用語集と正規化 → ナレッジ昇格 → 完了、を一時ディレクトリで通します。オントロジー（`scripts/wsonto/`）は `tests/test_onto_*.py` に別立てで、`tests/fixtures/onto_case/` を適合の基準にしています。W3C の語彙（RDFS/OWL・SHACL）との突き合わせだけは `rdflib` が要るので別に走らせます（無ければ skip）。

```
uv run --with rdflib --with pyshacl python3 -m unittest tests/test_onto_w3c.py tests/test_onto_parity.py
```

## ライセンス

MIT（[LICENSE](LICENSE)）。
