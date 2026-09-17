"""wsonto — 定義のアンチパターンの検収（lint）。

取り決めは `scripts/wsonto/README.md` の「lint.py」を参照。ここは実行時は
標準ライブラリだけで動く（Python 3.9 以上）。`schema.py` が SchemaError で
落とすもの（共通と同名の型など）はここでは見ない。ここが見るのは、構文的には
正しいが業務上のアンチパターンに落ちている定義（Palantir の 8 つのアンチ
パターンのうち機械で見られるもの）。

見るのは origin が自分の範囲のもの: `schema.scope == "project"` なら
origin == "project" の型・リンク型・アクション型だけ、"common" なら全部
（common の schema では全要素の origin が "common" なので結果は同じ）。
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from .schema import ObjectType, Schema

GENERIC_WORDS = {
    "date", "data", "info", "value", "item", "misc",
    "related", "link", "flag", "text", "name2", "tmp",
}
TECH_PREFIXES = ("etl_", "ingested_", "row_")
TECH_SUFFIXES = ("_hash", "_ts", "_job_id")
TIME_MACHINE_RE = re.compile(r"(V\d+|Old|Bak|Copy|Backup)$")
MAX_ACTIONS_PER_TYPE = 10
MAX_OWN_PROPERTIES = 20
MIN_INSTANCES_FOR_GOD_OBJECT = 10
MIN_SPARSE_PROPERTIES_FOR_GOD_OBJECT = 5
SPARSE_FILL_RATE = 0.3
MIN_DESCRIPTION_LEN = 20

MISNOMER = "MISNOMER"
SET_ACTION = "SET_ACTION"
ACTION_SPRAWL = "ACTION_SPRAWL"
KITCHEN_SINK = "KITCHEN_SINK"
GOD_OBJECT = "GOD_OBJECT"
TIME_MACHINE = "TIME_MACHINE"
SILO_NAME = "SILO_NAME"
THIN_DESCRIPTION = "THIN_DESCRIPTION"


@dataclass
class Finding:
    level: str  # "error" | "warn"（今は全部 warn。止めるのは schema.py の仕事）
    code: str
    where: str
    message: str


def _own(items: dict, scope: str) -> dict:
    if scope == "project":
        return {name: item for name, item in items.items() if item.origin == "project"}
    return dict(items)


def lint(schema: Schema, objects: Optional[dict] = None) -> list[Finding]:
    findings: list[Finding] = []
    own_types = _own(schema.object_types, schema.scope)
    own_links = _own(schema.link_types, schema.scope)
    own_actions = _own(schema.action_types, schema.scope)

    _lint_misnomer(own_types, own_links, findings)
    _lint_set_action(own_actions, findings)
    _lint_action_sprawl(own_actions, findings)
    _lint_kitchen_sink(own_types, findings)
    _lint_time_machine(own_types, findings)
    _lint_silo_name(own_types, schema, findings)
    _lint_thin_description(own_actions, findings)
    if objects:
        _lint_god_object(own_types, schema, objects, findings)

    findings.sort(key=lambda f: f.where)
    return findings


def _lint_misnomer(own_types: dict, own_links: dict, findings: list) -> None:
    for tname, ot in own_types.items():
        for pname in ot.properties:
            if pname in GENERIC_WORDS:
                findings.append(Finding(
                    "warn", MISNOMER, f"object_types.{tname}.properties.{pname}",
                    f"プロパティ名 '{pname}' が汎用語で中身が分からない。"
                    f"何の{pname}か分かる名前に（例: delivered_on）",
                ))
    for lname, lt in own_links.items():
        if lname in GENERIC_WORDS:
            findings.append(Finding(
                "warn", MISNOMER, f"link_types.{lname}",
                f"リンク名 '{lname}' が汎用語で中身が分からない。"
                "何を指すリンクか分かる名前に（例: assigned_to）",
            ))
        if lt.inverse and lt.inverse in GENERIC_WORDS:
            findings.append(Finding(
                "warn", MISNOMER, f"link_types.{lname}.inverse",
                f"逆向きの名前 '{lt.inverse}' が汎用語で中身が分からない。"
                "何を指すか分かる名前に",
            ))
        if not lt.label:
            findings.append(Finding(
                "warn", MISNOMER, f"link_types.{lname}.label",
                f"リンク '{lname}' に label が無い。人が読める日本語の名前を付ける",
            ))


def _rule_is_single_prop_modify(rule: dict) -> bool:
    if "modify" not in rule:
        return False
    if rule.get("link") or rule.get("unlink"):
        return False
    return len(rule.get("set") or {}) == 1


def _lint_set_action(own_actions: dict, findings: list) -> None:
    for aname, at in own_actions.items():
        if not (aname.startswith("Set") or aname.startswith("Update")):
            continue
        if len(at.rules) == 1 and _rule_is_single_prop_modify(at.rules[0]):
            findings.append(Finding(
                "warn", SET_ACTION, f"action_types.{aname}",
                f"'{aname}' は 1 プロパティを set するだけの操作。"
                "プロパティの上げ下げでなく業務の操作の単位でアクションをまとめる"
                "（例: SetStatus ではなく Ship / Cancel）",
            ))


def _lint_action_sprawl(own_actions: dict, findings: list) -> None:
    counts: dict = {}
    for at in own_actions.values():
        targeted = {p.object_type for p in at.parameters.values() if p.object_type}
        for t in targeted:
            counts[t] = counts.get(t, 0) + 1
    for tname, count in counts.items():
        if count > MAX_ACTIONS_PER_TYPE:
            findings.append(Finding(
                "warn", ACTION_SPRAWL, f"object_types.{tname}",
                f"'{tname}' を対象にするアクションが {count} 個ある。"
                "似たアクションを引数（enum や object_type）でまとめて数を減らす",
            ))


def _lint_kitchen_sink(own_types: dict, findings: list) -> None:
    for tname, ot in own_types.items():
        for pname in ot.properties:
            if pname == "job_id" or pname.startswith(TECH_PREFIXES) or pname.endswith(TECH_SUFFIXES):
                findings.append(Finding(
                    "warn", KITCHEN_SINK, f"object_types.{tname}.properties.{pname}",
                    f"プロパティ '{pname}' は ETL・取り込みの都合の列に見える。"
                    "業務の言葉のプロパティだけを残し、技術列は取り込み側に置く",
                ))
        if len(ot.properties) > MAX_OWN_PROPERTIES:
            findings.append(Finding(
                "warn", KITCHEN_SINK, f"object_types.{tname}",
                f"'{tname}' 自前のプロパティが {len(ot.properties)} 個ある。"
                "役割ごとに型を分けるか extends で共通部分を括り出す",
            ))


def _lint_time_machine(own_types: dict, findings: list) -> None:
    for tname in own_types:
        if TIME_MACHINE_RE.search(tname):
            findings.append(Finding(
                "warn", TIME_MACHINE, f"object_types.{tname}",
                f"型名 '{tname}' が版・退避先らしい接尾辞で終わっている。"
                "履歴が要るなら別の型やプロパティで表し、型名はバージョンで増やさない",
            ))


def _names_overlap(a: ObjectType, b: ObjectType) -> bool:
    if a.label and b.label and a.label == b.label:
        return True
    a_aliases = {x for x in a.aliases if x}
    b_aliases = {x for x in b.aliases if x}
    return bool(a_aliases & b_aliases)


def _lint_silo_name(own_types: dict, schema: Schema, findings: list) -> None:
    for tname, ot in own_types.items():
        for oname, other in schema.object_types.items():
            if oname == tname:
                continue
            if _names_overlap(ot, other):
                findings.append(Finding(
                    "warn", SILO_NAME, f"object_types.{tname}",
                    f"'{tname}' の label/aliases が '{oname}' と重なっている。"
                    "同じ実体の型が 2 つに分かれていないか確かめ、片方に寄せるか名前を分ける",
                ))
                break


def _lint_thin_description(own_actions: dict, findings: list) -> None:
    for aname, at in own_actions.items():
        desc = at.description or ""
        if len(desc) < MIN_DESCRIPTION_LEN:
            findings.append(Finding(
                "warn", THIN_DESCRIPTION, f"action_types.{aname}",
                f"'{aname}' の description が短すぎる（{len(desc)} 字）。"
                "エージェントは説明文で道具を選ぶので、いつ使うか・何をするかを書く",
            ))


def _lint_god_object(own_types: dict, schema: Schema, objects: dict, findings: list) -> None:
    for tname in own_types:
        if not schema.concrete(tname):
            continue
        instances = objects.get(tname)
        if not isinstance(instances, dict) or not instances:
            continue
        n = len(instances)
        if n < MIN_INSTANCES_FOR_GOD_OBJECT:
            continue
        sparse: list = []
        for pname, prop in schema.props(tname).items():
            if prop.required or prop.default is not None:
                continue
            filled = sum(
                1 for inst in instances.values()
                if isinstance(inst, dict) and inst.get(pname) is not None
            )
            if filled / n < SPARSE_FILL_RATE:
                sparse.append(pname)
        if len(sparse) >= MIN_SPARSE_PROPERTIES_FOR_GOD_OBJECT:
            findings.append(Finding(
                "warn", GOD_OBJECT, f"object_types.{tname}",
                f"'{tname}'（実体 {n} 件）で {', '.join(sorted(sparse))} の埋まりが 3 割未満。"
                "使われていないプロパティを削るか、別の型に分ける",
            ))
