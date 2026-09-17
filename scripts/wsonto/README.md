# wsonto — オントロジーのエンジン（構成とモジュール間の取り決め）

`scripts/ws onto …` の中身。定義（`ontology.json`）を読み、実体（`objects.json`）への照会・前提条件の判定・実行・実行待ち・記録を行う。
設計判断は `docs/adr/0022`。使い方は README の「オントロジー」節と `.agents/skills/ontology-define/`。ここはコードを直す人のための取り決め。

## 守ること

- **実行時は標準ライブラリだけ・Python 3.9 以上。** `match` 文、`zip(strict=)`、括弧つきの複数 `with`、`tomllib` は使わない。型注釈の `X | None` は `from __future__ import annotations` の下でだけ使う（実行時に評価される場所では `Optional`）。
- 利用者に見せるエラーは `errors.py` の例外（`OntoError` の子）で、日本語 1 行。何を直せばよいかを書く。
- 公開リポジトリなので、コード・テスト・fixture に私的な ID・絶対パス・実在の人名を入れない。
- hook から呼ばれる経路（`scripts/ws hook …`）では wsonto を import しない（毎ツール呼び出しで走るので遅くしない）。例外は UserPromptSubmit が承認の文面に一致したときだけ。

## 置き場と範囲

| 範囲 | ディレクトリ | 補足 |
|---|---|---|
| 共通（自社） | `knowledges/ontology/` | どの案件からも見える |
| 案件 | `projects/<案件>/knowledges/ontology/` | 共通の型を使える。案件の実体から共通の実体へリンクできる（逆は不可）。共通と同じ名前の型・リンク型・アクション型・定数は定義できない（`SchemaError`） |

ディレクトリの中身:

| ファイル | 中身 | 書く人 |
|---|---|---|
| `ontology.json` | 定義（正本） | `define apply` の承認時だけ |
| `objects.json` | 実体 | エンジン（`engine.act` / `approve`）だけ |
| `log.jsonl` | 記録。1 行 1 件、追記のみ | エンジンだけ |
| `proposals/P-0001.json`・`S-0001.json` | 実行待ち（アクション／定義の変更） | エンジンだけ |
| `questions.json` | 答えたい質問＝評価セット | `define apply` か人 |
| `index.md` | 人が読む表と Mermaid の図（自動生成） | `export.to_markdown` |
| `.lock/` | ロック（git 管理外） | `store.locked` |

## ontology.json

見本は `tests/fixtures/onto_case/`（架空の案件支援。`common/` が自社の部署・人・決裁権限、`project/` が案件の決定・台数・単価・見積・宿題・担当。この形式で書けて、`project/questions.json` の期待どおりに動くことが適合テストの前提）。

```
{
  "ontology": "<名前>", "version": <int>, "description": "...",
  "prefixes": {"schema": "https://schema.org/"},
  "governance": {"schema_changes": "stage" | "auto"},      # 省略時 stage
  "constants": {"UPPER_SNAKE": <値>},                        # 式から名前で参照。引数では上書きできない
  "object_types": {"<Type>": {
      "label", "aliases": [..], "description", "same_as": "prefix:Local",
      "extends": ["<Type>"], "abstract": bool,
      "label_property": "<prop>", "alias_property": "<prop>",   # 実体の呼び名・別名（transcript normalize が使う）
      "summary": ["<prop>", ..],                                # 照会の既定の列
      "properties": {"<prop>": {
          "type": "string|text|int|number|bool|date|datetime|enum", "values": [..],   # enum のとき
          "required": bool, "many": bool, "min", "max", "pattern", "unique": bool, "default",
          "label", "description", "agent_visible": bool              # 省略時 true
      }}}},
  "link_types": {"<link>": {
      "label", "from": "<Type>", "to": "<Type>", "min": int, "max": int|null,        # from 1 件が持てる to の件数。省略時 0..∞
      "inverse": "<name>", "inverse_label", "inverse_min": int, "inverse_max": int|null}},
  "action_types": {"<Action>": {
      "label", "description",
      "parameters": {"<param>": {"type": ..., "values": [..], "min", "max", "pattern"} | {"object_type": "<Type>"}, + "required", "many", "label"},
      "criteria": [{"when": "<式>", "message": "<雛形>"}],
      "rules": [ <下記> ],
      "approval": "auto" | "stage" | {"stage_if": "<式>", "role": "<名前>"},          # 省略時 stage
      "returns": "<as の名前>", "next": "<雛形>"}}
}
```

名前の規則: 型とアクションは `^[A-Z][A-Za-z0-9]*$`、プロパティ・リンク・逆向きの名前・引数は `^[a-z][a-z0-9_]*$`、定数は `^[A-Z][A-Z0-9_]*$`。
`id`・`type`・`actor` は予約語。1 つの型の上で、プロパティ名・その型から出るリンク名・その型に入るリンクの逆向きの名前は重なってはいけない（式では同じ `obj.name` で引くため）。

ルール（上から順に、実体の写しに適用する。値はすべて**式**。文字列の定数は `"'active'"` のように式の中で引用符を付ける）:

```
{"create": "<Type>", "as": "<名前>", "id": "<雛形。{seq} はその型の連番>", "set": {"<prop>": "<式>"}, "link": {"<link>": "<式: 実体か実体のリスト>"}}
{"modify": "<引数か as の名前>", "set": {...}, "link": {...}, "unlink": {"<link>": "<式>"}}
{"delete": "<引数か as の名前>"}
```

どのルールにも `"if": "<式>"` を付けられる（偽ならそのルールを飛ばす）。`link` の式が `None` か空のリストなら何も結ばない（省略できる引数をそのまま渡せるようにするため）。`max` が 1 のリンクへの `link` は付け替え（今の相手を外して結ぶ）、それ以外は追加（重複は足さない）。`set` の式の値はそのプロパティの型に直して入れる（`date` は `YYYY-MM-DD` の文字列で保存）。

雛形（`message`・`next`・`id`）は `{式}` を評価して埋める。評価に失敗した `{…}` はそのまま残す（理由文を出すこと自体は失敗させない）。

## objects.json

```
{"_meta": {"seq": {"Estimate": 1}},
 "<Type>": {"<id>": {"<prop>": <値>, "_links": {"<link>": ["<Type>:<id>", ..]}}}}
```

- 実体は**具体的な型**の下に置く。参照は常に `"<Type>:<id>"`（下位の型の実体も指せるようにするため）。
- リンクは from 側の実体の `_links` にだけ持つ。逆向きは読み込み時に索引を作る。
- `date` は `YYYY-MM-DD`、`datetime` は ISO 8601 の文字列で保存し、式に渡すときに `datetime.date` / `datetime.datetime` に直す。
- 案件の実体から共通の実体への参照は、自分の store に無ければ共通の store から引く。案件の型は共通の型を `extends` できる（`Stakeholder` は共通の `Person` の一種）。案件のリンク型の逆向きの名前は、共通の型の実体からも引ける（共通の `Person` の実体に `leads` を聞けば空のリスト）。
- 書き出しは `sort_keys=True, indent=1, ensure_ascii=False`（git の差分を安定させる）。

## モジュールと公開 API

依存の向きは一方通行: `errors` ← `expr` ← `schema` ← `lint` / `store` ← `validate` ← `engine` ← `query` / `evals` / `govern` ← `cli`。`export` は `schema` と objects.json の生の dict だけを見る。

### expr.py — 式

```python
compile_expr(src: str, allowed_names: set[str] | None = None) -> Expr   # 構文と許可リストを検査。allowed_names があれば自由変数がその中に収まるかも見る
class Expr: src: str; names: set[str]; def eval(self, env: Mapping[str, Any]) -> Any
render(template: str, env: Mapping[str, Any]) -> str                   # "{sizing.title}・{sizing.nodes} 台" を埋める
BUILTINS: dict[str, Callable]
```

- Python の式の部分集合。`ast.parse(src, mode="eval")` の結果を**許可リスト**で検査してから、自前の評価器で木をたどる（`eval` / `compile` は使わない）。
- 許すノード: `BoolOp`（and / or）、`UnaryOp`（not・単項 −）、`BinOp`（+ − * / // %）、`Compare`（== != < <= > >= in not in is is not）、`IfExp`、`Name`、`Attribute`、`Constant`（str / int / float / bool / None）、`List`、`Tuple`、`Call`（関数は `BUILTINS` の名前だけ。キーワード引数と `*` は不可）、`GeneratorExp`・`ListComp`（for の対象は名前 1 つ。`async` 不可）。それ以外は `ExprError`。
- `_` で始まる名前と属性は構文検査の時点で拒否する。
- 属性 `a.b` の意味: a が実体の顔（`onto_get` を持つもの）なら `a.onto_get("b")`。a がリストなら各要素に適用して 1 段平らにする（`est.priced_by.unit_price_yen` は単価のリスト）。a が `None` なら `None`。a が Mapping（`actor`）ならキー引き。それ以外は `ExprError`。`onto_get` の `KeyError` は「〈型〉に 〈名前〉 は無い」の `ExprError` にする。
- `None` との大小比較（`<` `<=` `>` `>=`）は例外にせず `False`（閉世界: 値が無ければ条件は満たされない）。
- `BUILTINS`: `len` `count`（= len）`sum` `min` `max` `any` `all` `none`（空か全部偽）`exists`（None でも空でもない）`abs` `round` `int` `float` `str` `today()` `days_since(d)` `days_between(a, b)`。`today()` は `env["__today__"]` があればそれ（テストと評価を決定的にする）、無ければ今日。`days_since(None)` は `None`。
- `env` は Mapping なら何でもよい（照会では、名前を実体の `onto_get` に流す Mapping を渡す）。
- 裸の名前は 内包表記の束縛 → `env` の順に引く。`BUILTINS` の名前は**呼び出しの位置でだけ**関数になる（引数やプロパティが `count` や `max` という名前でも、裸で書けばその値）。
- `*` は数どうしだけ（`'x' * 10**9` のような列の掛け算は `ExprError`）。式は 2,000 字まで。`none(x)` と `count(x)` は、x が `None`（それぞれ真・0）や 1 件のリンク（リストでない実体）でも使える。`days_between` はどちらかが `None` なら `None`。

### schema.py — 定義の読み込みとメタモデル検査

```python
load_schema(dir: Path, common_dir: Path | None = None) -> Schema        # dir/ontology.json。無ければ OntoError
parse_schema(doc: dict, common: Schema | None = None, source: str = "") -> Schema   # 誤りは SchemaError(problems) に全部集める
merge_patch(doc: dict, patch: dict) -> dict      # キー単位の再帰マージ。値が {"$delete": true} ならそのキーを消す。元の doc は変えない
schema_hash(doc: dict) -> str                    # 正準 JSON（sort_keys, separators=(",",":")）の sha256 の先頭 12 桁
```

`Schema`（dataclass。属性）: `doc` `name` `version` `hash` `scope`（"common" / "project"）`common` `governance` `prefixes` `constants` `object_types: dict[str, ObjectType]` `link_types: dict[str, LinkType]` `action_types: dict[str, ActionType]`。共通の定義も同じ dict に入れ、各要素の `origin`（"common" / "project"）で区別する。

メソッド: `is_a(type, ancestor) -> bool` / `subtypes(type) -> list[str]`（自分を含む）/ `props(type) -> dict[str, Prop]`（継承込み）/ `links_from(type) -> dict[str, LinkType]`（その型と上位の型が from のリンク）/ `links_to(type) -> dict[str, LinkType]`（**逆向きの名前** → LinkType。その型と上位の型が to のリンクのうち inverse を持つものだけ）/ `concrete(type) -> bool`。

dataclass: `ObjectType(name, label, aliases, description, same_as, extends, abstract, properties, summary, label_property, alias_property, origin)`、`Prop(name, type, values, required, many, min, max, pattern, unique, default, label, description, agent_visible)`、`LinkType(name, label, from_type, to_type, min, max, inverse, inverse_label, inverse_min, inverse_max, description, origin)`、`ActionType(name, label, description, parameters, criteria, rules, approval, returns, next, origin)`、`Param(name, type, values, object_type, required, many, label, min, max, pattern)`、`Criterion(when: Expr, message: str)`、`Approval(mode: "auto"|"stage"|"stage_if", when: Expr | None, role: str | None)`。ルールは検査済みの dict のまま持ち、式の文字列は `Expr` に置き換える。

メタモデル検査で落とすもの: 名前の規則・予約語、参照先（extends・from・to・object_type・ルールの型／プロパティ／リンク・`returns`）の不在、extends の循環、1 つの型の上でのプロパティ名・リンク名・逆向きの名前の衝突、enum に values が無い、min > max、引数に `type` と `object_type` の両方または両方無い、式の構文と許可外の名前（使える名前は 引数・`as` の名前（そのルールより前で作ったもの）・定数・`actor`・`BUILTINS`）、共通と同じ名前の再定義、知らないキー（打ち間違いを黙って通さない）。

### lint.py — アンチパターンの検収

見るのは自分の範囲（origin）の定義だけ。level はいまは全部 warn（止めるのは schema.py の SchemaError。lint は人の承認の材料）。

```python
lint(schema: Schema, objects: dict | None = None) -> list[Finding]     # Finding(level: "error"|"warn", code, where, message)
```

| code | 見るもの | level |
|---|---|---|
| `MISNOMER` | プロパティ・リンク名が逆向きの名前が汎用語（`date` `data` `info` `value` `item` `misc` `related` `link` `flag` `text` `name2` `tmp`）。リンクに label が無い | warn |
| `SET_ACTION` | 名前が `Set`/`Update` で始まり、ルールが 1 プロパティの変更だけ | warn |
| `ACTION_SPRAWL` | 1 つの型を対象（引数の object_type）にするアクションが 10 を超える | warn |
| `KITCHEN_SINK` | 技術列らしい名前（`etl_` `ingested_` `row_` で始まる、`_hash` `_ts` `_job_id` で終わる、`job_id`）。1 つの型に自前のプロパティが 20 超 | warn |
| `GOD_OBJECT` | objects があるとき: 実体 10 件以上の型で、埋まっている率が 30% 未満のプロパティが 5 つ以上 | warn |
| `TIME_MACHINE` | 型名が `V<数字>` `Old` `Bak` `Copy` `Backup` で終わる | warn |
| `SILO_NAME` | 別の型と label か aliases が重なる | warn |
| `THIN_DESCRIPTION` | アクションの description が無いか 20 字未満（エージェントは説明文で道具を選ぶ） | warn |

### store.py — 実体の保管

```python
class Store:
    def __init__(self, dir: Path, schema: Schema, common: "Store | None" = None)   # 無い objects.json は空として扱う
    def get(self, ref: str) -> ObjView | None            # "Type:id"。自分に無ければ common
    def find(self, type_name: str, id: str) -> ObjView | None    # 型の下位も探す（引数 order=o1 の解決に使う）。2 つ以上当たれば StoreError
    def all(self, type_name: str, include_subtypes: bool = True) -> list[ObjView]   # 共通の store の実体も含める（自分の分が先）
    def put(self, type_name, id, props: dict, links: dict[str, list[str]]) -> None   # メモリ上だけ
    def remove(self, ref: str) -> None
    def next_seq(self, type_name: str) -> int            # _meta.seq を進めて返す
    def snapshot(self) -> "Store"                        # 深い写し（取り消し・評価用）。common は共有でよい
    def to_doc(self) -> dict
    def commit(self) -> str                              # locked() の中で tmp に書いて os.replace。新しい file_hash を返す
    def file_hash(self) -> str                           # objects.json のバイト列の sha256 の先頭 16 桁。無ければ ""
class ObjView:                                           # 読み取り専用の顔
    ref: str; type: str; id: str
    def onto_get(self, name: str) -> Any                 # "id"・"type"・プロパティ（未設定は default か None。date は date に直す）・リンク（max == 1 なら ObjView | None、それ以外はリスト）・逆向きの名前（inverse_max == 1 なら単体）。知らない名前は KeyError
    def to_dict(self, select: list[str] | None = None, agent: bool = False) -> dict   # agent=True なら agent_visible: false を落とす
locked(dir: Path, timeout: float = 5.0, stale: float = 60.0)   # contextmanager。dir/.lock を os.mkdir で取り、取れなければ StoreError
```

### validate.py — 制約の検査（SHACL Core の部分集合、閉世界）

```python
validate(store: Store, refs: Iterable[str] | None = None) -> list[Violation]   # Violation(ref, path, code, message)
```

refs があれば、その実体と、リンクでつながる実体（逆向きの件数を見るため）だけを見る。code は SHACL の部品に合わせる:
`CLOSED`（定義に無いプロパティ・リンク）`DATATYPE` `MIN_COUNT`（required・リンクの min・inverse_min）`MAX_COUNT` `IN`（enum）`MIN_INCLUSIVE` `MAX_INCLUSIVE` `PATTERN` `CLASS`（リンク先の型が to の下位でない）`NODE`（リンク先が無い）`UNIQUE` `ABSTRACT`（abstract な型の実体）。

### engine.py — アクションの実行・実行待ち・記録

```python
@dataclass
class Actor: kind: str          # "agent" | "human"
             name: str; session: str | None = None
@dataclass
class Result: status: str       # "committed" | "staged" | "rejected"
              action: str; params: dict; messages: list[str]; violations: list; edits: list[dict]
              proposal_id: str | None; returned: str | None; next: str
act(store, action: str, raw_params: dict[str, str], actor: Actor, *, why: str = "", dry_run: bool = False,
    today: date | None = None, task: str | None = None, refs: list[str] | None = None) -> Result
approve(store, proposal_id: str, approver: Actor, *, today: date | None = None) -> Result   # approver.kind != "human" は OntoError
reject(store, proposal_id: str, approver: Actor, reason: str) -> None
proposals(store, status: str = "open") -> list[dict]
read_log(dir: Path, **filters) -> list[dict]
verify_chain(store) -> list[str]        # 最後の記録の store_hash_after と objects.json の今のハッシュが違えば 1 行返す
adopt(store, actor: Actor, note: str) -> None   # 人が手で直した実体を記録に取り込む（kind: adopt）。人だけ
```

`act` の順序: ① 引数を型で直す（`object_type` の引数は `store.find`。`many` はカンマ区切り。必須の欠落・型の不一致・`min`/`max`/`values`/`pattern` の違反・存在しない実体・知らない引数は拒否）② 前提条件を全部評価し、満たさないものの message を全部集める（1 つでもあれば rejected）③ `store.snapshot()` にルールを順に適用 ④ 触った実体を `validate`（違反があれば rejected。元の store は変えない）⑤ 承認の要否（`stage` か、`stage_if` の式が真。式は `as` の名前も使えるので、計算した総額で判定できる）⑥ 要らなければ `commit` して記録。要るなら `proposals/P-NNNN.json` を書いて記録（実体は変えない）。`dry_run` は何も書かない。

`approve` は積んだ時点の結果を信用せず、今の store で ①〜④ をやり直してから ⑥（拒否になったら proposal は open のまま、Result は rejected）。

記録 1 行: `ts` `kind`（act / approve / reject / schema / adopt）`action` `actor{kind,name,session}` `params` `status` `messages` `edits[{op: create|modify|delete, ref, before, after}]` `proposal` `why` `task` `refs` `schema{name,version,hash}` `store_hash_before` `store_hash_after`。拒否も残す。

### query.py — 照会

```python
query(store, type_name: str, where: str | None = None, select: list[str] | None = None, limit: int = 20, agent: bool = False) -> tuple[list[dict], int]   # 行と、絞り込み後の全件数
show(store, ref: str, agent: bool = False) -> dict      # 値・出るリンク・入るリンク（1 つ先は ref と summary の列）・関係する open の proposal
format_rows(rows: list[dict], max_chars: int = 2000) -> str   # 1 行 1 件の詰めた表。超えたら「… 他 N 件（--where で絞る）」
```

`where` の中の裸の名前は、その実体のプロパティ・リンク・逆向きの名前（`status == 'active' and nodes >= 10`、`any('IdP' in w.name for w in leads)`）。定数も使える。`select` は `prop` か `link.prop`。省略時は `id` と型の `summary`。

### evals.py — 答えたい質問

```python
run_questions(store, doc: dict, actor: Actor) -> list[QResult]   # QResult(id, ok: bool, detail: str)
```

必ず `store.snapshot()` の上で、記録もメモリ上に取って走らせる（本物を変えない）。`doc["today"]` を `today` に使う。`kind`: `query`（`expect.ids` と順不同で一致）/ `action`（`given` の手順を先に流してから本体。`expect.status`、あれば `expect.messages` と完全一致、あれば `expect.returned` の各キーが返った実体の値と一致）/ `log`（`given` を流したあとの記録の `actions` と `statuses`）。

### export.py — 書き出し

```python
to_jsonschema(schema: Schema) -> dict          # {"actions": {name: {"name", "description", "input_schema"}}, "objects": {type: <JSON Schema>}}
to_turtle(schema: Schema, objects: dict | None = None, base: str | None = None) -> str   # RDFS/OWL の語彙 + SHACL の形 + 実体のトリプル
to_mermaid(schema: Schema) -> str              # erDiagram
to_markdown(schema: Schema, objects: dict | None = None) -> str    # index.md の本文（型の表・Mermaid・アクションの前提条件と承認）
```

Turtle の決め: 既定の base は `https://example.com/onto/<名前>#`（接頭辞 `ex:`）。型は `owl:Class`（`rdfs:label`・`rdfs:subClassOf`・same_as は `rdfs:seeAlso`）。プロパティは `ex:<prop>` の `owl:DatatypeProperty`、リンクは `ex:<link>` の `owl:ObjectProperty`（inverse があれば `owl:inverseOf ex:<inverse>`）。**両端は `rdfs:domain` / `rdfs:range` では書かず、`schema:domainIncludes` / `schema:rangeIncludes`（推論を起こさない注釈）で書く。** `rdfs:range` は制約ではなく推論規則なので、RDFS 推論つきで検査すると型違いのリンク先に型が付いてしまい、`sh:class` が効かなくなる（pySHACL で実測）。制約は SHACL だけに持たせ、RDFS 推論は `rdfs:subClassOf` による型の包含にだけ使う。形は型ごとに `ex:<Type>Shape a sh:NodeShape; sh:targetClass ex:<Type>; sh:closed true; sh:ignoredProperties (rdf:type …)`（`sh:targetClass` は下位の型の実体にも当たるので、上位の型の形の ignoredProperties には、下位の型だけが持つプロパティとリンクを足す。制約そのものは下位の型の形が受け持つ）、継承込みのプロパティとリンクを `sh:property` に並べ、`sh:datatype`（string/text→xsd:string、int→xsd:integer、number→xsd:decimal、bool→xsd:boolean、date→xsd:date、datetime→xsd:dateTime）・`sh:in`・`sh:minCount`/`sh:maxCount`・`sh:minInclusive`/`sh:maxInclusive`・`sh:pattern`・`sh:class`、逆向きの件数は `sh:path [ sh:inversePath ex:<link> ]`。実体は `<base の # を / に替えたもの><Type>/<id>`。`unique` は SHACL Core に無いので書き出さない。

### govern.py — 定義の変更

```python
propose(store, patch: dict, actor: Actor, *, why: str = "") -> GovResult      # GovResult(status: "committed"|"staged"|"rejected", messages, findings, proposal_id, version)
approve_schema(onto_dir: Path, common_dir: Path | None, proposal_id: str, approver: Actor) -> GovResult
```

`propose`: `merge_patch` → `parse_schema`（SchemaError なら rejected で problems を全部返す）→ `lint`（error があれば rejected。warn は findings に入れて人に見せる）→ 今の実体を新しい定義で `validate`（違反があれば rejected で一覧）→ governance が stage で actor が人でなければ `proposals/S-NNNN.json`（`{"id", "kind": "schema", "status": "open", "patch", "summary": [差分の要約の行], "findings": [...], "actor", "why", "created"}`）を書いて staged。auto か、actor が人なら反映。`patch` に `governance` が含まれるときは常に stage（人の承認が要る）。
反映: `version` を 1 上げて `ontology.json` を原子的に置き換え（`sort_keys` はしない。キーの順は元のまま、`indent=2, ensure_ascii=False`）、`index.md` を作り直し（`export.to_markdown` に frontmatter `title` / `summary` を付ける。summary は「オントロジー: 型 N・つながり N・できること N（名前の列挙）。読むのは scripts/ws onto query / show、変えるのは scripts/ws onto act だけ」の 1 行で 200 字以内）、記録に `kind: schema`（`edits` の代わりに `patch` と新旧の `schema.hash`）。`questions` キーを持つ patch は `questions.json` にマージする。
`approve_schema` は、積んだあとに定義が変わっていても通るよう、**今の** ontology.json に patch を当て直して検査からやり直す。

### cli.py — `scripts/ws onto …` の入口

`scripts/ws` は `onto` の後ろの引数を丸ごと渡すだけ（ws の起動時に wsonto を import しない）。

```python
@dataclass
class Ctx:
    root: Path                       # リポジトリのルート
    current_project: str | None      # 現在のタスクの案件名
    current_task: str | None         # 現在のタスクの相対パス（記録の task に入れる）
    session: str | None              # エージェントのセッション ID（環境変数）。あればエージェント
    is_tty: bool                     # 標準入力が端末か
    user: str                        # 人の名前（環境変数 WS_USER。無ければ "human"）
main(argv: list[str], ctx: Ctx) -> int                  # 終了コード。0 反映・照会の成功 / 3 実行待ち / 4 拒否 / 1 その他の誤り
handle_prompt(prompt: str, ctx: Ctx) -> str | None      # UserPromptSubmit から。承認・却下の文面なら実行して結果の文（1〜3 行）。違えば None
doctor_problems(ctx: Ctx) -> list[str]                  # 全範囲の 制約違反・lint の warn・7 日を超えた実行待ち・評価の失敗・ハッシュの不一致
alias_pairs(ctx: Ctx, project: str | None) -> dict[str, str]   # transcript normalize 用 {別名: 正式表記}。共通 → 案件の順で案件が勝つ。2 字未満は捨てる
pending_count(root: Path) -> int                        # ステータスライン用。proposals/*.json の status open を数えるだけ（定義を読まない）
```

範囲の決め方: `--common` なら共通、`--project <案件>` ならその案件、どちらも無ければ 現在のタスクの案件（オントロジーがあれば）→ 共通。置き場は `root/knowledges/ontology` と `root/projects/<案件>/knowledges/ontology`。
誰が実行したか: `ctx.session` があればエージェント（`Actor("agent", "claude-code" か "codex", session)`）。無くて `is_tty` なら人。どちらでもなければ `Actor("agent", "script")`。**approve / reject / adopt は 人（session 無し かつ TTY）でなければ拒否**し、`handle_prompt` 経由（人の発言）は人として扱う。

| コマンド | 中身 |
|---|---|
| `init [--common\|--project X]` | 空の定義（governance: stage）と index.md を作る。既にあれば何もしない |
| `types` | 型（label・件数）とアクション（label・description の 1 文目・承認）の一覧。1 行 1 件 |
| `describe <型かアクション>` | 型: プロパティ・出るリンク・入るリンク。アクション: 引数・前提条件（式と message）・承認・next |
| `query <型> [--where 式] [--select a,b] [--limit N] [--count] [--json] [--max-chars N]` | `query.query` → `format_rows`。エージェントなら agent=True |
| `show <型:id か id> [--type 型] [--json]` | `query.show` → `format_show` |
| `act <アクション> [名前=値 …] [--why 文] [--ref path …] [--dry-run] [--json]` | `engine.act`。1 行目に `反映` / `実行待ち P-0001（承認は人。「承認 P-0001」と送る）` / `拒否`、続けて理由文、返った実体の要約、`次:` の案内 |
| `define apply <patch.json> [--why 文]` | `govern.propose` |
| `approve <[範囲/]P-… か S-…>` / `reject <id> --reason 文` | 人だけ。P は `engine.approve`、S は `govern.approve_schema` |
| `proposals [--all]` | 実行待ちの一覧（id・アクションと引数の要約・誰が・いつ・役割） |
| `validate` / `lint` / `eval` | 全件の制約検査 / 検収 / questions.json の評価。問題があれば終了コード 1 |
| `export --format jsonschema\|turtle\|mermaid\|markdown [--out path]` | 書き出し。turtle は共通の定義と実体も含める |
| `log [--object 型:id] [--action 名前] [--limit N]` | 記録の照会（古い順。1 行 1 件に詰める） |
| `adopt --note 文` | 人だけ。手で直した実体を記録に取り込む |

`handle_prompt` の文面: `^\s*(承認|却下|approve|reject)\s+((?:[\w-]+/)?[PS]-\d{4})(?:\s+(.+))?$`。範囲の省略時は 現在のタスクの案件 → 共通 → 全案件 の順に open のものを探し、2 つ以上当たれば `承認 <案件か common>/P-0001` の形で選び直させる文を返す。却下の後ろの文は理由。

### scripts/ws への組み込み（hook・doctor・normalize・ステータスライン）

- `onto` サブコマンド: 後ろの引数を `cli.main` に渡す（`argparse.REMAINDER`）。
- PreToolUse（**現在のタスクの有無に関係なく**。`"scripts/ws" in blob` の素通しより**前**に置く）:
  1. ツール入力のどこかに `knowledges/ontology/` の `objects.json`・`log.jsonl`・`proposals/`・`.lock` が出てきたら拒否（読みも書きも）。理由文で `scripts/ws onto query / show / log / act` に誘導する。
  2. Edit / Write / MultiEdit / NotebookEdit の対象が `knowledges/ontology/` の下（`ontology.json`・`index.md`・`questions.json` を含む全部）なら拒否し、`scripts/ws onto define apply <patch.json>` に誘導する。Read は通す。Codex CLI のファイル編集は `tool_name` が `apply_patch` で、対象はパッチ本文（`tool_input.command`）の `*** Update File: <path>` / `*** Add File:` / `*** Delete File:` / `*** Move to:` の行に入る（0.153.4 の実機で記録）。これも同じ扱いで拒否する。
  3. Bash / PowerShell / shell のコマンドが `onto\s+(approve|reject|adopt)` を含む、または `claude` / `codex` の起動と `(承認|却下|approve|reject)\s+\S*[PS]-\d{4}` を同時に含むなら拒否（承認は人だけ）。
  4. Bash / PowerShell / shell のコマンドが `knowledges/ontology/` に触れていて `scripts/ws onto` の呼び出しでないとき、読むだけの語（`cat` `head` `tail` `less` `wc` `ls` `grep` `rg` `jq` `git diff` `git log` `git status`）で始まり `>` `tee` `-i` を含まないものだけ通す。
  5. パスを書かずに実体へ触れる形も止める: コマンドの中の `cd` / `pushd` の行き先が `knowledges/ontology` なら拒否。hook の入力の `cwd` がオントロジーのディレクトリの中なら、`cd` で出る以外の全ツールを拒否（Bash の `cd` はセッションに残り、次のコマンドや Grep にはパスが現れないため）。コマンドが `knowledges/ontology` に触れていて `objects.json`・`log.jsonl`・`proposals`・`.lock` の名前がどこかに出てきたら拒否。
  - 環境変数 `WS_ONTO_MAINT=1` が **hook のプロセス**にあれば 1・2・4 を止めない（agent-ws 自体の保守用。エージェントの Bash からは hook のプロセスの環境を変えられない）。3 は常に効く。
- UserPromptSubmit: キャッシュの判定より前に、文面が承認・却下の形なら `cli.handle_prompt` を呼び、結果を `additionalContext` の JSON で返して**その発言は通す**（エージェントが結果を見て続けられるように）。
- `doctor`: `cli.doctor_problems` の行を足す。`transcript normalize`: `cli.alias_pairs` を用語集の対に合流（用語集が勝つ）。どちらも、オントロジーのディレクトリが 1 つも無ければ wsonto を import しない。
- ステータスライン: `knowledges/ontology/proposals` か `projects/*/knowledges/ontology/proposals` に open があれば `承認待ち N` を足す。

## テスト

- `python3 -m unittest discover -s tests`（標準ライブラリだけで全部通ること。rdflib が無ければ W3C の突き合わせは skip）。
- `tests/fixtures/onto_case/` は適合の基準なので、テストを通すために書き換えない。形式を変える必要が出たら、まず取り決め（この文書）を直す。
- 実体を変えるテストは一時ディレクトリに fixture を写してから行う。
