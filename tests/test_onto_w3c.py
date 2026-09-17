"""export.py の書き出しと W3C の道具（rdflib・pySHACL・owlrl）との突き合わせ。

rdflib / pyshacl / owlrl が import できない環境では丸ごと skip する。

`CASES` と `mutate_*` はここが正本。自前の検査（validate.py）と一致するかの
テストは、ここを import して同じ壊し方・同じ期待を再利用する想定（このチケッ
トの担当は書き出し側と pySHACL / SPARQL / RDFS 推論の側だけ）。
"""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from wsonto import export, schema  # noqa: E402

FIXTURE_BASE = Path(__file__).resolve().parent / "fixtures" / "onto_case"
BASE = "https://example.com/onto/acme-migration#"
ENTITY_NS = "https://example.com/onto/acme-migration/"


def _load_schema():
    return schema.load_schema(FIXTURE_BASE / "project", common_dir=FIXTURE_BASE / "common")


def _load_objects():
    project = json.loads((FIXTURE_BASE / "project" / "objects.json").read_text(encoding="utf-8"))
    common = json.loads((FIXTURE_BASE / "common" / "objects.json").read_text(encoding="utf-8"))
    return project, common


# --- 違反データ ---------------------------------------------------------
# `mutate_xxx(project_objects, common_objects)` は、呼び出す側が deep copy した
# 辞書を受け取って 1 か所だけ壊す（形は README「objects.json」のとおり）。


def mutate_decision_status_invalid(project_objects: dict, common_objects: dict) -> None:
    project_objects["Decision"]["D-1"]["status"] = "unknown"


def mutate_price_negative(project_objects: dict, common_objects: dict) -> None:
    project_objects["PriceItem"]["pi-node"]["unit_price_yen"] = -1


def mutate_action_item_owner_missing(project_objects: dict, common_objects: dict) -> None:
    del project_objects["ActionItem"]["A-1"]["_links"]["owner"]


def mutate_action_item_owner_two(project_objects: dict, common_objects: dict) -> None:
    project_objects["ActionItem"]["A-1"]["_links"]["owner"] = [
        "Stakeholder:yamada", "Stakeholder:tanaka",
    ]


def mutate_sd1_superseded_twice(project_objects: dict, common_objects: dict) -> None:
    project_objects["SizingDecision"]["SD-3"] = {
        "title": "もう一つの見直し",
        "nodes": 10,
        "decided_on": "2026-09-10",
        "status": "active",
        "source": "テスト用",
        "_links": {"supersedes": ["SizingDecision:SD-1"]},
    }


def mutate_action_item_owner_wrong_class(project_objects: dict, common_objects: dict) -> None:
    project_objects["ActionItem"]["A-1"]["_links"]["owner"] = ["CustomerSystem:orders"]


def mutate_decision_extra_prop(project_objects: dict, common_objects: dict) -> None:
    project_objects["Decision"]["D-1"]["foo"] = "bar"


def mutate_sd2_title_missing(project_objects: dict, common_objects: dict) -> None:
    del project_objects["SizingDecision"]["SD-2"]["title"]


# (名前, 壊す関数, 結果テキストに含まれるはずの部分文字列の一覧)
CASES = [
    ("decision_status_invalid", mutate_decision_status_invalid,
     ["/Decision/D-1", "InConstraintComponent"]),
    ("price_negative", mutate_price_negative,
     ["/PriceItem/pi-node", "MinInclusiveConstraintComponent"]),
    ("action_item_owner_missing", mutate_action_item_owner_missing,
     ["/ActionItem/A-1", "MinCountConstraintComponent"]),
    ("action_item_owner_two", mutate_action_item_owner_two,
     ["/ActionItem/A-1", "MaxCountConstraintComponent"]),
    ("sd1_superseded_twice", mutate_sd1_superseded_twice,
     ["/SizingDecision/SD-1", "MaxCountConstraintComponent"]),
    ("action_item_owner_wrong_class", mutate_action_item_owner_wrong_class,
     ["/ActionItem/A-1", "ClassConstraintComponent"]),
    ("decision_extra_prop", mutate_decision_extra_prop,
     ["/Decision/D-1", "ClosedConstraintComponent"]),
    ("sd2_title_missing", mutate_sd2_title_missing,
     ["/SizingDecision/SD-2", "MinCountConstraintComponent"]),
]


try:
    import rdflib
    import owlrl
    from pyshacl import validate as shacl_validate
    HAVE_RDF = True
except ImportError:
    HAVE_RDF = False


def _graph_from_ttl(ttl: str):
    g = rdflib.Graph()
    g.parse(data=ttl, format="turtle")
    return g


def _validate_case(sch, name, mutate):
    project, common = _load_objects()
    project = copy.deepcopy(project)
    common = copy.deepcopy(common)
    mutate(project, common)
    ttl = export.to_turtle(sch, objects=[project, common])
    g = _graph_from_ttl(ttl)
    return shacl_validate(g, shacl_graph=g, ont_graph=g, inference="rdfs")


@unittest.skipUnless(HAVE_RDF, "rdflib / pyshacl / owlrl が無い環境では skip")
class ShaclConformanceTest(unittest.TestCase):
    def test_fixture_conforms(self):
        sch = _load_schema()
        project, common = _load_objects()
        ttl = export.to_turtle(sch, objects=[project, common])
        g = _graph_from_ttl(ttl)
        conforms, _results_graph, text = shacl_validate(
            g, shacl_graph=g, ont_graph=g, inference="rdfs",
        )
        self.assertTrue(conforms, text)

    def test_violations(self):
        sch = _load_schema()
        for name, mutate, expects in CASES:
            with self.subTest(name=name):
                conforms, _results_graph, text = _validate_case(sch, name, mutate)
                self.assertFalse(conforms, f"{name}: 違反が検出されなかった\n{text}")
                for expect in expects:
                    self.assertIn(expect, text, f"{name}: {expect!r} が結果に無い\n{text}")


@unittest.skipUnless(HAVE_RDF, "rdflib / pyshacl / owlrl が無い環境では skip")
class RdfsAndSparqlTest(unittest.TestCase):
    def _closed_graph(self):
        sch = _load_schema()
        project, common = _load_objects()
        ttl = export.to_turtle(sch, objects=[project, common])
        g = _graph_from_ttl(ttl)
        owlrl.DeductiveClosure(owlrl.RDFS_Semantics).expand(g)
        return g

    def test_subtype_instances_are_inferred_as_ancestor(self):
        g = self._closed_graph()
        person = rdflib.URIRef(BASE + "Person")
        decision = rdflib.URIRef(BASE + "Decision")
        tanaka = rdflib.URIRef(ENTITY_NS + "Stakeholder/tanaka")
        sd2 = rdflib.URIRef(ENTITY_NS + "SizingDecision/SD-2")
        self.assertIn((tanaka, rdflib.RDF.type, person), g)
        self.assertIn((sd2, rdflib.RDF.type, decision), g)

    def test_sparql_active_decisions(self):
        g = self._closed_graph()
        rows = g.query(
            """
            PREFIX ex: <%s>
            SELECT ?s WHERE { ?s a ex:Decision ; ex:status "active" . }
            """ % BASE
        )
        ids = {str(row.s).rsplit("/", 1)[-1] for row in rows}
        self.assertEqual(ids, {"D-1", "SD-2"})

    def test_sparql_workstreams_led_by_tanaka(self):
        g = self._closed_graph()
        tanaka = ENTITY_NS + "Stakeholder/tanaka"
        rows = g.query(
            """
            PREFIX ex: <%s>
            SELECT ?ws WHERE { ?ws ex:lead <%s> . }
            """ % (BASE, tanaka)
        )
        ids = {str(row.ws).rsplit("/", 1)[-1] for row in rows}
        self.assertEqual(ids, {"ws-idp"})

    def test_wrong_class_link_does_not_infer_range_type(self):
        # schema:domainIncludes / schema:rangeIncludes は注釈であって推論規則では
        # ないので、型違いのリンク先（CustomerSystem）に ex:Person 型が推論で
        # 付いてはいけない（rdfs:range を使っていた頃はここで型が付き、sh:class
        # の違反検出が効かなくなっていた）。
        sch = _load_schema()
        project, common = _load_objects()
        project = copy.deepcopy(project)
        common = copy.deepcopy(common)
        mutate_action_item_owner_wrong_class(project, common)
        ttl = export.to_turtle(sch, objects=[project, common])
        g = _graph_from_ttl(ttl)
        owlrl.DeductiveClosure(owlrl.RDFS_Semantics).expand(g)
        orders = rdflib.URIRef(ENTITY_NS + "CustomerSystem/orders")
        person = rdflib.URIRef(BASE + "Person")
        self.assertNotIn((orders, rdflib.RDF.type, person), g)


if __name__ == "__main__":
    unittest.main()
