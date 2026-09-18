"""wsonto — アクションの実行・実行待ち・承認・記録。

取り決めは `scripts/wsonto/README.md` の「engine.py」を参照。実行時は標準
ライブラリだけで動く（Python 3.9 以上）。
"""
from __future__ import annotations

import copy
import datetime
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .errors import ExprError, OntoError, StoreError
from .expr import render
from .store import ObjView, Store, locked
from .validate import Violation, validate

_MANY_SPLIT_RE = re.compile(r"\s*,\s*")


# --- 公開の dataclass -------------------------------------------------------


@dataclass
class Actor:
    kind: str  # "agent" | "human"
    name: str
    session: Optional[str] = None

    def as_env(self) -> dict:
        return {"kind": self.kind, "name": self.name, "session": self.session}


@dataclass
class Result:
    status: str  # "committed" | "staged" | "rejected"
    action: str
    params: dict
    messages: list = field(default_factory=list)
    violations: list = field(default_factory=list)
    edits: list = field(default_factory=list)
    proposal_id: Optional[str] = None
    returned: Optional[str] = None
    next: str = ""


# --- act ---------------------------------------------------------------


def act(
    store: Store,
    action: str,
    raw_params: dict,
    actor: Actor,
    *,
    why: str = "",
    dry_run: bool = False,
    today: Optional[datetime.date] = None,
    task: Optional[str] = None,
    refs: Optional[list] = None,
) -> Result:
    if dry_run:
        snap = store.snapshot()
        return _run_action(
            store, snap, action, raw_params, actor,
            why=why, today=today, task=task, refs=refs, dry_run=True,
        )
    with locked(store.dir):
        store.reload()
        snap = store.snapshot()
        return _run_action(
            store, snap, action, raw_params, actor,
            why=why, today=today, task=task, refs=refs, dry_run=False,
        )


def _new_violations(before: list, after: list) -> list:
    """`after` にあって `before` には無かった違反だけを返す。同一性は (ref, path, code)。

    実行前から在る無関係な違反（人が手で入れたものなど）では止めない。
    """
    remaining = list(before)
    new: list = []
    for v in after:
        key = (v.ref, v.path, v.code)
        for i, b in enumerate(remaining):
            if (b.ref, b.path, b.code) == key:
                del remaining[i]
                break
        else:
            new.append(v)
    return new


def _run_action(
    store: Store, snap: Store, action_name: str, raw_params: dict, actor: Actor,
    *, why: str, today: Optional[datetime.date], task: Optional[str],
    refs: Optional[list], dry_run: bool,
) -> Result:
    schema_obj = snap.schema
    at = schema_obj.action_types.get(action_name)
    if at is None:
        raise OntoError(f"アクション '{action_name}' は定義に無い")
    store_hash_before = store.file_hash()

    def rejected(messages: list, violations: Optional[list] = None, edits: Optional[list] = None) -> Result:
        return _finish(
            store, action_name=action_name, raw_params=raw_params, status="rejected",
            messages=messages, violations=violations or [], edits=edits or [],
            actor=actor, why=why, task=task, refs=refs, schema_obj=schema_obj,
            store_hash_before=store_hash_before, store_hash_after=store_hash_before,
            proposal_id=None, returned=None, next_text="", dry_run=dry_run, kind="act",
        )

    try:
        # --- ① 引数を直す ---
        params, problems = _coerce_params(at, raw_params, snap)
        if problems:
            return rejected(problems)

        env: dict = dict(params)
        env.update(schema_obj.constants)
        env["actor"] = actor.as_env()
        env["__today__"] = today

        # --- ② 前提条件 ---
        crit_messages = []
        for c in at.criteria:
            try:
                ok = bool(c.when.eval(env)) if c.when is not None else True
            except ExprError:
                ok = False
            if not ok:
                crit_messages.append(render(c.message, env))
        if crit_messages:
            return rejected(crit_messages)

        # --- ③ ルールを snap に適用 ---
        edits: list = []
        touched: set = set()
        try:
            _apply_rules(at.rules, snap, env, touched, edits)
        except OntoError as e:
            return rejected([str(e)], edits=edits)

        # --- ④ 検証（写し全体。実行前の store 全体の validate には無かった違反だけを見る） ---
        before_violations = validate(store)
        after_violations = validate(snap)
        new_violations = _new_violations(before_violations, after_violations)
        if new_violations:
            return rejected([v.message for v in new_violations], violations=new_violations, edits=edits)

        # --- ⑤ 承認の要否（人が直接 act しても要る。承認そのものは人だけができる） ---
        approval_role = at.approval.role if at.approval else None
        mode = at.approval.mode if at.approval is not None else "stage"
        if mode == "auto":
            needs_approval = False
        elif mode == "stage":
            needs_approval = True
        else:  # stage_if
            when = at.approval.when if at.approval is not None else None
            needs_approval = bool(when.eval(env)) if when is not None else True

        returned_ref = None
        if at.returns:
            obj = env.get(at.returns)
            if isinstance(obj, ObjView):
                returned_ref = obj.ref
        next_text = render(at.next, env) if at.next else ""
    except OntoError:
        raise
    except Exception as e:  # noqa: BLE001 -- アクションの定義か実体が想定外の形でも記録を残して拒否する
        return rejected([f"内部エラー: {type(e).__name__}: {e}（アクションの定義か実体が想定外の形）"])

    # --- ⑥ 反映 or 実行待ち ---
    if needs_approval:
        proposal_id = _next_proposal_id(store.dir)
        msg = f"承認が要る（役割: {approval_role}）" if approval_role else "承認が要る"
        if not dry_run:
            _write_proposal(
                store.dir, proposal_id, action_name=action_name, raw_params=raw_params,
                actor=actor, why=why, approval_role=approval_role, task=task, refs=refs,
                edits=edits, next_text=next_text,
            )
        return _finish(
            store, action_name=action_name, raw_params=raw_params, status="staged",
            messages=[msg], violations=[], edits=edits, actor=actor, why=why, task=task,
            refs=refs, schema_obj=schema_obj, store_hash_before=store_hash_before,
            store_hash_after=store_hash_before, proposal_id=proposal_id,
            returned=returned_ref, next_text=next_text, dry_run=dry_run, kind="act",
        )

    if dry_run:
        return _finish(
            store, action_name=action_name, raw_params=raw_params, status="committed",
            messages=[], violations=[], edits=edits, actor=actor, why=why, task=task,
            refs=refs, schema_obj=schema_obj, store_hash_before=store_hash_before,
            store_hash_after=store_hash_before, proposal_id=None, returned=returned_ref,
            next_text=next_text, dry_run=True, kind="act",
        )

    new_hash = snap.commit(lock=False)
    store.reload()
    return _finish(
        store, action_name=action_name, raw_params=raw_params, status="committed",
        messages=[], violations=[], edits=edits, actor=actor, why=why, task=task,
        refs=refs, schema_obj=schema_obj, store_hash_before=store_hash_before,
        store_hash_after=new_hash, proposal_id=None, returned=returned_ref,
        next_text=next_text, dry_run=False, kind="act",
    )


# --- 引数の型直し -----------------------------------------------------------


def _coerce_params(at, raw_params: dict, snap: Store) -> "tuple[dict, list]":
    problems: list = []
    known = set(at.parameters)
    for key in raw_params:
        if key not in known:
            problems.append(f"引数 '{key}' は知らない引数です")

    parsed: dict = {}
    for name, p in at.parameters.items():
        present = name in raw_params
        raw = raw_params.get(name) if present else None
        if not present or raw is None:
            if p.required:
                problems.append(f"引数 '{name}' は必須です")
            else:
                parsed[name] = [] if p.many else None
            continue
        value, errs = _coerce_one(p, raw, snap, name)
        if errs:
            problems.extend(errs)
        else:
            parsed[name] = value
    return parsed, problems


def _coerce_one(p, raw: Any, snap: Store, name: str) -> "tuple[Any, list]":
    problems: list = []
    if p.object_type:
        if p.many:
            values = []
            for item in _split_many(raw):
                obj, err = _resolve_ref(item, p.object_type, snap)
                if err:
                    problems.append(f"引数 '{name}': {err}")
                else:
                    values.append(obj)
            return values, problems
        obj, err = _resolve_ref(raw, p.object_type, snap)
        if err:
            problems.append(f"引数 '{name}': {err}")
            return None, problems
        return obj, problems

    if p.many:
        values = []
        for item in _split_many(raw):
            v, err = _coerce_scalar(p.type, p.values, item)
            if err:
                problems.append(f"引数 '{name}': {err}")
                continue
            berr = _check_bounds(p, v)
            if berr:
                problems.append(f"引数 '{name}': {berr}")
                continue
            values.append(v)
        return values, problems

    v, err = _coerce_scalar(p.type, p.values, raw)
    if err:
        problems.append(f"引数 '{name}': {err}")
        return None, problems
    berr = _check_bounds(p, v)
    if berr:
        problems.append(f"引数 '{name}': {berr}")
        return None, problems
    return v, problems


def _split_many(raw: Any) -> list:
    if isinstance(raw, list):
        return list(raw)
    if isinstance(raw, str):
        s = raw.strip()
        if not s:
            return []
        return [piece.strip() for piece in _MANY_SPLIT_RE.split(s)]
    return [raw]


def _coerce_scalar(ptype: Optional[str], values: Optional[list], raw: Any) -> "tuple[Any, Optional[str]]":
    try:
        if ptype == "int":
            if isinstance(raw, bool):
                return None, "int である必要がある"
            if isinstance(raw, int):
                return raw, None
            if isinstance(raw, str):
                return int(raw.strip()), None
            return None, "int である必要がある"
        if ptype == "number":
            if isinstance(raw, bool):
                return None, "number である必要がある"
            if isinstance(raw, (int, float)):
                return raw, None
            if isinstance(raw, str):
                s = raw.strip()
                return (float(s) if any(c in s for c in ".eE") else int(s)), None
            return None, "number である必要がある"
        if ptype == "bool":
            if isinstance(raw, bool):
                return raw, None
            if isinstance(raw, str):
                s = raw.strip().lower()
                if s in ("true", "1", "yes"):
                    return True, None
                if s in ("false", "0", "no"):
                    return False, None
            return None, "bool として解釈できない（true/false/1/0/yes/no）"
        if ptype == "date":
            if isinstance(raw, datetime.datetime):
                return None, "date として解釈できない"
            if isinstance(raw, datetime.date):
                return raw, None
            if isinstance(raw, str):
                return datetime.date.fromisoformat(raw.strip()), None
            return None, "date（YYYY-MM-DD）として解釈できない"
        if ptype == "datetime":
            if isinstance(raw, datetime.datetime):
                return raw, None
            if isinstance(raw, str):
                s = raw.strip()
                s2 = s[:-1] + "+00:00" if s.endswith("Z") else s
                return datetime.datetime.fromisoformat(s2), None
            return None, "datetime として解釈できない"
        if ptype == "enum":
            if raw not in (values or []):
                return None, f"値 {raw!r} は許された値にない（{values}）"
            return raw, None
        if ptype in ("string", "text"):
            if isinstance(raw, str):
                return raw, None
            return None, "文字列である必要がある"
    except (ValueError, TypeError) as e:
        return None, f"{ptype} として解釈できない（{e}）"
    return None, f"知らない型 {ptype!r}"


def _check_bounds(p, v: Any) -> Optional[str]:
    if p.min is not None:
        try:
            under = v < p.min
        except TypeError:
            under = False
        if under:
            return f"{p.min} 以上である必要がある（今 {v!r}）"
    if p.max is not None:
        try:
            over = v > p.max
        except TypeError:
            over = False
        if over:
            return f"{p.max} 以下である必要がある（今 {v!r}）"
    if p.pattern is not None and isinstance(v, str):
        if re.search(p.pattern, v) is None:
            return f"パターン '{p.pattern}' に合わない"
    return None


def _resolve_ref(raw: Any, expected_type: str, snap: Store) -> "tuple[Optional[ObjView], Optional[str]]":
    if not isinstance(raw, str) or not raw.strip():
        return None, "id が空です"
    raw = raw.strip()
    if ":" in raw:
        t, _, id_ = raw.partition(":")
    else:
        t, id_ = expected_type, raw
    try:
        obj = snap.find(t, id_)
    except StoreError as e:
        return None, str(e)
    if obj is None:
        return None, f"'{raw}' に一致する実体が見つからない（{expected_type}）"
    if not snap.schema.is_a(obj.type, expected_type):
        return None, f"'{raw}' の型 '{obj.type}' は '{expected_type}' ではない"
    return obj, None


# --- ルールの適用 -----------------------------------------------------------


def _apply_rules(rules: list, snap: Store, env: dict, touched: set, edits: list) -> None:
    for rule in rules:
        if_expr = rule.get("if")
        if if_expr is not None and not if_expr.eval(env):
            continue
        if "create" in rule:
            _apply_create(rule, snap, env, touched, edits)
        elif "modify" in rule:
            _apply_modify(rule, snap, env, touched, edits)
        elif "delete" in rule:
            _apply_delete(rule, snap, env, touched, edits)


def _apply_create(rule: dict, snap: Store, env: dict, touched: set, edits: list) -> None:
    ctype = rule["create"]
    as_name = rule["as"]
    id_tmpl = rule.get("id")
    seq = snap.next_seq(ctype)
    if id_tmpl:
        id_env = dict(env)
        id_env["seq"] = seq
        new_id = render(id_tmpl, id_env)
    else:
        new_id = f"{ctype}-{seq}"
    ref = f"{ctype}:{new_id}"
    if snap.get(ref) is not None:
        raise OntoError(f"id '{new_id}' は '{ctype}' で既に使われている")

    props_schema = snap.schema.props(ctype)
    props_out: dict = {}
    for pname, expr in (rule.get("set") or {}).items():
        value = expr.eval(env) if expr is not None else None
        if value is None:
            continue
        props_out[pname] = _to_storage(props_schema.get(pname), value)

    links_out: dict = {}
    for lname, expr in (rule.get("link") or {}).items():
        value = expr.eval(env) if expr is not None else None
        refs_list = _link_value_to_refs(value)
        if refs_list:
            links_out[lname] = refs_list

    snap.put(ctype, new_id, props_out, links_out)
    touched.add(ref)
    edits.append({"op": "create", "ref": ref, "before": None, "after": copy.deepcopy(snap.doc[ctype][new_id])})
    env[as_name] = snap.get(ref)


def _is_foreign(snap: Store, type_name: str, id_: str) -> bool:
    """target が自分の store に無い（共通の store から引いた）実体かどうか。"""
    entities = snap.doc.get(type_name)
    return not (entities and id_ in entities)


def _apply_modify(rule: dict, snap: Store, env: dict, touched: set, edits: list) -> None:
    target_name = rule["modify"]
    target = env.get(target_name)
    if target is None:
        return
    if _is_foreign(snap, target.type, target.id):
        raise OntoError(f"共通（自社）の実体 '{target.ref}' は、案件のアクションからは変えられない。共通のアクションを使う")
    ref = target.ref
    rec = snap.doc[target.type][target.id]
    before = copy.deepcopy(rec)

    props_schema = snap.schema.props(target.type)
    links_schema = snap.schema.links_from(target.type)
    for pname, expr in (rule.get("set") or {}).items():
        value = expr.eval(env) if expr is not None else None
        if value is None:
            rec.pop(pname, None)
        else:
            rec[pname] = _to_storage(props_schema.get(pname), value)

    rec_links = rec.setdefault("_links", {})
    for lname, expr in (rule.get("link") or {}).items():
        value = expr.eval(env) if expr is not None else None
        refs_list = _link_value_to_refs(value)
        if not refs_list:
            continue
        lt = links_schema.get(lname)
        if lt is not None and lt.max == 1:
            rec_links[lname] = [refs_list[0]]
        else:
            existing = rec_links.setdefault(lname, [])
            for r in refs_list:
                if r not in existing:
                    existing.append(r)

    for lname, expr in (rule.get("unlink") or {}).items():
        value = expr.eval(env) if expr is not None else None
        refs_list = _link_value_to_refs(value)
        if not refs_list:
            continue
        existing = rec_links.get(lname)
        if existing:
            remaining = [r for r in existing if r not in refs_list]
            if remaining:
                rec_links[lname] = remaining
            else:
                del rec_links[lname]

    if not rec_links:
        rec.pop("_links", None)

    snap._rev_index = None
    after = copy.deepcopy(snap.doc[target.type][target.id])
    touched.add(ref)
    edits.append({"op": "modify", "ref": ref, "before": before, "after": after})
    env[target_name] = snap.get(ref)


def _apply_delete(rule: dict, snap: Store, env: dict, touched: set, edits: list) -> None:
    target_name = rule["delete"]
    target = env.get(target_name)
    if target is None:
        return
    if _is_foreign(snap, target.type, target.id):
        raise OntoError(f"共通（自社）の実体 '{target.ref}' は、案件のアクションからは変えられない。共通のアクションを使う")
    ref = target.ref
    before = copy.deepcopy(snap.doc[target.type][target.id])
    snap.remove(ref)
    touched.add(ref)
    edits.append({"op": "delete", "ref": ref, "before": before, "after": None})


def _to_storage(prop, value: Any) -> Any:
    if prop is None or value is None:
        return value
    if prop.type == "date" and isinstance(value, datetime.date) and not isinstance(value, datetime.datetime):
        return value.isoformat()
    if prop.type == "datetime" and isinstance(value, datetime.datetime):
        return value.isoformat()
    return value


def _link_value_to_refs(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, ObjView):
        return [value.ref]
    if isinstance(value, list):
        return [v.ref for v in value if isinstance(v, ObjView)]
    return []


# --- 記録・実行待ちの読み書き ------------------------------------------------


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat()


def _finish(
    store: Store, *, action_name: str, raw_params: dict, status: str, messages: list,
    violations: list, edits: list, actor: Actor, why: str, task: Optional[str],
    refs: Optional[list], schema_obj, store_hash_before: str, store_hash_after: str,
    proposal_id: Optional[str], returned: Optional[str], next_text: str, dry_run: bool,
    kind: str, extra: Optional[dict] = None,
) -> Result:
    if not dry_run:
        entry = {
            "ts": _now_iso(),
            "kind": kind,
            "action": action_name,
            "actor": actor.as_env(),
            "params": raw_params,
            "status": status,
            "messages": messages,
            "edits": edits,
            "proposal": proposal_id,
            "why": why,
            "task": task,
            "refs": refs or [],
            "schema": {"name": schema_obj.name, "version": schema_obj.version, "hash": schema_obj.hash},
            "store_hash_before": store_hash_before,
            "store_hash_after": store_hash_after,
        }
        if extra:
            entry.update(extra)
        _append_log(store.dir, entry)
    return Result(
        status=status, action=action_name, params=raw_params, messages=messages,
        violations=violations, edits=edits, proposal_id=proposal_id, returned=returned, next=next_text,
    )


def _append_log(dir: Path, entry: dict) -> None:
    path = Path(dir) / "log.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def write_log_entry(dir: Path, entry: dict) -> None:
    """`govern.py` が記録 1 行を書くための薄い公開ラッパー（中身は `_append_log` と同じ）。"""
    _append_log(dir, entry)


def _next_proposal_id(dir: Path) -> str:
    pdir = Path(dir) / "proposals"
    n = 1
    if pdir.exists():
        nums = []
        for f in pdir.glob("P-*.json"):
            try:
                nums.append(int(f.stem.split("-", 1)[1]))
            except (IndexError, ValueError):
                continue
        if nums:
            n = max(nums) + 1
    return f"P-{n:04d}"


def _write_proposal(
    dir: Path, proposal_id: str, *, action_name: str, raw_params: dict, actor: Actor, why: str,
    approval_role: Optional[str], task: Optional[str], refs: Optional[list], edits: list, next_text: str,
) -> None:
    pdir = Path(dir) / "proposals"
    pdir.mkdir(parents=True, exist_ok=True)
    doc = {
        "id": proposal_id, "kind": "action", "status": "open", "action": action_name,
        "params": raw_params, "actor": actor.as_env(), "why": why, "role": approval_role,
        "created": _now_iso(), "task": task, "refs": refs or [],
        "preview": {"edits": edits, "next": next_text},
        "decided_by": None, "decided_at": None, "reason": None,
    }
    text = json.dumps(doc, sort_keys=True, indent=1, ensure_ascii=False) + "\n"
    (pdir / f"{proposal_id}.json").write_text(text, encoding="utf-8")


def _read_proposal(dir: Path, proposal_id: str) -> dict:
    path = Path(dir) / "proposals" / f"{proposal_id}.json"
    if not path.exists():
        raise OntoError(f"実行待ち '{proposal_id}' が見つからない")
    return json.loads(path.read_text(encoding="utf-8"))


def _write_proposal_doc(dir: Path, proposal_id: str, doc: dict) -> None:
    path = Path(dir) / "proposals" / f"{proposal_id}.json"
    path.write_text(json.dumps(doc, sort_keys=True, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


# --- approve / reject / proposals -------------------------------------------


def approve(store: Store, proposal_id: str, approver: Actor, *, today: Optional[datetime.date] = None) -> Result:
    if approver.kind != "human":
        raise OntoError("承認は人だけができる")
    with locked(store.dir):
        store.reload()
        prop = _read_proposal(store.dir, proposal_id)
        if prop.get("status") != "open":
            raise OntoError(f"実行待ち '{proposal_id}' は open ではない（今 {prop.get('status')}）")

        actor_raw = prop.get("actor") or {}
        original_actor = Actor(actor_raw.get("kind", "agent"), actor_raw.get("name", ""), actor_raw.get("session"))
        action_name = prop.get("action")
        raw_params = prop.get("params") or {}
        why = prop.get("why") or ""
        task = prop.get("task")
        refs = prop.get("refs") or []

        snap = store.snapshot()
        schema_obj = snap.schema
        store_hash_before = store.file_hash()
        at = schema_obj.action_types.get(action_name)

        def rejected(messages: list, violations: Optional[list] = None, edits: Optional[list] = None) -> Result:
            return _finish(
                store, action_name=action_name, raw_params=raw_params, status="rejected",
                messages=messages, violations=violations or [], edits=edits or [],
                actor=original_actor, why=why, task=task, refs=refs, schema_obj=schema_obj,
                store_hash_before=store_hash_before, store_hash_after=store_hash_before,
                proposal_id=proposal_id, returned=None, next_text="", dry_run=False, kind="approve",
            )

        if at is None:
            return rejected([f"アクション '{action_name}' は定義に無い"])

        try:
            params, problems = _coerce_params(at, raw_params, snap)
            if problems:
                return rejected(problems)

            env: dict = dict(params)
            env.update(schema_obj.constants)
            env["actor"] = original_actor.as_env()
            env["__today__"] = today

            crit_messages = []
            for c in at.criteria:
                try:
                    ok = bool(c.when.eval(env)) if c.when is not None else True
                except ExprError:
                    ok = False
                if not ok:
                    crit_messages.append(render(c.message, env))
            if crit_messages:
                return rejected(crit_messages)

            edits: list = []
            touched: set = set()
            try:
                _apply_rules(at.rules, snap, env, touched, edits)
            except OntoError as e:
                return rejected([str(e)], edits=edits)

            before_violations = validate(store)
            after_violations = validate(snap)
            new_violations = _new_violations(before_violations, after_violations)
            if new_violations:
                return rejected([v.message for v in new_violations], violations=new_violations, edits=edits)

            returned_ref = None
            if at.returns:
                obj = env.get(at.returns)
                if isinstance(obj, ObjView):
                    returned_ref = obj.ref
            next_text = render(at.next, env) if at.next else ""
        except OntoError:
            raise
        except Exception as e:  # noqa: BLE001 -- アクションの定義か実体が想定外の形でも記録を残して拒否する
            return rejected([f"内部エラー: {type(e).__name__}: {e}（アクションの定義か実体が想定外の形）"])

        new_hash = snap.commit(lock=False)
        store.reload()

        prop["status"] = "approved"
        prop["decided_by"] = approver.as_env()
        prop["decided_at"] = _now_iso()
        _write_proposal_doc(store.dir, proposal_id, prop)

        return _finish(
            store, action_name=action_name, raw_params=raw_params, status="committed",
            messages=[], violations=[], edits=edits, actor=original_actor, why=why, task=task,
            refs=refs, schema_obj=schema_obj, store_hash_before=store_hash_before,
            store_hash_after=new_hash, proposal_id=proposal_id, returned=returned_ref,
            next_text=next_text, dry_run=False, kind="approve",
            extra={"approved_by": approver.as_env()},
        )


def reject(store: Store, proposal_id: str, approver: Actor, reason: str) -> None:
    if approver.kind != "human":
        raise OntoError("承認は人だけができる")
    with locked(store.dir):
        store.reload()
        prop = _read_proposal(store.dir, proposal_id)
        if prop.get("status") != "open":
            raise OntoError(f"実行待ち '{proposal_id}' は open ではない（今 {prop.get('status')}）")

        prop["status"] = "rejected"
        prop["decided_by"] = approver.as_env()
        prop["decided_at"] = _now_iso()
        prop["reason"] = reason
        _write_proposal_doc(store.dir, proposal_id, prop)

        actor_raw = prop.get("actor") or {}
        original_actor = Actor(actor_raw.get("kind", "agent"), actor_raw.get("name", ""), actor_raw.get("session"))
        schema_obj = store.schema
        store_hash = store.file_hash()
        _append_log(store.dir, {
            "ts": _now_iso(), "kind": "reject", "action": prop.get("action"),
            "actor": original_actor.as_env(), "params": prop.get("params") or {}, "status": "rejected",
            "messages": [reason], "edits": [], "proposal": proposal_id, "why": prop.get("why") or "",
            "task": prop.get("task"), "refs": prop.get("refs") or [],
            "schema": {"name": schema_obj.name, "version": schema_obj.version, "hash": schema_obj.hash},
            "store_hash_before": store_hash, "store_hash_after": store_hash,
            "approved_by": approver.as_env(),
        })


def proposals(store: Store, status: Optional[str] = "open") -> list:
    pdir = Path(store.dir) / "proposals"
    if not pdir.exists():
        return []
    out = []
    for f in sorted(pdir.glob("P-*.json"), key=lambda p: p.stem):
        try:
            doc = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if status is None or doc.get("status") == status:
            out.append(doc)
    return out


# --- 記録の読み出し・検証 ----------------------------------------------------


def _read_log_lines(dir: Path) -> "tuple[list, list]":
    """log.jsonl を読み、読めた行の dict と、JSON として読めなかった行番号（1 始まり）を返す。

    壊れた行（git のマージの衝突マーカーなど）が 1 つあっても、他の行は読めた分だけ返す。
    """
    path = Path(dir) / "log.jsonl"
    if not path.exists():
        return [], []
    entries: list = []
    bad_lines: list = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            bad_lines.append(i)
    return entries, bad_lines


def read_log(
    dir: Path, action: Optional[str] = None, object: Optional[str] = None,
    since: Optional[str] = None, limit: Optional[int] = None,
) -> list:
    entries, _bad_lines = _read_log_lines(dir)
    out = []
    for entry in entries:
        if action is not None and entry.get("action") != action:
            continue
        if object is not None and not _entry_mentions(entry, object):
            continue
        if since is not None and str(entry.get("ts", "")) < str(since):
            continue
        out.append(entry)
    if limit is not None:
        out = out[:limit]
    return out


def _entry_mentions(entry: dict, ref: str) -> bool:
    _type_name, _, id_ = ref.partition(":")
    for e in entry.get("edits") or []:
        if e.get("ref") == ref:
            return True
    for v in (entry.get("params") or {}).values():
        if isinstance(v, str):
            if v == ref or v == id_:
                return True
            if id_ in [s.strip() for s in v.split(",")]:
                return True
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, str) and (item == ref or item == id_):
                    return True
    return False


def verify_chain(store: Store) -> list:
    entries, bad_lines = _read_log_lines(store.dir)
    issues: list = [
        f"log.jsonl の {n} 行目が JSON として読めない（マージの衝突の跡なら手で直す）"
        for n in bad_lines
    ]
    last_hash = None
    for entry in entries:
        h = entry.get("store_hash_after")
        if h:
            last_hash = h
    if last_hash is not None:
        current = store.file_hash()
        if current != last_hash:
            issues.append(
                "objects.json が記録に無い形で書き換えられている。人が直したなら "
                f"scripts/ws onto adopt で取り込む（記録の store_hash_after={last_hash!r}、今の file_hash={current!r}）"
            )
    return issues


def adopt(store: Store, actor: Actor, note: str) -> None:
    if actor.kind != "human":
        raise OntoError("記録の取り込みは人だけができる")
    with locked(store.dir):
        store.reload()
        schema_obj = store.schema
        current = store.file_hash()
        _append_log(store.dir, {
            "ts": _now_iso(), "kind": "adopt", "action": None, "actor": actor.as_env(),
            "params": {}, "status": "committed", "messages": [note] if note else [],
            "edits": [], "proposal": None, "why": note or "", "task": None, "refs": [],
            "schema": {"name": schema_obj.name, "version": schema_obj.version, "hash": schema_obj.hash},
            "store_hash_before": current, "store_hash_after": current,
        })
