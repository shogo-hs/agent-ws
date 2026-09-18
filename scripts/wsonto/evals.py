"""wsonto — 答えたい質問（questions.json）の評価。

取り決めは `scripts/wsonto/README.md` の「evals.py」を参照。実行時は標準
ライブラリだけで動く（Python 3.9 以上）。
"""
from __future__ import annotations

import datetime
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .engine import Actor, act, read_log
from .store import Store


@dataclass
class QResult:
    id: str
    ok: bool
    detail: str = ""


def run_questions(store: Store, doc: dict, actor: Actor) -> list:
    today_str = doc.get("today")
    today = datetime.date.fromisoformat(today_str) if today_str else None
    return [_run_one(store, q, actor, today) for q in doc.get("questions", [])]


def _run_one(store: Store, q: dict, actor: Actor, today: Optional[datetime.date]) -> QResult:
    qid = q.get("id", "?")
    kind = q.get("kind")
    tmpdir = tempfile.mkdtemp(prefix="wsonto-eval-")
    try:
        tmp_path = Path(tmpdir)
        src_objects = store.dir / "objects.json"
        if src_objects.exists():
            shutil.copy2(src_objects, tmp_path / "objects.json")
        src_onto = store.dir / "ontology.json"
        if src_onto.exists():
            shutil.copy2(src_onto, tmp_path / "ontology.json")
        tmp_store = Store(tmp_path, store.schema, common=store.common)

        if kind == "query":
            return _run_query(tmp_store, q, today, qid)
        if kind == "action":
            return _run_action_question(tmp_store, q, actor, today, qid)
        if kind == "log":
            return _run_log_question(tmp_store, q, actor, today, qid)
        return QResult(qid, False, f"知らない kind '{kind}'")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def _run_query(tmp_store: Store, q: dict, today: Optional[datetime.date], qid: str) -> QResult:
    try:
        from . import query  # 遅延 import。query.py が無ければ ImportError。
    except ImportError:
        return QResult(qid, False, "query.py が無い")
    try:
        rows, _total = query.query(tmp_store, q["type"], where=q.get("where"), limit=None, today=today)
    except TypeError:
        rows, _total = query.query(tmp_store, q["type"], where=q.get("where"))
    except Exception as e:  # noqa: BLE001 -- 評価は失敗を ok=False として続行するため広く捕まえる
        return QResult(qid, False, f"query の実行に失敗した（{e}）")
    got_ids = sorted(r.get("id") for r in rows)
    want_ids = sorted((q.get("expect") or {}).get("ids") or [])
    if got_ids == want_ids:
        return QResult(qid, True, "")
    return QResult(qid, False, f"期待 ids={want_ids} 実際 ids={got_ids}")


def _run_given(tmp_store: Store, given: list, actor: Actor, today: Optional[datetime.date]) -> None:
    for g in given:
        act(tmp_store, g["action"], g.get("params") or {}, actor, today=today)


def _run_action_question(tmp_store: Store, q: dict, actor: Actor, today: Optional[datetime.date], qid: str) -> QResult:
    _run_given(tmp_store, q.get("given") or [], actor, today)
    result = act(tmp_store, q["action"], q.get("params") or {}, actor, today=today)
    expect = q.get("expect") or {}

    want_status = expect.get("status")
    if want_status is not None and result.status != want_status:
        return QResult(qid, False, f"期待 status={want_status!r} 実際 status={result.status!r}")

    if "messages" in expect and result.messages != expect["messages"]:
        return QResult(qid, False, f"期待 messages={expect['messages']} 実際 messages={result.messages}")

    if "returned" in expect:
        if not result.returned:
            return QResult(qid, False, f"期待 returned={expect['returned']} 実際 returned={result.returned!r}")
        obj = tmp_store.get(result.returned)
        if obj is None:
            return QResult(qid, False, f"returned '{result.returned}' が見つからない")
        for k, v in expect["returned"].items():
            got = obj.onto_get(k)
            got_cmp = got.isoformat() if isinstance(got, datetime.date) else got
            if got_cmp != v:
                return QResult(qid, False, f"期待 {k}={v!r} 実際 {k}={got_cmp!r}")

    return QResult(qid, True, "")


def _run_log_question(tmp_store: Store, q: dict, actor: Actor, today: Optional[datetime.date], qid: str) -> QResult:
    _run_given(tmp_store, q.get("given") or [], actor, today)
    entries = read_log(tmp_store.dir)
    got_actions = [e.get("action") for e in entries]
    got_statuses = [e.get("status") for e in entries]
    expect = q.get("expect") or {}

    if "actions" in expect and got_actions != expect["actions"]:
        return QResult(qid, False, f"期待 actions={expect['actions']} 実際 actions={got_actions}")
    if "statuses" in expect and got_statuses != expect["statuses"]:
        return QResult(qid, False, f"期待 statuses={expect['statuses']} 実際 statuses={got_statuses}")

    return QResult(qid, True, "")
