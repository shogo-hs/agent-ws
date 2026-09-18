"""store.py / validate.py の適合テスト。標準ライブラリだけで動く（unittest）。

実体を変えるテストは fixture を一時ディレクトリに写してから行う（取り決め通り）。
"""
from __future__ import annotations

import datetime
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from wsonto import schema, store, validate  # noqa: E402
from wsonto.errors import StoreError  # noqa: E402

FIXTURE_BASE = Path(__file__).resolve().parent / "fixtures" / "onto_case"


class OntoCaseTest(unittest.TestCase):
    """common / project の fixture を一時ディレクトリに写して Store を組む。"""

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        base = Path(tmp.name)
        shutil.copytree(FIXTURE_BASE / "common", base / "common")
        shutil.copytree(FIXTURE_BASE / "project", base / "project")
        self.common_dir = base / "common"
        self.project_dir = base / "project"
        self.common_schema = schema.load_schema(self.common_dir)
        self.project_schema = schema.load_schema(self.project_dir, common_dir=self.common_dir)
        self.common_store = store.Store(self.common_dir, self.common_schema)
        self.project_store = store.Store(self.project_dir, self.project_schema, common=self.common_store)


# --- validate: fixture 自体は違反 0 件 -------------------------------------


class FixtureValidatesCleanTest(OntoCaseTest):
    def test_common_validates_clean(self) -> None:
        self.assertEqual(validate.validate(self.common_store), [])

    def test_project_validates_clean(self) -> None:
        self.assertEqual(validate.validate(self.project_store), [])


# --- ObjView: リンク・逆向き・日付の変換 -----------------------------------


class ObjViewLinkTest(OntoCaseTest):
    def test_supersedes_is_single_objview(self) -> None:
        sd2 = self.project_store.get("SizingDecision:SD-2")
        supersedes = sd2.onto_get("supersedes")
        self.assertEqual(supersedes.ref, "SizingDecision:SD-1")

    def test_superseded_by_is_single_objview(self) -> None:
        sd1 = self.project_store.get("SizingDecision:SD-1")
        superseded_by = sd1.onto_get("superseded_by")
        self.assertEqual(superseded_by.ref, "SizingDecision:SD-2")

    def test_date_property_becomes_date(self) -> None:
        sd2 = self.project_store.get("SizingDecision:SD-2")
        self.assertEqual(sd2.onto_get("decided_on"), datetime.date(2026, 9, 2))

    def test_status_is_active(self) -> None:
        sd2 = self.project_store.get("SizingDecision:SD-2")
        self.assertEqual(sd2.onto_get("status"), "active")

    def test_unknown_name_raises_keyerror(self) -> None:
        d1 = self.project_store.get("Decision:D-1")
        with self.assertRaises(KeyError):
            d1.onto_get("no_such_name")


class CommonThroughProjectTest(OntoCaseTest):
    """案件の Store 経由で共通の実体を引いたときの forward/inverse。"""

    def test_find_sato_via_project_returns_common_person(self) -> None:
        sato = self.project_store.find("Person", "sato")
        self.assertIsNotNone(sato)
        self.assertEqual(sato.type, "Person")
        authorities = sato.onto_get("authorities")
        self.assertEqual(len(authorities), 1)
        self.assertEqual(authorities[0].onto_get("limit_yen"), 5000000)
        self.assertEqual(sato.onto_get("leads"), [])

    def test_find_tanaka_is_stakeholder(self) -> None:
        tanaka = self.project_store.find("Person", "tanaka")
        self.assertEqual(tanaka.type, "Stakeholder")
        leads = tanaka.onto_get("leads")
        self.assertEqual([o.ref for o in leads], ["Workstream:ws-idp"])

    def test_find_ambiguous_raises_storeerror(self) -> None:
        # 同じ id を Decision とその下位の SizingDecision の両方に仕込むと 2 件当たる。
        self.project_store.doc["Decision"]["D-dup"] = {
            "title": "重複1", "decided_on": "2026-09-01", "status": "active", "source": "テスト",
        }
        self.project_store.doc["SizingDecision"]["D-dup"] = {
            "title": "重複2", "nodes": 1, "decided_on": "2026-09-01", "status": "active", "source": "テスト",
        }
        with self.assertRaises(StoreError):
            self.project_store.find("Decision", "D-dup")


class AllTest(OntoCaseTest):
    def test_all_person_includes_stakeholder_and_common(self) -> None:
        people = self.project_store.all("Person")
        self.assertEqual(sum(1 for p in people if p.type == "Stakeholder"), 2)
        self.assertEqual(sum(1 for p in people if p.type == "Person"), 4)

    def test_all_decision_includes_subtypes(self) -> None:
        decisions = self.project_store.all("Decision")
        self.assertEqual(sorted(d.id for d in decisions), ["D-1", "SD-1", "SD-2"])


class ToDictTest(OntoCaseTest):
    def test_agent_true_hides_email_and_phone(self) -> None:
        yamada = self.project_store.get("Stakeholder:yamada")
        full = yamada.to_dict(agent=False)
        agent = yamada.to_dict(agent=True)
        self.assertIn("email", full)
        self.assertIn("phone", full)
        self.assertNotIn("email", agent)
        self.assertNotIn("phone", agent)


# --- validate: 違反の検出（1 件ずつ） ---------------------------------------


class ViolationDetectionTest(OntoCaseTest):
    def test_workstream_missing_state_keeps_default(self) -> None:
        del self.project_store.doc["Workstream"]["ws-idp"]["state"]
        violations = validate.validate(self.project_store, refs=["Workstream:ws-idp"])
        self.assertEqual(violations, [])

    def test_decision_status_unknown_is_in(self) -> None:
        self.project_store.doc["Decision"]["D-1"]["status"] = "unknown"
        violations = validate.validate(self.project_store, refs=["Decision:D-1"])
        self.assertTrue(any(v.code == "IN" for v in violations), violations)

    def test_price_item_negative_is_min_inclusive(self) -> None:
        self.project_store.doc["PriceItem"]["pi-node"]["unit_price_yen"] = -1
        violations = validate.validate(self.project_store, refs=["PriceItem:pi-node"])
        self.assertTrue(any(v.code == "MIN_INCLUSIVE" for v in violations), violations)

    def test_action_item_owner_missing_is_min_count(self) -> None:
        del self.project_store.doc["ActionItem"]["A-1"]["_links"]["owner"]
        violations = validate.validate(self.project_store, refs=["ActionItem:A-1"])
        self.assertTrue(
            any(v.code == "MIN_COUNT" and v.path == "owner" for v in violations), violations
        )

    def test_action_item_owner_two_people_is_max_count(self) -> None:
        self.project_store.doc["ActionItem"]["A-1"]["_links"]["owner"] = [
            "Stakeholder:yamada", "Stakeholder:tanaka",
        ]
        violations = validate.validate(self.project_store, refs=["ActionItem:A-1"])
        self.assertTrue(
            any(v.code == "MAX_COUNT" and v.path == "owner" for v in violations), violations
        )

    def test_second_decision_replacing_sd1_is_max_count(self) -> None:
        self.project_store.doc["SizingDecision"]["SD-3"] = {
            "title": "再見直し", "nodes": 10, "decided_on": "2026-09-05",
            "status": "active", "source": "テスト",
            "_links": {"supersedes": ["SizingDecision:SD-1"]},
        }
        violations = validate.validate(self.project_store, refs=["SizingDecision:SD-3"])
        self.assertTrue(
            any(
                v.code == "MAX_COUNT" and v.ref == "SizingDecision:SD-1"
                for v in violations
            ),
            violations,
        )

    def test_dangling_link_is_node(self) -> None:
        self.project_store.doc["ActionItem"]["A-1"]["_links"]["owner"] = ["Stakeholder:ghost"]
        violations = validate.validate(self.project_store, refs=["ActionItem:A-1"])
        self.assertTrue(any(v.code == "NODE" for v in violations), violations)

    def test_owner_wrong_type_is_class(self) -> None:
        self.project_store.doc["ActionItem"]["A-1"]["_links"]["owner"] = ["CustomerSystem:orders"]
        violations = validate.validate(self.project_store, refs=["ActionItem:A-1"])
        self.assertTrue(any(v.code == "CLASS" for v in violations), violations)

    def test_undefined_property_is_closed(self) -> None:
        self.project_store.doc["Decision"]["D-1"]["not_a_real_prop"] = "x"
        violations = validate.validate(self.project_store, refs=["Decision:D-1"])
        self.assertTrue(
            any(v.code == "CLOSED" and v.path == "not_a_real_prop" for v in violations), violations
        )

    def test_department_duplicate_name_is_unique(self) -> None:
        self.common_store.doc["Department"]["tech2"] = {"name": "技術部"}
        violations = validate.validate(self.common_store, refs=["Department:tech2"])
        self.assertTrue(any(v.code == "UNIQUE" for v in violations), violations)

    def test_required_title_missing_is_min_count(self) -> None:
        del self.project_store.doc["Decision"]["D-1"]["title"]
        violations = validate.validate(self.project_store, refs=["Decision:D-1"])
        self.assertTrue(
            any(v.code == "MIN_COUNT" and v.path == "title" for v in violations), violations
        )

    def test_bad_date_format_is_datatype(self) -> None:
        self.project_store.doc["SizingDecision"]["SD-2"]["decided_on"] = "2026/09/02"
        violations = validate.validate(self.project_store, refs=["SizingDecision:SD-2"])
        self.assertTrue(
            any(v.code == "DATATYPE" and v.path == "decided_on" for v in violations), violations
        )


# --- Store: commit / snapshot / next_seq / locked --------------------------


class CommitTest(OntoCaseTest):
    def test_commit_changes_file_hash(self) -> None:
        before = self.project_store.file_hash()
        self.project_store.put(
            "Meeting", "m-test", {"title": "臨時会議", "held_on": "2026-09-10"}, {}
        )
        new_hash = self.project_store.commit()
        after = self.project_store.file_hash()
        self.assertEqual(new_hash, after)
        self.assertNotEqual(before, after)
        reloaded = store.Store(self.project_dir, self.project_schema, common=self.common_store)
        self.assertIn("m-test", reloaded.doc["Meeting"])

    def test_missing_file_hash_is_empty_string(self) -> None:
        (self.project_dir / "objects.json").unlink()
        self.assertEqual(self.project_store.file_hash(), "")


class SnapshotTest(OntoCaseTest):
    def test_snapshot_does_not_affect_original(self) -> None:
        snap = self.project_store.snapshot()
        snap.put("Meeting", "m-snap", {"title": "スナップ用", "held_on": "2026-09-11"}, {})
        self.assertNotIn("m-snap", self.project_store.doc.get("Meeting", {}))
        self.assertIn("m-snap", snap.doc["Meeting"])


class NextSeqTest(OntoCaseTest):
    def test_next_seq_continues_from_meta(self) -> None:
        self.assertEqual(self.project_store.next_seq("SizingDecision"), 3)
        self.assertEqual(self.project_store.next_seq("SizingDecision"), 4)

    def test_next_seq_starts_at_one_for_unknown_type(self) -> None:
        self.assertEqual(self.project_store.next_seq("NewType"), 1)


class LockedTest(OntoCaseTest):
    def test_second_lock_times_out(self) -> None:
        with store.locked(self.project_dir, timeout=2.0):
            start = time.monotonic()
            with self.assertRaises(StoreError):
                with store.locked(self.project_dir, timeout=0.3):
                    pass
            self.assertLess(time.monotonic() - start, 2.0)

    def test_stale_lock_is_taken_over(self) -> None:
        lock_path = self.project_dir / ".lock"
        lock_path.mkdir()
        with store.locked(self.project_dir, timeout=1.0, stale=0.0):
            pass
        self.assertFalse(lock_path.exists())


if __name__ == "__main__":
    unittest.main()
