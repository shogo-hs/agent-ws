"""wsonto — 実体の保管（objects.json の読み書きと照会）。

取り決めは `scripts/wsonto/README.md` の「store.py」を参照。実行時は標準
ライブラリだけで動く（Python 3.9 以上）。
"""
from __future__ import annotations

import copy
import datetime
import hashlib
import json
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Optional

from .errors import HiddenPropertyError, StoreError

_MISSING = object()


class Store:
    """objects.json の読み書きと照会。`common` があれば自分に無い実体をそちらへ回す。"""

    def __init__(self, dir: Path, schema, common: "Optional[Store]" = None) -> None:
        self.dir = Path(dir)
        self.schema = schema
        self.common = common
        self.doc = self._load_doc()
        self._rev_index: Optional[dict] = None
        self.hide_hidden: bool = False  # query.py が agent=True のとき一時的に立てる

    # --- 読み込み -----------------------------------------------------

    def _load_doc(self) -> dict:
        path = self.dir / "objects.json"
        if not path.exists():
            return {"_meta": {"seq": {}}}
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise StoreError(f"{path}: JSON として読めない（{e}）") from e
        if not isinstance(doc, dict):
            raise StoreError(f"{path}: objects.json はオブジェクトである必要がある")
        doc.setdefault("_meta", {})
        doc["_meta"].setdefault("seq", {})
        return doc

    @classmethod
    def _wrap(cls, dir: Path, schema, doc: dict, common: "Optional[Store]") -> "Store":
        self = cls.__new__(cls)
        self.dir = Path(dir)
        self.schema = schema
        self.common = common
        self.doc = doc
        self._rev_index = None
        self.hide_hidden = False
        return self

    # --- 照会 -----------------------------------------------------------

    def get(self, ref: str) -> "Optional[ObjView]":
        type_name, _, id_ = ref.partition(":")
        rec = self.doc.get(type_name, {}).get(id_)
        if rec is not None:
            return ObjView(self, type_name, id_, rec)
        if self.common is not None:
            got = self.common.get(ref)
            if got is not None:
                return ObjView(self, got.type, got.id, got._record)
        return None

    def find(self, type_name: str, id_: str) -> "Optional[ObjView]":
        candidates = []
        for t in self.schema.subtypes(type_name):
            entities = self.doc.get(t)
            if entities and id_ in entities:
                candidates.append((t, entities[id_]))
        if len(candidates) > 1:
            hit = ", ".join(f"{t}:{id_}" for t, _ in candidates)
            raise StoreError(f"'{type_name}:{id_}' に一致する実体が複数ある（{hit}）")
        if len(candidates) == 1:
            t, rec = candidates[0]
            return ObjView(self, t, id_, rec)
        if self.common is not None:
            got = self.common.find(type_name, id_)
            if got is not None:
                return ObjView(self, got.type, got.id, got._record)
        return None

    def all(self, type_name: str, include_subtypes: bool = True) -> "list[ObjView]":
        types = self.schema.subtypes(type_name) if include_subtypes else [type_name]
        out: "list[ObjView]" = []
        for t in types:
            entities = self.doc.get(t)
            if not entities:
                continue
            for id_, rec in entities.items():
                out.append(ObjView(self, t, id_, rec))
        if self.common is not None:
            for view in self.common.all(type_name, include_subtypes):
                out.append(ObjView(self, view.type, view.id, view._record))
        return out

    # --- 書き込み（メモリ上だけ） ---------------------------------------

    def put(self, type_name: str, id_: str, props: dict, links: "Optional[dict]" = None) -> None:
        rec = dict(props)
        if links:
            rec["_links"] = {name: list(refs) for name, refs in links.items()}
        self.doc.setdefault(type_name, {})[id_] = rec
        self._rev_index = None

    def remove(self, ref: str) -> None:
        type_name, _, id_ = ref.partition(":")
        entities = self.doc.get(type_name)
        if not entities or id_ not in entities:
            raise StoreError(f"'{ref}' が見つからないので削除できない")
        del entities[id_]
        self._rev_index = None

    def next_seq(self, type_name: str) -> int:
        seq = self.doc["_meta"]["seq"]
        n = seq.get(type_name, 0) + 1
        seq[type_name] = n
        return n

    # --- 取り消し・書き出し ---------------------------------------------

    def snapshot(self) -> "Store":
        return Store._wrap(self.dir, self.schema, copy.deepcopy(self.doc), self.common)

    def to_doc(self) -> dict:
        return self.doc

    def reload(self) -> None:
        """objects.json を読み直す（メモリ上の変更は捨てる）。"""
        self.doc = self._load_doc()
        self._rev_index = None

    def commit(self, lock: bool = True) -> str:
        self.dir.mkdir(parents=True, exist_ok=True)

        def _write() -> None:
            path = self.dir / "objects.json"
            tmp = self.dir / f".objects.json.tmp{os.getpid()}"
            text = json.dumps(self.doc, sort_keys=True, indent=1, ensure_ascii=False) + "\n"
            tmp.write_text(text, encoding="utf-8")
            os.replace(tmp, path)

        if lock:
            with locked(self.dir):
                _write()
        else:
            _write()
        return self.file_hash()

    def file_hash(self) -> str:
        path = self.dir / "objects.json"
        if not path.exists():
            return ""
        return hashlib.sha256(path.read_bytes()).hexdigest()[:16]

    # --- 逆向きの索引（put/remove のあとは作り直す） ----------------------

    def _ensure_rev_index(self) -> dict:
        if self._rev_index is None:
            idx: dict = {}
            for type_name, entities in self.doc.items():
                if type_name == "_meta" or not isinstance(entities, dict):
                    continue
                for id_, rec in entities.items():
                    from_ref = f"{type_name}:{id_}"
                    for link_name, refs in (rec.get("_links") or {}).items():
                        for to_ref in refs:
                            idx.setdefault(to_ref, {}).setdefault(link_name, []).append(from_ref)
            self._rev_index = idx
        return self._rev_index


class ObjView:
    """実体の読み取り専用の顔。プロパティ・リンク・逆向きの名前を `onto_get` で引く。"""

    __slots__ = ("store", "type", "id", "_record")

    def __init__(self, store: Store, type_name: str, id_: str, record: dict) -> None:
        self.store = store
        self.type = type_name
        self.id = id_
        self._record = record

    @property
    def ref(self) -> str:
        return f"{self.type}:{self.id}"

    def __repr__(self) -> str:
        return f"ObjView({self.ref!r})"

    def onto_get(self, name: str) -> Any:
        if name == "id":
            return self.id
        if name == "type":
            return self.type
        props = self.store.schema.props(self.type)
        if name in props:
            prop = props[name]
            if self.store.hide_hidden and not prop.agent_visible:
                raise HiddenPropertyError(f"'{self.type}' の '{name}' は非表示のプロパティ")
            return self._prop_value(prop)
        links_from = self.store.schema.links_from(self.type)
        if name in links_from:
            return self._forward_link(links_from[name])
        links_to = self.store.schema.links_to(self.type)
        if name in links_to:
            return self._inverse_link(links_to[name])
        raise KeyError(f"'{self.type}' に '{name}' は無い")

    def _prop_value(self, prop) -> Any:
        raw = self._record.get(prop.name, _MISSING)
        if raw is _MISSING:
            if prop.many:
                return []
            if prop.default is not None:
                return self._convert_scalar(prop, prop.default)
            return None
        if prop.many:
            if not isinstance(raw, list):
                return []
            return [self._convert_scalar(prop, v) for v in raw]
        return self._convert_scalar(prop, raw)

    @staticmethod
    def _convert_scalar(prop, value: Any) -> Any:
        if value is None:
            return None
        if prop.type == "date" and isinstance(value, str):
            return datetime.date.fromisoformat(value)
        if prop.type == "datetime" and isinstance(value, str):
            s = value[:-1] + "+00:00" if value.endswith("Z") else value
            return datetime.datetime.fromisoformat(s)
        return value

    def _forward_link(self, lt) -> Any:
        refs = (self._record.get("_links") or {}).get(lt.name, [])
        resolved = [self.store.get(r) for r in refs]
        resolved = [r for r in resolved if r is not None]
        if lt.max == 1:
            return resolved[0] if resolved else None
        return resolved

    def _inverse_link(self, lt) -> Any:
        self.store._ensure_rev_index()
        from_refs = list(self.store._rev_index.get(self.ref, {}).get(lt.name, []))
        if self.store.common is not None:
            self.store.common._ensure_rev_index()
            from_refs += self.store.common._rev_index.get(self.ref, {}).get(lt.name, [])
        resolved = [self.store.get(r) for r in from_refs]
        resolved = [r for r in resolved if r is not None]
        if lt.inverse_max == 1:
            return resolved[0] if resolved else None
        return resolved

    def to_dict(self, select: "Optional[list]" = None, agent: bool = False) -> dict:
        if select is None:
            out: dict = {"id": self.id, "type": self.type}
            for pname, prop in self.store.schema.props(self.type).items():
                if agent and not prop.agent_visible:
                    continue
                out[pname] = _jsonify(self.onto_get(pname))
            return out
        out = {}
        for item in select:
            link_name, sep, prop_name = item.partition(".")
            if sep:
                target = self.onto_get(link_name)
                if target is None:
                    value: Any = None
                elif isinstance(target, list):
                    value = [t.onto_get(prop_name) for t in target]
                else:
                    value = target.onto_get(prop_name)
            else:
                value = self.onto_get(item)
            out[item] = _jsonify(value)
        return out


def _jsonify(value: Any) -> Any:
    if isinstance(value, ObjView):
        return value.ref
    if isinstance(value, datetime.date):
        return value.isoformat()
    if isinstance(value, list):
        return [_jsonify(v) for v in value]
    return value


@contextmanager
def locked(dir: Path, timeout: float = 5.0, stale: float = 60.0):
    """`dir/.lock` を `os.mkdir` で取る。取れなければ timeout 秒で `StoreError`。"""
    dir = Path(dir)
    lock_path = dir / ".lock"
    start = time.monotonic()
    acquired = False
    while True:
        try:
            os.mkdir(lock_path)
            acquired = True
            break
        except FileExistsError:
            try:
                age = time.time() - lock_path.stat().st_mtime
            except FileNotFoundError:
                continue
            if age > stale:
                try:
                    lock_path.rmdir()
                except OSError:
                    pass
                continue
            if time.monotonic() - start >= timeout:
                raise StoreError(f"{lock_path}: ロックが取れない（他の処理が使用中の可能性がある）")
            time.sleep(0.1)
    try:
        yield
    finally:
        if acquired:
            try:
                lock_path.rmdir()
            except OSError:
                pass
