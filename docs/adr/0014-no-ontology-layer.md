# 0014. 重いオントロジー（グラフ DB・MCP・precondition）は入れない。軽い関係層は実務で判断する
- 状態: 保留（軽い層の採否は案件 3 つ分の LESSONS を見て決める） / 日付: 2026-09-09

## 状況
「オントロジーを入れればエージェントが意味を理解して成果物の品質が上がり、手戻りのトークンが消える。前提を毎回プロンプトで書くのも面倒」という仮説を検討した。手がかりは記事 2 本。Qiita の解説は operational-ontology（オブジェクト・リンク・アクションと precondition）と AWS の context-ontology-accelerator（Neptune）を、note の実践記は Ubie の「会社の地図」（1 カード 1 YAML・用語＋別名＋関係＋担当＋出所・MCP の lookup / expand / seeds）を指す。推進・反対・実験設計の 3 つの立場で草案を検討させた。初稿は「入れない」だったが、実案件ゼロ・bench 未計測で「不要」の根拠が無いと指摘を受け、判断を実務に委ねる形に改めた。

## 決定
- グラフ DB・SPARQL・オントロジー MCP・precondition 型は入れない。agent-ws が書くのは文書で、案件データへ書き込むアクションを持たないため止める対象が無い。これは実務の有無に関係なく成り立つ
- Ubie 型の「カードの束」は `knowledges/glossary.md` と `knowledges/` と同型で、無いのは「関係」だけ。これが要るかは**まだ決めない**。bench はその失敗の型を測っておらず、実案件も回っていない
- 実務で試せるように任意の欄を足す: 用語集の「関係」列（`glossary add --relation`）と、ナレッジの frontmatter `relates_to` / `supersedes`。空でも doctor は警告しない
- 成果物を人に直された手戻りは LESSONS.md に型を付けて残す: 「古い数字」「誤った関係者」「決定違反」。案件が 3 つ回ったらこの 3 型を数え、欄を必須にするか、消すかを決める
- bench の制約シナリオ（conflict / stale8 / contact × A / A+rules / A+onto、n=8・約 18 ドル）は合成データでの裏取りとして別に回す

## 理由
- 前提を毎回書く問題は既に解いてある（ADR 0009 の注入）。ただし注入は現在の案件の分だけで、案件横断の地図は agent-ws に無い（ADR 0004）。Ubie の地図が主眼にする範囲はここ
- bench では数字の答えを求めた 115 セッションで誤り 0、失敗 37 回はすべて聞き返し。しかし 4 シナリオは単一の事実の想起で、決定違反・関係の辿り違い・古い前提の混入は未計測。「要らない」とは言えない
- Ubie の実測（地図単体 43 / 都度検索 112 / 併用 119 / 全件 125、150 点満点・著者の相対評価）が示すのは、全件を読めない規模で検索と組んだときに効くこと。agent-ws は 1 案件約 3,000 字で全部注入できるが、実案件がその規模に収まるかは分からない
- トークンの論点はグラフ・MCP 型にだけ当たる（RepoGraph −11% / +7%、ADR 0012）。欄に書く形なら追加は 100 字未満で無視できる。争点は「効くか」と「維持されるか」で、それは使って数えるしかない

## 捨てた案
- **operational-ontology を MCP で繋ぐ**: 止めるべき書き込みアクションが無い。Node・pnpm・SQLite が増える
- **context-ontology-accelerator**: 本番向け基盤（Neptune・OIDC・Smithy）。アイドルで約 930 ドル/月（Qiita の引用）。1 人の案件フォルダには過大
- **今の時点で「入れない」と決める**（この ADR の初稿）: 実案件ゼロ・bench 未計測で「不要」の根拠が無い
- **欄を最初から必須にする**: 使い道の無い欄は埋められず腐る（Ubie「人手で維持する台帳は必ず腐る」）。任意にして、埋まるかどうか自体を証拠にする

## 影響
`templates/project/knowledges/glossary.md` に「関係」列、`templates/knowledge.md` に `relates_to` / `supersedes`、`scripts/ws glossary add --relation`、AGENTS.md「同じ失敗を繰り返さない」に手戻りの 3 型。bench の corpus は変えない（比較可能性）。判断の期限は案件 3 つ。引き金: 3 型の LESSONS が出る／1 案件のナレッジが全文注入に収まらない／エージェントが案件データへ書き込むアクションを持つ（このときだけ precondition 型を再検討）。

根拠: `docs/sources/ontology.md` #1〜#4・`docs/sources/token-reduction-tools.md` #12〜#13・`bench/results/runs.jsonl`・`bench/results/runs_ts8.jsonl`・`bench/results/summary.md`
