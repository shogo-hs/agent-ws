"""engine.py / evals.py の適合テスト。標準ライブラリだけで動く（unittest）。

実体を変えるテストは fixture を一時ディレクトリに写してから行う（取り決め通り）。
"""
from __future__ import annotations

import datetime
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from wsonto import engine, evals, schema, store  # noqa: E402
from wsonto.errors import OntoError  # noqa: E402

FIXTURE_BASE = Path(__file__).resolve().parent / "fixtures" / "onto_case"
TODAY = datetime.date(2026, 9, 16)

AGENT = engine.Actor("agent", "test-agent", "s1")
HUMAN = engine.Actor("human", "reviewer")


def _base_estimate_params(**overrides) -> dict:
    params = {
        "title": "運用の見積", "sizing": "SD-2", "items": "pi-node,pi-monitor",
        "months": "12", "approver": "sato",
    }
    params.update(overrides)
    return params


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
        self._orig_project_objects = (self.project_dir / "objects.json").read_bytes()
        self._orig_common_objects = (self.common_dir / "objects.json").read_bytes()

    def assertProjectObjectsUnchanged(self) -> None:
        self.assertEqual((self.project_dir / "objects.json").read_bytes(), self._orig_project_objects)

    def assertCommonObjectsUnchanged(self) -> None:
        self.assertEqual((self.common_dir / "objects.json").read_bytes(), self._orig_common_objects)


# --- IssueEstimate: 前提条件・計算・承認 -------------------------------------


class IssueEstimateTest(OntoCaseTest):
    def test_sd1_rejected_keeps_objects_unchanged(self) -> None:
        result = engine.act(
            self.project_store, "IssueEstimate", _base_estimate_params(sizing="SD-1"), AGENT, today=TODAY,
        )
        self.assertEqual(result.status, "rejected")
        self.assertEqual(
            result.messages,
            ["置き換え済みの決定（提案時の台数・8 台）を前提にしている。現行の決定は PoC の結果で見直した台数（12 台）"],
        )
        self.assertProjectObjectsUnchanged()

    def test_12_nodes_committed(self) -> None:
        result = engine.act(
            self.project_store, "IssueEstimate", _base_estimate_params(), AGENT, today=TODAY,
        )
        self.assertEqual(result.status, "committed")
        self.assertEqual(result.returned, "Estimate:E-1")
        self.assertIn("月額 410000 円", result.next)

        est = self.project_store.get("Estimate:E-1")
        self.assertIsNotNone(est)
        self.assertEqual(est.onto_get("nodes"), 12)
        self.assertEqual(est.onto_get("monthly_yen"), 410000)
        self.assertEqual(est.onto_get("total_yen"), 4920000)
        self.assertEqual(est.onto_get("based_on").ref, "SizingDecision:SD-2")
        self.assertEqual(sorted(o.ref for o in est.onto_get("priced_by")), ["PriceItem:pi-monitor", "PriceItem:pi-node"])
        self.assertEqual(est.onto_get("approver").ref, "Person:sato")
        self.assertCommonObjectsUnchanged()

    def test_expired_price_rejected(self) -> None:
        result = engine.act(
            self.project_store, "IssueEstimate", _base_estimate_params(items="pi-node-old"), AGENT, today=TODAY,
        )
        self.assertEqual(result.status, "rejected")
        self.assertEqual(result.messages, ["有効期限の切れた単価が含まれている"])

    def test_takahashi_no_authority_rejected(self) -> None:
        result = engine.act(
            self.project_store, "IssueEstimate",
            _base_estimate_params(items="pi-node", approver="takahashi"), AGENT, today=TODAY,
        )
        self.assertEqual(result.status, "rejected")
        self.assertEqual(result.messages, ["高橋一郎 に見積の決裁権限が無い"])

    def test_multiple_criteria_fail_together(self) -> None:
        result = engine.act(
            self.project_store, "IssueEstimate",
            _base_estimate_params(sizing="SD-1", items="pi-node-old", approver="takahashi"), AGENT, today=TODAY,
        )
        self.assertEqual(result.status, "rejected")
        self.assertEqual(len(result.messages), 3)

    def test_human_direct_action_still_stages_when_approval_required(self) -> None:
        # 人が直接 act しても、承認の要否（stage_if）はそのまま評価される。
        # 承認そのものは相変わらず人だけができる。
        result = engine.act(
            self.project_store, "IssueEstimate", _base_estimate_params(months="24"), HUMAN, today=TODAY,
        )
        self.assertEqual(result.status, "staged")
        self.assertIsNotNone(result.proposal_id)
        self.project_store.reload()
        self.assertNotIn("E-1", self.project_store.doc.get("Estimate", {}))

        approved = engine.approve(self.project_store, result.proposal_id, HUMAN, today=TODAY)
        self.assertEqual(approved.status, "committed")
        est = self.project_store.get("Estimate:E-1")
        self.assertIsNotNone(est)


class IssueEstimateArgumentErrorsTest(OntoCaseTest):
    def test_unknown_argument(self) -> None:
        result = engine.act(
            self.project_store, "IssueEstimate", _base_estimate_params(bogus="x"), AGENT, today=TODAY,
        )
        self.assertEqual(result.status, "rejected")
        self.assertTrue(any("bogus" in m for m in result.messages), result.messages)

    def test_missing_required_argument(self) -> None:
        params = _base_estimate_params()
        del params["approver"]
        result = engine.act(self.project_store, "IssueEstimate", params, AGENT, today=TODAY)
        self.assertEqual(result.status, "rejected")
        self.assertTrue(any("approver" in m for m in result.messages), result.messages)

    def test_months_not_int(self) -> None:
        result = engine.act(
            self.project_store, "IssueEstimate", _base_estimate_params(months="abc"), AGENT, today=TODAY,
        )
        self.assertEqual(result.status, "rejected")
        self.assertTrue(any("months" in m for m in result.messages), result.messages)

    def test_months_below_min(self) -> None:
        result = engine.act(
            self.project_store, "IssueEstimate", _base_estimate_params(months="0"), AGENT, today=TODAY,
        )
        self.assertEqual(result.status, "rejected")
        self.assertTrue(any("months" in m for m in result.messages), result.messages)

    def test_sizing_not_found(self) -> None:
        result = engine.act(
            self.project_store, "IssueEstimate", _base_estimate_params(sizing="SD-999"), AGENT, today=TODAY,
        )
        self.assertEqual(result.status, "rejected")
        self.assertTrue(any("sizing" in m for m in result.messages), result.messages)

    def test_items_with_unknown_id(self) -> None:
        result = engine.act(
            self.project_store, "IssueEstimate", _base_estimate_params(items="pi-node,pi-ghost"), AGENT, today=TODAY,
        )
        self.assertEqual(result.status, "rejected")
        self.assertTrue(any("items" in m for m in result.messages), result.messages)


# --- 実行待ち・承認 ----------------------------------------------------------


class StagingAndApprovalTest(OntoCaseTest):
    def test_24_months_stages_then_human_approves(self) -> None:
        result = engine.act(
            self.project_store, "IssueEstimate", _base_estimate_params(months="24"), AGENT, today=TODAY,
        )
        self.assertEqual(result.status, "staged")
        self.assertIsNotNone(result.proposal_id)

        prop_path = self.project_dir / "proposals" / f"{result.proposal_id}.json"
        self.assertTrue(prop_path.exists())
        prop = json.loads(prop_path.read_text(encoding="utf-8"))
        self.assertEqual(prop["status"], "open")
        self.assertEqual(prop["action"], "IssueEstimate")

        self.project_store.reload()
        self.assertNotIn("E-1", self.project_store.doc.get("Estimate", {}))

        with self.assertRaises(OntoError):
            engine.approve(self.project_store, result.proposal_id, AGENT, today=TODAY)

        approved = engine.approve(self.project_store, result.proposal_id, HUMAN, today=TODAY)
        self.assertEqual(approved.status, "committed")
        est = self.project_store.get("Estimate:E-1")
        self.assertIsNotNone(est)
        self.assertEqual(est.onto_get("total_yen"), 9840000)

        prop = json.loads(prop_path.read_text(encoding="utf-8"))
        self.assertEqual(prop["status"], "approved")

    def test_superseded_sizing_rejects_approval_and_keeps_proposal_open(self) -> None:
        staged = engine.act(
            self.project_store, "IssueEstimate", _base_estimate_params(months="24"), AGENT, today=TODAY,
        )
        self.assertEqual(staged.status, "staged")

        record = engine.act(
            self.project_store, "RecordSizingDecision",
            {"title": "16台への見直し", "nodes": "16", "decided_on": "2026-09-10", "source": "2026-09-10 定例",
             "supersedes": "SD-2"},
            AGENT, today=TODAY,
        )
        self.assertEqual(record.status, "committed")

        result = engine.approve(self.project_store, staged.proposal_id, HUMAN, today=TODAY)
        self.assertEqual(result.status, "rejected")
        self.assertTrue(any("置き換え済み" in m for m in result.messages), result.messages)

        prop_path = self.project_dir / "proposals" / f"{staged.proposal_id}.json"
        prop = json.loads(prop_path.read_text(encoding="utf-8"))
        self.assertEqual(prop["status"], "open")
        self.project_store.reload()
        self.assertNotIn("E-1", self.project_store.doc.get("Estimate", {}))


# --- RecordSizingDecision ----------------------------------------------------


class RecordSizingDecisionTest(OntoCaseTest):
    def test_supersedes_sets_status_and_inverse(self) -> None:
        result = engine.act(
            self.project_store, "RecordSizingDecision",
            {"title": "16台への見直し", "nodes": "16", "decided_on": "2026-09-10", "source": "2026-09-10 定例",
             "supersedes": "SD-2"},
            AGENT, today=TODAY,
        )
        self.assertEqual(result.status, "committed")
        self.assertEqual(result.returned, "SizingDecision:SD-3")

        sd2 = self.project_store.get("SizingDecision:SD-2")
        self.assertEqual(sd2.onto_get("status"), "superseded")
        self.assertEqual(sd2.onto_get("superseded_by").ref, "SizingDecision:SD-3")

    def test_supersedes_omitted_is_ok(self) -> None:
        result = engine.act(
            self.project_store, "RecordSizingDecision",
            {"title": "独立の見直し", "nodes": "20", "decided_on": "2026-09-10", "source": "2026-09-10 定例"},
            AGENT, today=TODAY,
        )
        self.assertEqual(result.status, "committed")

    def test_future_decided_on_rejected(self) -> None:
        result = engine.act(
            self.project_store, "RecordSizingDecision",
            {"title": "未来の決定", "nodes": "10", "decided_on": "2026-09-20", "source": "テスト"},
            AGENT, today=TODAY,
        )
        self.assertEqual(result.status, "rejected")
        self.assertEqual(result.messages, ["決定日が未来になっている"])


# --- ActionItem --------------------------------------------------------------


class ActionItemTest(OntoCaseTest):
    def test_close_twice_second_rejected(self) -> None:
        first = engine.act(self.project_store, "CloseActionItem", {"item": "A-1"}, AGENT, today=TODAY)
        self.assertEqual(first.status, "committed")
        second = engine.act(self.project_store, "CloseActionItem", {"item": "A-1"}, AGENT, today=TODAY)
        self.assertEqual(second.status, "rejected")
        self.assertEqual(second.messages, ["すでに完了している"])

    def test_add_action_item_without_meeting(self) -> None:
        result = engine.act(
            self.project_store, "AddActionItem",
            {"title": "資料を送る", "owner": "yamada"}, AGENT, today=TODAY,
        )
        self.assertEqual(result.status, "committed")
        item = self.project_store.get(result.returned)
        self.assertEqual(item.onto_get("raised_in"), None)


# --- dry_run -------------------------------------------------------------


class DryRunTest(OntoCaseTest):
    def test_dry_run_writes_nothing(self) -> None:
        result = engine.act(
            self.project_store, "IssueEstimate", _base_estimate_params(), AGENT, today=TODAY, dry_run=True,
        )
        self.assertEqual(result.status, "committed")
        self.assertProjectObjectsUnchanged()
        self.assertFalse((self.project_dir / "log.jsonl").exists())
        self.assertFalse((self.project_dir / "proposals").exists())

    def test_dry_run_staged_writes_nothing(self) -> None:
        result = engine.act(
            self.project_store, "IssueEstimate", _base_estimate_params(months="24"), AGENT, today=TODAY, dry_run=True,
        )
        self.assertEqual(result.status, "staged")
        self.assertProjectObjectsUnchanged()
        self.assertFalse((self.project_dir / "log.jsonl").exists())
        self.assertFalse((self.project_dir / "proposals").exists())


# --- 記録 ----------------------------------------------------------------


class LogTest(OntoCaseTest):
    def test_log_lines_have_required_fields(self) -> None:
        engine.act(
            self.project_store, "IssueEstimate", _base_estimate_params(), AGENT, today=TODAY,
            why="見積の依頼", task="tasks/20260916_estimate", refs=["Decision:D-1"],
        )
        engine.act(
            self.project_store, "IssueEstimate", _base_estimate_params(sizing="SD-1"), AGENT, today=TODAY,
        )
        engine.act(
            self.project_store, "IssueEstimate", _base_estimate_params(months="24"), AGENT, today=TODAY,
        )

        entries = engine.read_log(self.project_dir)
        self.assertEqual(len(entries), 3)
        statuses = [e["status"] for e in entries]
        self.assertEqual(statuses, ["committed", "rejected", "staged"])

        committed, rejected, staged = entries
        for e in entries:
            for key in ("ts", "actor", "params", "status", "schema", "store_hash_before", "store_hash_after"):
                self.assertIn(key, e)
            self.assertIn("hash", e["schema"])

        self.assertNotEqual(committed["store_hash_before"], committed["store_hash_after"])
        self.assertEqual(rejected["store_hash_before"], rejected["store_hash_after"])
        self.assertEqual(staged["store_hash_before"], staged["store_hash_after"])
        self.assertEqual(committed["task"], "tasks/20260916_estimate")
        self.assertEqual(committed["refs"], ["Decision:D-1"])

    def test_read_log_filters_by_object(self) -> None:
        engine.act(
            self.project_store, "IssueEstimate", _base_estimate_params(sizing="SD-2"), AGENT, today=TODAY,
        )
        matches = engine.read_log(self.project_dir, object="SizingDecision:SD-2")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["action"], "IssueEstimate")


class VerifyChainTest(OntoCaseTest):
    def test_no_log_is_empty(self) -> None:
        self.assertEqual(engine.verify_chain(self.project_store), [])

    def test_after_act_matches(self) -> None:
        engine.act(self.project_store, "IssueEstimate", _base_estimate_params(), AGENT, today=TODAY)
        self.assertEqual(engine.verify_chain(self.project_store), [])

    def test_hand_edit_is_detected(self) -> None:
        engine.act(self.project_store, "IssueEstimate", _base_estimate_params(), AGENT, today=TODAY)
        doc = json.loads((self.project_dir / "objects.json").read_text(encoding="utf-8"))
        doc.setdefault("Meeting", {})["m-hand"] = {"title": "手で足した", "held_on": "2026-09-16"}
        (self.project_dir / "objects.json").write_text(
            json.dumps(doc, sort_keys=True, indent=1, ensure_ascii=False) + "\n", encoding="utf-8",
        )
        issues = engine.verify_chain(self.project_store)
        self.assertEqual(len(issues), 1)

    def test_agent_adopt_raises(self) -> None:
        with self.assertRaises(OntoError):
            engine.adopt(self.project_store, AGENT, "手で直した")

    def test_human_adopt_clears_chain(self) -> None:
        engine.act(self.project_store, "IssueEstimate", _base_estimate_params(), AGENT, today=TODAY)
        doc = json.loads((self.project_dir / "objects.json").read_text(encoding="utf-8"))
        doc.setdefault("Meeting", {})["m-hand"] = {"title": "手で足した", "held_on": "2026-09-16"}
        (self.project_dir / "objects.json").write_text(
            json.dumps(doc, sort_keys=True, indent=1, ensure_ascii=False) + "\n", encoding="utf-8",
        )
        self.assertEqual(len(engine.verify_chain(self.project_store)), 1)
        engine.adopt(self.project_store, HUMAN, "手で直した分を取り込む")
        self.assertEqual(engine.verify_chain(self.project_store), [])


# --- 共通の store: TransferPerson --------------------------------------------


class TransferPersonTest(OntoCaseTest):
    def test_agent_stages_human_approves(self) -> None:
        result = engine.act(
            self.common_store, "TransferPerson", {"person": "suzuki", "to": "tech"}, AGENT, today=TODAY,
        )
        self.assertEqual(result.status, "staged")

        approved = engine.approve(self.common_store, result.proposal_id, HUMAN, today=TODAY)
        self.assertEqual(approved.status, "committed")

        suzuki = self.common_store.get("Person:suzuki")
        self.assertEqual(suzuki.onto_get("belongs_to").ref, "Department:tech")
        keiei = self.common_store.get("Department:keiei")
        self.assertNotIn("Person:suzuki", [m.ref for m in keiei.onto_get("members")])


# --- 検証による取り消し（④） --------------------------------------------------


class ValidateRollbackTest(unittest.TestCase):
    """validate 違反での rejected は objects.json を一切書かない。"""

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        doc = {
            "ontology": "rollback-test", "version": 1,
            "object_types": {
                "Widget": {
                    "label": "Widget", "summary": ["price"],
                    "properties": {"price": {"type": "int", "required": True, "min": 0, "label": "Price"}},
                },
            },
            "action_types": {
                "SetPrice": {
                    "label": "Set price",
                    "description": "テスト用の最小アクション。price をそのまま設定する。",
                    "parameters": {"price": {"type": "int", "required": True, "label": "Price"}},
                    "rules": [{"create": "Widget", "as": "w", "id": "W-{seq}", "set": {"price": "price"}}],
                    "approval": "auto", "returns": "w",
                },
            },
        }
        self.schema = schema.parse_schema(doc)
        self.store = store.Store(self.dir, self.schema)

    def test_negative_price_rejected_and_no_file_written(self) -> None:
        result = engine.act(self.store, "SetPrice", {"price": "-1"}, AGENT, today=TODAY)
        self.assertEqual(result.status, "rejected")
        self.assertTrue(result.violations)
        self.assertFalse((self.dir / "objects.json").exists())

        log_path = self.dir / "log.jsonl"
        self.assertTrue(log_path.exists())
        lines = log_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1)
        entry = json.loads(lines[0])
        self.assertEqual(entry["status"], "rejected")


# --- evals.run_questions ------------------------------------------------


class RunQuestionsTest(OntoCaseTest):
    def _questions_doc(self) -> dict:
        return json.loads((FIXTURE_BASE / "project" / "questions.json").read_text(encoding="utf-8"))

    def test_fixture_questions_all_ok(self) -> None:
        doc = self._questions_doc()
        results = evals.run_questions(self.project_store, doc, AGENT)
        self.assertEqual(len(results), len(doc["questions"]))
        failed = [(r.id, r.detail) for r in results if not r.ok]
        self.assertEqual(failed, [])

    def test_tampered_expectation_is_not_ok(self) -> None:
        doc = self._questions_doc()
        for q in doc["questions"]:
            if q["id"] == "Q3":
                q["expect"]["ids"] = ["SD-1"]  # わざと誤った期待にする
        results = evals.run_questions(self.project_store, doc, AGENT)
        by_id = {r.id: r for r in results}
        self.assertFalse(by_id["Q3"].ok)
        self.assertTrue(by_id["Q3"].detail)

    def test_run_questions_does_not_touch_real_store(self) -> None:
        before_objects = (self.project_dir / "objects.json").read_bytes()
        log_path = self.project_dir / "log.jsonl"
        log_existed_before = log_path.exists()

        evals.run_questions(self.project_store, self._questions_doc(), AGENT)

        self.assertEqual((self.project_dir / "objects.json").read_bytes(), before_objects)
        self.assertEqual(log_path.exists(), log_existed_before)


# --- ④ 検証は写し全体を見る（X-1） -------------------------------------------


class WholeStoreValidateTest(unittest.TestCase):
    """delete / unlink で宙に浮いたリンクが検査されず反映されてしまわないこと。"""

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        doc = {
            "ontology": "x1-test", "version": 1,
            "object_types": {
                "Task": {
                    "label": "Task", "summary": ["title"],
                    "properties": {"title": {"type": "string", "required": True, "label": "Title"}},
                },
                "Note": {
                    "label": "Note", "summary": ["title"],
                    "properties": {"title": {"type": "string", "required": True, "label": "Title"}},
                },
                "Log": {
                    "label": "Log", "summary": ["title"],
                    "properties": {"title": {"type": "string", "required": True, "label": "Title"}},
                },
            },
            "link_types": {
                "about": {
                    "label": "about", "from": "Note", "to": "Task", "min": 1,
                    "inverse": "notes", "inverse_label": "notes", "inverse_min": 1,
                },
            },
            "action_types": {
                "DeleteTask": {
                    "label": "Delete task",
                    "description": "テスト用: task を削除する（宙に浮いたリンクの検査を確かめる）。",
                    "parameters": {"task": {"object_type": "Task", "required": True, "label": "Task"}},
                    "rules": [{"delete": "task"}],
                    "approval": "auto",
                },
                "UnlinkNote": {
                    "label": "Unlink note",
                    "description": "テスト用: note の about を外す（inverse_min の検査を確かめる）。",
                    "parameters": {"note": {"object_type": "Note", "required": True, "label": "Note"}},
                    "rules": [{"modify": "note", "unlink": {"about": "note.about"}}],
                    "approval": "auto",
                },
                "AddLog": {
                    "label": "Add log",
                    "description": "テスト用: 無関係な正当なアクション（既存の違反があっても通ることを確かめる）。",
                    "parameters": {"title": {"type": "string", "required": True, "label": "Title"}},
                    "rules": [{"create": "Log", "as": "l", "id": "L-{seq}", "set": {"title": "title"}}],
                    "approval": "auto", "returns": "l",
                },
            },
        }
        self.schema = schema.parse_schema(doc)
        (self.dir / "objects.json").write_text(json.dumps({
            "_meta": {"seq": {}},
            "Task": {"t1": {"title": "Task 1"}},
            "Note": {
                "n1": {"title": "Note 1", "_links": {"about": ["Task:t1"]}},
                # 実行前から在る無関係な違反（先の無いリンク）。
                "n2": {"title": "Note 2", "_links": {"about": ["Task:ghost"]}},
            },
        }, ensure_ascii=False), encoding="utf-8")
        self.store = store.Store(self.dir, self.schema)

    def test_delete_leaves_dangling_link_and_is_rejected(self) -> None:
        result = engine.act(self.store, "DeleteTask", {"task": "t1"}, AGENT, today=TODAY)
        self.assertEqual(result.status, "rejected")
        self.assertTrue(
            any("about" in m and "Task:t1" in m and "見つからない" in m for m in result.messages),
            result.messages,
        )
        after = json.loads((self.dir / "objects.json").read_text(encoding="utf-8"))
        self.assertIn("t1", after["Task"])

    def test_unlink_breaks_inverse_min_and_is_rejected(self) -> None:
        result = engine.act(self.store, "UnlinkNote", {"note": "n1"}, AGENT, today=TODAY)
        self.assertEqual(result.status, "rejected")
        after = json.loads((self.dir / "objects.json").read_text(encoding="utf-8"))
        self.assertEqual(after["Note"]["n1"].get("_links", {}).get("about"), ["Task:t1"])

    def test_preexisting_unrelated_violation_does_not_block_valid_action(self) -> None:
        result = engine.act(self.store, "AddLog", {"title": "新しい仕事"}, AGENT, today=TODAY)
        self.assertEqual(result.status, "committed")


# --- 案件のアクションは共通の実体を modify / delete できない（X-3） -----------


class CommonEntityProtectionTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        base = Path(tmp.name)
        self.common_dir = base / "common"
        self.project_dir = base / "project"
        self.common_dir.mkdir()
        self.project_dir.mkdir()

        common_doc = {
            "ontology": "common-x3", "version": 1,
            "object_types": {
                "Person": {
                    "label": "Person", "summary": ["name"],
                    "properties": {"name": {"type": "string", "required": True, "label": "Name"}},
                },
            },
        }
        (self.common_dir / "ontology.json").write_text(
            json.dumps(common_doc, ensure_ascii=False), encoding="utf-8",
        )
        (self.common_dir / "objects.json").write_text(
            json.dumps({"_meta": {"seq": {}}, "Person": {"sato": {"name": "Sato"}}}, ensure_ascii=False),
            encoding="utf-8",
        )
        self._orig_common_objects = (self.common_dir / "objects.json").read_bytes()

        project_doc = {
            "ontology": "project-x3", "version": 1,
            "action_types": {
                "RenamePerson": {
                    "label": "Rename person",
                    "description": "テスト用: 案件のアクションから共通の Person を modify しようとする。",
                    "parameters": {
                        "person": {"object_type": "Person", "required": True, "label": "Person"},
                        "name": {"type": "string", "required": True, "label": "Name"},
                    },
                    "rules": [{"modify": "person", "set": {"name": "name"}}],
                    "approval": "auto",
                },
            },
        }
        (self.project_dir / "ontology.json").write_text(
            json.dumps(project_doc, ensure_ascii=False), encoding="utf-8",
        )
        (self.project_dir / "objects.json").write_text(
            json.dumps({"_meta": {"seq": {}}}, ensure_ascii=False), encoding="utf-8",
        )

        self.common_schema = schema.load_schema(self.common_dir)
        self.project_schema = schema.load_schema(self.project_dir, common_dir=self.common_dir)
        self.common_store = store.Store(self.common_dir, self.common_schema)
        self.project_store = store.Store(self.project_dir, self.project_schema, common=self.common_store)

    def test_modify_common_entity_is_rejected(self) -> None:
        result = engine.act(
            self.project_store, "RenamePerson", {"person": "sato", "name": "Suzuki"}, AGENT, today=TODAY,
        )
        self.assertEqual(result.status, "rejected")
        self.assertTrue(any("共通" in m and "Person:sato" in m for m in result.messages), result.messages)
        self.assertEqual((self.common_dir / "objects.json").read_bytes(), self._orig_common_objects)

        entries = engine.read_log(self.project_dir)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["status"], "rejected")


class InternalErrorSafetyNetTest(OntoCaseTest):
    """ルールの評価などで想定外の例外が出ても、スタックトレースで落とさず rejected で記録する。"""

    def test_unexpected_exception_in_rule_is_rejected_not_crashed(self) -> None:
        class _BrokenExpr:
            def eval(self, env):
                raise KeyError("boom")

        at = self.project_store.schema.action_types["AddActionItem"]
        original = at.rules[0]["set"]["title"]
        at.rules[0]["set"]["title"] = _BrokenExpr()
        try:
            result = engine.act(
                self.project_store, "AddActionItem",
                {"title": "資料を送る", "owner": "yamada"}, AGENT, today=TODAY,
            )
        finally:
            at.rules[0]["set"]["title"] = original

        self.assertEqual(result.status, "rejected")
        self.assertTrue(any("内部エラー" in m and "KeyError" in m for m in result.messages), result.messages)
        entries = engine.read_log(self.project_dir)
        self.assertEqual(entries[-1]["status"], "rejected")


# --- エンジンの前提条件は非表示のプロパティも読める（X-4） --------------------


class CriteriaCanReadHiddenPropertyTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        doc = {
            "ontology": "x4-test", "version": 1,
            "object_types": {
                "Person": {
                    "label": "Person", "summary": ["name"],
                    "properties": {
                        "name": {"type": "string", "required": True, "label": "Name"},
                        "secret_code": {"type": "string", "label": "Code", "agent_visible": False},
                    },
                },
            },
            "action_types": {
                "CheckCode": {
                    "label": "Check code",
                    "description": "テスト用: 非表示のプロパティを前提条件で読む。",
                    "parameters": {"person": {"object_type": "Person", "required": True, "label": "Person"}},
                    "criteria": [
                        {"when": "person.secret_code == 'abc'", "message": "コードが違う"},
                    ],
                    "approval": "auto",
                },
            },
        }
        self.schema = schema.parse_schema(doc)
        (self.dir / "objects.json").write_text(json.dumps({
            "_meta": {"seq": {}},
            "Person": {"p1": {"name": "Taro", "secret_code": "abc"}},
        }, ensure_ascii=False), encoding="utf-8")
        self.store = store.Store(self.dir, self.schema)

    def test_criterion_reads_hidden_property_directly(self) -> None:
        result = engine.act(self.store, "CheckCode", {"person": "p1"}, AGENT, today=TODAY)
        self.assertEqual(result.status, "committed")


# --- 壊れた記録の行があっても落ちない（X-6） ----------------------------------


class BrokenLogLineTest(OntoCaseTest):
    def test_merge_conflict_marker_line_is_skipped_not_crashed(self) -> None:
        engine.act(self.project_store, "IssueEstimate", _base_estimate_params(), AGENT, today=TODAY)
        log_path = self.project_dir / "log.jsonl"
        with log_path.open("a", encoding="utf-8") as f:
            f.write("<<<<<<< HEAD\n")

        entries = engine.read_log(self.project_dir)
        self.assertEqual(len(entries), 1)  # 壊れた行は飛ばす

        issues = engine.verify_chain(self.project_store)
        self.assertEqual(len(issues), 1)
        self.assertIn("2 行目", issues[0])
        self.assertIn("読めない", issues[0])


if __name__ == "__main__":
    unittest.main()
