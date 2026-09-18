---
name: ontology-define
description: 業務の型・つながり・できること（アクション）・定数を新しく定義する、または直すとき。「うちの業務の型を定義して」「この操作をエージェントにやらせたい」「新しい種類の実体を扱いたい」で使う。実体を 1 件足す・変えるだけなら、既にある型・アクションを act で呼ぶ（このスキルは使わない）。
---
# ontology-define

ゴール: 業務の型・つながり・できること（アクション）・定数が `ontology.json` に定義され、`scripts/ws onto eval` で「答えたい質問」がすべて通っている状態。

## いつ使う / 使わない

- 使う: 新しい種類の実体（型）・関係（つながり）・業務の操作（アクション）・変わりやすい定数が足りないとき。
- 使わない: 実体を 1 件足す・変えるだけなら、既にある型・アクションを `scripts/ws onto act <アクション> 名前=値 …` で呼ぶ。型を新しく作る必要は無い。

## 手順（8 段階。Stanford の Ontology Development 101 の 7 段＋公開と評価）

1. **範囲を決めて「答えたい質問」を 5 つ書く**（型より先。そのまま `questions.json` になる）。「IdP 連携の担当は誰か」のように具体的に書く。
2. **既にある型を探す**（`scripts/ws onto types`）。共通の型（`Person` など）を使い回し、専用の型が要るときだけ新規に作る。schema.org に近いものがあれば `same_as` を付ける。
3. **質問から名詞と動詞を抜く。** 名詞の候補が型、動詞の候補がアクション。
4. **型と is-a を決める。**「すべての A は B か」と言えるときだけ `extends` する（例: `Stakeholder extends Person`）。言えないならつながり（`link_types`）にする。
5. **プロパティを決める。** 現場の呼び名で書く（`nodes` であって `node_count_v2` ではない）。型（string/int/date/enum など）・必須・列挙を決める。
6. **制約とアクションを決める。** 業務の操作を単位にする（1 プロパティだけ変える `SetXxx`/`UpdateXxx` を作らず、既存のアクションに寄せる）。前提条件（`criteria`）は現実の状態で書く（「期限が切れていない」であって「エージェントが確認済み」ではない）。計算は `set` の式に書き、エージェントに計算させない。取り消せない・金額の大きい操作は `approval` を `stage` にする。日数・上限のように変わりやすい値は `constants` に出す。
7. **実体を入れる。** 直接 `objects.json` を書かず、決めたアクション経由で入れる（記録するアクションが無ければ、まず `RecordXxx` のようなアクションを作る）。
8. **`scripts/ws onto define apply <patch.json>`** を実行し、返ってきた lint の警告を読む。人に「承認 S-0001」と送ってもらう。反映されたら `scripts/ws onto eval` で 1 の質問がすべて通るか確かめる。通らなければ 4〜6 に戻る。

## patch.json の最小例

既存の型に列挙のプロパティを 1 つ足す例（宿題に優先度を足す）:

```json
{
  "object_types": {
    "ActionItem": {
      "properties": {
        "priority": {"type": "enum", "values": ["low", "normal", "high"], "default": "normal", "label": "優先度"}
      }
    }
  }
}
```

`merge_patch` はキー単位の再帰マージです。既存のキーを消すときだけ `{"$delete": true}` を使います。

## 式の書き方（Python の式の部分集合）

- 文字列の定数は引用符ごと書く: `"'active'"`。
- リンクをたどる: `sizing.superseded_by.title`（実体 → 実体 → プロパティ）。
- 複数件のリンクを畳み込む: `sum(i.unit_price_yen for i in items)`。
- 使える関数: `len` `sum` `min` `max` `any` `all` `none`（空か全部偽）`exists` `today()` `days_since(d)` `days_between(a, b)`。
- 使えないもの: `import`・代入・キーワード引数・`*` の付いた呼び出し・`async` の内包表記・`_` で始まる名前。式は 2,000 字まで。

## 検収（lint が見るもの）

| code | 直し方 |
|---|---|
| `MISNOMER` | プロパティ・リンクの名前を業務の言葉に直す（`data`/`value`/`item` のような汎用語をやめる） |
| `SET_ACTION` | 1 プロパティだけを変えるアクションをやめ、業務の操作単位のアクションにまとめる |
| `ACTION_SPRAWL` | 1 つの型へのアクションが 10 を超えたら型を分けるか、似たアクションを引数で束ねる |
| `KITCHEN_SINK` | ETL・ハッシュ・ジョブ ID のような技術列を実体に持たせない |
| `GOD_OBJECT` | 実体 10 件以上でスカスカな（埋まっている率 30% 未満の）プロパティが 5 つ以上あれば型を見直す |
| `TIME_MACHINE` | `V2`/`Old`/`Bak` のような型を作らず、`status` プロパティで表す |
| `SILO_NAME` | 他の型と label・aliases が紛らわしいなら名前を変える |
| `THIN_DESCRIPTION` | アクションの description を 20 字以上、エージェントが選べる説明にする |

## つまずきどころ

- 定義ファイル（`ontology.json`）を Edit で直接書き換えようとして hook に拒否される → patch を書いて `scripts/ws onto define apply` する。
- 共通と同じ名前の型を案件で作ろうとして `SchemaError` になる → 共通の型を `extends` する（同名の再定義はできない）。
- 全社の業務を一度にモデル化しようとして手が止まる → 1 の「答えたい質問」5 つに答えられる分だけ定義する。範囲を広げるのは、次の案件で質問が増えてから。
