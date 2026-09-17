"""wsonto — 定義（ontology.json）の変更。

取り決めは `scripts/wsonto/README.md` の「govern.py」を参照。実行時は標準
ライブラリだけで動く（Python 3.9 以上）。パッチを当てた候補の定義を
メタモデル検査（schema.py）・lint（lint.py）・既存実体との整合検査
（validate.py）にかけてから、governance の設定と誰が実行したかで
即時反映するか実行待ちに積むかを決める。
"""
from __future__ import annotations

import copy
import datetime
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from . import export
from .engine import Actor, write_log_entry
from .errors import OntoError, SchemaError
from .lint import Finding, lint
from .schema import Schema, load_schema, merge_patch, parse_schema, schema_hash
from .store import Store, locked
from .validate import validate


@dataclass
class GovResult:
    status: str  # "committed" | "staged" | "rejected"
    messages: list = field(default_factory=list)
    findings: list = field(default_factory=list)  # list[Finding]
    proposal_id: Optional[str] = None
    version: Optional[int] = None


# --- propose -----------------------------------------------------------


def propose(store: Store, patch: dict, actor: Actor, *, why: str = "") -> GovResult:
    dir = Path(store.dir)
    common_schema = store.schema.common

    with locked(dir):
        old_doc = _read_ontology_doc(dir)
        schema_patch = {k: v for k, v in patch.items() if k != "questions"}
        new_doc = merge_patch(old_doc, schema_patch)
        try:
            candidate = parse_schema(new_doc, common=common_schema, source=str(dir / "ontology.json"))
        except SchemaError as e:
            return GovResult("rejected", list(e.problems), [], None, None)

        entity_store = Store(dir, candidate, common=store.common)
        findings = lint(candidate, entity_store.doc)
        error_findings = [f for f in findings if f.level == "error"]
        if error_findings:
            return GovResult("rejected", [f.message for f in error_findings], findings, None, None)

        violations = validate(entity_store)
        if violations:
            return GovResult("rejected", [v.message for v in violations], findings, None, None)

        if _needs_approval(patch, candidate):
            proposal_id = _next_schema_proposal_id(dir)
            _write_schema_proposal(dir, proposal_id, patch=patch, actor=actor, why=why, findings=findings)
            return GovResult("staged", [], findings, proposal_id, None)

        version, _final = _commit(
            dir, old_doc=old_doc, new_doc=new_doc, patch=patch, actor=actor, why=why,
            common_schema=common_schema, proposal_id=None,
        )
        return GovResult("committed", [], findings, None, version)


def _needs_approval(patch: dict, candidate: Schema) -> bool:
    # 「実行者が人なら承認を省く」はやらない（疑似端末や session 変数の偽装で素通りするため）。
    # 誰が叩いたかに関係なく governance だけで決める。反映は auto のときか、approve_schema を通ったときだけ。
    if "governance" in patch:
        return True
    return candidate.governance.get("schema_changes", "stage") != "auto"


# --- approve_schema ------------------------------------------------------


def approve_schema(
    onto_dir: Path, common_dir: Optional[Path], proposal_id: str, approver: Actor
) -> GovResult:
    if approver.kind != "human":
        raise OntoError("承認は人だけができる")
    onto_dir = Path(onto_dir)
    common_dir = Path(common_dir) if common_dir is not None else None

    with locked(onto_dir):
        prop = _read_schema_proposal(onto_dir, proposal_id)
        if prop.get("status") != "open":
            raise OntoError(f"実行待ち '{proposal_id}' は open ではない（今 {prop.get('status')}）")

        patch = prop.get("patch") or {}
        why = prop.get("why") or ""
        actor_raw = prop.get("actor") or {}
        original_actor = Actor(actor_raw.get("kind", "agent"), actor_raw.get("name", ""), actor_raw.get("session"))

        common_schema = load_schema(common_dir) if common_dir is not None else None
        old_doc = _read_ontology_doc(onto_dir)
        schema_patch = {k: v for k, v in patch.items() if k != "questions"}
        new_doc = merge_patch(old_doc, schema_patch)
        try:
            candidate = parse_schema(new_doc, common=common_schema, source=str(onto_dir / "ontology.json"))
        except SchemaError as e:
            return GovResult("rejected", list(e.problems), [], proposal_id, None)

        common_store = Store(common_dir, common_schema) if common_dir is not None else None
        entity_store = Store(onto_dir, candidate, common=common_store)
        findings = lint(candidate, entity_store.doc)
        error_findings = [f for f in findings if f.level == "error"]
        if error_findings:
            return GovResult("rejected", [f.message for f in error_findings], findings, proposal_id, None)

        violations = validate(entity_store)
        if violations:
            return GovResult("rejected", [v.message for v in violations], findings, proposal_id, None)

        version, _final = _commit(
            onto_dir, old_doc=old_doc, new_doc=new_doc, patch=patch, actor=original_actor, why=why,
            common_schema=common_schema, proposal_id=proposal_id, approved_by=approver,
        )

        prop["status"] = "approved"
        prop["decided_by"] = approver.as_env()
        prop["decided_at"] = _now_iso()
        _write_schema_proposal_doc(onto_dir, proposal_id, prop)

        return GovResult("committed", [], findings, proposal_id, version)


# --- 反映（原子的な書き換え・index.md・questions.json・記録） -----------------


def _commit(
    dir: Path, *, old_doc: dict, new_doc: dict, patch: dict, actor: Actor, why: str,
    common_schema: Optional[Schema], proposal_id: Optional[str], approved_by: Optional[Actor] = None,
) -> "tuple[int, Schema]":
    dir = Path(dir)
    old_version = old_doc.get("version", 0)
    old_hash = schema_hash(old_doc)
    version = int(old_version) + 1

    final_doc = copy.deepcopy(new_doc)
    final_doc["version"] = version

    path = dir / "ontology.json"
    tmp = dir / f".ontology.json.tmp{os.getpid()}"
    tmp.write_text(json.dumps(final_doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)

    final_schema = parse_schema(final_doc, common=common_schema, source=str(path))

    write_index_md(dir, final_schema)

    if "questions" in patch:
        _merge_questions(dir, patch["questions"])

    entry = {
        "ts": _now_iso(), "kind": "schema", "action": None, "actor": actor.as_env(),
        "params": {}, "status": "committed", "messages": [], "patch": patch,
        "proposal": proposal_id, "why": why, "task": None, "refs": [],
        "schema_before": {"version": old_version, "hash": old_hash},
        "schema_after": {"version": version, "hash": final_schema.hash},
        "approved_by": approved_by.as_env() if approved_by is not None else None,
    }
    write_log_entry(dir, entry)
    return version, final_schema


def _merge_questions(dir: Path, questions_patch) -> None:
    path = Path(dir) / "questions.json"
    doc = {}
    if path.exists():
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            doc = {}
    merged = merge_patch(doc, questions_patch) if isinstance(questions_patch, dict) else questions_patch
    path.write_text(json.dumps(merged, sort_keys=True, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def write_index_md(dir: Path, schema_obj: Schema) -> None:
    """index.md を作り直す（`init` と `_commit` の両方から使う）。件数は載せない（`onto types` / `query` で見る）。"""
    body = export.to_markdown(schema_obj)
    summary = _build_summary(schema_obj)
    updated = datetime.date.today().isoformat()
    text = f'---\ntitle: "オントロジー"\nsummary: "{summary}"\nupdated: "{updated}"\n---\n\n{body}'
    (Path(dir) / "index.md").write_text(text, encoding="utf-8")


def _build_summary(schema_obj: Schema) -> str:
    # 案件の要約には案件で定義したものだけを数える（共通の分は共通の index.md に載る。起動時の注入に同じ名前を 2 度入れない）
    own = lambda d: {k: v for k, v in d.items() if schema_obj.scope == "common" or v.origin == "project"}  # noqa: E731
    types, links, actions = own(schema_obj.object_types), own(schema_obj.link_types), own(schema_obj.action_types)
    names = "・".join(sorted(actions))
    head = f"オントロジー: 型 {len(types)}・つながり {len(links)}・できること {len(actions)}（"
    tail = "）。読むのは scripts/ws onto query / show、変えるのは scripts/ws onto act だけ"
    if schema_obj.scope == "project":
        tail = "）。共通の型も使える。読むのは scripts/ws onto query / show、変えるのは scripts/ws onto act だけ"
    summary = (head + names + tail).replace('"', "'")
    if len(summary) > 200:
        budget = max(0, 200 - len(head) - len("…" + tail) - 1)
        summary = (head + names[:budget] + "…" + tail).replace('"', "'")
    return summary


# --- 読み書きの小道具 ---------------------------------------------------------


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat()


def _read_ontology_doc(dir: Path) -> dict:
    path = Path(dir) / "ontology.json"
    if not path.exists():
        raise OntoError(f"{path}: ontology.json が見つからない")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise OntoError(f"{path}: JSON として読めない（{e}）")


def _summarize_patch(patch: dict) -> list:
    lines = []
    for key, value in patch.items():
        if key == "questions":
            continue
        if key in ("object_types", "link_types", "action_types", "constants") and isinstance(value, dict):
            for name in value:
                lines.append(f"{key}.{name}")
        else:
            lines.append(key)
    return lines


def _next_schema_proposal_id(dir: Path) -> str:
    pdir = Path(dir) / "proposals"
    n = 1
    if pdir.exists():
        nums = []
        for f in pdir.glob("S-*.json"):
            try:
                nums.append(int(f.stem.split("-", 1)[1]))
            except (IndexError, ValueError):
                continue
        if nums:
            n = max(nums) + 1
    return f"S-{n:04d}"


def _write_schema_proposal(dir: Path, proposal_id: str, *, patch: dict, actor: Actor, why: str, findings: list) -> None:
    pdir = Path(dir) / "proposals"
    pdir.mkdir(parents=True, exist_ok=True)
    doc = {
        "id": proposal_id, "kind": "schema", "status": "open", "patch": patch,
        "summary": _summarize_patch(patch),
        "findings": [{"level": f.level, "code": f.code, "where": f.where, "message": f.message} for f in findings],
        "actor": actor.as_env(), "why": why, "created": _now_iso(),
        "decided_by": None, "decided_at": None, "reason": None,
    }
    _write_schema_proposal_doc(dir, proposal_id, doc)


def _read_schema_proposal(dir: Path, proposal_id: str) -> dict:
    path = Path(dir) / "proposals" / f"{proposal_id}.json"
    if not path.exists():
        raise OntoError(f"実行待ち '{proposal_id}' が見つからない")
    return json.loads(path.read_text(encoding="utf-8"))


def _write_schema_proposal_doc(dir: Path, proposal_id: str, doc: dict) -> None:
    path = Path(dir) / "proposals" / f"{proposal_id}.json"
    path.write_text(json.dumps(doc, sort_keys=True, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
