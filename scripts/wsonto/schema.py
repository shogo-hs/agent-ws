"""wsonto — 定義（ontology.json）の読み込みとメタモデル検査。

取り決めは `scripts/wsonto/README.md` の「schema.py」を参照。ここは実行時は
標準ライブラリだけで動く（Python 3.9 以上）。誤りは 1 件で止めず、problems に
全部集めて `SchemaError` を 1 回だけ投げる。
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .errors import ExprError, OntoError, SchemaError
from .expr import Expr, compile_expr

TYPE_NAME_RE = re.compile(r"^[A-Z][A-Za-z0-9]*$")
NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
CONST_NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
RESERVED_NAMES = {"id", "type", "actor"}
BUILTIN_PREFIXES = {"schema", "rdfs", "owl", "skos", "xsd"}
PROP_TYPES = {"string", "text", "int", "number", "bool", "date", "datetime", "enum"}

TOP_KEYS = {
    "ontology", "version", "description", "prefixes", "governance",
    "constants", "object_types", "link_types", "action_types",
}
OBJECT_TYPE_KEYS = {
    "label", "aliases", "description", "same_as", "extends", "abstract",
    "label_property", "alias_property", "summary", "properties",
}
PROP_KEYS = {
    "type", "values", "required", "many", "min", "max", "pattern",
    "unique", "default", "label", "description", "agent_visible",
}
LINK_TYPE_KEYS = {
    "label", "from", "to", "min", "max", "inverse", "inverse_label",
    "inverse_min", "inverse_max", "description",
}
ACTION_TYPE_KEYS = {
    "label", "description", "parameters", "criteria", "rules",
    "approval", "returns", "next",
}
PARAM_KEYS = {"type", "values", "object_type", "required", "many", "label", "min", "max", "pattern"}
CRITERION_KEYS = {"when", "message"}
RULE_CREATE_KEYS = {"create", "as", "id", "set", "link", "if"}
RULE_MODIFY_KEYS = {"modify", "set", "link", "unlink", "if"}
RULE_DELETE_KEYS = {"delete", "if"}
APPROVAL_KEYS = {"stage_if", "role"}

_BRACE_RE = re.compile(r"\{([^{}]*)\}")


# --- dataclass ---------------------------------------------------------


@dataclass
class Prop:
    name: str
    type: Optional[str] = None
    values: Optional[list] = None
    required: bool = False
    many: bool = False
    min: Any = None
    max: Any = None
    pattern: Optional[str] = None
    unique: bool = False
    default: Any = None
    label: Optional[str] = None
    description: Optional[str] = None
    agent_visible: bool = True


@dataclass
class ObjectType:
    name: str
    label: Optional[str] = None
    aliases: list = field(default_factory=list)
    description: Optional[str] = None
    same_as: Optional[str] = None
    extends: list = field(default_factory=list)
    abstract: bool = False
    properties: dict = field(default_factory=dict)
    summary: list = field(default_factory=list)
    label_property: Optional[str] = None
    alias_property: Optional[str] = None
    origin: str = "project"


@dataclass
class LinkType:
    name: str
    label: Optional[str] = None
    from_type: str = ""
    to_type: str = ""
    min: int = 0
    max: Any = None
    inverse: Optional[str] = None
    inverse_label: Optional[str] = None
    inverse_min: int = 0
    inverse_max: Any = None
    description: Optional[str] = None
    origin: str = "project"


@dataclass
class Param:
    name: str
    type: Optional[str] = None
    values: Optional[list] = None
    object_type: Optional[str] = None
    required: bool = False
    many: bool = False
    label: Optional[str] = None
    min: Any = None  # エンジンが引数の値を検査する（プロパティと同じ意味）
    max: Any = None
    pattern: Optional[str] = None


@dataclass
class Criterion:
    when: Optional[Expr]
    message: str = ""


@dataclass
class Approval:
    mode: str = "stage"
    when: Optional[Expr] = None
    role: Optional[str] = None


@dataclass
class ActionType:
    name: str
    label: Optional[str] = None
    description: Optional[str] = None
    parameters: dict = field(default_factory=dict)
    criteria: list = field(default_factory=list)
    rules: list = field(default_factory=list)
    approval: Optional[Approval] = None
    returns: Optional[str] = None
    next: Optional[str] = None
    origin: str = "project"


@dataclass
class Schema:
    doc: dict
    name: str
    version: int
    hash: str
    scope: str
    common: Optional["Schema"]
    governance: dict
    prefixes: dict
    constants: dict
    object_types: dict
    link_types: dict
    action_types: dict

    def is_a(self, type_name: str, ancestor: str, _seen: Optional[set] = None) -> bool:
        if type_name == ancestor:
            return True
        if _seen is None:
            _seen = set()
        if type_name in _seen:
            return False
        _seen.add(type_name)
        ot = self.object_types.get(type_name)
        if ot is None:
            return False
        return any(self.is_a(parent, ancestor, _seen) for parent in ot.extends)

    def subtypes(self, type_name: str) -> list:
        return [name for name in self.object_types if self.is_a(name, type_name)]

    def props(self, type_name: str, _seen: Optional[set] = None) -> dict:
        if _seen is None:
            _seen = set()
        if type_name in _seen:
            return {}
        _seen.add(type_name)
        ot = self.object_types.get(type_name)
        if ot is None:
            return {}
        result: dict = {}
        for parent in ot.extends:
            result.update(self.props(parent, _seen))
        result.update(ot.properties)
        return result

    def links_from(self, type_name: str) -> dict:
        return {
            name: lt for name, lt in self.link_types.items()
            if self.is_a(type_name, lt.from_type)
        }

    def links_to(self, type_name: str) -> dict:
        result = {}
        for lt in self.link_types.values():
            if lt.inverse and self.is_a(type_name, lt.to_type):
                result[lt.inverse] = lt
        return result

    def concrete(self, type_name: str) -> bool:
        ot = self.object_types.get(type_name)
        if ot is None:
            return False
        return not ot.abstract


# --- 公開関数 -------------------------------------------------------------


def load_schema(dir: Path, common_dir: Optional[Path] = None) -> Schema:
    common = None
    if common_dir is not None:
        common = load_schema(common_dir, None)
    path = Path(dir) / "ontology.json"
    if not path.exists():
        raise OntoError(f"{path}: ontology.json が見つからない")
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise OntoError(f"{path}: JSON として読めない（{e}）")
    return parse_schema(doc, common=common, source=str(path))


def merge_patch(doc: dict, patch: dict) -> dict:
    result = copy.deepcopy(doc)
    _merge_into(result, patch)
    return result


def _merge_into(base: dict, patch: dict) -> None:
    for key, value in patch.items():
        if isinstance(value, dict) and value == {"$delete": True}:
            base.pop(key, None)
        elif isinstance(value, dict) and isinstance(base.get(key), dict):
            _merge_into(base[key], value)
        else:
            base[key] = copy.deepcopy(value)


def schema_hash(doc: dict) -> str:
    canon = json.dumps(doc, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()[:12]


# --- 内部ヘルパー ----------------------------------------------------------


def _check_unknown_keys(d: Any, allowed: set, where: str, problems: list) -> None:
    if not isinstance(d, dict):
        return
    for key in d:
        if key not in allowed:
            problems.append(f"{where}: 知らないキー '{key}'")


def _compile_expr_safe(src: Any, allowed_names: set, where: str, problems: list) -> Optional[Expr]:
    if not isinstance(src, str):
        problems.append(f"{where}: 式は文字列である必要がある")
        return None
    try:
        return compile_expr(src, allowed_names=allowed_names)
    except ExprError as e:
        problems.append(f"{where}: {e}")
        return None


def _check_template(tmpl: Any, allowed_names: set, where: str, problems: list) -> None:
    if tmpl is None:
        return
    if not isinstance(tmpl, str):
        problems.append(f"{where}: 雛形は文字列である必要がある")
        return
    for m in _BRACE_RE.finditer(tmpl):
        piece = m.group(1)
        if not piece.strip():
            continue
        try:
            compile_expr(piece, allowed_names=allowed_names)
        except ExprError as e:
            problems.append(f"{where}: 雛形の式 '{{{piece}}}' が不正（{e}）")


def _check_default_value(ptype: Optional[str], values: Optional[list], many: bool, default: Any) -> bool:
    def ok_one(v: Any) -> bool:
        if ptype in ("string", "text"):
            return isinstance(v, str)
        if ptype == "int":
            return isinstance(v, int) and not isinstance(v, bool)
        if ptype == "number":
            return isinstance(v, (int, float)) and not isinstance(v, bool)
        if ptype == "bool":
            return isinstance(v, bool)
        if ptype in ("date", "datetime"):
            return isinstance(v, str)
        if ptype == "enum":
            return v in (values or [])
        return True

    if many:
        if not isinstance(default, list):
            return False
        return all(ok_one(v) for v in default)
    return ok_one(default)


def _parse_prop(tname: str, pname: str, praw: Any, problems: list) -> Optional[Prop]:
    where = f"object_types.{tname}.properties.{pname}"
    if not NAME_RE.match(pname):
        problems.append(f"{where}: プロパティ名の形式が不正")
    if pname in RESERVED_NAMES:
        problems.append(f"{where}: 予約語はプロパティ名に使えない")
    if not isinstance(praw, dict):
        problems.append(f"{where}: 定義はオブジェクトである必要がある")
        return None
    _check_unknown_keys(praw, PROP_KEYS, where, problems)

    ptype = praw.get("type")
    if ptype not in PROP_TYPES:
        problems.append(f"{where}: type が不正（{ptype!r}）")
        ptype = ptype if ptype in PROP_TYPES else None
    values = praw.get("values")
    if ptype == "enum" and not values:
        problems.append(f"{where}: enum なのに values が無い")

    pmin = praw.get("min")
    pmax = praw.get("max")
    if pmin is not None and pmax is not None and pmin > pmax:
        problems.append(f"{where}: min が max より大きい")

    pattern = praw.get("pattern")
    if pattern is not None:
        try:
            re.compile(pattern)
        except re.error as e:
            problems.append(f"{where}: pattern が正規表現として不正（{e}）")

    if "default" in praw:
        if not _check_default_value(ptype, values, bool(praw.get("many", False)), praw.get("default")):
            problems.append(f"{where}: default が type/values に合わない")

    return Prop(
        name=pname,
        type=ptype,
        values=list(values) if values else None,
        required=bool(praw.get("required", False)),
        many=bool(praw.get("many", False)),
        min=pmin,
        max=pmax,
        pattern=pattern,
        unique=bool(praw.get("unique", False)),
        default=praw.get("default"),
        label=praw.get("label"),
        description=praw.get("description"),
        agent_visible=bool(praw.get("agent_visible", True)),
    )


def _detect_extends_cycles(own_type_names: set, object_types: dict, problems: list) -> None:
    color: dict = {}
    reported: set = set()

    def visit(name: str, path: list) -> None:
        color[name] = 1
        path.append(name)
        ot = object_types.get(name)
        if ot is not None:
            for parent in ot.extends:
                if parent not in object_types:
                    continue
                c = color.get(parent, 0)
                if c == 1:
                    idx = path.index(parent) if parent in path else 0
                    cycle = path[idx:] + [parent]
                    key = tuple(sorted(set(cycle)))
                    if key not in reported:
                        reported.add(key)
                        problems.append(
                            f"object_types.{cycle[0]}.extends: 継承が循環している（{' -> '.join(cycle)}）"
                        )
                elif c == 0:
                    visit(parent, path)
        path.pop()
        color[name] = 2

    for name in own_type_names:
        if color.get(name, 0) == 0:
            visit(name, [])


def _resolve_target_type(target: Any, params: dict, as_types: dict) -> Optional[str]:
    if not isinstance(target, str):
        return None
    if target in as_types:
        return as_types[target]
    p = params.get(target)
    if p is not None and p.object_type:
        return p.object_type
    return None


def _target_is_many_param(target: Any, params: dict) -> bool:
    p = params.get(target) if isinstance(target, str) else None
    return bool(p is not None and p.many)


def _all_as_names(raw: dict) -> set:
    names = set()
    for r in (raw.get("rules") or []):
        if isinstance(r, dict) and "create" in r and isinstance(r.get("as"), str):
            names.add(r["as"])
    return names


def _parse_param(aname: str, pname: str, praw: Any, all_type_names: set, problems: list) -> Optional[Param]:
    where = f"action_types.{aname}.parameters.{pname}"
    if not NAME_RE.match(pname):
        problems.append(f"{where}: 引数名の形式が不正")
    if pname in RESERVED_NAMES:
        problems.append(f"{where}: 予約語は引数名に使えない")
    if not isinstance(praw, dict):
        problems.append(f"{where}: 定義はオブジェクトである必要がある")
        return None
    _check_unknown_keys(praw, PARAM_KEYS, where, problems)

    has_type = "type" in praw
    has_obj = "object_type" in praw
    if has_type and has_obj:
        problems.append(f"{where}: type と object_type の両方は指定できない")
    if not has_type and not has_obj:
        problems.append(f"{where}: type か object_type のどちらかが必要")

    ptype = praw.get("type")
    if has_type and ptype not in PROP_TYPES:
        problems.append(f"{where}.type: 値が不正（{ptype!r}）")
    values = praw.get("values")
    if has_type and ptype == "enum" and not values:
        problems.append(f"{where}: enum なのに values が無い")

    obj_type = praw.get("object_type")
    if has_obj and obj_type not in all_type_names:
        problems.append(f"{where}.object_type: 参照先の型 '{obj_type}' が無い")

    pmin, pmax, pattern = praw.get("min"), praw.get("max"), praw.get("pattern")
    if has_obj and (pmin is not None or pmax is not None or pattern is not None):
        problems.append(f"{where}: min / max / pattern は実体への参照（object_type）には付けられない")
    if pmin is not None and pmax is not None:
        try:
            if pmin > pmax:
                problems.append(f"{where}: min が max より大きい")
        except TypeError:
            problems.append(f"{where}: min と max を比べられない")
    if pattern is not None:
        try:
            re.compile(pattern)
        except (re.error, TypeError):
            problems.append(f"{where}.pattern: 正規表現として壊れている")

    return Param(
        name=pname,
        type=ptype if has_type else None,
        values=list(values) if values else None,
        object_type=obj_type if has_obj else None,
        required=bool(praw.get("required", False)),
        many=bool(praw.get("many", False)),
        label=praw.get("label"),
        min=pmin,
        max=pmax,
        pattern=pattern,
    )


def parse_schema(doc: dict, common: Optional[Schema] = None, source: str = "") -> Schema:
    problems: list = []

    if not isinstance(doc, dict):
        raise SchemaError(["ontology.json はオブジェクトである必要がある"], source)

    _check_unknown_keys(doc, TOP_KEYS, "(トップレベル)", problems)

    name = doc.get("ontology", "")
    version = doc.get("version", 0)

    governance_raw = doc.get("governance", {})
    governance = dict(governance_raw) if isinstance(governance_raw, dict) else {}
    governance.setdefault("schema_changes", "stage")

    prefixes_raw = doc.get("prefixes", {})
    prefixes = dict(prefixes_raw) if isinstance(prefixes_raw, dict) else {}
    common_prefixes = set(common.prefixes) if common else set()
    all_prefixes = set(prefixes) | common_prefixes | BUILTIN_PREFIXES

    # --- constants ---
    constants = dict(common.constants) if common else {}
    for cname, cval in (doc.get("constants") or {}).items():
        if not CONST_NAME_RE.match(cname):
            problems.append(f"constants.{cname}: 定数名の形式が不正")
        if common and cname in common.constants:
            problems.append(f"constants.{cname}: 共通の定数と同名で再定義できない")
        constants[cname] = cval

    # --- object_types: pass 1（自分の定義を作る）---
    object_types = dict(common.object_types) if common else {}
    own_type_names: set = set()
    for tname, raw in (doc.get("object_types") or {}).items():
        own_type_names.add(tname)
        if not TYPE_NAME_RE.match(tname):
            problems.append(f"object_types.{tname}: 型名の形式が不正")
        if tname in RESERVED_NAMES:
            problems.append(f"object_types.{tname}: 予約語は型名に使えない")
        if common and tname in common.object_types:
            problems.append(f"object_types.{tname}: 共通の型と同名で再定義できない")
        if not isinstance(raw, dict):
            problems.append(f"object_types.{tname}: 定義はオブジェクトである必要がある")
            continue
        _check_unknown_keys(raw, OBJECT_TYPE_KEYS, f"object_types.{tname}", problems)

        properties = {}
        for pname, praw in (raw.get("properties") or {}).items():
            prop = _parse_prop(tname, pname, praw, problems)
            if prop is not None:
                properties[pname] = prop

        same_as = raw.get("same_as")
        if same_as is not None:
            prefix = same_as.split(":", 1)[0] if isinstance(same_as, str) and ":" in same_as else same_as
            if prefix not in all_prefixes:
                problems.append(f"object_types.{tname}.same_as: 接頭辞 '{prefix}' が prefixes に無い")

        object_types[tname] = ObjectType(
            name=tname,
            label=raw.get("label"),
            aliases=list(raw.get("aliases") or []),
            description=raw.get("description"),
            same_as=same_as,
            extends=list(raw.get("extends") or []),
            abstract=bool(raw.get("abstract", False)),
            properties=properties,
            summary=list(raw.get("summary") or []),
            label_property=raw.get("label_property"),
            alias_property=raw.get("alias_property"),
            origin="project" if common is not None else "common",
        )

    all_type_names = set(object_types)

    # --- object_types: pass 2（extends の参照と循環）---
    for tname in own_type_names:
        ot = object_types.get(tname)
        if ot is None:
            continue
        for parent in ot.extends:
            if parent not in all_type_names:
                problems.append(f"object_types.{tname}.extends: 参照先の型 '{parent}' が無い")
    _detect_extends_cycles(own_type_names, object_types, problems)

    # --- link_types ---
    link_types = dict(common.link_types) if common else {}
    for lname, raw in (doc.get("link_types") or {}).items():
        if not NAME_RE.match(lname):
            problems.append(f"link_types.{lname}: リンク名の形式が不正")
        if lname in RESERVED_NAMES:
            problems.append(f"link_types.{lname}: 予約語はリンク名に使えない")
        if common and lname in common.link_types:
            problems.append(f"link_types.{lname}: 共通のリンク型と同名で再定義できない")
        if not isinstance(raw, dict):
            problems.append(f"link_types.{lname}: 定義はオブジェクトである必要がある")
            continue
        where = f"link_types.{lname}"
        _check_unknown_keys(raw, LINK_TYPE_KEYS, where, problems)

        from_type = raw.get("from")
        to_type = raw.get("to")
        if from_type not in all_type_names:
            problems.append(f"{where}.from: 参照先の型 '{from_type}' が無い")
        if to_type not in all_type_names:
            problems.append(f"{where}.to: 参照先の型 '{to_type}' が無い")

        lmin = raw.get("min", 0)
        lmax = raw.get("max")
        if lmin is not None and lmax is not None and lmin > lmax:
            problems.append(f"{where}: min が max より大きい")

        inverse = raw.get("inverse")
        if inverse is not None:
            if not NAME_RE.match(inverse):
                problems.append(f"{where}.inverse: 逆向きの名前の形式が不正")
            if inverse in RESERVED_NAMES:
                problems.append(f"{where}.inverse: 予約語は逆向きの名前に使えない")

        inv_min = raw.get("inverse_min", 0)
        inv_max = raw.get("inverse_max")
        if inv_min is not None and inv_max is not None and inv_min > inv_max:
            problems.append(f"{where}: inverse_min が inverse_max より大きい")

        link_types[lname] = LinkType(
            name=lname,
            label=raw.get("label"),
            from_type=from_type,
            to_type=to_type,
            min=lmin,
            max=lmax,
            inverse=inverse,
            inverse_label=raw.get("inverse_label"),
            inverse_min=inv_min,
            inverse_max=inv_max,
            description=raw.get("description"),
            origin="project" if common is not None else "common",
        )

    # ここで一旦 Schema を組み、以降の検査（継承込みの参照）に使う。
    schema = Schema(
        doc=doc,
        name=name,
        version=version,
        hash=schema_hash(doc),
        scope="project" if common is not None else "common",
        common=common,
        governance=governance,
        prefixes=prefixes,
        constants=constants,
        object_types=object_types,
        link_types=link_types,
        action_types={},
    )

    # --- プロパティ名・出るリンク名・入るリンクの逆向き名の衝突（型ごと）---
    for tname in object_types:
        props_ = schema.props(tname)
        links_from_ = schema.links_from(tname)
        links_to_ = schema.links_to(tname)
        owner_of: dict = {}
        for group_label, group in (
            ("プロパティ", props_), ("出るリンク", links_from_), ("入るリンクの逆向き", links_to_),
        ):
            for key in group:
                prev = owner_of.get(key)
                if prev is not None and prev != group_label:
                    problems.append(
                        f"object_types.{tname}: 名前 '{key}' が {prev}と{group_label}で重複している"
                    )
                else:
                    owner_of.setdefault(key, group_label)

    # --- summary / label_property / alias_property が実在するプロパティを指すか（自分の型だけ）---
    for tname in own_type_names:
        ot = object_types.get(tname)
        if ot is None:
            continue
        props_ = schema.props(tname)
        where = f"object_types.{tname}"
        for s in ot.summary:
            if s not in props_:
                problems.append(f"{where}.summary: プロパティ '{s}' が無い")
        if ot.label_property is not None and ot.label_property not in props_:
            problems.append(f"{where}.label_property: プロパティ '{ot.label_property}' が無い")
        if ot.alias_property is not None and ot.alias_property not in props_:
            problems.append(f"{where}.alias_property: プロパティ '{ot.alias_property}' が無い")

    # --- action_types ---
    action_types = dict(common.action_types) if common else {}
    for aname, raw in (doc.get("action_types") or {}).items():
        if not TYPE_NAME_RE.match(aname):
            problems.append(f"action_types.{aname}: アクション名の形式が不正")
        if common and aname in common.action_types:
            problems.append(f"action_types.{aname}: 共通のアクション型と同名で再定義できない")
        if not isinstance(raw, dict):
            problems.append(f"action_types.{aname}: 定義はオブジェクトである必要がある")
            continue
        where = f"action_types.{aname}"
        _check_unknown_keys(raw, ACTION_TYPE_KEYS, where, problems)

        params: dict = {}
        for pname, praw in (raw.get("parameters") or {}).items():
            p = _parse_param(aname, pname, praw, all_type_names, problems)
            if p is not None:
                params[pname] = p
        param_names = set(params)
        all_as = _all_as_names(raw)
        const_names = set(constants)
        allowed_full = param_names | all_as | const_names | {"actor"}
        allowed_no_as = param_names | const_names | {"actor"}

        # criteria
        criteria = []
        for i, craw in enumerate(raw.get("criteria") or []):
            cwhere = f"{where}.criteria[{i}]"
            if not isinstance(craw, dict):
                problems.append(f"{cwhere}: 定義はオブジェクトである必要がある")
                continue
            _check_unknown_keys(craw, CRITERION_KEYS, cwhere, problems)
            when_expr = _compile_expr_safe(craw.get("when"), allowed_no_as, f"{cwhere}.when", problems)
            message = craw.get("message", "")
            _check_template(message, allowed_full, f"{cwhere}.message", problems)
            criteria.append(Criterion(when=when_expr, message=message if isinstance(message, str) else ""))

        # rules
        rules_out: list = []
        as_types: dict = {}
        for i, rraw in enumerate(raw.get("rules") or []):
            rwhere = f"{where}.rules[{i}]"
            if not isinstance(rraw, dict):
                problems.append(f"{rwhere}: 定義はオブジェクトである必要がある")
                continue
            allowed_expr = param_names | set(as_types) | const_names | {"actor"}

            if "create" in rraw:
                _check_unknown_keys(rraw, RULE_CREATE_KEYS, rwhere, problems)
                ctype = rraw.get("create")
                as_name = rraw.get("as")
                if ctype not in all_type_names:
                    problems.append(f"{rwhere}.create: 参照先の型 '{ctype}' が無い")
                if not as_name:
                    problems.append(f"{rwhere}: create に as が無い")
                elif not isinstance(as_name, str) or not NAME_RE.match(as_name) or as_name in RESERVED_NAMES:
                    problems.append(f"{rwhere}.as: 名前の形式が不正")

                id_tmpl = rraw.get("id")
                _check_template(id_tmpl, allowed_expr | {"seq"}, f"{rwhere}.id", problems)

                target_props = schema.props(ctype) if ctype in all_type_names else {}
                target_links = schema.links_from(ctype) if ctype in all_type_names else {}
                new_set = {}
                for prop_name, expr_src in (rraw.get("set") or {}).items():
                    if prop_name not in target_props:
                        problems.append(f"{rwhere}.set.{prop_name}: '{ctype}' にプロパティが無い")
                    new_set[prop_name] = _compile_expr_safe(
                        expr_src, allowed_expr, f"{rwhere}.set.{prop_name}", problems
                    )
                new_link = {}
                for link_name, expr_src in (rraw.get("link") or {}).items():
                    if link_name not in target_links:
                        problems.append(f"{rwhere}.link.{link_name}: '{ctype}' から出るリンクでない")
                    new_link[link_name] = _compile_expr_safe(
                        expr_src, allowed_expr, f"{rwhere}.link.{link_name}", problems
                    )
                if_expr = None
                if "if" in rraw:
                    if_expr = _compile_expr_safe(rraw.get("if"), allowed_expr, f"{rwhere}.if", problems)

                rules_out.append({
                    "create": ctype, "as": as_name, "id": id_tmpl,
                    "set": new_set, "link": new_link, "if": if_expr,
                })
                if isinstance(as_name, str) and NAME_RE.match(as_name) and ctype in all_type_names:
                    as_types[as_name] = ctype

            elif "modify" in rraw:
                _check_unknown_keys(rraw, RULE_MODIFY_KEYS, rwhere, problems)
                target = rraw.get("modify")
                target_type = _resolve_target_type(target, params, as_types)
                if target_type is None:
                    problems.append(f"{rwhere}.modify: 対象 '{target}' が引数（object_type）でも as の名前でもない")
                elif _target_is_many_param(target, params):
                    problems.append(f"{rwhere}.modify: modify / delete の対象に many の引数は使えない")
                target_props = schema.props(target_type) if target_type else {}
                target_links = schema.links_from(target_type) if target_type else {}
                new_set = {}
                for prop_name, expr_src in (rraw.get("set") or {}).items():
                    if prop_name not in target_props:
                        problems.append(f"{rwhere}.set.{prop_name}: '{target_type}' にプロパティが無い")
                    new_set[prop_name] = _compile_expr_safe(
                        expr_src, allowed_expr, f"{rwhere}.set.{prop_name}", problems
                    )
                new_link = {}
                for link_name, expr_src in (rraw.get("link") or {}).items():
                    if link_name not in target_links:
                        problems.append(f"{rwhere}.link.{link_name}: '{target_type}' から出るリンクでない")
                    new_link[link_name] = _compile_expr_safe(
                        expr_src, allowed_expr, f"{rwhere}.link.{link_name}", problems
                    )
                new_unlink = {}
                for link_name, expr_src in (rraw.get("unlink") or {}).items():
                    if link_name not in target_links:
                        problems.append(f"{rwhere}.unlink.{link_name}: '{target_type}' から出るリンクでない")
                    new_unlink[link_name] = _compile_expr_safe(
                        expr_src, allowed_expr, f"{rwhere}.unlink.{link_name}", problems
                    )
                if_expr = None
                if "if" in rraw:
                    if_expr = _compile_expr_safe(rraw.get("if"), allowed_expr, f"{rwhere}.if", problems)

                rules_out.append({
                    "modify": target, "set": new_set, "link": new_link,
                    "unlink": new_unlink, "if": if_expr,
                })

            elif "delete" in rraw:
                _check_unknown_keys(rraw, RULE_DELETE_KEYS, rwhere, problems)
                target = rraw.get("delete")
                target_type = _resolve_target_type(target, params, as_types)
                if target_type is None:
                    problems.append(f"{rwhere}.delete: 対象 '{target}' が引数（object_type）でも as の名前でもない")
                elif _target_is_many_param(target, params):
                    problems.append(f"{rwhere}.delete: modify / delete の対象に many の引数は使えない")
                if_expr = None
                if "if" in rraw:
                    if_expr = _compile_expr_safe(rraw.get("if"), allowed_expr, f"{rwhere}.if", problems)
                rules_out.append({"delete": target, "if": if_expr})

            else:
                problems.append(f"{rwhere}: create/modify/delete のいずれでもない")

        # approval
        approval_raw = raw.get("approval", "stage")
        if approval_raw in ("auto", "stage"):
            approval = Approval(mode=approval_raw)
        elif isinstance(approval_raw, dict):
            _check_unknown_keys(approval_raw, APPROVAL_KEYS, f"{where}.approval", problems)
            when_expr = None
            if "stage_if" in approval_raw:
                when_expr = _compile_expr_safe(
                    approval_raw.get("stage_if"), allowed_full, f"{where}.approval.stage_if", problems
                )
            approval = Approval(mode="stage_if", when=when_expr, role=approval_raw.get("role"))
        else:
            problems.append(f"{where}.approval: approval の値が不正（{approval_raw!r}）")
            approval = Approval(mode="stage")

        returns = raw.get("returns")
        if returns is not None and returns not in all_as:
            problems.append(f"{where}.returns: as の名前 '{returns}' が無い")

        next_tmpl = raw.get("next")
        _check_template(next_tmpl, allowed_full, f"{where}.next", problems)

        action_types[aname] = ActionType(
            name=aname,
            label=raw.get("label"),
            description=raw.get("description"),
            parameters=params,
            criteria=criteria,
            rules=rules_out,
            approval=approval,
            returns=returns,
            next=next_tmpl,
            origin="project" if common is not None else "common",
        )

    schema.action_types = action_types

    if problems:
        raise SchemaError(problems, source)
    return schema
