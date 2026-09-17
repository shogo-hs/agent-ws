"""同梱の見本（knowledges/ontology と projects/_example/knowledges/ontology）が、適合の基準（tests/fixtures/onto_case）と同じ内容で、
そのまま検査・検収・評価を通ることの確認。  python3 -m unittest tests/test_onto_examples.py

見本は消してよいものなので（README）、無ければ skip する。
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from wsonto import engine, evals, lint, schema, store, validate  # noqa: E402

FIXTURE = REPO / "tests" / "fixtures" / "onto_case"
COMMON = REPO / "knowledges" / "ontology"
EXAMPLE = REPO / "projects" / "_example" / "knowledges" / "ontology"


@unittest.skipUnless((COMMON / "ontology.json").exists() and (EXAMPLE / "ontology.json").exists(), "同梱の見本が無い（消してある）")
class ShippedExamplesTest(unittest.TestCase):
    def test_same_content_as_the_conformance_fixture(self):
        pairs = [(COMMON, FIXTURE / "common", ("ontology.json", "objects.json")),
                 (EXAMPLE, FIXTURE / "project", ("ontology.json", "objects.json", "questions.json"))]
        for shipped, fixture, names in pairs:
            for name in names:
                with self.subTest(file=f"{shipped.name}/{name}"):
                    self.assertEqual(json.loads((shipped / name).read_text(encoding="utf-8")),
                                     json.loads((fixture / name).read_text(encoding="utf-8")),
                                     "見本と tests/fixtures/onto_case がずれている。どちらかを直したら、もう片方にも写す")

    def test_examples_validate_lint_and_answer_their_questions(self):
        cschema = schema.load_schema(COMMON)
        pschema = schema.load_schema(EXAMPLE, COMMON)
        cstore = store.Store(COMMON, cschema)
        pstore = store.Store(EXAMPLE, pschema, cstore)
        self.assertEqual(validate.validate(cstore), [])
        self.assertEqual(validate.validate(pstore), [])
        self.assertEqual(lint.lint(cschema), [])
        self.assertEqual(lint.lint(pschema, pstore.to_doc()), [])
        doc = json.loads((EXAMPLE / "questions.json").read_text(encoding="utf-8"))
        results = evals.run_questions(pstore, doc, engine.Actor("agent", "test-agent", "s1"))
        self.assertEqual([(r.id, r.detail) for r in results if not r.ok], [])
        self.assertEqual(len(results), len(doc["questions"]))

    def test_index_md_is_listed_with_a_one_line_summary(self):
        for d in (COMMON, EXAMPLE):
            text = (d / "index.md").read_text(encoding="utf-8")
            summary = [l for l in text.splitlines() if l.startswith("summary:")]
            self.assertEqual(len(summary), 1)
            self.assertLessEqual(len(summary[0]), 230)  # 起動時の注入に 1 行で載る

    def test_index_md_has_no_counts_section(self):
        # 件数は onto act で実体が増減すると古くなる。onto types / query で見る
        for d in (COMMON, EXAMPLE):
            text = (d / "index.md").read_text(encoding="utf-8")
            self.assertNotIn("## 件数", text)


if __name__ == "__main__":
    unittest.main()
