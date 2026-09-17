"""wsonto — 書き出し（JSON Schema・Turtle・Mermaid・Markdown）。

取り決めは `scripts/wsonto/README.md` の「export.py」を参照。ここは実行時は
標準ライブラリだけで動く（Python 3.9 以上）。`schema.Schema` と、objects.json を
`json.load` しただけの生の dict しか見ない（`store.py` に依存しない）。
"""
from __future__ import annotations

from typing import Any, Optional

from .schema import LinkType, ObjectType, Param, Prop, Schema

# --- 型マッピング -----------------------------------------------------------

XSD_DATATYPE = {
    "string": "xsd:string",
    "text": "xsd:string",
    "int": "xsd:integer",
    "number": "xsd:decimal",
    "bool": "xsd:boolean",
    "date": "xsd:date",
    "datetime": "xsd:dateTime",
    "enum": "xsd:string",
}

CORE_PREFIXES = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "sh": "http://www.w3.org/ns/shacl#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "schema": "https://schema.org/",
}


# --- JSON Schema ------------------------------------------------------------


def _scalar_type_schema(
    ptype: Optional[str], values: Optional[list], pmin: Any, pmax: Any,
    pattern: Optional[str], many: bool, label: Optional[str] = None,
) -> dict:
    if ptype in ("string", "text"):
        t: dict = {"type": "string"}
    elif ptype == "int":
        t = {"type": "integer"}
    elif ptype == "number":
        t = {"type": "number"}
    elif ptype == "bool":
        t = {"type": "boolean"}
    elif ptype == "date":
        t = {"type": "string", "format": "date"}
    elif ptype == "datetime":
        t = {"type": "string", "format": "date-time"}
    elif ptype == "enum":
        t = {"type": "string", "enum": list(values or [])}
    else:
        t = {}
    if pmin is not None:
        t["minimum"] = pmin
    if pmax is not None:
        t["maximum"] = pmax
    if pattern:
        t["pattern"] = pattern
    if many:
        t = {"type": "array", "items": t}
    if label:
        t["description"] = label
    return t


def _prop_json_schema(prop: Prop) -> dict:
    return _scalar_type_schema(prop.type, prop.values, prop.min, prop.max, prop.pattern, prop.many, prop.label)


def _param_json_schema(schema: Schema, param: Param) -> dict:
    if param.object_type:
        ot = schema.object_types.get(param.object_type)
        label = ot.label if ot is not None and ot.label else param.object_type
        item = {"type": "string", "description": f"{label} の id"}
        if param.many:
            return {"type": "array", "items": item}
        return item
    return _scalar_type_schema(param.type, param.values, param.min, param.max, param.pattern, param.many, param.label)


def to_jsonschema(schema: Schema) -> dict:
    actions: dict = {}
    for aname, action in schema.action_types.items():
        properties: dict = {}
        required: list = []
        for pname, param in action.parameters.items():
            properties[pname] = _param_json_schema(schema, param)
            if param.required:
                required.append(pname)
        actions[aname] = {
            "name": aname,
            "description": action.description or "",
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": False,
            },
        }

    objects: dict = {}
    for tname in schema.object_types:
        properties = {}
        required = []
        for pname, prop in schema.props(tname).items():
            properties[pname] = _prop_json_schema(prop)
            if prop.required:
                required.append(pname)
        objects[tname] = {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        }

    return {"actions": actions, "objects": objects}


# --- Turtle ------------------------------------------------------------


def _esc(value: Any) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\r", "\\r").replace("\n", "\\n")


def _literal_for(ptype: Optional[str], value: Any) -> str:
    if ptype == "bool":
        return '"{}"^^xsd:boolean'.format("true" if value else "false")
    if ptype == "int":
        return f'"{value}"^^xsd:integer'
    if ptype == "number":
        return f'"{value}"^^xsd:decimal'
    if ptype == "date":
        return f'"{value}"^^xsd:date'
    if ptype == "datetime":
        return f'"{value}"^^xsd:dateTime'
    return f'"{_esc(value)}"'


def _literal_guess(value: Any) -> str:
    if isinstance(value, bool):
        return '"{}"^^xsd:boolean'.format("true" if value else "false")
    if isinstance(value, int):
        return f'"{value}"^^xsd:integer'
    if isinstance(value, float):
        return f'"{value}"^^xsd:decimal'
    return f'"{_esc(value)}"'


def _turtle_prefixes(schema: Schema, base: str) -> list:
    prefixes = dict(CORE_PREFIXES)
    if schema.common is not None:
        prefixes.update(schema.common.prefixes)
    prefixes.update(schema.prefixes)
    lines = [f"@prefix ex: <{base}> ."]
    for name in sorted(prefixes):
        lines.append(f"@prefix {name}: <{prefixes[name]}> .")
    return lines


def _class_triples(tname: str, ot: ObjectType) -> list:
    lines = [f"ex:{tname} a owl:Class ."]
    if ot.label:
        lines.append(f'ex:{tname} rdfs:label "{_esc(ot.label)}"@ja .')
    for parent in ot.extends:
        lines.append(f"ex:{tname} rdfs:subClassOf ex:{parent} .")
    if ot.same_as:
        lines.append(f"ex:{tname} rdfs:seeAlso {ot.same_as} .")
    return lines


def _datatype_prop_triples(pname: str, entries: list) -> list:
    # rdfs:domain / rdfs:range は書かない。RDFS 推論つきの検査（pySHACL の
    # inference="rdfs"）では rdfs:range が値ノードに型を「推論」してしまい、
    # sh:class の違反検出を無効化する（実測で確認済み）。schema:domainIncludes /
    # schema:rangeIncludes は推論を起こさない注釈なので、制約は SHACL（sh:datatype
    # 等）だけに持たせつつ「意図した両端」を残せる。複数の型が同じ名前を自前で
    # 宣言していても、推論が起きないので domainIncludes を全部並べてよい。
    lines = [f"ex:{pname} a owl:DatatypeProperty ."]
    prop = entries[0][1]
    dt = XSD_DATATYPE.get(prop.type)
    if dt:
        lines.append(f"ex:{pname} schema:rangeIncludes {dt} .")
    for tname, _prop in entries:
        lines.append(f"ex:{pname} schema:domainIncludes ex:{tname} .")
    return lines


def _object_prop_triples(lname: str, lt: LinkType) -> list:
    lines = [
        f"ex:{lname} a owl:ObjectProperty .",
        f"ex:{lname} schema:domainIncludes ex:{lt.from_type} .",
        f"ex:{lname} schema:rangeIncludes ex:{lt.to_type} .",
    ]
    if lt.inverse:
        lines.append(f"ex:{lname} owl:inverseOf ex:{lt.inverse} .")
    return lines


def _prop_shape(pname: str, prop: Prop) -> str:
    parts = [f"sh:path ex:{pname}"]
    dt = XSD_DATATYPE.get(prop.type)
    if dt:
        parts.append(f"sh:datatype {dt}")
    if prop.type == "enum" and prop.values:
        vals = " ".join(f'"{_esc(v)}"' for v in prop.values)
        parts.append(f"sh:in ( {vals} )")
    if prop.required:
        parts.append("sh:minCount 1")
    if not prop.many:
        parts.append("sh:maxCount 1")
    if prop.min is not None:
        parts.append(f"sh:minInclusive {prop.min}")
    if prop.max is not None:
        parts.append(f"sh:maxInclusive {prop.max}")
    if prop.pattern:
        parts.append(f'sh:pattern "{_esc(prop.pattern)}"')
    return "[ " + " ; ".join(parts) + " ]"


def _link_shape(lname: str, lt: LinkType) -> str:
    parts = [f"sh:path ex:{lname}", f"sh:class ex:{lt.to_type}"]
    if lt.min:
        parts.append(f"sh:minCount {lt.min}")
    if lt.max is not None:
        parts.append(f"sh:maxCount {lt.max}")
    return "[ " + " ; ".join(parts) + " ]"


def _inverse_link_shape(lt: LinkType) -> str:
    parts = [f"sh:path [ sh:inversePath ex:{lt.name} ]", f"sh:class ex:{lt.from_type}"]
    if lt.inverse_min:
        parts.append(f"sh:minCount {lt.inverse_min}")
    if lt.inverse_max is not None:
        parts.append(f"sh:maxCount {lt.inverse_max}")
    return "[ " + " ; ".join(parts) + " ]"


def _shape_triples(schema: Schema, tname: str) -> list:
    props = schema.props(tname)
    links_from = schema.links_from(tname)
    links_to = schema.links_to(tname)

    subj = f"ex:{tname}Shape"
    lines = [
        f"{subj} a sh:NodeShape .",
        f"{subj} sh:targetClass ex:{tname} .",
        "{} sh:closed true .".format(subj),
    ]

    # sh:closed は「自分の型」だけで判定すると、下位の型の実体が RDFS の
    # rdfs:subClassOf を通じてこの型の targetClass にも一致してしまい、下位の型
    # だけが持つプロパティが誤って CLOSED 違反になる（pySHACL で実測して確認済
    # み）。下位の型だけが持つプロパティ・出るリンクは ignoredProperties に足し
    # て、実際の制約（required・datatype 等）は下位の型自身の Shape に任せる。
    ignored = {"rdf:type"}
    own_props = set(props)
    own_links = set(links_from)
    for sub in schema.subtypes(tname):
        if sub == tname:
            continue
        for pname in schema.props(sub):
            if pname not in own_props:
                ignored.add(f"ex:{pname}")
        for lname in schema.links_from(sub):
            if lname not in own_links:
                ignored.add(f"ex:{lname}")
    lines.append(f"{subj} sh:ignoredProperties ( {' '.join(sorted(ignored))} ) .")

    for pname, prop in sorted(props.items()):
        lines.append(f"{subj} sh:property {_prop_shape(pname, prop)} .")
    for lname, lt in sorted(links_from.items()):
        lines.append(f"{subj} sh:property {_link_shape(lname, lt)} .")
    for _inv_name, lt in sorted(links_to.items()):
        if lt.inverse_min or lt.inverse_max is not None:
            lines.append(f"{subj} sh:property {_inverse_link_shape(lt)} .")
    return lines


def _normalize_objects(objects: Any) -> list:
    if objects is None:
        return []
    if isinstance(objects, list):
        return objects
    return [objects]


def _entity_triples(schema: Schema, objects: Any, entity_ns: str) -> list:
    lines: list = []
    for od in _normalize_objects(objects):
        for tname, entities in od.items():
            if tname == "_meta" or not isinstance(entities, dict):
                continue
            props_def = schema.props(tname)
            for eid, edata in entities.items():
                subj = f"<{entity_ns}{tname}/{eid}>"
                lines.append(f"{subj} a ex:{tname} .")
                seen = set()
                for pname, prop in props_def.items():
                    seen.add(pname)
                    if pname in edata:
                        value = edata[pname]
                    elif prop.default is not None:
                        value = prop.default
                    else:
                        continue
                    values = value if (prop.many and isinstance(value, list)) else [value]
                    for v in values:
                        lines.append(f"{subj} ex:{pname} {_literal_for(prop.type, v)} .")
                # 定義に無いプロパティも書き出す（自前の検査の CLOSED 違反と揃える）
                for key, value in edata.items():
                    if key == "_links" or key in seen:
                        continue
                    values = value if isinstance(value, list) else [value]
                    for v in values:
                        lines.append(f"{subj} ex:{key} {_literal_guess(v)} .")
                for lname, refs in (edata.get("_links") or {}).items():
                    for ref in refs:
                        rtype, rid = ref.split(":", 1)
                        lines.append(f"{subj} ex:{lname} <{entity_ns}{rtype}/{rid}> .")
    return lines


def to_turtle(schema: Schema, objects: Any = None, base: Optional[str] = None) -> str:
    base = base or f"https://example.com/onto/{schema.name}#"
    entity_ns = base.replace("#", "/")

    lines = list(_turtle_prefixes(schema, base))
    lines.append("")

    for tname in sorted(schema.object_types):
        lines.extend(_class_triples(tname, schema.object_types[tname]))
    lines.append("")

    owners: dict = {}
    for tname, ot in schema.object_types.items():
        for pname, prop in ot.properties.items():
            owners.setdefault(pname, []).append((tname, prop))
    for pname in sorted(owners):
        entries = sorted(owners[pname], key=lambda e: e[0])
        lines.extend(_datatype_prop_triples(pname, entries))
    lines.append("")

    for lname in sorted(schema.link_types):
        lines.extend(_object_prop_triples(lname, schema.link_types[lname]))
    lines.append("")

    for tname in sorted(schema.object_types):
        lines.extend(_shape_triples(schema, tname))

    entity_lines = _entity_triples(schema, objects, entity_ns)
    if entity_lines:
        lines.append("")
        lines.extend(entity_lines)

    return "\n".join(lines) + "\n"


# --- Mermaid ------------------------------------------------------------


def _mmesc(value: Any) -> str:
    return str(value).replace('"', "'").replace("\n", " ").replace("\r", " ")


def _card_token_left(mn: int, mx: Any) -> str:
    many = mn and mn >= 1
    one = mx == 1
    if many:
        return "||" if one else "}|"
    return "|o" if one else "}o"


def _card_token_right(mn: int, mx: Any) -> str:
    many = mn and mn >= 1
    one = mx == 1
    if many:
        return "||" if one else "|{"
    return "o|" if one else "o{"


def to_mermaid(schema: Schema) -> str:
    lines = ["erDiagram"]
    for tname in sorted(schema.object_types):
        ot = schema.object_types[tname]
        lines.append(f"    {tname} {{")
        for pname, prop in ot.properties.items():
            mtype = prop.type or "string"
            if prop.label:
                lines.append(f'        {mtype} {pname} "{_mmesc(prop.label)}"')
            else:
                lines.append(f"        {mtype} {pname}")
        lines.append("    }")

    for lname in sorted(schema.link_types):
        lt = schema.link_types[lname]
        left = _card_token_left(lt.inverse_min, lt.inverse_max)
        right = _card_token_right(lt.min, lt.max)
        label = lt.label or lname
        lines.append(f'    {lt.from_type} {left}--{right} {lt.to_type} : "{_mmesc(label)}"')

    for tname in sorted(schema.object_types):
        ot = schema.object_types[tname]
        for parent in ot.extends:
            lines.append(f'    {tname} }}|..|| {parent} : "の一種"')

    return "\n".join(lines) + "\n"


# --- Markdown ------------------------------------------------------------


def _constraint_str(obj: Any) -> str:
    bits = []
    values = getattr(obj, "values", None)
    if values:
        bits.append("値: " + "/".join(str(v) for v in values))
    pmin = getattr(obj, "min", None)
    if pmin is not None:
        bits.append(f"min={pmin}")
    pmax = getattr(obj, "max", None)
    if pmax is not None:
        bits.append(f"max={pmax}")
    pattern = getattr(obj, "pattern", None)
    if pattern:
        bits.append(f"pattern={pattern}")
    if getattr(obj, "unique", False):
        bits.append("unique")
    default = getattr(obj, "default", None)
    if default is not None:
        bits.append(f"default={default}")
    if getattr(obj, "many", False):
        bits.append("many")
    return "、".join(bits) if bits else "-"


def to_markdown(schema: Schema, objects: Any = None) -> str:
    lines: list = []
    # 案件の index.md には案件で定義したものだけを並べる（共通の分は共通の index.md にある。図には両方を描く）
    own = lambda d: schema.scope == "common" or d.origin == "project"  # noqa: E731
    shared = sorted(n for n, d in schema.object_types.items() if not own(d))
    if shared:
        lines.append("共通（自社）の型も使える: " + "・".join(shared) + "。定義は共通の `knowledges/ontology/index.md`。")
        lines.append("")

    lines.append("## 型")
    lines.append("")
    for tname in sorted(schema.object_types):
        ot = schema.object_types[tname]
        if not own(ot):
            continue
        lines.append(f"### {tname}（{ot.label or tname}）")
        lines.append("")
        if ot.description:
            lines.append(ot.description)
            lines.append("")
        lines.append("| 名前 | label | 型 | 必須 | 制約 |")
        lines.append("|---|---|---|---|---|")
        for pname, prop in schema.props(tname).items():
            lines.append(
                f"| {pname} | {prop.label or '-'} | {prop.type} | {'○' if prop.required else ''} "
                f"| {_constraint_str(prop)} |"
            )
        lines.append("")

    lines.append("## つながり")
    lines.append("")
    lines.append("| 名前 | label | from → to | 件数 | 逆向き |")
    lines.append("|---|---|---|---|---|")
    for lname in sorted(schema.link_types):
        lt = schema.link_types[lname]
        if not own(lt):
            continue
        card = "{}..{}".format(lt.min, lt.max if lt.max is not None else "*")
        inv = "-"
        if lt.inverse:
            inv_card = "{}..{}".format(lt.inverse_min, lt.inverse_max if lt.inverse_max is not None else "*")
            inv = f"{lt.inverse}（{inv_card}）"
        lines.append(f"| {lname} | {lt.label or '-'} | {lt.from_type} → {lt.to_type} | {card} | {inv} |")
    lines.append("")

    lines.append("```mermaid")
    lines.append(to_mermaid(schema).rstrip("\n"))
    lines.append("```")
    lines.append("")

    lines.append("## できること")
    lines.append("")
    for aname in sorted(schema.action_types):
        action = schema.action_types[aname]
        if not own(action):
            continue
        lines.append(f"### {aname}（{action.label or aname}）")
        lines.append("")
        if action.description:
            lines.append(action.description)
            lines.append("")
        lines.append("| 引数 | label | 型 | 必須 | 制約 |")
        lines.append("|---|---|---|---|---|")
        for pname, param in action.parameters.items():
            ptype = param.type if param.type else f"{param.object_type} の id"
            lines.append(
                f"| {pname} | {param.label or '-'} | {ptype} | {'○' if param.required else ''} "
                f"| {_constraint_str(param)} |"
            )
        lines.append("")

        if action.criteria:
            lines.append("前提条件:")
            for crit in action.criteria:
                src = crit.when.src if crit.when else ""
                lines.append(f"- `{src}` → {crit.message}")
            lines.append("")

        appr = action.approval
        if appr is not None:
            if appr.mode == "auto":
                lines.append("承認: 自動")
            elif appr.mode == "stage":
                lines.append("承認: 必ず実行待ち")
            else:
                src = appr.when.src if appr.when else ""
                lines.append(f"承認: `{src}` のとき実行待ち（担当: {appr.role or '-'}）")
            lines.append("")

    if objects:
        counts: dict = {}
        for od in _normalize_objects(objects):
            for tname, entities in od.items():
                if tname == "_meta" or not isinstance(entities, dict):
                    continue
                counts[tname] = counts.get(tname, 0) + len(entities)
        if counts:
            lines.append("## 件数")
            lines.append("")
            lines.append("| 型 | 件数 |")
            lines.append("|---|---|")
            for tname in sorted(counts):
                lines.append(f"| {tname} | {counts[tname]} |")
            lines.append("")

    return "\n".join(lines) + "\n"
