"""自前の検査（validate.py・閉世界）と W3C の検査器（pySHACL）が、同じ違反データに同じ判定を出すことの突き合わせ。

  python3 -m unittest tests/test_onto_parity.py
  uv run --with rdflib --with pyshacl python3 -m unittest tests/test_onto_parity.py   # pySHACL 側も走らせる

違反データの一覧（CASES）は tests/test_onto_w3c.py と共有する。自前の側は標準ライブラリだけで常に走り、
pySHACL の側は rdflib / pyshacl が無ければ skip する。
"""
from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
sys.path.insert(0, str(HERE))

from wsonto import export, schema, store, validate  # noqa: E402
import test_onto_w3c as w3c  # noqa: E402

FIXTURE = HERE / "fixtures" / "onto_case"
# SHACL の部品名 → 自前の検査の code
SHACL_TO_NATIVE = {
    "InConstraintComponent": "IN",
    "MinInclusiveConstraintComponent": "MIN_INCLUSIVE",
    "MinCountConstraintComponent": "MIN_COUNT",
    "MaxCountConstraintComponent": "MAX_COUNT",
    "ClassConstraintComponent": "CLASS",
    "ClosedConstraintComponent": "CLOSED",
}


class ParityTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="onto-parity-"))
        shutil.copytree(FIXTURE, self.tmp / "case")
        self.cdir, self.pdir = self.tmp / "case" / "common", self.tmp / "case" / "project"
        self.cschema = schema.load_schema(self.cdir)
        self.pschema = schema.load_schema(self.pdir, self.cdir)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _native(self, project: dict, common: dict):
        (self.pdir / "objects.json").write_text(json.dumps(project, ensure_ascii=False), encoding="utf-8")
        (self.cdir / "objects.json").write_text(json.dumps(common, ensure_ascii=False), encoding="utf-8")
        cstore = store.Store(self.cdir, self.cschema)
        pstore = store.Store(self.pdir, self.pschema, cstore)
        return validate.validate(pstore) + validate.validate(cstore)

    def _objects(self):
        return tuple(json.loads((d / "objects.json").read_text(encoding="utf-8")) for d in (FIXTURE / "project", FIXTURE / "common"))

    def test_clean_fixture_passes_both(self):
        project, common = self._objects()
        self.assertEqual(self._native(project, common), [])
        if w3c.HAVE_RDF:
            g = w3c._graph_from_ttl(export.to_turtle(self.pschema, objects=[project, common]))
            conforms, _, text = w3c.shacl_validate(g, shacl_graph=g, ont_graph=g, inference="rdfs")
            self.assertTrue(conforms, text)

    def test_each_violation_is_caught_by_both_with_the_same_kind(self):
        for name, mutate, (entity_path, component) in w3c.CASES:
            with self.subTest(case=name):
                project, common = (copy.deepcopy(d) for d in self._objects())
                mutate(project, common)
                found = {(v.ref, v.code) for v in self._native(project, common)}
                ref = entity_path.strip("/").replace("/", ":")
                self.assertIn((ref, SHACL_TO_NATIVE[component]), found, f"自前の検査が {ref} の {component} 相当を出していない: {found}")
                if w3c.HAVE_RDF:
                    g = w3c._graph_from_ttl(export.to_turtle(self.pschema, objects=[project, common]))
                    conforms, _, text = w3c.shacl_validate(g, shacl_graph=g, ont_graph=g, inference="rdfs")
                    self.assertFalse(conforms)
                    self.assertIn(entity_path, text)
                    self.assertIn(component, text)


if __name__ == "__main__":
    unittest.main()
