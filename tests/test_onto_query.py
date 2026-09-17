"""query.py（query / show / format_rows / format_show）の適合テスト。

標準ライブラリだけで動く（unittest）。実体を変えるテストは fixture を一時ディレクトリに
写してから行う（取り決め通り）。
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

from wsonto import query, schema, store  # noqa: E402
from wsonto.errors import ExprError, OntoError  # noqa: E402

FIXTURE_BASE = Path(__file__).resolve().parent / "fixtures" / "onto_case"
TODAY = datetime.date(2026, 9, 16)


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


# --- questions.json の Q1〜Q3 と同じ照会 ------------------------------------


class QuestionsParityTest(OntoCaseTest):
    def test_q1_person_leads_idp(self) -> None:
        rows, total = query.query(
            self.project_store, "Person", "any('IdP' in w.name for w in leads)"
        )
        self.assertEqual([r["id"] for r in rows], ["tanaka"])
        self.assertEqual(total, 1)

    def test_q2_customer_system_affected_by_idp(self) -> None:
        rows, total = query.query(
            self.project_store, "CustomerSystem", "any('IdP' in w.name for w in affected_by)"
        )
        self.assertEqual([r["id"] for r in rows], ["billing", "inventory", "orders"])
        self.assertEqual(total, 3)

    def test_q3_sizing_decision_active(self) -> None:
        rows, total = query.query(self.project_store, "SizingDecision", "status == 'active'")
        self.assertEqual([r["id"] for r in rows], ["SD-2"])
        self.assertEqual(total, 1)


# --- 上位の型での照会（下位にしか無い名前） ---------------------------------


class SupertypeQueryTest(OntoCaseTest):
    def test_decision_query_includes_all_subtypes(self) -> None:
        rows, total = query.query(self.project_store, "Decision")
        self.assertEqual([r["id"] for r in rows], ["D-1", "SD-1", "SD-2"])
        self.assertEqual(total, 3)

    def test_decision_query_skips_entities_without_the_name(self) -> None:
        rows, total = query.query(self.project_store, "Decision", "nodes >= 10")
        self.assertEqual([r["id"] for r in rows], ["SD-2"])
        self.assertEqual(total, 1)

    def test_name_no_entity_has_is_exprerror(self) -> None:
        with self.assertRaises(ExprError):
            query.query(self.project_store, "Decision", "no_such_name_xyz == 1")


# --- リンク先の値での絞り込み・日付・定数 -----------------------------------


class LinkAndDateFilterTest(OntoCaseTest):
    def test_action_item_owner_name_and_state(self) -> None:
        rows, total = query.query(
            self.project_store, "ActionItem", "owner.name == '山田太郎' and state == 'open'"
        )
        self.assertEqual([r["id"] for r in rows], ["A-1"])
        self.assertEqual(total, 1)

    def test_price_item_expired_by_days_since(self) -> None:
        rows, total = query.query(
            self.project_store,
            "PriceItem",
            "valid_until is not None and days_since(valid_until) > 0",
            today=TODAY,
        )
        self.assertEqual([r["id"] for r in rows], ["pi-node-old"])
        self.assertEqual(total, 1)

    def test_constant_is_usable_in_where(self) -> None:
        rows, total = query.query(
            self.project_store, "PriceItem", "MIN_CONTRACT_MONTHS == 1"
        )
        self.assertEqual(total, 3)


# --- select ------------------------------------------------------------


class SelectTest(OntoCaseTest):
    def test_link_dot_prop_select(self) -> None:
        rows, _ = query.query(
            self.project_store,
            "SizingDecision",
            select=["title", "supersedes.title", "superseded_by.title"],
        )
        by_id = {r["id"]: r for r in rows}
        self.assertEqual(by_id["SD-1"]["supersedes.title"], None)
        self.assertEqual(by_id["SD-1"]["superseded_by.title"], "PoC の結果で見直した台数")
        self.assertEqual(by_id["SD-2"]["supersedes.title"], "提案時の台数")
        self.assertEqual(by_id["SD-2"]["superseded_by.title"], None)
        # id は常に先頭
        self.assertEqual(next(iter(by_id["SD-1"])), "id")

    def test_default_select_is_summary_of_concrete_type(self) -> None:
        rows, _ = query.query(self.project_store, "SizingDecision")
        self.assertEqual(
            set(rows[0].keys()), {"id", "type", "title", "nodes", "decided_on", "status"}
        )

    def test_agent_true_hides_email_value_with_placeholder(self) -> None:
        rows, _ = query.query(
            self.project_store,
            "Person",
            where="id == 'sato'",
            select=["name", "email"],
            agent=True,
        )
        self.assertEqual(rows[0]["email"], "（非表示）")

    def test_agent_false_shows_email_value(self) -> None:
        rows, _ = query.query(
            self.project_store,
            "Person",
            where="id == 'sato'",
            select=["name", "email"],
            agent=False,
        )
        self.assertEqual(rows[0]["email"], "sato@example.com")


# --- agent_visible: false の非表示が where / リンク越しの select にも及ぶ（X-4） ---


class HiddenPropertyQueryTest(OntoCaseTest):
    def test_where_on_hidden_prop_agent_vs_human(self) -> None:
        with self.assertRaises(ExprError):
            query.query(self.project_store, "Person", "email == 'sato@example.com'", agent=True)
        rows, total = query.query(
            self.project_store, "Person", "email == 'sato@example.com'", agent=False
        )
        self.assertEqual(total, 1)

    def test_select_link_prop_hides_subtype_only_hidden_prop_for_agent(self) -> None:
        # Workstream.lead は宣言上 Person だが、実際の相手は Stakeholder（phone が非表示）。
        rows_agent, _ = query.query(
            self.project_store, "Workstream", where="id == 'ws-poc'", select=["lead.phone"], agent=True,
        )
        self.assertEqual(rows_agent[0]["lead.phone"], "（非表示）")
        rows_human, _ = query.query(
            self.project_store, "Workstream", where="id == 'ws-poc'", select=["lead.phone"], agent=False,
        )
        self.assertEqual(rows_human[0]["lead.phone"], "03-0000-0000")

    def test_hide_hidden_flag_is_restored_after_query(self) -> None:
        query.query(self.project_store, "Person", agent=True)
        self.assertFalse(self.project_store.hide_hidden)
        self.assertFalse(self.common_store.hide_hidden)


# --- select に存在しない名前を渡すと OntoError（X-5） -------------------------


class SelectUnknownNameTest(OntoCaseTest):
    def test_unknown_select_name_raises_ontoerror_with_available_names(self) -> None:
        with self.assertRaises(OntoError) as cm:
            query.query(self.project_store, "Person", select=["nope"])
        msg = str(cm.exception)
        self.assertIn("nope", msg)
        self.assertIn("使える名前", msg)


# --- limit / 全件数 / id 順 --------------------------------------------------


class LimitAndOrderTest(OntoCaseTest):
    def test_limit_truncates_and_total_counts_all(self) -> None:
        rows, total = query.query(self.project_store, "PriceItem", limit=2)
        self.assertEqual([r["id"] for r in rows], ["pi-monitor", "pi-node"])
        self.assertEqual(total, 3)

    def test_limit_none_returns_all(self) -> None:
        rows, total = query.query(self.project_store, "PriceItem", limit=None)
        self.assertEqual(len(rows), 3)
        self.assertEqual(total, 3)


# --- エラー --------------------------------------------------------------


class QueryErrorTest(OntoCaseTest):
    def test_unknown_type_raises_ontoerror(self) -> None:
        with self.assertRaises(OntoError):
            query.query(self.project_store, "NoSuchType")

    def test_broken_where_raises_exprerror(self) -> None:
        with self.assertRaises(ExprError):
            query.query(self.project_store, "Decision", "status = 'active'")


# --- show ----------------------------------------------------------------


class ShowTest(OntoCaseTest):
    def test_show_by_ref_has_inverse_leads(self) -> None:
        d = query.show(self.project_store, "Stakeholder:tanaka")
        self.assertEqual(d["type"], "Stakeholder")
        self.assertEqual([it["ref"] for it in d["inverse"]["leads"]], ["Workstream:ws-idp"])

    def test_show_by_type_and_id_common_person(self) -> None:
        d = query.show(self.project_store, "sato", type_name="Person")
        self.assertEqual(d["ref"], "Person:sato")
        self.assertEqual(len(d["inverse"]["authorities"]), 1)

    def test_show_agent_true_drops_email(self) -> None:
        d = query.show(self.project_store, "sato", type_name="Person", agent=True)
        self.assertNotIn("email", d["props"])

    def test_show_agent_false_keeps_email(self) -> None:
        d = query.show(self.project_store, "sato", type_name="Person", agent=False)
        self.assertIn("email", d["props"])

    def test_show_sd1_inverse_superseded_by(self) -> None:
        d = query.show(self.project_store, "SizingDecision:SD-1")
        self.assertEqual(
            [it["ref"] for it in d["inverse"]["superseded_by"]], ["SizingDecision:SD-2"]
        )

    def test_show_unknown_ref_raises_ontoerror(self) -> None:
        with self.assertRaises(OntoError):
            query.show(self.project_store, "SizingDecision:no-such-id")


class ShowProposalsTest(OntoCaseTest):
    def _write_proposal(self, status: str) -> None:
        proposals_dir = self.project_dir / "proposals"
        proposals_dir.mkdir(parents=True, exist_ok=True)
        doc = {
            "id": "P-0001",
            "kind": "action",
            "status": status,
            "action": "IssueEstimate",
            "params": {"sizing": "SD-2"},
        }
        (proposals_dir / "P-0001.json").write_text(
            json.dumps(doc, ensure_ascii=False), encoding="utf-8"
        )

    def test_open_proposal_is_listed(self) -> None:
        self._write_proposal("open")
        d = query.show(self.project_store, "SizingDecision:SD-2")
        self.assertEqual(d["proposals"], ["P-0001"])

    def test_approved_proposal_is_not_listed(self) -> None:
        self._write_proposal("approved")
        d = query.show(self.project_store, "SizingDecision:SD-2")
        self.assertEqual(d["proposals"], [])

    def test_no_proposals_dir_is_empty_list(self) -> None:
        d = query.show(self.project_store, "SizingDecision:SD-2")
        self.assertEqual(d["proposals"], [])


# --- format_rows -----------------------------------------------------------


class FormatRowsTest(unittest.TestCase):
    def test_header_list_join_none_and_bool(self) -> None:
        rows = [
            {"id": "a1", "name": "アルファ", "active": True, "tags": ["x", "y"]},
            {"id": "a2", "name": None, "active": False, "tags": []},
        ]
        text = query.format_rows(rows)
        lines = text.split("\n")
        self.assertEqual(lines[0], "id | name | active | tags")
        self.assertEqual(lines[1], "a1 | アルファ | true | x,y")
        self.assertEqual(lines[2], "a2 | - | false | -")  # 空のリストも「-」

    def test_empty_rows_is_zero_message(self) -> None:
        self.assertEqual(query.format_rows([]), "（0 件）")

    def test_max_chars_truncates_with_remaining_count(self) -> None:
        rows = [{"id": f"r{i}"} for i in range(50)]
        text = query.format_rows(rows, max_chars=15)
        self.assertIn("r3", text)
        self.assertNotIn("r4\n", text)
        self.assertNotIn("r49", text)
        self.assertTrue(
            text.endswith("… 他 46 件（--where で絞るか --select で列を減らす）"), text
        )

    def test_total_greater_than_rows_appends_count(self) -> None:
        rows = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
        text = query.format_rows(rows, total=10)
        self.assertTrue(text.endswith("（全 10 件中 3 件）"), text)

    def test_type_column_hidden_when_single_type(self) -> None:
        rows = [{"id": "a", "type": "X", "name": "n"}]
        text = query.format_rows(rows)
        self.assertEqual(text.split("\n")[0], "id | name")

    def test_type_column_shown_when_multiple_types(self) -> None:
        rows = [{"id": "a", "type": "X"}, {"id": "b", "type": "Y"}]
        text = query.format_rows(rows)
        self.assertEqual(text.split("\n")[0], "id | type")


# --- format_show -------------------------------------------------------


class FormatShowTest(OntoCaseTest):
    def test_inverse_leads_line(self) -> None:
        d = query.show(self.project_store, "Stakeholder:tanaka")
        text = query.format_show(d)
        self.assertIn("Stakeholder:tanaka", text.splitlines()[0])
        lines = [ln for ln in text.splitlines() if ln.startswith("← leads:")]
        self.assertEqual(len(lines), 1)
        self.assertIn("Workstream:ws-idp", lines[0])


if __name__ == "__main__":
    unittest.main()
