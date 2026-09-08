# オントロジー層を入れるかを検討した根拠

`docs/adr/0014`（重いオントロジーは入れない。軽い関係層は実務で判断する）の根拠にした出典。
発端は解説記事 2 本（#1・#4）。#1 が根拠にしている 2 つの実装（#2・#3）を一次情報として当たった。

判断の物差しは bench の実測（`bench/results/runs.jsonl`・`runs_ts8.jsonl` の verdict / stale_n / other_task / denied）と、
グラフ・オントロジー MCP の第三者実測（[token-reduction-tools.md](token-reduction-tools.md) #12・#13）。

各行のファイルに取得日時・引用・原文（`.orig.md`）がある。ページは書き換わるので、規則を見直すときは再取得して差分を見る。

## 解説記事・実践記（二次情報）

| # | 出典（題名と URL） | 取得日時 | ファイル | 何の根拠か |
|---|---|---|---|---|
| 1 | AI駆動開発のためのオントロジー（Qiita・Syoitu・2026-09-07） — https://qiita.com/Syoitu/items/d41d234876e1bfadbf32 | 2026-09-08T23:45:56+09:00 | [snapshots/20260908_2345_AI駆動開発のためのオントロジー.md](../snapshots/20260908_2345_AI駆動開発のためのオントロジー.md) | オントロジーの定義（クラス・プロパティ・関係・制約）。「プロンプトに書くのと何が違うか」＝機械的に検証・追跡できるデータとして永続化できること。precondition が出荷済み注文のキャンセルを拒否するデモ。AWS 実装のコスト警告（アイドルで約 930 ドル/月）の引用 |
| 4 | AIに会社の地図を持たせたら、3年目社員のように働き始めた（note・ymdpharm3・2026-07-21） — https://note.com/ymdpharm3/n/n8515d151e56d | 2026-09-08T23:52:10+09:00 | [snapshots/20260908_2352_AIに会社の地図を持たせたら、3年目社員のように働き始めた_〜精度とトークン効率.md](../snapshots/20260908_2352_AIに会社の地図を持たせたら、3年目社員のように働き始めた_〜精度とトークン効率.md) | Ubie の「会社の地図」。1 カード 1 YAML（用語・別名・関係・担当・出所）、3 ヶ月変わらない事実だけを載せる、MCP の lookup / expand / seeds。著者の計測: 何も無し 8 / 地図単体 43 / 都度検索 112 / 併用 119 / 全件 125（品質スコア、150 点満点、相対評価。全件は 1 回答 8 分超）。599 枚・関係 1,179 本・別名 3,274 個。所要 2 日 |

## 一次情報（実装の README）

| # | 出典（題名と URL） | 取得日時 | ファイル | 何の根拠か |
|---|---|---|---|---|
| 2 | operational-ontology（gura105） — https://github.com/gura105/operational-ontology | 2026-09-08T23:46:01+09:00 | [snapshots/20260908_2346_GitHub_-_gura105_operational-ontology_A_.md](../snapshots/20260908_2346_GitHub_-_gura105_operational-ontology_A_.md) | パターンの前提は「他システムが持つ統合済みの物理データ」と「名前の付いた書き込みアクション」。precondition はその書き込みを止める。OWL/RDF を使わない理由（推論器は注文をキャンセルできない）。フォークして使い npm パッケージにしない。Node 24・SQLite・Zod・MCP SDK |
| 3 | context-ontology-accelerator（aws） — https://github.com/aws/context-ontology-accelerator | 2026-09-08T23:46:56+09:00 | [snapshots/20260908_2346_GitHub_-_aws_context-ontology-accelerato.md](../snapshots/20260908_2346_GitHub_-_aws_context-ontology-accelerato.md) | Scan → Model → Serve の本番向け基盤。SPARQL federation と MCP で agent に文脈を出す。前提が Python 3.12・Node 22・Docker・Java 17・Smithy |

## 既にある台帳・実測

- グラフ・オントロジー MCP のトークン実測: [token-reduction-tools.md](token-reduction-tools.md) #12（RepoGraph: ターン −11%・トークン +7%）・#13（serena +93%、CodeGraph +22〜47%）
- bench の失敗の型: `bench/results/runs.jsonl` と `runs_ts8.jsonl` の `verdict`。数字の答えを求めた 115 セッション（trap・chain/S2）で数字を間違えた回は 0。失敗 37 回はすべて「どのタスクか聞き返して止まる」（仕組みなしの B/C だけ）。agent-ws（A）は 55/55 正解、他タスクへの立ち入り 0、`stale_n` の機械ヒットは目視で全件が経緯の記述（README「計測」）
- bench の案件 1 つぶんのナレッジの量: `bench/corpus/projects/acme/knowledges/` の 5 ファイルで約 3,000 字。SessionStart の注入とナレッジ 3 本の Read で全部読める規模
- オントロジー一般の割に合わない型（先行調査）: 単一チームの語彙統一だけが目的なら用語集と DB 制約で足りる／スチュワード不在だと 2 四半期で腐る／全社を先にモデル化しようとして死ぬ。W3C 仕様と実務記事を当たった別の調査の結論で、このリポジトリには写していない

## 再取得の手順

`WS_ROOT=$PWD uv run python3 scripts/ws ref add <URL> --dir docs/snapshots --summary "<1文>"` で
該当行の URL を撮り直し、上の表のファイル欄を新しいファイル名に差し替える。
