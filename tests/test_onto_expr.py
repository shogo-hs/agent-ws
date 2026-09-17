"""expr.py の適合テスト。標準ライブラリだけで動く（unittest）。"""
from __future__ import annotations

import datetime
import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from wsonto import expr  # noqa: E402
from wsonto.errors import ExprError  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "onto_case" / "project" / "ontology.json"
_BRACE_RE = re.compile(r"\{([^{}]+)\}")


class FakeEntity:
    """実体の顔（onto_get を持つ）の代用クラス。"""

    def __init__(self, type_name: str, **props):
        self.type = type_name
        self._props = props

    def onto_get(self, name):
        if name == "type":
            return self.type
        if name in self._props:
            return self._props[name]
        raise KeyError(name)


class FixtureCompilesTest(unittest.TestCase):
    """project/ontology.json に出てくる式・雛形が全部 compile できることを確かめる。"""

    def test_all_expressions_and_templates_compile(self):
        doc = json.loads(FIXTURE.read_text(encoding="utf-8"))
        exprs = []
        templates = []
        for action in doc["action_types"].values():
            for c in action.get("criteria", []):
                exprs.append(c["when"])
                templates.append(c.get("message", ""))
            for r in action.get("rules", []):
                if "if" in r:
                    exprs.append(r["if"])
                for v in r.get("set", {}).values():
                    exprs.append(v)
                for v in r.get("link", {}).values():
                    exprs.append(v)
                if "id" in r:
                    templates.append(r["id"])
            approval = action.get("approval")
            if isinstance(approval, dict) and "stage_if" in approval:
                exprs.append(approval["stage_if"])
            if "next" in action:
                templates.append(action["next"])

        self.assertTrue(exprs, "fixture から式が 1 つも取れていない（読み取りが壊れている）")

        failures = []
        for src in exprs:
            try:
                expr.compile_expr(src)
            except ExprError as e:
                failures.append(f"{src!r}: {e}")
        for template in templates:
            for piece in _BRACE_RE.findall(template):
                try:
                    expr.compile_expr(piece)
                except ExprError as e:
                    failures.append(f"{piece!r} (in {template!r}): {e}")
        self.assertEqual(failures, [], "\n".join(failures))


class EvalTest(unittest.TestCase):
    def test_attribute_access_on_entity_face(self):
        sizing = FakeEntity("SizingDecision", nodes=12, status="active")
        e = expr.compile_expr("sizing.status == 'active'", allowed_names={"sizing"})
        self.assertTrue(e.eval({"sizing": sizing}))

    def test_sum_over_items_with_per_node_price(self):
        sizing = FakeEntity("SizingDecision", nodes=12, status="active")
        items = [
            FakeEntity("PriceItem", unit_price_yen=30000, per_node=True),
            FakeEntity("PriceItem", unit_price_yen=50000, per_node=False),
        ]
        src = "sum(i.unit_price_yen * (sizing.nodes if i.per_node else 1) for i in items)"
        e = expr.compile_expr(src, allowed_names={"sizing", "items"})
        self.assertEqual(e.eval({"sizing": sizing, "items": items}), 410000)

    def test_all_valid_until_within_days_since(self):
        today = datetime.date(2026, 9, 17)
        src = "all(i.valid_until is None or days_since(i.valid_until) <= 0 for i in items)"
        e = expr.compile_expr(src, allowed_names={"items"})

        ok_items = [
            FakeEntity("PriceItem", valid_until=None),
            FakeEntity("PriceItem", valid_until=datetime.date(2026, 9, 17)),
            FakeEntity("PriceItem", valid_until=datetime.date(2026, 12, 31)),
        ]
        self.assertTrue(e.eval({"items": ok_items, "__today__": today}))

        expired_items = [
            FakeEntity("PriceItem", valid_until=None),
            FakeEntity("PriceItem", valid_until=datetime.date(2026, 8, 31)),
        ]
        self.assertFalse(e.eval({"items": expired_items, "__today__": today}))

    def test_stage_if_authority_limit(self):
        src = (
            "not any(a.kind == 'estimate' and (a.limit_yen is None or est.total_yen <= a.limit_yen)"
            " for a in approver.authorities)"
        )
        e = expr.compile_expr(src, allowed_names={"approver", "est"})
        est = FakeEntity("Estimate", total_yen=410000)

        within_limit = FakeEntity(
            "Person", authorities=[FakeEntity("ApprovalAuthority", kind="estimate", limit_yen=500000)]
        )
        self.assertFalse(e.eval({"approver": within_limit, "est": est}))

        over_limit = FakeEntity(
            "Person", authorities=[FakeEntity("ApprovalAuthority", kind="estimate", limit_yen=100000)]
        )
        self.assertTrue(e.eval({"approver": over_limit, "est": est}))

    def test_list_attribute_flattens_one_level(self):
        ws_list = [
            FakeEntity("Workstream", tags=["a", "b"]),
            FakeEntity("Workstream", tags=["c"]),
        ]
        e = expr.compile_expr("ws_list.tags", allowed_names={"ws_list"})
        self.assertEqual(e.eval({"ws_list": ws_list}), ["a", "b", "c"])

    def test_none_attribute_access_is_none(self):
        e = expr.compile_expr("maybe.title", allowed_names={"maybe"})
        self.assertIsNone(e.eval({"maybe": None}))

    def test_none_order_comparison_is_false(self):
        for op in ("<", "<=", ">", ">="):
            e = expr.compile_expr(f"maybe {op} 5", allowed_names={"maybe"})
            self.assertFalse(e.eval({"maybe": None}), op)

    def test_in_and_not_in(self):
        e = expr.compile_expr("'IdP' in w.name", allowed_names={"w"})
        w = FakeEntity("Workstream", name="IdP 連携")
        self.assertTrue(e.eval({"w": w}))

        e2 = expr.compile_expr("x in items", allowed_names={"x", "items"})
        self.assertTrue(e2.eval({"x": 2, "items": [1, 2, 3]}))
        self.assertFalse(e2.eval({"x": 9, "items": [1, 2, 3]}))

        e3 = expr.compile_expr("x not in items", allowed_names={"x", "items"})
        self.assertFalse(e3.eval({"x": None, "items": [1, 2, 3]}))
        self.assertFalse(e3.eval({"x": 1, "items": None}))

    def test_iteration_cap(self):
        items = list(range(100_001))
        e = expr.compile_expr("sum(x for x in items)", allowed_names={"items"})
        with self.assertRaises(ExprError):
            e.eval({"items": items})


class RejectionTest(unittest.TestCase):
    BAD_EXPRS = [
        "__import__('os')",
        "().__class__",
        "a._x",
        "_x",
        "lambda: 1",
        "open('f')",
        "f(x=1)",
        "f(*a)",
        "x[0]",
        "{1: 2}",
        "x := 1",
        'f"{x}"',
        "await x",
        "a.b()",
        "sum.__call__",
    ]

    def test_all_rejected_at_compile_time(self):
        for src in self.BAD_EXPRS:
            with self.subTest(src=src):
                with self.assertRaises(ExprError):
                    expr.compile_expr(src)

    def test_allowed_names_rejects_outside_free_variables(self):
        with self.assertRaises(ExprError):
            expr.compile_expr("x + y", allowed_names={"x"})
        # 許可された名前だけなら通る
        e = expr.compile_expr("x + 1", allowed_names={"x"})
        self.assertEqual(e.eval({"x": 1}), 2)


class RenderTest(unittest.TestCase):
    def test_render_success(self):
        out = expr.render("{a} + {b} = {a + b}", {"a": 1, "b": 2})
        self.assertEqual(out, "1 + 2 = 3")

    def test_render_none_and_date(self):
        d = datetime.date(2026, 9, 17)
        out = expr.render("期限: {due}・値: {maybe}", {"due": d, "maybe": None})
        self.assertEqual(out, "期限: 2026-09-17・値: （なし）")

    def test_render_leaves_failed_braces_untouched(self):
        out = expr.render("わかる: {a}・わからない: {c.d}", {"a": 1})
        self.assertEqual(out, "わかる: 1・わからない: {c.d}")


class ReviewFixesTest(unittest.TestCase):
    """レビューで足した決め: 関数名と同じ名前の変数・列の掛け算の禁止・長さの上限・none/count の寛容さ。"""

    def test_bare_name_same_as_builtin_is_a_variable(self):
        e = expr.compile_expr("count >= 2 and max == 5", allowed_names={"count", "max"})
        self.assertEqual(e.names, {"count", "max"})
        self.assertTrue(e.eval({"count": 3, "max": 5}))
        self.assertEqual(expr.compile_expr("count(xs) + max(xs)").eval({"xs": [1, 4]}), 6)

    def test_sequence_multiplication_is_rejected(self):
        for src in ("'x' * 1000000000", "[1] * 1000000000", "n * 'x'"):
            with self.assertRaises(expr.ExprError):
                expr.compile_expr(src).eval({"n": 3})
        self.assertEqual(expr.compile_expr("n * 30000").eval({"n": 12}), 360000)

    def test_source_length_and_depth_limits(self):
        with self.assertRaises(expr.ExprError):
            expr.compile_expr("1 + " * 1000 + "1")
        with self.assertRaises(expr.ExprError):
            expr.compile_expr("(" * 500 + "1" + ")" * 500)

    def test_none_and_count_accept_single_or_missing(self):
        self.assertTrue(expr.compile_expr("none(x)").eval({"x": None}))
        self.assertTrue(expr.compile_expr("none(x)").eval({"x": []}))
        self.assertFalse(expr.compile_expr("none(x)").eval({"x": object()}))
        self.assertEqual(expr.compile_expr("count(x)").eval({"x": None}), 0)


if __name__ == "__main__":
    unittest.main()
