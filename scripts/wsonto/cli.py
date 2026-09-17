"""wsonto — `scripts/ws onto …` の入口。

取り決めは `scripts/wsonto/README.md` の「cli.py」を参照。実行時は標準
ライブラリだけで動く（Python 3.9 以上）。`scripts/ws` はここを import せず、
`onto` の後ろの引数をまるごと `main(argv, ctx)` に渡すだけ（起動を遅くしない）。
出力はエージェントが読む前提で詰める（見出し・飾りの線は出さない）。
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from . import engine, evals, export, govern
from . import lint as lint_mod
from . import query as query_mod
from .errors import OntoError
from .schema import Schema, load_schema, parse_schema
from .store import Store
from .validate import validate

_STATUS_CODE = {"committed": 0, "staged": 3, "rejected": 4}
_HUMAN_ONLY_MSG = "承認・却下・取り込みは人だけができる（エージェントからは実行できない）。人に「承認 P-0001」と送ってもらう"
_PROMPT_RE = re.compile(r"^\s*(承認|却下|approve|reject)\s+((?:[\w-]+/)?[PS]-\d{4})(?:\s+(.+))?$")
# eval/doctor が答えたい質問を評価するときの実行者は固定（誰が叩いても結果が変わらないように。
# ここでの actor は評価専用で、記録には残らない＝engine.Actor の他の使いどころとは独立）
_EVAL_ACTOR = engine.Actor("agent", "eval")


@dataclass
class Ctx:
    root: Path
    current_project: Optional[str]
    current_task: Optional[str]
    session: Optional[str]
    is_tty: bool
    user: str


# --- 範囲・誰が実行したか ------------------------------------------------


def _common_dir(ctx: Ctx) -> Path:
    return Path(ctx.root) / "knowledges" / "ontology"


def _project_dir(ctx: Ctx, project: str) -> Path:
    return Path(ctx.root) / "projects" / project / "knowledges" / "ontology"


def _resolve_scope(ctx: Ctx, args) -> "tuple[Path, Optional[Path], str]":
    """戻り値: (対象の onto dir, その common dir（案件なら共通、共通自身なら None）, 表示名)"""
    if getattr(args, "common", False):
        return _common_dir(ctx), None, "common"
    project = getattr(args, "project", None)
    if project:
        return _project_dir(ctx, project), _common_dir(ctx), project
    if ctx.current_project:
        pdir = _project_dir(ctx, ctx.current_project)
        if (pdir / "ontology.json").exists():
            return pdir, _common_dir(ctx), ctx.current_project
    return _common_dir(ctx), None, "common"


def _load(dir_: Path, common_dir: Optional[Path]) -> "tuple[Schema, Store]":
    if not (Path(dir_) / "ontology.json").exists():
        raise OntoError(f"{dir_} にオントロジーが無い（scripts/ws onto init で作る）")
    sch = load_schema(Path(dir_), common_dir=common_dir)
    common_store = Store(common_dir, sch.common) if common_dir is not None else None
    st = Store(dir_, sch, common=common_store)
    return sch, st


def _actor_for(ctx: Ctx) -> engine.Actor:
    if ctx.session:
        name = "codex" if os.environ.get("CODEX_THREAD_ID") else "claude-code"
        return engine.Actor("agent", name, ctx.session)
    if ctx.is_tty:
        return engine.Actor("human", ctx.user)
    return engine.Actor("agent", "script")


def _is_agent(ctx: Ctx) -> bool:
    return ctx.session is not None


def _is_human_ctx(ctx: Ctx) -> bool:
    return ctx.session is None and ctx.is_tty


# --- 実行待ちの範囲をまたいだ検索（approve / reject / handle_prompt 共通）------


def _split_scope_id(id_arg: str) -> "tuple[Optional[str], str]":
    if "/" in id_arg:
        scope, _, bare = id_arg.rpartition("/")
        return scope, bare
    return None, id_arg


def _named_scope_dirs(ctx: Ctx, name: str) -> "list[tuple[Path, Optional[Path], str]]":
    if name == "common":
        return [(_common_dir(ctx), None, "common")]
    return [(_project_dir(ctx, name), _common_dir(ctx), name)]


def _all_scope_dirs(ctx: Ctx) -> "list[tuple[Path, Optional[Path], str]]":
    common_dir = _common_dir(ctx)
    seen = set()
    out = []
    if ctx.current_project:
        out.append((_project_dir(ctx, ctx.current_project), common_dir, ctx.current_project))
        seen.add(ctx.current_project)
    out.append((common_dir, None, "common"))
    seen.add("common")
    projects_root = Path(ctx.root) / "projects"
    if projects_root.exists():
        for p in sorted(projects_root.iterdir()):
            if not p.is_dir() or p.name in seen:
                continue
            out.append((p / "knowledges" / "ontology", common_dir, p.name))
    return out


def _find_proposal_dirs(ctx: Ctx, scope_name: Optional[str], proposal_id: str) -> "list[tuple[Path, Optional[Path], str]]":
    candidates = _named_scope_dirs(ctx, scope_name) if scope_name else _all_scope_dirs(ctx)
    hits = []
    for d, cd, name in candidates:
        path = d / "proposals" / f"{proposal_id}.json"
        if not path.exists():
            continue
        if scope_name:
            hits.append((d, cd, name))
            continue
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(doc, dict) and doc.get("status") == "open":
            hits.append((d, cd, name))
    return hits


# --- 表示 -----------------------------------------------------------------


def _result_to_dict(result: engine.Result) -> dict:
    return {
        "status": result.status, "action": result.action, "params": result.params,
        "messages": result.messages,
        "violations": [
            {"ref": v.ref, "path": v.path, "code": v.code, "message": v.message} for v in result.violations
        ],
        "edits": result.edits, "proposal_id": result.proposal_id, "returned": result.returned, "next": result.next,
    }


def _print_act_result(result: engine.Result, store: Store, ctx: Ctx, as_json: bool) -> int:
    if as_json:
        print(json.dumps(_result_to_dict(result), ensure_ascii=False))
        return _STATUS_CODE[result.status]
    lines = []
    if result.status == "committed":
        lines.append("反映")
    elif result.status == "staged":
        lines.append(f"実行待ち {result.proposal_id}（承認は人。「承認 {result.proposal_id}」と送る）")
    else:
        lines.append("拒否")
    lines.extend(result.messages)
    if result.status == "committed" and result.returned:
        obj = store.get(result.returned)
        if obj is not None:
            d = query_mod.show(store, result.returned, agent=_is_agent(ctx))
            lines.append(query_mod.format_show(d))
    if result.status == "staged":
        # 実行待ちのあいだ、実体はまだ無い。アクションの next（できた実体の値を使え、の類）を出すと、無い値を文書に書かせてしまう
        lines.append(f"次: まだ反映されていない。人に「承認 {result.proposal_id}」と送ってもらい、承認の結果が返ってから続ける。")
    elif result.next:
        lines.append(f"次: {result.next}")
    print("\n".join(lines))
    return _STATUS_CODE[result.status]


def _print_gov_result(result: govern.GovResult) -> int:
    lines = []
    if result.status == "committed":
        lines.append(f"反映 版 {result.version}")
    elif result.status == "staged":
        lines.append(f"実行待ち {result.proposal_id}（承認は人。「承認 {result.proposal_id}」と送る）")
    else:
        lines.append("拒否")
    lines.extend(result.messages)
    for f in result.findings:
        if f.level == "warn":
            lines.append(f"警告: [{f.code}] {f.message}")
    print("\n".join(lines))
    return _STATUS_CODE[result.status]


def _act_result_detail(st: Store, result: engine.Result) -> str:
    if not result.returned:
        return result.action
    obj = st.get(result.returned)
    if obj is None:
        return f"{result.action} → {result.returned}"
    ot = st.schema.object_types.get(obj.type)
    bits = []
    if ot and ot.summary:
        for p in ot.summary:
            v = obj.onto_get(p)
            if v is not None:
                bits.append(f"{p} {v}")
    tail = f"（{'・'.join(bits)}）" if bits else ""
    return f"{result.action} → {result.returned}{tail}"


# --- 各サブコマンド ---------------------------------------------------------


def _parse_kv(items: list) -> dict:
    out = {}
    for item in items:
        if "=" not in item:
            raise OntoError(f"引数は 名前=値 の形にしてください（'{item}'）")
        k, _, v = item.partition("=")
        out[k] = v
    return out


def _cmd_init(args, ctx: Ctx) -> int:
    dir_, common_dir, name = _resolve_scope(ctx, args)
    onto_path = dir_ / "ontology.json"
    if onto_path.exists():
        print("既にある（何もしない）")
        return 0
    doc = {
        "ontology": name, "version": 1, "governance": {"schema_changes": "stage"},
        "object_types": {}, "link_types": {}, "action_types": {},
    }
    dir_.mkdir(parents=True, exist_ok=True)
    onto_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    common_schema = None
    if common_dir is not None and (common_dir / "ontology.json").exists():
        common_schema = load_schema(common_dir)
    sch = parse_schema(doc, common=common_schema, source=str(onto_path))
    govern.write_index_md(dir_, sch)
    print(f"作成: {onto_path}")
    return 0


def _approval_label(appr) -> str:
    if appr is None:
        return "stage"
    return appr.mode


def _cmd_types(args, ctx: Ctx) -> int:
    dir_, common_dir, _name = _resolve_scope(ctx, args)
    sch, st = _load(dir_, common_dir)
    lines = []
    for tname in sorted(sch.object_types):
        ot = sch.object_types[tname]
        count = len(st.all(tname))
        lines.append(f"{tname}（{ot.label or tname}） {count}")
    for aname in sorted(sch.action_types):
        at = sch.action_types[aname]
        desc = (at.description or "").split("。")[0]
        lines.append(f"{aname}（{at.label or aname}） — {desc} [{_approval_label(at.approval)}]")
    print("\n".join(lines))
    return 0


def _describe_type(sch: Schema, tname: str) -> int:
    ot = sch.object_types[tname]
    lines = [f"{tname}（{ot.label or tname}）"]
    for pname, prop in sch.props(tname).items():
        bits = [prop.type or "?"]
        if prop.required:
            bits.append("required")
        if prop.values:
            bits.append("値:" + "/".join(str(v) for v in prop.values))
        lines.append(f"  {pname}: {' '.join(bits)}")
    for lname, lt in sch.links_from(tname).items():
        lines.append(f"→ {lname}: {lt.to_type}（{lt.label or ''}）")
    for iname, lt in sch.links_to(tname).items():
        lines.append(f"← {iname}: {lt.from_type}（{lt.inverse_label or ''}）")
    print("\n".join(lines))
    return 0


def _describe_action(sch: Schema, aname: str) -> int:
    at = sch.action_types[aname]
    lines = [f"{aname}（{at.label or aname}）"]
    if at.description:
        lines.append(at.description)
    for pname, p in at.parameters.items():
        ptype = p.type if p.type else f"{p.object_type} の id"
        req = " required" if p.required else ""
        lines.append(f"  {pname}: {ptype}{req}")
    for c in at.criteria:
        src = c.when.src if c.when else ""
        lines.append(f"前提: {src} → {c.message}")
    appr = at.approval
    if appr is not None:
        if appr.mode == "auto":
            lines.append("承認: auto")
        elif appr.mode == "stage":
            lines.append("承認: stage")
        else:
            src = appr.when.src if appr.when else ""
            lines.append(f"承認: stage_if {src}（役割: {appr.role or '-'}）")
    if at.next:
        lines.append(f"next: {at.next}")
    print("\n".join(lines))
    return 0


def _cmd_describe(args, ctx: Ctx) -> int:
    dir_, common_dir, _name = _resolve_scope(ctx, args)
    sch, _st = _load(dir_, common_dir)
    if args.name in sch.object_types:
        return _describe_type(sch, args.name)
    if args.name in sch.action_types:
        return _describe_action(sch, args.name)
    print(f"ws: '{args.name}' という型・アクションは無い", file=sys.stderr)
    return 1


def _cmd_query(args, ctx: Ctx) -> int:
    dir_, common_dir, _name = _resolve_scope(ctx, args)
    _sch, st = _load(dir_, common_dir)
    select = args.select.split(",") if args.select else None
    agent = _is_agent(ctx)
    rows, total = query_mod.query(
        st, args.type, where=args.where, select=select,
        limit=None if args.count else args.limit, agent=agent,
    )
    if args.count:
        print(len(rows))
        return 0
    if args.json:
        print(json.dumps(rows, ensure_ascii=False))
        return 0
    print(query_mod.format_rows(rows, total=total, max_chars=args.max_chars))
    return 0


def _find_any(st: Store, id_: str) -> "list[tuple[str, str]]":
    """id をすべての型（own + common）の実体バケットから探す（具体的な型の下に置かれているので、
    継承関係による二重ヒットは起きない）。"""
    seen = set()
    hits = []
    docs = [st.doc]
    if st.common is not None:
        docs.append(st.common.doc)
    for doc in docs:
        for tname, entities in doc.items():
            if tname == "_meta" or not isinstance(entities, dict):
                continue
            if id_ in entities:
                ref = f"{tname}:{id_}"
                if ref not in seen:
                    seen.add(ref)
                    hits.append((tname, ref))
    return hits


def _cmd_show(args, ctx: Ctx) -> int:
    dir_, common_dir, _name = _resolve_scope(ctx, args)
    _sch, st = _load(dir_, common_dir)
    agent = _is_agent(ctx)
    if args.type:
        d = query_mod.show(st, args.ref_or_id, type_name=args.type, agent=agent)
    elif ":" in args.ref_or_id:
        d = query_mod.show(st, args.ref_or_id, agent=agent)
    else:
        hits = _find_any(st, args.ref_or_id)
        if not hits:
            print(f"ws: '{args.ref_or_id}' は見つからない", file=sys.stderr)
            return 1
        if len(hits) > 1:
            opts = "、".join(ref for _t, ref in hits)
            print(f"ws: '{args.ref_or_id}' が複数の型にある。--type で選ぶ: {opts}", file=sys.stderr)
            return 1
        d = query_mod.show(st, hits[0][1], agent=agent)
    if args.json:
        print(json.dumps(d, ensure_ascii=False))
        return 0
    print(query_mod.format_show(d))
    return 0


def _cmd_act(args, ctx: Ctx) -> int:
    dir_, common_dir, _name = _resolve_scope(ctx, args)
    sch, st = _load(dir_, common_dir)
    at = sch.action_types.get(args.action)
    if at is None:
        print(f"ws: アクション '{args.action}' は定義に無い", file=sys.stderr)
        return 1
    target_store = st.common if (at.origin == "common" and st.common is not None) else st
    params = _parse_kv(args.params)
    actor = _actor_for(ctx)
    result = engine.act(
        target_store, args.action, params, actor, why=args.why,
        dry_run=args.dry_run, task=ctx.current_task, refs=args.ref or None,
    )
    return _print_act_result(result, target_store, ctx, args.json)


def _cmd_define_apply(args, ctx: Ctx) -> int:
    dir_, common_dir, _name = _resolve_scope(ctx, args)
    _sch, st = _load(dir_, common_dir)
    patch_path = Path(args.patch_file)
    try:
        patch = json.loads(patch_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"ws: パッチファイルを読めない（{e}）", file=sys.stderr)
        return 1
    actor = _actor_for(ctx)
    result = govern.propose(st, patch, actor, why=args.why)
    return _print_gov_result(result)


def _cmd_approve(args, ctx: Ctx) -> int:
    if not _is_human_ctx(ctx):
        print(f"ws: {_HUMAN_ONLY_MSG}", file=sys.stderr)
        return 1
    scope_name, bare_id = _split_scope_id(args.id)
    hits = _find_proposal_dirs(ctx, scope_name, bare_id)
    if not hits:
        print(f"ws: '{bare_id}' が見つからない", file=sys.stderr)
        return 1
    if len(hits) > 1:
        opts = "、".join(f"{name}/{bare_id}" for _, _, name in hits)
        print(f"ws: '{bare_id}' が複数の範囲にある。「承認 <範囲>/{bare_id}」の形で選ぶ: {opts}", file=sys.stderr)
        return 1
    dir_, common_dir, _name = hits[0]
    approver = engine.Actor("human", ctx.user)
    if bare_id.startswith("S-"):
        result = govern.approve_schema(dir_, common_dir, bare_id, approver)
        return _print_gov_result(result)
    _sch, st = _load(dir_, common_dir)
    result = engine.approve(st, bare_id, approver)
    return _print_act_result(result, st, ctx, False)


def _cmd_reject(args, ctx: Ctx) -> int:
    if not _is_human_ctx(ctx):
        print(f"ws: {_HUMAN_ONLY_MSG}", file=sys.stderr)
        return 1
    scope_name, bare_id = _split_scope_id(args.id)
    hits = _find_proposal_dirs(ctx, scope_name, bare_id)
    if not hits:
        print(f"ws: '{bare_id}' が見つからない", file=sys.stderr)
        return 1
    if len(hits) > 1:
        opts = "、".join(f"{name}/{bare_id}" for _, _, name in hits)
        print(f"ws: '{bare_id}' が複数の範囲にある。「却下 <範囲>/{bare_id} 理由」の形で選ぶ: {opts}", file=sys.stderr)
        return 1
    dir_, common_dir, _name = hits[0]
    approver = engine.Actor("human", ctx.user)
    _sch, st = _load(dir_, common_dir)
    engine.reject(st, bare_id, approver, args.reason)
    print(f"却下: {bare_id}")
    return 0


def _cmd_proposals(args, ctx: Ctx) -> int:
    dir_, common_dir, _name = _resolve_scope(ctx, args)
    pdir = dir_ / "proposals"
    if not pdir.exists():
        print("（0 件）")
        return 0
    lines = []
    for f in sorted(pdir.glob("*.json")):
        try:
            doc = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not args.all and doc.get("status") != "open":
            continue
        actor = doc.get("actor") or {}
        who = actor.get("name", "?")
        created = doc.get("created", "")
        role = doc.get("role") or "-"
        if doc.get("kind") == "schema":
            summary = "、".join(doc.get("summary") or [])
        else:
            params = doc.get("params") or {}
            summary = f"{doc.get('action')}（" + ", ".join(f"{k}={v}" for k, v in params.items()) + "）"
        lines.append(f"{doc.get('id')} [{doc.get('status')}] {summary} - {who} {created} role={role}")
    print("\n".join(lines) if lines else "（0 件）")
    return 0


def _cmd_validate(args, ctx: Ctx) -> int:
    dir_, common_dir, _name = _resolve_scope(ctx, args)
    _sch, st = _load(dir_, common_dir)
    violations = validate(st)
    if not violations:
        print("問題なし")
        return 0
    for v in violations:
        print(f"{v.ref} {v.path} {v.code}: {v.message}")
    return 1


def _cmd_lint(args, ctx: Ctx) -> int:
    dir_, common_dir, _name = _resolve_scope(ctx, args)
    sch, st = _load(dir_, common_dir)
    findings = lint_mod.lint(sch, st.doc)
    if not findings:
        print("問題なし")
        return 0
    for f in findings:
        print(f"{f.level} {f.code} {f.where}: {f.message}")
    return 1


def _cmd_eval(args, ctx: Ctx) -> int:
    dir_, common_dir, _name = _resolve_scope(ctx, args)
    _sch, st = _load(dir_, common_dir)
    qpath = dir_ / "questions.json"
    if not qpath.exists():
        print("questions.json が無い")
        return 0
    doc = json.loads(qpath.read_text(encoding="utf-8"))
    results = evals.run_questions(st, doc, _EVAL_ACTOR)
    ok = 0
    for r in results:
        if r.ok:
            ok += 1
            print(f"{r.id} ok")
        else:
            print(f"{r.id} ng: {r.detail}")
    print(f"{ok}/{len(results)} ok")
    return 0 if ok == len(results) else 1


def _cmd_export(args, ctx: Ctx) -> int:
    dir_, common_dir, _name = _resolve_scope(ctx, args)
    sch, st = _load(dir_, common_dir)
    fmt = args.format
    if fmt == "jsonschema":
        text = json.dumps(export.to_jsonschema(sch), ensure_ascii=False, indent=2)
    elif fmt == "turtle":
        objects = [st.doc] + ([st.common.doc] if st.common is not None else [])
        text = export.to_turtle(sch, objects)
    elif fmt == "mermaid":
        text = export.to_mermaid(sch)
    else:
        text = export.to_markdown(sch, st.doc)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"書き出し: {args.out}")
    else:
        print(text)
    return 0


def _cmd_log(args, ctx: Ctx) -> int:
    dir_, _common_dir, _name = _resolve_scope(ctx, args)
    entries = engine.read_log(dir_, action=args.action, object=args.object, limit=args.limit)
    if not entries:
        print("（0 件）")
        return 0
    for e in entries:
        ts = e.get("ts", "")
        kind = e.get("kind", "")
        action = e.get("action") or "-"
        status = e.get("status", "")
        actor = (e.get("actor") or {}).get("name", "?")
        msgs = "、".join(e.get("messages") or [])
        print(f"{ts} {kind} {action} {status} {actor} {msgs}".rstrip())
    return 0


def _cmd_adopt(args, ctx: Ctx) -> int:
    if not _is_human_ctx(ctx):
        print(f"ws: {_HUMAN_ONLY_MSG}", file=sys.stderr)
        return 1
    dir_, common_dir, _name = _resolve_scope(ctx, args)
    _sch, st = _load(dir_, common_dir)
    engine.adopt(st, engine.Actor("human", ctx.user), args.note)
    print("取り込み完了")
    return 0


# --- argparse の組み立て -----------------------------------------------------


def _scope_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(add_help=False)
    g = p.add_mutually_exclusive_group()
    g.add_argument("--common", action="store_true")
    g.add_argument("--project")
    return p


def _build_parser() -> argparse.ArgumentParser:
    scope = _scope_parser()
    parser = argparse.ArgumentParser(prog="scripts/ws onto")
    sub = parser.add_subparsers(dest="cmd")

    p_init = sub.add_parser("init", parents=[scope])
    p_init.set_defaults(func=_cmd_init)

    p_types = sub.add_parser("types", parents=[scope])
    p_types.set_defaults(func=_cmd_types)

    p_describe = sub.add_parser("describe", parents=[scope])
    p_describe.add_argument("name")
    p_describe.set_defaults(func=_cmd_describe)

    p_query = sub.add_parser("query", parents=[scope])
    p_query.add_argument("type")
    p_query.add_argument("--where")
    p_query.add_argument("--select")
    p_query.add_argument("--limit", type=int, default=20)
    p_query.add_argument("--count", action="store_true")
    p_query.add_argument("--json", action="store_true")
    p_query.add_argument("--max-chars", type=int, default=2000)
    p_query.set_defaults(func=_cmd_query)

    p_show = sub.add_parser("show", parents=[scope])
    p_show.add_argument("ref_or_id")
    p_show.add_argument("--type")
    p_show.add_argument("--json", action="store_true")
    p_show.set_defaults(func=_cmd_show)

    p_act = sub.add_parser("act", parents=[scope])
    p_act.add_argument("action")
    p_act.add_argument("params", nargs="*")
    p_act.add_argument("--why", default="")
    p_act.add_argument("--ref", action="append", default=[])
    p_act.add_argument("--dry-run", action="store_true")
    p_act.add_argument("--json", action="store_true")
    p_act.set_defaults(func=_cmd_act)

    p_define = sub.add_parser("define")
    define_sub = p_define.add_subparsers(dest="define_cmd")
    p_apply = define_sub.add_parser("apply", parents=[scope])
    p_apply.add_argument("patch_file")
    p_apply.add_argument("--why", default="")
    p_apply.set_defaults(func=_cmd_define_apply)

    p_approve = sub.add_parser("approve")
    p_approve.add_argument("id")
    p_approve.set_defaults(func=_cmd_approve)

    p_reject = sub.add_parser("reject")
    p_reject.add_argument("id")
    p_reject.add_argument("--reason", default="")
    p_reject.set_defaults(func=_cmd_reject)

    p_proposals = sub.add_parser("proposals", parents=[scope])
    p_proposals.add_argument("--all", action="store_true")
    p_proposals.set_defaults(func=_cmd_proposals)

    p_validate = sub.add_parser("validate", parents=[scope])
    p_validate.set_defaults(func=_cmd_validate)

    p_lint = sub.add_parser("lint", parents=[scope])
    p_lint.set_defaults(func=_cmd_lint)

    p_eval = sub.add_parser("eval", parents=[scope])
    p_eval.set_defaults(func=_cmd_eval)

    p_export = sub.add_parser("export", parents=[scope])
    p_export.add_argument("--format", required=True, choices=["jsonschema", "turtle", "mermaid", "markdown"])
    p_export.add_argument("--out")
    p_export.set_defaults(func=_cmd_export)

    p_log = sub.add_parser("log", parents=[scope])
    p_log.add_argument("--object")
    p_log.add_argument("--action")
    p_log.add_argument("--limit", type=int)
    p_log.set_defaults(func=_cmd_log)

    p_adopt = sub.add_parser("adopt", parents=[scope])
    p_adopt.add_argument("--note", default="")
    p_adopt.set_defaults(func=_cmd_adopt)

    return parser


def main(argv: list, ctx: Ctx) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else 1
        return 0 if code == 0 else 1
    func = getattr(args, "func", None)
    if func is None:
        parser.print_help()
        return 1
    try:
        return func(args, ctx)
    except OntoError as e:
        print(f"ws: {e}", file=sys.stderr)
        return 1
    except Exception as e:  # noqa: BLE001 -- スタックトレースを見せない。原因は WS_DEBUG=1 で
        if os.environ.get("WS_DEBUG") == "1":
            traceback.print_exc()
        print(
            f"ws: 内部エラー（{type(e).__name__}: {e}）。定義か実体が想定外の形。scripts/ws onto validate で確かめる",
            file=sys.stderr,
        )
        return 1


# --- UserPromptSubmit からの承認・却下 ---------------------------------------


def handle_prompt(prompt: str, ctx: Ctx) -> Optional[str]:
    m = _PROMPT_RE.match(prompt)
    if not m:
        return None
    verb, id_arg, rest = m.group(1), m.group(2), m.group(3)
    is_approve = verb in ("承認", "approve")
    scope_name, bare_id = _split_scope_id(id_arg)
    try:
        hits = _find_proposal_dirs(ctx, scope_name, bare_id)
        if not hits:
            return f"'{bare_id}' が見つからない"
        if len(hits) > 1:
            verb_label = "承認" if is_approve else "却下"
            opts = "、".join(f"{name}/{bare_id}" for _, _, name in hits)
            return f"'{bare_id}' が複数の範囲にある。「{verb_label} <範囲>/{bare_id}」の形で選ぶ: {opts}"
        dir_, common_dir, _name = hits[0]
        approver = engine.Actor("human", ctx.user)
        if is_approve:
            if bare_id.startswith("S-"):
                result = govern.approve_schema(dir_, common_dir, bare_id, approver)
                if result.status == "committed":
                    return f"人が {bare_id} を承認し、定義を版 {result.version} に更新した。"
                return f"{bare_id} は承認時の再検査で拒否された: {'、'.join(result.messages)}。実行待ちのまま"
            _sch, st = _load(dir_, common_dir)
            result = engine.approve(st, bare_id, approver)
            if result.status == "committed":
                detail = _act_result_detail(st, result)
                return f"人が {bare_id} を承認し、実行した: {detail}"
            return f"{bare_id} は承認時の再検査で拒否された: {'、'.join(result.messages)}。実行待ちのまま"
        _sch, st = _load(dir_, common_dir)
        engine.reject(st, bare_id, approver, rest or "")
        return f"人が {bare_id} を却下した: {rest or '（理由なし）'}"
    except Exception as e:  # noqa: BLE001 -- hook を落とさない
        return f"'{bare_id}' の処理でエラーが起きた: {e}"


# --- doctor / transcript normalize / ステータスライン ------------------------


def doctor_problems(ctx: Ctx) -> list:
    common_dir = _common_dir(ctx)
    dirs = []
    if (common_dir / "ontology.json").exists():
        dirs.append((common_dir, None, "knowledges/ontology"))
    projects_root = Path(ctx.root) / "projects"
    if projects_root.exists():
        for p in sorted(projects_root.iterdir()):
            if not p.is_dir():
                continue
            pdir = p / "knowledges" / "ontology"
            if (pdir / "ontology.json").exists():
                dirs.append((pdir, common_dir, f"projects/{p.name}/knowledges/ontology"))
    if not dirs:
        return []

    problems = []
    for dir_, common_dir_arg, label in dirs:
        try:
            sch, st = _load(dir_, common_dir_arg)
        except OntoError as e:
            problems.append(f"{label}: {e}")
            continue
        except Exception as e:  # noqa: BLE001 -- 1 範囲の想定外の壊れ方で doctor 全体を落とさない
            problems.append(f"{label}: 定義の読み込み で内部エラー（{type(e).__name__}: {e}）")
            continue

        try:
            for v in validate(st):
                problems.append(f"{label}: {v.ref} {v.path} {v.code} {v.message}")
        except Exception as e:  # noqa: BLE001
            problems.append(f"{label}: validate で内部エラー（{type(e).__name__}: {e}）")

        try:
            for f in lint_mod.lint(sch, st.doc):
                if f.level == "warn":
                    problems.append(f"{label}: lint {f.code} {f.where} {f.message}")
        except Exception as e:  # noqa: BLE001
            problems.append(f"{label}: lint で内部エラー（{type(e).__name__}: {e}）")

        try:
            pdir = dir_ / "proposals"
            if pdir.exists():
                now = datetime.datetime.now(datetime.timezone.utc)
                for pf in sorted(pdir.glob("*.json")):
                    try:
                        doc = json.loads(pf.read_text(encoding="utf-8"))
                    except (OSError, json.JSONDecodeError):
                        continue
                    if not isinstance(doc, dict) or doc.get("status") != "open":
                        continue
                    created = doc.get("created")
                    if not created:
                        continue
                    try:
                        created_dt = datetime.datetime.fromisoformat(created)
                    except ValueError:
                        continue
                    if created_dt.tzinfo is None:
                        created_dt = created_dt.replace(tzinfo=datetime.timezone.utc)
                    age_days = (now - created_dt).days
                    if age_days > 7:
                        problems.append(f"{label}: 実行待ち {doc.get('id')} が {age_days} 日 open のまま")
        except Exception as e:  # noqa: BLE001
            problems.append(f"{label}: 実行待ち で内部エラー（{type(e).__name__}: {e}）")

        qpath = dir_ / "questions.json"
        if qpath.exists():
            try:
                qdoc = json.loads(qpath.read_text(encoding="utf-8"))
                for r in evals.run_questions(st, qdoc, _EVAL_ACTOR):
                    if not r.ok:
                        problems.append(f"{label}: eval {r.id} 失敗 {r.detail}")
            except Exception as e:  # noqa: BLE001 -- doctor は落とさない
                problems.append(f"{label}: 評価 で内部エラー（{type(e).__name__}: {e}）")

        try:
            for line in engine.verify_chain(st):
                problems.append(f"{label}: {line}")
        except Exception as e:  # noqa: BLE001
            problems.append(f"{label}: ハッシュの鎖 で内部エラー（{type(e).__name__}: {e}）")

    return problems


def _effective_alias_label(sch: Schema, tname: str) -> "tuple[Optional[str], Optional[str]]":
    """自分の型に alias_property/label_property が無ければ extends を遡って探す
    （Stakeholder は自分では持たず、共通の Person から受け継ぐ）。"""
    ot = sch.object_types.get(tname)
    if ot is None:
        return None, None
    if ot.alias_property or ot.label_property:
        return ot.alias_property, ot.label_property
    for parent in ot.extends:
        ap, lp = _effective_alias_label(sch, parent)
        if ap or lp:
            return ap, lp
    return None, None


def _add_alias(pairs: dict, alias, label: str) -> None:
    if not alias or not isinstance(alias, str):
        return
    if len(alias) < 2:
        return
    if alias == label:
        return
    pairs[alias] = label


def alias_pairs(ctx: Ctx, project: Optional[str]) -> dict:
    pairs: dict = {}
    common_dir = _common_dir(ctx)
    dirs = []
    if (common_dir / "ontology.json").exists():
        dirs.append((common_dir, None))
    if project:
        pdir = _project_dir(ctx, project)
        if (pdir / "ontology.json").exists():
            dirs.append((pdir, common_dir))
    for dir_, common_dir_arg in dirs:
        try:
            sch, st = _load(dir_, common_dir_arg)
        except OntoError:
            continue
        for tname, ot in sch.object_types.items():
            label = ot.label or tname
            for alias in ot.aliases:
                _add_alias(pairs, alias, label)
            alias_prop, label_prop = _effective_alias_label(sch, tname)
            if not alias_prop or not label_prop:
                continue
            for obj in st.all(tname, include_subtypes=False):
                label_val = obj.onto_get(label_prop)
                if label_val is None:
                    continue
                label_str = str(label_val)
                alias_val = obj.onto_get(alias_prop)
                vals = alias_val if isinstance(alias_val, list) else ([alias_val] if alias_val else [])
                for v in vals:
                    _add_alias(pairs, v, label_str)
    return pairs


def pending_count(root: Path) -> int:
    root = Path(root)
    pdirs = [root / "knowledges" / "ontology" / "proposals"]
    projects_root = root / "projects"
    if projects_root.exists():
        for p in sorted(projects_root.iterdir()):
            if p.is_dir():
                pdirs.append(p / "knowledges" / "ontology" / "proposals")
    total = 0
    for pdir in pdirs:
        if not pdir.exists():
            continue
        for f in pdir.glob("*.json"):
            try:
                doc = json.loads(f.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(doc, dict) and doc.get("status") == "open":
                total += 1
    return total
