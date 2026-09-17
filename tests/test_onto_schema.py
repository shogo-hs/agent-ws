"""schema.py の適合テスト。標準ライブラリだけで動く（unittest）。"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from wsonto import schema  # noqa: E402
from wsonto.errors import SchemaError  # noqa: E402
from wsonto.expr import Expr  # noqa: E402

FIXTURE_BASE = Path(__file__).resolve().parent / "fixtures" / "onto_case"


def _load_common():
    return schema.load_schema(FIXTURE_BASE / "common")


def _load_project(common=None):
    if common is None:
        common = _load_common()
    return schema.load_schema(FIXTURE_BASE / "project", common_dir=FIXTURE_BASE / "common")


class FixtureLoadTest(unittest.TestCase):
    """fixture の common / project が取り決めどおりに読めることを確かめる。"""

    def test_common_loads_alone(self):
        common = _load_common()
        self.assertEqual(common.scope, "common")
        self.assertIn("Person", common.object_types)
        self.assertEqual(common.object_types["Person"].origin, "common")

    def test_project_loads_with_common(self):
        common = _load_common()
        project = schema.load_schema(FIXTURE_BASE / "project", common_dir=FIXTURE_BASE / "common")
        self.assertEqual(project.scope, "project")
        self.assertIn("Person", project.object_types)  # common の型も同じ dict に入る
        self.assertEqual(project.object_types["Person"].origin, "common")
        self.assertIn("Stakeholder", project.object_types)
        self.assertEqual(project.object_types["Stakeholder"].origin, "project")

    def test_stakeholder_is_person_subtype_with_inherited_props(self):
        project = _load_project()
        self.assertTrue(project.is_a("Stakeholder", "Person"))
        props = project.props("Stakeholder")
        for pname in ("name", "aliases", "email"):
            self.assertIn(pname, props)
        # 自分のプロパティも入っている
        self.assertIn("side", props)

    def test_sizing_decision_is_decision_subtype(self):
        project = _load_project()
        self.assertTrue(project.is_a("SizingDecision", "Decision"))
        props = project.props("SizingDecision")
        self.assertIn("title", props)  # Decision から継承
        self.assertIn("nodes", props)  # 自分の分

    def test_subtypes_person_includes_stakeholder(self):
        project = _load_project()
        self.assertIn("Stakeholder", project.subtypes("Person"))
        self.assertIn("Person", project.subtypes("Person"))  # 自分を含む

    def test_links_to_person(self):
        project = _load_project()
        names = set(project.links_to("Person"))
        for expected in ("leads", "approves", "action_items", "authorities"):
            self.assertIn(expected, names)

    def test_links_to_sizing_decision(self):
        project = _load_project()
        names = set(project.links_to("SizingDecision"))
        self.assertIn("superseded_by", names)
        self.assertIn("estimates", names)

    def test_links_from_sizing_decision(self):
        project = _load_project()
        names = set(project.links_from("SizingDecision"))
        self.assertIn("supersedes", names)

    def test_issue_estimate_approval_stage_if_is_expr(self):
        project = _load_project()
        approval = project.action_types["IssueEstimate"].approval
        self.assertEqual(approval.mode, "stage_if")
        self.assertIsInstance(approval.when, Expr)

    def test_add_action_item_criteria_empty_ok(self):
        project = _load_project()
        self.assertEqual(project.action_types["AddActionItem"].criteria, [])

    def test_transfer_person_approval_mode_stage(self):
        common = _load_common()
        approval = common.action_types["TransferPerson"].approval
        self.assertEqual(approval.mode, "stage")


def _minimal(**object_types):
    return {"ontology": "t", "version": 1, "object_types": object_types}


class RejectionTest(unittest.TestCase):
    """わざと壊した定義が、全部の誤りをまとめて problems に入ることを確かめる。"""

    def test_combined_errors_reported_together(self):
        doc = _minimal(
            badName={
                "properties": {"status": {"type": "enum"}},  # values が無い
                "extends": ["NoSuchType"],  # 存在しない extends
            }
        )
        with self.assertRaises(SchemaError) as cm:
            schema.parse_schema(doc)
        problems = cm.exception.problems
        self.assertGreaterEqual(len(problems), 3)
        joined = " / ".join(problems)
        self.assertIn("型名の形式が不正", joined)
        self.assertIn("values が無い", joined)
        self.assertIn("extends", joined)

    def test_extends_cycle(self):
        doc = _minimal(A={"extends": ["B"]}, B={"extends": ["A"]})
        with self.assertRaises(SchemaError) as cm:
            schema.parse_schema(doc)
        self.assertTrue(any("循環" in p for p in cm.exception.problems))

    def test_prop_name_and_inverse_link_name_collision(self):
        doc = {
            "ontology": "t", "version": 1,
            "object_types": {
                "Bar": {},
                "Foo": {"properties": {"leads": {"type": "string"}}},
            },
            "link_types": {
                "assign": {"label": "割当", "from": "Bar", "to": "Foo", "inverse": "leads"},
            },
        }
        with self.assertRaises(SchemaError) as cm:
            schema.parse_schema(doc)
        self.assertTrue(any("重複" in p for p in cm.exception.problems))

    def test_duplicate_name_with_common_is_rejected(self):
        common_doc = _minimal(Person={"properties": {"name": {"type": "string"}}})
        common = schema.parse_schema(common_doc)
        project_doc = _minimal(Person={"properties": {"name": {"type": "string"}}})
        with self.assertRaises(SchemaError) as cm:
            schema.parse_schema(project_doc, common=common)
        self.assertTrue(any("再定義" in p for p in cm.exception.problems))

    def test_expr_disallowed_name_is_rejected(self):
        doc = {
            "ontology": "t", "version": 1,
            "object_types": {},
            "action_types": {
                "DoIt": {
                    "parameters": {"x": {"type": "int"}},
                    "criteria": [{"when": "bogus_name > 0", "message": "だめ"}],
                }
            },
        }
        with self.assertRaises(SchemaError) as cm:
            schema.parse_schema(doc)
        self.assertTrue(any("bogus_name" in p for p in cm.exception.problems))

    def test_expr_disallowed_syntax_is_rejected(self):
        doc = {
            "ontology": "t", "version": 1,
            "object_types": {},
            "action_types": {
                "DoIt": {
                    "parameters": {"x": {"type": "int"}},
                    "criteria": [{"when": "__import__('os')", "message": "だめ"}],
                }
            },
        }
        with self.assertRaises(SchemaError):
            schema.parse_schema(doc)

    def test_unknown_key_is_rejected(self):
        doc = _minimal(Foo={"lable": "誤字"})
        with self.assertRaises(SchemaError) as cm:
            schema.parse_schema(doc)
        joined = " / ".join(cm.exception.problems)
        self.assertIn("知らないキー", joined)
        self.assertIn("lable", joined)

    def test_min_greater_than_max_is_rejected(self):
        doc = _minimal(Foo={"properties": {"n": {"type": "int", "min": 10, "max": 5}}})
        with self.assertRaises(SchemaError) as cm:
            schema.parse_schema(doc)
        self.assertTrue(any("min" in p and "max" in p for p in cm.exception.problems))

    def test_param_with_both_type_and_object_type_is_rejected(self):
        doc = {
            "ontology": "t", "version": 1,
            "object_types": {"Foo": {}},
            "action_types": {
                "DoIt": {"parameters": {"x": {"type": "int", "object_type": "Foo"}}},
            },
        }
        with self.assertRaises(SchemaError) as cm:
            schema.parse_schema(doc)
        self.assertTrue(any("両方" in p for p in cm.exception.problems))


class MergePatchTest(unittest.TestCase):
    def test_add_replace_delete_and_original_unchanged(self):
        doc = {"a": 1, "b": {"c": 2, "d": 3}, "e": 5}
        patch = {"b": {"c": 99, "d": {"$delete": True}}, "f": 10}
        result = schema.merge_patch(doc, patch)
        self.assertEqual(result, {"a": 1, "b": {"c": 99}, "e": 5, "f": 10})
        # 元の doc は変わらない
        self.assertEqual(doc, {"a": 1, "b": {"c": 2, "d": 3}, "e": 5})


class SchemaHashTest(unittest.TestCase):
    def test_hash_independent_of_key_order(self):
        h1 = schema.schema_hash({"a": 1, "b": 2})
        h2 = schema.schema_hash({"b": 2, "a": 1})
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 12)


if __name__ == "__main__":
    unittest.main()
