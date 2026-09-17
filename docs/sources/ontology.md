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

## 0022（業務を動かす層としてのオントロジー）の根拠

`docs/adr/0022` の根拠にした一次資料。0014 のとき（#1〜#4）は解説記事と 2 つの実装だけを見ていた。今回は、参照した設計（Palantir の公式ドキュメント）と W3C の仕様に当たった。
引用は各ファイルの「引用した記述」に原文のまま置き、`.orig.md` の中に実在することを機械で突き合わせてある。

| # | 出典（題名と URL） | 取得日時 | ファイル | 何の根拠か |
|---|---|---|---|---|
| 5 | Why create an Ontology?（Palantir Foundry docs） — https://www.palantir.com/docs/foundry/ontology/why-ontology | 2026-09-17T23:04:57+09:00 | [snapshots/20260917_2304_Palantir.md](../snapshots/20260917_2304_Palantir.md) | 承認の既定を「実行待ち」にした根拠。オントロジーは企業のデータでなく意思決定を表す、と書き、意思決定を Data / Logic / Action / Security に分ける。既定ではアクションは AI が実行待ちに置くところまでで、最終レビューは人、と書いている |
| 6 | Action types: Overview（Palantir Foundry docs） — https://www.palantir.com/docs/foundry/action-types/overview | 2026-09-17T23:05:09+09:00 | [snapshots/20260917_2305_Palantir.md](../snapshots/20260917_2305_Palantir.md) | アクションを「1 つ以上の実体を変える 1 回のトランザクション」にした根拠（全部成功か全部取り消し）。アクション型は 変更の定義で、実行時にオントロジーへ反映される |
| 7 | Submission criteria（Palantir Foundry docs） — https://www.palantir.com/docs/foundry/action-types/submission-criteria | 2026-09-17T23:05:18+09:00 | [snapshots/20260917_2305_Palantir_18.md](../snapshots/20260917_2305_Palantir_18.md) | 前提条件（`criteria` の `when` と `message`）の根拠。提出条件はアクションを提出できるかを決める条件で、満たさないときの失敗メッセージが利用者に表示される。条件の雛形は Current user / Parameter / Execution context の 3 つ |
| 8 | Ontology design: Anti-patterns（Palantir Foundry docs） — https://www.palantir.com/docs/foundry/ontology/ontology-anti-patterns | 2026-09-17T23:05:27+09:00 | [snapshots/20260917_2305_Palantir_27.md](../snapshots/20260917_2305_Palantir_27.md) | lint の検収項目の根拠。System Silos・The Kitchen Sink・The God Object・Action Sprawl などの定義。`SET_ACTION`（1 プロパティだけ変える操作の乱立）は Action Sprawl の定義そのもの |
| 9 | Ontology design: Best practices（Palantir Foundry docs） — https://www.palantir.com/docs/foundry/ontology/ontology-best-practices | 2026-09-17T23:05:37+09:00 | [snapshots/20260917_2305_Palantir_37.md](../snapshots/20260917_2305_Palantir_37.md) | 「現実をモデル化し、ソースデータを写さない」。原則は指針であって法ではない、と書いている。lint を全部 warn にして人の承認の材料に留めた根拠 |
| 10 | AIP Logic integration with Automate（Palantir Foundry docs） — https://www.palantir.com/docs/foundry/logic/aip-logic-integration-automate | 2026-09-17T23:05:44+09:00 | [snapshots/20260917_2305_Palantir_44.md](../snapshots/20260917_2305_Palantir_44.md) | 実行待ち（`proposals/`）と人の承認の根拠。編集を自動で適用するか、人のレビュー待ちに積むかを選べ、承認するとアクションが実行される |
| 11 | Shapes Constraint Language (SHACL)（W3C Recommendation） — https://www.w3.org/TR/shacl/ | 2026-09-17T23:05:50+09:00 | [snapshots/20260917_2305_Shapes_Constraint_Language_(SHACL).md](../snapshots/20260917_2305_Shapes_Constraint_Language_(SHACL).md) | 制約検査（`validate.py`）の code と Turtle の書き出しの仕様の根拠。`sh:closed`・`sh:class`・`sh:minCount`、および SHACL の「型の実体」の定義（下位クラスの実体も含む）。上位の型の閉じた形が下位の型だけのプロパティを違反にした原因 |
| 12 | schema.org: rangeIncludes / domainIncludes / Data model — https://schema.org/rangeIncludes ・ https://schema.org/domainIncludes ・ https://schema.org/docs/datamodel.html | 2026-09-17T23:05:56+09:00 ほか | [rangeIncludes](../snapshots/20260917_2305_rangeIncludes_-_Schema.org_Property.md)・[domainIncludes](../snapshots/20260917_2306_domainIncludes_-_Schema.org_Property.md)・[Data model](../snapshots/20260917_2311_Data_model_-_Schema.org.md) | 語彙の両端を `schema:domainIncludes` / `schema:rangeIncludes` で書いた先例。「プロパティの値に期待される型（の 1 つ）」を表す注釈で、schema.org は複数の domain / range を許した理由を「実用上の判断」（単一だと人工的な型が増える）と書いている。**推論を避けるため、とは書いていない**（それはこのリポジトリの実測。下記） |
| 13 | Building Effective AI Agents（Anthropic） — https://www.anthropic.com/research/building-effective-agents | 2026-09-17T23:06:06+09:00 | [snapshots/20260917_2306_Building_Effective_AI_Agents.md](../snapshots/20260917_2306_Building_Effective_AI_Agents.md) | 読む道具（`query` / `show`）と変える道具（`act`）を分けた根拠。顧客データや注文履歴を引くツールと、返金やチケット更新のような行為を別に挙げ、エージェントはチェックポイントで人のフィードバックを待てる、と書いている |
| 14 | Reducing Hallucinations with the Ontology in Palantir AIP（Palantir Blog） — https://blog.palantir.com/reducing-hallucinations-with-the-ontology-in-palantir-aip-288552477383 | 2026-09-17T23:06:14+09:00 | [snapshots/20260917_2306_Reducing_Hallucinations_with_the_Ontolog.md](../snapshots/20260917_2306_Reducing_Hallucinations_with_the_Ontolog.md) | 3 段の対策の根拠: 実体を照会して接地する／方程式・予測・シミュレーションのような計算は専用の関数に任せる（agent-ws では月額・総額をエンジンが計算する）／提案は直接書き戻さず承認待ちに積む |

このリポジトリで実測したこと:

- `tests/test_onto_parity.py`: 自前の検査（`validate.py`・閉世界）と pySHACL が、きれいなデータと違反データ 8 通り（列挙に無い値・下限違反・必須のリンクの欠落・件数の超過・逆向きの件数の超過・リンク先の型違い・定義に無いプロパティ・必須のプロパティの欠落）で同じ判定を出す。
- `tests/test_onto_w3c.py`: 語彙に `rdfs:range` を書き出すと、RDFS 推論つきの検査（pySHACL の `inference="rdfs"`）で型違いのリンク先に型が付き、`sh:class` が効かなくなった。`schema:rangeIncludes` に替えたあと、推論後も型が付かないことを `test_wrong_class_link_does_not_infer_range_type` が確かめている。RDFS 推論は `rdfs:subClassOf` による型の包含（案件の関係者は人の一種、台数の決定は決定の一種）にだけ使う。

## 再取得の手順

`WS_ROOT=$PWD uv run python3 scripts/ws ref add <URL> --dir docs/snapshots --summary "<1文>"` で
該当行の URL を撮り直し、上の表のファイル欄を新しいファイル名に差し替える。
