"""export.py の適合テスト。標準ライブラリだけで動く（unittest）。"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from wsonto import export, schema  # noqa: E402

FIXTURE_BASE = Path(__file__).resolve().parent / "fixtures" / "onto_case"


def _load_project():
    return schema.load_schema(FIXTURE_BASE / "project", common_dir=FIXTURE_BASE / "common")


class JSONSchemaTest(unittest.TestCase):
    def test_issue_estimate_input_schema(self):
        sch = _load_project()
        doc = export.to_jsonschema(sch)
        action = doc["actions"]["IssueEstimate"]
        input_schema = action["input_schema"]

        self.assertEqual(
            set(input_schema["required"]),
            {"title", "sizing", "items", "months", "approver"},
        )
        self.assertEqual(input_schema["additionalProperties"], False)

        self.assertEqual(input_schema["properties"]["items"]["type"], "array")
        self.assertEqual(input_schema["properties"]["items"]["items"]["type"], "string")

        self.assertEqual(input_schema["properties"]["months"]["type"], "integer")
        self.assertEqual(input_schema["properties"]["months"]["minimum"], 1)

        self.assertEqual(input_schema["properties"]["sizing"]["type"], "string")
        self.assertIn("台数の決定", input_schema["properties"]["sizing"]["description"])

    def test_objects_section_has_object_types(self):
        sch = _load_project()
        doc = export.to_jsonschema(sch)
        self.assertIn("Decision", doc["objects"])
        decision_schema = doc["objects"]["Decision"]
        self.assertEqual(decision_schema["additionalProperties"], False)
        self.assertIn("title", decision_schema["required"])
        self.assertEqual(decision_schema["properties"]["status"]["enum"], ["active", "superseded"])


class TurtleTest(unittest.TestCase):
    def test_subclass_triples(self):
        sch = _load_project()
        ttl = export.to_turtle(sch)
        self.assertIn("ex:SizingDecision rdfs:subClassOf ex:Decision .", ttl)
        self.assertIn("ex:Stakeholder rdfs:subClassOf ex:Person .", ttl)

    def test_inverse_of_and_inverse_path(self):
        sch = _load_project()
        ttl = export.to_turtle(sch)
        self.assertIn("owl:inverseOf ex:superseded_by", ttl)
        self.assertIn("sh:inversePath ex:supersedes", ttl)

    def test_enum_in_constraint(self):
        sch = _load_project()
        ttl = export.to_turtle(sch)
        self.assertIn('sh:in ( "active" "superseded" )', ttl)

    def test_unique_is_not_exported(self):
        sch = _load_project()
        ttl = export.to_turtle(sch)
        self.assertNotIn("sh:unique", ttl)

    def test_vocabulary_uses_schema_includes_not_rdfs_domain_range(self):
        sch = _load_project()
        ttl = export.to_turtle(sch)
        # rdfs:domain / rdfs:range は RDFS 推論つきの検査で値ノードに型を推論して
        # しまい、sh:class の違反検出を無効化する（自前の検査との不一致の原因に
        # なる）。制約は SHACL だけに持たせ、語彙側は推論を起こさない
        # schema:domainIncludes / schema:rangeIncludes で意図した両端を残す。
        self.assertNotIn("rdfs:domain", ttl)
        self.assertNotIn("rdfs:range", ttl)
        self.assertIn("schema:rangeIncludes ex:Person", ttl)

    def test_entities_include_default_for_missing_required_prop(self):
        sch = _load_project()
        objects = {
            "_meta": {"seq": {}},
            "Workstream": {
                "ws-x": {"name": "テスト領域", "_links": {"lead": ["Stakeholder:tanaka"]}},
            },
        }
        ttl = export.to_turtle(sch, objects=objects)
        # state は required かつ default "not_started" を持つ。未設定でもトリプルが出る。
        self.assertIn('ex:state "not_started" .', ttl)


class MermaidTest(unittest.TestCase):
    def test_starts_with_er_diagram_and_lists_all_types(self):
        sch = _load_project()
        mmd = export.to_mermaid(sch)
        self.assertTrue(mmd.startswith("erDiagram"))
        for tname in sch.object_types:
            self.assertIn(tname, mmd)


class MarkdownTest(unittest.TestCase):
    def test_issue_estimate_criteria_messages(self):
        sch = _load_project()
        md = export.to_markdown(sch)
        self.assertIn("有効期限の切れた単価が含まれている", md)
        self.assertIn("に見積の決裁権限が無い", md)
        self.assertIn("契約月数は", md)

    def test_no_counts_section_even_with_objects(self):
        # 件数は onto act の実行のたびに古くなるので index.md には載せない（onto types / query で見る）
        sch = _load_project()
        objects = {"Decision": {"d1": {"title": "x", "status": "active"}}}
        md = export.to_markdown(sch, objects=objects)
        self.assertNotIn("## 件数", md)
        self.assertTrue(md.startswith("件数と中身は"))


class EscapingTest(unittest.TestCase):
    def test_string_escaping_does_not_break_turtle(self):
        doc = {
            "ontology": "esc-case",
            "version": 1,
            "object_types": {
                "Widget": {
                    "label": 'variant "A"\nwith newline',
                    "properties": {
                        "name": {"type": "string", "required": True, "label": "名前"},
                    },
                },
            },
        }
        sch = schema.parse_schema(doc)
        ttl = export.to_turtle(sch)
        self.assertIn('\\"A\\"', ttl)
        self.assertIn("\\n", ttl)
        self.assertIn("ex:Widget a owl:Class .", ttl)


if __name__ == "__main__":
    unittest.main()
