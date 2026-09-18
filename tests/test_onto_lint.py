"""lint.py の適合テスト。標準ライブラリだけで動く（unittest）。"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from wsonto import lint, schema  # noqa: E402

FIXTURE_BASE = Path(__file__).resolve().parent / "fixtures" / "onto_case"


def _load_common():
    return schema.load_schema(FIXTURE_BASE / "common")


def _load_project(common=None):
    if common is None:
        common = _load_common()
    return schema.load_schema(FIXTURE_BASE / "project", common_dir=FIXTURE_BASE / "common")


def _doc(object_types=None, link_types=None, action_types=None, constants=None):
    doc = {"ontology": "t", "version": 1}
    doc["object_types"] = object_types or {}
    if link_types is not None:
        doc["link_types"] = link_types
    if action_types is not None:
        doc["action_types"] = action_types
    if constants is not None:
        doc["constants"] = constants
    return doc


def _codes(findings, code):
    return [f for f in findings if f.code == code]


class FixtureLintTest(unittest.TestCase):
    """見本の定義はきれいであること（lint が 0 件）。"""

    def test_common_is_clean(self):
        common = _load_common()
        self.assertEqual(lint.lint(common), [])

    def test_project_is_clean(self):
        project = _load_project()
        self.assertEqual(lint.lint(project), [])

    def test_project_is_clean_with_objects(self):
        project = _load_project()
        objects = json.loads((FIXTURE_BASE / "project" / "objects.json").read_text(encoding="utf-8"))
        self.assertEqual(lint.lint(project, objects), [])


class MisnomerTest(unittest.TestCase):
    def test_generic_property_name(self):
        doc = _doc(object_types={
            "Order": {"label": "注文", "properties": {"date": {"type": "date", "label": "日付"}}},
        })
        s = schema.parse_schema(doc)
        findings = _codes(lint.lint(s), lint.MISNOMER)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].where, "object_types.Order.properties.date")

    def test_link_without_label(self):
        doc = _doc(
            object_types={"A": {"label": "えー"}, "B": {"label": "びー"}},
            link_types={"assign": {"from": "A", "to": "B"}},
        )
        s = schema.parse_schema(doc)
        findings = _codes(lint.lint(s), lint.MISNOMER)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].where, "link_types.assign.label")


class SetActionTest(unittest.TestCase):
    def test_four_single_property_modify_actions_are_flagged(self):
        order_props = {
            "status": {"type": "enum", "values": ["open", "closed"], "label": "状態"},
            "reason": {"type": "string", "label": "理由"},
            "refund_yen": {"type": "int", "label": "返金額"},
            "address": {"type": "string", "label": "住所"},
        }
        actions = {}
        for aname, pname, praw in [
            ("SetStatus", "status", order_props["status"]),
            ("SetReason", "reason", order_props["reason"]),
            ("SetRefundYen", "refund_yen", order_props["refund_yen"]),
            ("UpdateAddress", "address", order_props["address"]),
        ]:
            actions[aname] = {
                "description": f"注文の {pname} だけを書き換えるテスト用の操作（1 プロパティの modify）",
                "parameters": {
                    "order": {"object_type": "Order", "required": True, "label": "注文"},
                    pname: dict(praw, required=True),
                },
                "rules": [{"modify": "order", "set": {pname: pname}}],
            }
        doc = _doc(
            object_types={"Order": {"label": "注文", "properties": order_props}},
            action_types=actions,
        )
        s = schema.parse_schema(doc)
        findings = _codes(lint.lint(s), lint.SET_ACTION)
        self.assertEqual(len(findings), 4)
        self.assertEqual(
            {f.where for f in findings},
            {f"action_types.{n}" for n in ("SetStatus", "SetReason", "SetRefundYen", "UpdateAddress")},
        )


class ActionSprawlTest(unittest.TestCase):
    def test_eleven_actions_on_one_type(self):
        actions = {}
        for i in range(1, 12):
            actions[f"Op{i}"] = {
                "description": f"部品を操作するテスト用のアクション（番号 {i}）",
                "parameters": {"w": {"object_type": "Widget", "required": True, "label": "対象"}},
                "rules": [{"modify": "w", "set": {"name": "'x'"}}],
            }
        doc = _doc(
            object_types={"Widget": {"label": "部品", "properties": {"name": {"type": "string", "label": "名前"}}}},
            action_types=actions,
        )
        s = schema.parse_schema(doc)
        findings = _codes(lint.lint(s), lint.ACTION_SPRAWL)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].where, "object_types.Widget")


class KitchenSinkTest(unittest.TestCase):
    def test_technical_looking_property_names(self):
        doc = _doc(object_types={"Ingest": {"label": "取込", "properties": {
            "etl_loaded_at": {"type": "datetime", "label": "取込日時"},
            "row_hash": {"type": "string", "label": "行ハッシュ"},
            "title": {"type": "string", "label": "題"},
        }}})
        s = schema.parse_schema(doc)
        findings = _codes(lint.lint(s), lint.KITCHEN_SINK)
        self.assertEqual(len(findings), 2)
        self.assertEqual(
            {f.where for f in findings},
            {"object_types.Ingest.properties.etl_loaded_at", "object_types.Ingest.properties.row_hash"},
        )

    def test_too_many_own_properties(self):
        props = {f"p{i}": {"type": "string", "label": f"p{i}"} for i in range(1, 22)}
        doc = _doc(object_types={"Big": {"label": "大きい型", "properties": props}})
        s = schema.parse_schema(doc)
        findings = _codes(lint.lint(s), lint.KITCHEN_SINK)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].where, "object_types.Big")


class TimeMachineTest(unittest.TestCase):
    def test_versioned_and_backup_type_names(self):
        doc = _doc(object_types={
            "OrderV2": {"label": "注文2"},
            "CustomerOld": {"label": "顧客旧"},
            "Normal": {"label": "普通"},
        })
        s = schema.parse_schema(doc)
        findings = _codes(lint.lint(s), lint.TIME_MACHINE)
        self.assertEqual(len(findings), 2)
        self.assertEqual(
            {f.where for f in findings},
            {"object_types.OrderV2", "object_types.CustomerOld"},
        )


class SiloNameTest(unittest.TestCase):
    def test_two_own_types_share_a_label(self):
        doc = _doc(object_types={"Client": {"label": "顧客"}, "Customer": {"label": "顧客"}})
        s = schema.parse_schema(doc)
        findings = _codes(lint.lint(s), lint.SILO_NAME)
        self.assertEqual(len(findings), 2)
        self.assertEqual(
            {f.where for f in findings},
            {"object_types.Client", "object_types.Customer"},
        )

    def test_project_type_shares_label_with_common_type(self):
        common = schema.parse_schema(_doc(object_types={"Person": {"label": "人"}}))
        project = schema.parse_schema(_doc(object_types={"Individual": {"label": "人"}}), common=common)
        findings = _codes(lint.lint(project), lint.SILO_NAME)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].where, "object_types.Individual")


class ThinDescriptionTest(unittest.TestCase):
    def test_action_without_description(self):
        doc = _doc(action_types={"DoThing": {"parameters": {}}})
        s = schema.parse_schema(doc)
        findings = _codes(lint.lint(s), lint.THIN_DESCRIPTION)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].where, "action_types.DoThing")


class GodObjectTest(unittest.TestCase):
    def _schema_and_props(self):
        doc = _doc(object_types={"Ticket": {"label": "チケット", "properties": {
            "title": {"type": "string", "required": True, "label": "題"},
            "opt1": {"type": "string", "label": "opt1"},
            "opt2": {"type": "string", "label": "opt2"},
            "opt3": {"type": "string", "label": "opt3"},
            "opt4": {"type": "string", "label": "opt4"},
            "opt5": {"type": "string", "label": "opt5"},
        }}})
        return schema.parse_schema(doc)

    def test_ten_instances_with_sparse_optional_properties(self):
        s = self._schema_and_props()
        objects = {"Ticket": {f"t{i}": {"title": f"Ticket {i}"} for i in range(1, 11)}}
        findings = _codes(lint.lint(s, objects), lint.GOD_OBJECT)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].where, "object_types.Ticket")

    def test_nine_instances_do_not_trigger(self):
        s = self._schema_and_props()
        objects = {"Ticket": {f"t{i}": {"title": f"Ticket {i}"} for i in range(1, 10)}}
        findings = _codes(lint.lint(s, objects), lint.GOD_OBJECT)
        self.assertEqual(findings, [])


class ScopeFilterTest(unittest.TestCase):
    """origin が自分の範囲のものだけを見る（共通の指摘は案件の lint に出ない）。"""

    def test_common_generic_property_not_reported_when_linting_project(self):
        common = schema.parse_schema(_doc(object_types={
            "Thing": {"label": "モノ", "properties": {"date": {"type": "date", "label": "日付"}}},
        }))
        # 対照: common 単体を lint すれば拾える（仕組みが実際に働いていることの確認）
        common_findings = _codes(lint.lint(common), lint.MISNOMER)
        self.assertEqual(len(common_findings), 1)
        self.assertEqual(common_findings[0].where, "object_types.Thing.properties.date")

        project = schema.parse_schema(
            _doc(object_types={"Extended": {"label": "拡張", "extends": ["Thing"]}}), common=common,
        )
        project_findings = _codes(lint.lint(project), lint.MISNOMER)
        self.assertEqual(project_findings, [])


if __name__ == "__main__":
    unittest.main()
