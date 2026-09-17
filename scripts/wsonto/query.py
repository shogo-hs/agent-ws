"""wsonto — 照会（query / show）。

エージェントが業務の状態を読むための道具。取り決めは `scripts/wsonto/README.md` の
「query.py — 照会」を参照。実行時は標準ライブラリだけで動く（Python 3.9 以上）。
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from contextlib import contextmanager
from typing import Any, Optional

from .errors import ExprError, HiddenPropertyError, OntoError
from .expr import Expr, compile_expr
from .store import _jsonify  # noqa: SLF001 -- 同じ package 内の共有ヘルパーを再利用する

_HIDDEN = "（非表示）"


@contextmanager
def _agent_visibility(store: Any, agent: bool):
    """agent=True の間だけ、store（と繋がっている common）の非表示プロパティを隠す。"""
    stores = []
    if agent:
        stores.append(store)
        if getattr(store, "common", None) is not None:
            stores.append(store.common)
        for s in stores:
            s.hide_hidden = True
    try:
        yield
    finally:
        for s in stores:
            s.hide_hidden = False


class _MissingName(ExprError):
    """where の裸の名前が、この実体にも定数にも無いときに投げる。

    下位の型にしか無い名前を上位の型の照会で使ったとき、この実体だけ「条件に
    合わない」として飛ばすために `query` の側で捕まえる（他の ExprError とは
    区別する）。
    """


class _WhereEnv(Mapping):
    """where の裸の名前を、実体の onto_get → 定数の順で引く小さな Mapping。"""

    __slots__ = ("_obj", "_constants", "_today")

    def __init__(self, obj: Any, constants: dict, today: Any) -> None:
        self._obj = obj
        self._constants = constants
        self._today = today

    def __getitem__(self, key: str) -> Any:
        if key == "__today__":
            if self._today is None:
                raise KeyError(key)
            return self._today
        try:
            return self._obj.onto_get(key)
        except HiddenPropertyError:
            raise ExprError(f"{key} は照会に使えない（非表示のプロパティ）") from None
        except KeyError:
            pass
        if key in self._constants:
            return self._constants[key]
        raise _MissingName(f"{self._obj.type} に {key} は無い")

    def __iter__(self):
        return iter(())

    def __len__(self) -> int:
        return 0


# --- query ------------------------------------------------------------


def query(
    store: Any,
    type_name: str,
    where: Optional[str] = None,
    select: Optional[list] = None,
    limit: Optional[int] = 20,
    agent: bool = False,
    today: Any = None,
) -> "tuple[list[dict], int]":
    schema = store.schema
    if type_name not in schema.object_types:
        raise OntoError(f"知らない型 '{type_name}'")

    with _agent_visibility(store, agent):
        compiled: Optional[Expr] = compile_expr(where) if where else None

        matched: list = []
        attempted = 0
        missing_count = 0
        last_missing: Optional[_MissingName] = None
        for obj in store.all(type_name):
            if compiled is None:
                matched.append(obj)
                continue
            attempted += 1
            env = _WhereEnv(obj, schema.constants, today)
            try:
                ok = compiled.eval(env)
            except _MissingName as e:
                missing_count += 1
                last_missing = e
                continue
            if ok:
                matched.append(obj)

        if compiled is not None and attempted > 0 and missing_count == attempted:
            raise last_missing  # type: ignore[misc]

        matched.sort(key=lambda o: o.id)
        total = len(matched)
        rows_objs = matched if limit is None else matched[:limit]
        built = [_build_row(o, select) for o in rows_objs]

        if select is not None and built:
            missing_everywhere = set(built[0][1])
            for _row, missing in built[1:]:
                missing_everywhere &= missing
            if missing_everywhere:
                name = sorted(missing_everywhere)[0]
                raise OntoError(
                    f"'{type_name}' に '{name}' は無い。使える名前: "
                    f"{', '.join(_available_names(schema, type_name))}"
                )

        rows = [row for row, _missing in built]
    return rows, total


def _default_cols(schema: Any, type_name: str) -> list:
    ot = schema.object_types.get(type_name)
    return list(ot.summary) if ot is not None else []


def _available_names(schema: Any, type_name: str) -> list:
    names = ["id"]
    names += sorted(schema.props(type_name))
    names += sorted(schema.links_from(type_name))
    names += sorted(schema.links_to(type_name))
    return names


def _resolve_column(obj: Any, col: str) -> Any:
    link_name, sep, prop_name = col.partition(".")
    try:
        if sep:
            target = obj.onto_get(link_name)
            if target is None:
                value: Any = None
            elif isinstance(target, list):
                value = [t.onto_get(prop_name) for t in target]
            else:
                value = target.onto_get(prop_name)
        else:
            value = obj.onto_get(col)
    except HiddenPropertyError:
        return _HIDDEN
    return _jsonify(value)


def _build_row(obj: Any, select: Optional[list]) -> "tuple[dict, set]":
    schema = obj.store.schema
    cols = _default_cols(schema, obj.type) if select is None else [
        c for c in select if c not in ("id", "type")
    ]
    row: dict = {"id": obj.id, "type": obj.type}
    missing: set = set()
    for col in cols:
        if col in row:
            continue
        try:
            row[col] = _resolve_column(obj, col)
        except KeyError:
            row[col] = "-"
            missing.add(col)
    return row, missing


# --- show ---------------------------------------------------------------


def _label_of(obj: Any) -> Any:
    schema = obj.store.schema
    ot = schema.object_types.get(obj.type)
    if ot is None:
        return obj.id
    if ot.label_property:
        return _jsonify(obj.onto_get(ot.label_property))
    if ot.summary:
        return _jsonify(obj.onto_get(ot.summary[0]))
    return obj.id


def _link_entries(obj: Any, name: str) -> list:
    target = obj.onto_get(name)
    if target is None:
        return []
    targets = target if isinstance(target, list) else [target]
    return [{"ref": t.ref, "label": _label_of(t)} for t in targets]


def _proposals_for(store: Any, ref: str, id_: str) -> list:
    props_dir = store.dir / "proposals"
    if not props_dir.exists():
        return []
    out = []
    for path in sorted(props_dir.glob("*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(doc, dict) or doc.get("status") != "open":
            continue
        params = doc.get("params") or {}
        hit = False
        for v in params.values():
            values = v if isinstance(v, list) else [v]
            if ref in values or id_ in values:
                hit = True
                break
        if hit and doc.get("id"):
            out.append(doc["id"])
    return out


def show(
    store: Any, ref_or_id: str, type_name: Optional[str] = None, agent: bool = False
) -> dict:
    with _agent_visibility(store, agent):
        if type_name is not None:
            obj = store.find(type_name, ref_or_id)
            ref = f"{obj.type}:{obj.id}" if obj is not None else f"{type_name}:{ref_or_id}"
        else:
            ref = ref_or_id
            obj = store.get(ref_or_id)
        if obj is None:
            raise OntoError(f"'{ref}' は見つからない")

        schema = obj.store.schema
        ot = schema.object_types.get(obj.type)
        type_label = ot.label if ot is not None and ot.label else obj.type

        props: dict = {}
        for pname, prop in schema.props(obj.type).items():
            if agent and not prop.agent_visible:
                continue
            value = obj.onto_get(pname)
            if value is None:
                continue
            if isinstance(value, list) and not value:
                continue
            props[pname] = _jsonify(value)

        links: dict = {}
        for lname in schema.links_from(obj.type):
            entries = _link_entries(obj, lname)
            if entries:
                links[lname] = entries

        inverse: dict = {}
        for iname in schema.links_to(obj.type):
            entries = _link_entries(obj, iname)
            if entries:
                inverse[iname] = entries

        return {
            "ref": obj.ref,
            "type": obj.type,
            "type_label": type_label,
            "props": props,
            "links": links,
            "inverse": inverse,
            "proposals": _proposals_for(store, obj.ref, obj.id),
        }


# --- 表示（人とエージェントが読む詰めたテキスト） --------------------------


def _fmt_value(value: Any) -> str:
    if isinstance(value, list):
        return ",".join(_fmt_value(v) for v in value) or "-"  # 空のリストも「無い」として揃える
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def format_rows(rows: list, total: Optional[int] = None, max_chars: int = 2000) -> str:
    if not rows:
        return "（0 件）"

    cols: list = list(rows[0].keys())
    seen = set(cols)
    for r in rows[1:]:
        for k in r.keys():
            if k not in seen:
                cols.append(k)
                seen.add(k)
    types = {r.get("type") for r in rows if "type" in r}
    if "type" in cols and len(types) <= 1:
        cols.remove("type")

    header = " | ".join(cols)
    lines = [header]
    char_count = len(header)
    shown = 0
    truncated = False
    for r in rows:
        line = " | ".join(_fmt_value(r.get(c)) for c in cols)
        if shown > 0 and char_count + 1 + len(line) > max_chars:
            truncated = True
            break
        lines.append(line)
        char_count += 1 + len(line)
        shown += 1

    text = "\n".join(lines)
    remaining = len(rows) - shown
    if truncated and remaining > 0:
        text += f"\n… 他 {remaining} 件（--where で絞るか --select で列を減らす）"
    if total is not None and total > len(rows):
        text += f"\n（全 {total} 件中 {len(rows)} 件）"
    return text


def format_show(d: dict) -> str:
    lines = [f"{d['ref']}（{d['type_label']}）"]
    for name, value in d.get("props", {}).items():
        lines.append(f"  {name}: {_fmt_value(value)}")
    for name, entries in d.get("links", {}).items():
        joined = ", ".join(f"{it['ref']}（{it['label']}）" for it in entries)
        lines.append(f"→ {name}: {joined}")
    for name, entries in d.get("inverse", {}).items():
        joined = ", ".join(f"{it['ref']}（{it['label']}）" for it in entries)
        lines.append(f"← {name}: {joined}")
    proposals = d.get("proposals") or []
    if proposals:
        lines.append(f"実行待ち: {', '.join(proposals)}")
    return "\n".join(lines)
