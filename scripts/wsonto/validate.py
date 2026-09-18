"""wsonto — 制約の検査（SHACL Core の部分集合、閉世界）。

取り決めは `scripts/wsonto/README.md` の「validate.py」を参照。実行時は標準
ライブラリだけで動く（Python 3.9 以上）。
"""
from __future__ import annotations

import datetime
import re
from dataclasses import dataclass
from typing import Any, Iterable, Optional

_MISSING = object()


@dataclass
class Violation:
    ref: str
    path: str
    code: str
    message: str


def validate(store, refs: "Optional[Iterable[str]]" = None) -> "list[Violation]":
    store._ensure_rev_index()
    violations: "list[Violation]" = []

    if refs is None:
        targets = []
        for type_name, entities in store.doc.items():
            if type_name == "_meta" or not isinstance(entities, dict):
                continue
            for id_ in entities:
                targets.append((type_name, id_))
    else:
        closure = _closure(store, refs)
        targets = []
        for ref in sorted(closure):
            type_name, _, id_ = ref.partition(":")
            entities = store.doc.get(type_name)
            if entities and id_ in entities:
                targets.append((type_name, id_))

    for type_name, id_ in targets:
        rec = store.doc[type_name][id_]
        _validate_one(store, type_name, id_, rec, violations)
    return violations


def _closure(store, refs: "Iterable[str]") -> set:
    result: set = set()
    for ref in refs:
        result.add(ref)
        type_name, _, id_ = ref.partition(":")
        rec = store.doc.get(type_name, {}).get(id_)
        if rec is None:
            continue
        for _link_name, tos in (rec.get("_links") or {}).items():
            result.update(tos)
        inbound = store._rev_index.get(ref, {})
        for _link_name, froms in inbound.items():
            result.update(froms)
    return result


def _validate_one(store, type_name: str, id_: str, rec: dict, violations: "list") -> None:
    ref = f"{type_name}:{id_}"
    ot = store.schema.object_types.get(type_name)
    if ot is None:
        violations.append(Violation(ref, "$", "CLOSED", f"未定義の型 '{type_name}' の実体がある"))
        return
    if ot.abstract:
        violations.append(Violation(ref, "$", "ABSTRACT", f"抽象型 '{type_name}' の実体は作れない"))

    props = store.schema.props(type_name)
    links_from = store.schema.links_from(type_name)
    links_to = store.schema.links_to(type_name)
    rec_links = rec.get("_links") or {}

    for key in rec:
        if key == "_links":
            continue
        if key not in props:
            violations.append(Violation(ref, key, "CLOSED", f"定義に無いプロパティ '{key}' がある"))

    for link_name in rec_links:
        if link_name not in links_from:
            violations.append(
                Violation(ref, link_name, "CLOSED", f"'{type_name}' から出ないリンク '{link_name}' がある")
            )

    for pname, prop in props.items():
        _validate_prop(ref, pname, prop, rec, violations)

    for link_name, lt in links_from.items():
        _validate_forward_link(store, ref, link_name, lt, rec_links.get(link_name, []), violations)

    for inverse_name, lt in links_to.items():
        _validate_inverse_link(store, ref, inverse_name, lt, violations)

    _validate_unique(store, ref, type_name, rec, props, violations)


def _validate_prop(ref: str, pname: str, prop, rec: dict, violations: "list") -> None:
    present = pname in rec
    if not present:
        if prop.required and prop.default is None:
            violations.append(Violation(ref, pname, "MIN_COUNT", f"必須のプロパティ '{pname}' が無い"))
        return
    raw = rec[pname]
    if prop.many:
        if not isinstance(raw, list):
            violations.append(
                Violation(ref, pname, "DATATYPE", f"'{pname}' は many なのでリストである必要がある")
            )
            return
        for v in raw:
            _validate_scalar(ref, pname, prop, v, violations)
    else:
        if isinstance(raw, list):
            violations.append(Violation(ref, pname, "MAX_COUNT", f"'{pname}' は複数の値を持てない"))
            return
        _validate_scalar(ref, pname, prop, raw, violations)


def _validate_scalar(ref: str, pname: str, prop, value: Any, violations: "list") -> None:
    if not _check_datatype(prop.type, value):
        violations.append(
            Violation(ref, pname, "DATATYPE", f"'{pname}' の値の型が {prop.type} に合わない（{value!r}）")
        )
        return
    if prop.type == "enum" and value not in (prop.values or []):
        violations.append(Violation(ref, pname, "IN", f"'{pname}' の値 {value!r} は許された値にない"))
    if prop.min is not None:
        try:
            under = value < prop.min
        except TypeError:
            under = False
        if under:
            violations.append(
                Violation(ref, pname, "MIN_INCLUSIVE", f"'{pname}' は {prop.min} 以上である必要がある（今 {value!r}）")
            )
    if prop.max is not None:
        try:
            over = value > prop.max
        except TypeError:
            over = False
        if over:
            violations.append(
                Violation(ref, pname, "MAX_INCLUSIVE", f"'{pname}' は {prop.max} 以下である必要がある（今 {value!r}）")
            )
    if prop.pattern is not None and isinstance(value, str):
        if re.search(prop.pattern, value) is None:
            violations.append(
                Violation(ref, pname, "PATTERN", f"'{pname}' の値がパターン '{prop.pattern}' に合わない")
            )


def _check_datatype(ptype: "Optional[str]", value: Any) -> bool:
    if ptype in ("string", "text"):
        return isinstance(value, str)
    if ptype == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    if ptype == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if ptype == "bool":
        return isinstance(value, bool)
    if ptype == "date":
        if not isinstance(value, str):
            return False
        try:
            datetime.date.fromisoformat(value)
            return True
        except ValueError:
            return False
    if ptype == "datetime":
        if not isinstance(value, str):
            return False
        s = value[:-1] + "+00:00" if value.endswith("Z") else value
        try:
            datetime.datetime.fromisoformat(s)
            return True
        except ValueError:
            return False
    if ptype == "enum":
        return isinstance(value, str)
    return True


def _validate_forward_link(store, ref: str, link_name: str, lt, refs_list: list, violations: "list") -> None:
    if len(refs_list) < lt.min:
        violations.append(
            Violation(ref, link_name, "MIN_COUNT", f"リンク '{link_name}' が {lt.min} 件必要（今 {len(refs_list)} 件）")
        )
    if lt.max is not None and len(refs_list) > lt.max:
        violations.append(
            Violation(ref, link_name, "MAX_COUNT", f"リンク '{link_name}' は最大 {lt.max} 件（今 {len(refs_list)} 件）")
        )
    for to_ref in refs_list:
        target = store.get(to_ref)
        if target is None:
            violations.append(
                Violation(ref, link_name, "NODE", f"リンク '{link_name}' の先 '{to_ref}' が見つからない")
            )
            continue
        if not store.schema.is_a(target.type, lt.to_type):
            violations.append(
                Violation(
                    ref, link_name, "CLASS",
                    f"リンク '{link_name}' の先 '{to_ref}' の型が '{lt.to_type}' の下位でない",
                )
            )


def _validate_inverse_link(store, ref: str, inverse_name: str, lt, violations: "list") -> None:
    count = len(store._rev_index.get(ref, {}).get(lt.name, []))
    if count < lt.inverse_min:
        violations.append(
            Violation(ref, inverse_name, "MIN_COUNT", f"'{inverse_name}' が {lt.inverse_min} 件必要（今 {count} 件）")
        )
    if lt.inverse_max is not None and count > lt.inverse_max:
        violations.append(
            Violation(ref, inverse_name, "MAX_COUNT", f"'{inverse_name}' は最大 {lt.inverse_max} 件（今 {count} 件）")
        )


def _validate_unique(store, ref: str, type_name: str, rec: dict, props: dict, violations: "list") -> None:
    for pname, prop in props.items():
        if not prop.unique or pname not in rec:
            continue
        value = rec[pname]
        if isinstance(value, list):
            continue
        dup = None
        for other_type in store.schema.subtypes(type_name):
            entities = store.doc.get(other_type)
            if not entities:
                continue
            for other_id, other_rec in entities.items():
                other_ref = f"{other_type}:{other_id}"
                if other_ref == ref:
                    continue
                if other_rec.get(pname, _MISSING) == value:
                    dup = other_ref
                    break
            if dup:
                break
        if dup:
            violations.append(
                Violation(ref, pname, "UNIQUE", f"'{pname}' の値 {value!r} が重複している（{dup}）")
            )
