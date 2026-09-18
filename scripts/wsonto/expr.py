"""wsonto の式言語。

Python の式の部分集合を `ast.parse(src, mode="eval")` で構文木にし、許可リストで
検査してから、自前の評価器で木をたどって評価する。`eval` / `exec` / `compile` は
使わない。取り決めは `scripts/wsonto/README.md` の「expr.py — 式」を参照。
"""
from __future__ import annotations

import ast
import datetime
from collections.abc import Mapping
from typing import Any, Callable

from .errors import ExprError, HiddenPropertyError

_MAX_ITERATIONS = 100_000
_MAX_SRC = 2_000

_ALLOWED_BOOL_OPS = (ast.And, ast.Or)
_ALLOWED_UNARY_OPS = (ast.Not, ast.USub)
_ALLOWED_BIN_OPS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod)
_ALLOWED_CMP_OPS = (
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.In,
    ast.NotIn,
    ast.Is,
    ast.IsNot,
)
_BIN_FUNCS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.FloorDiv: lambda a, b: a // b,
    ast.Mod: lambda a, b: a % b,
}
_ORDER_OPS = {
    ast.Lt: lambda a, b: a < b,
    ast.LtE: lambda a, b: a <= b,
    ast.Gt: lambda a, b: a > b,
    ast.GtE: lambda a, b: a >= b,
}


def _b_none(items: Any) -> bool:
    if items is None:
        return True
    if not isinstance(items, (list, tuple)):
        return not items
    return not any(bool(x) for x in items)


def _b_count(items: Any) -> int:
    if items is None:
        return 0
    if not isinstance(items, (list, tuple, str)):
        return 1
    return len(items)


def _b_exists(x: Any) -> bool:
    if x is None:
        return False
    if isinstance(x, (list, str)):
        return len(x) > 0
    return True


def _b_today() -> datetime.date:
    return datetime.date.today()


def _b_days_since(d: Any) -> Any:
    if d is None:
        return None
    return (datetime.date.today() - d).days


def _b_days_between(a: Any, b: Any) -> Any:
    if a is None or b is None:
        return None
    return (b - a).days


BUILTINS: dict[str, Callable] = {
    "len": _b_count,
    "count": _b_count,
    "sum": sum,
    "min": min,
    "max": max,
    "any": any,
    "all": all,
    "none": _b_none,
    "exists": _b_exists,
    "abs": abs,
    "round": round,
    "int": int,
    "float": float,
    "str": str,
    "today": _b_today,
    "days_since": _b_days_since,
    "days_between": _b_days_between,
}


class Expr:
    """コンパイル済みの式。`src`（元の文字列）と `names`（自由変数）を持つ。"""

    __slots__ = ("src", "names", "_node")

    def __init__(self, src: str, node: ast.expr, names: set) -> None:
        self.src = src
        self.names = frozenset(names)
        self._node = node

    def eval(self, env: Mapping) -> Any:
        return _eval(self._node, env, {}, [0], self.src)

    def __repr__(self) -> str:
        return f"Expr({self.src!r})"


def compile_expr(src: str, allowed_names: set | None = None) -> Expr:
    if not isinstance(src, str) or len(src) > _MAX_SRC:
        raise ExprError(f"式は {_MAX_SRC} 字以内の文字列にしてください")
    names: set = set()
    try:
        tree = ast.parse(src, mode="eval")
        _check(tree.body, src, frozenset(), names)
    except (SyntaxError, ValueError) as e:
        raise ExprError(f"式 {src!r} の構文が誤っています（{e}）") from e
    except RecursionError:
        raise ExprError(f"式 {src[:40]!r}… の入れ子が深すぎます") from None
    if allowed_names is not None:
        extra = names - set(allowed_names)
        if extra:
            raise ExprError(
                f"式 {src!r} は許可されていない名前を使っています: {', '.join(sorted(extra))}"
            )
    return Expr(src, tree.body, names)


def render(template: str, env: Mapping) -> str:
    out = []
    i = 0
    n = len(template)
    while i < n:
        c = template[i]
        if c == "{":
            j = template.find("}", i + 1)
            if j == -1:
                out.append(template[i:])
                break
            piece = template[i + 1 : j]
            try:
                compiled = compile_expr(piece)
                value = compiled.eval(env)
                out.append(_render_value(value))
            except ExprError:
                out.append(template[i : j + 1])
            i = j + 1
        else:
            out.append(c)
            i += 1
    return "".join(out)


def _render_value(value: Any) -> str:
    if value is None:
        return "（なし）"
    if isinstance(value, datetime.date):
        return value.isoformat()
    return str(value)


# --- 構文検査（許可リスト）------------------------------------------------


def _reject(src: str, node: ast.AST) -> None:
    raise ExprError(f"式 {src!r} に許可されていない構文があります（{type(node).__name__}）")


def _check(node: ast.AST, src: str, bound: frozenset, names: set) -> None:
    if isinstance(node, ast.BoolOp):
        if not isinstance(node.op, _ALLOWED_BOOL_OPS):
            _reject(src, node)
        for v in node.values:
            _check(v, src, bound, names)
    elif isinstance(node, ast.UnaryOp):
        if not isinstance(node.op, _ALLOWED_UNARY_OPS):
            _reject(src, node)
        _check(node.operand, src, bound, names)
    elif isinstance(node, ast.BinOp):
        if not isinstance(node.op, _ALLOWED_BIN_OPS):
            _reject(src, node)
        _check(node.left, src, bound, names)
        _check(node.right, src, bound, names)
    elif isinstance(node, ast.Compare):
        for op in node.ops:
            if not isinstance(op, _ALLOWED_CMP_OPS):
                _reject(src, node)
        _check(node.left, src, bound, names)
        for c in node.comparators:
            _check(c, src, bound, names)
    elif isinstance(node, ast.IfExp):
        _check(node.test, src, bound, names)
        _check(node.body, src, bound, names)
        _check(node.orelse, src, bound, names)
    elif isinstance(node, ast.Name):
        if node.id.startswith("_"):
            raise ExprError(f"式 {src!r} は許可されていない名前 {node.id!r} を使っています")
        if node.id not in bound:
            names.add(node.id)  # 関数名と同じ名前（count・max など）でも、呼び出しでなければ変数として扱う
    elif isinstance(node, ast.Attribute):
        if node.attr.startswith("_"):
            raise ExprError(f"式 {src!r} は許可されていない属性 {node.attr!r} を使っています")
        _check(node.value, src, bound, names)
    elif isinstance(node, ast.Constant):
        if node.value is not None and not isinstance(node.value, (str, int, float, bool)):
            _reject(src, node)
    elif isinstance(node, (ast.List, ast.Tuple)):
        for e in node.elts:
            _check(e, src, bound, names)
    elif isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ExprError(f"式 {src!r} は BUILTINS の名前しか呼び出せません（メソッド呼び出しは不可）")
        fname = node.func.id
        if fname.startswith("_") or fname not in BUILTINS:
            raise ExprError(f"式 {src!r} は許可されていない関数 {fname!r} を呼んでいます")
        if node.keywords:
            raise ExprError(f"式 {src!r} はキーワード引数を使えません")
        for a in node.args:
            if isinstance(a, ast.Starred):
                raise ExprError(f"式 {src!r} は * 引数を使えません")
            _check(a, src, bound, names)
    elif isinstance(node, (ast.GeneratorExp, ast.ListComp)):
        local_bound = bound
        for gen in node.generators:
            if gen.is_async:
                raise ExprError(f"式 {src!r} は async for を使えません")
            if not isinstance(gen.target, ast.Name):
                raise ExprError(f"式 {src!r} の for の対象は名前 1 つにしてください")
            if gen.target.id.startswith("_"):
                raise ExprError(f"式 {src!r} は許可されていない名前 {gen.target.id!r} を使っています")
            _check(gen.iter, src, local_bound, names)
            local_bound = local_bound | {gen.target.id}
            for cond in gen.ifs:
                _check(cond, src, local_bound, names)
        _check(node.elt, src, local_bound, names)
    else:
        _reject(src, node)


# --- 評価 -------------------------------------------------------------


def _eval(node: ast.AST, env: Mapping, bound: dict, counter: list, src: str) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in bound:
            return bound[node.id]
        try:
            return env[node.id]
        except KeyError:
            raise ExprError(f"式 {src!r} の名前 {node.id!r} には値がありません") from None
    if isinstance(node, ast.Attribute):
        value = _eval(node.value, env, bound, counter, src)
        return _attr_get(value, node.attr, src)
    if isinstance(node, ast.BoolOp):
        result: Any = True if isinstance(node.op, ast.And) else False
        for v in node.values:
            result = _eval(v, env, bound, counter, src)
            if isinstance(node.op, ast.And):
                if not result:
                    return result
            else:
                if result:
                    return result
        return result
    if isinstance(node, ast.UnaryOp):
        value = _eval(node.operand, env, bound, counter, src)
        if isinstance(node.op, ast.Not):
            return not value
        try:
            return -value
        except TypeError as e:
            raise ExprError(f"式 {src!r} の単項 - の評価に失敗しました（{e}）") from e
    if isinstance(node, ast.BinOp):
        left = _eval(node.left, env, bound, counter, src)
        right = _eval(node.right, env, bound, counter, src)
        if isinstance(node.op, ast.Mult) and not (
            isinstance(left, (int, float)) and isinstance(right, (int, float))
        ):
            raise ExprError(f"式 {src!r} の * は数どうしにだけ使えます")
        try:
            return _BIN_FUNCS[type(node.op)](left, right)
        except ExprError:
            raise
        except Exception as e:
            raise ExprError(f"式 {src!r} の演算に失敗しました（{e}）") from e
    if isinstance(node, ast.Compare):
        left = _eval(node.left, env, bound, counter, src)
        for op, comp_node in zip(node.ops, node.comparators):
            right = _eval(comp_node, env, bound, counter, src)
            if not _compare_one(op, left, right, src):
                return False
            left = right
        return True
    if isinstance(node, ast.IfExp):
        test = _eval(node.test, env, bound, counter, src)
        if test:
            return _eval(node.body, env, bound, counter, src)
        return _eval(node.orelse, env, bound, counter, src)
    if isinstance(node, ast.List):
        return [_eval(e, env, bound, counter, src) for e in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_eval(e, env, bound, counter, src) for e in node.elts)
    if isinstance(node, ast.Call):
        fname = node.func.id  # type: ignore[union-attr]
        args = [_eval(a, env, bound, counter, src) for a in node.args]
        return _call_builtin(fname, args, env, src)
    if isinstance(node, (ast.GeneratorExp, ast.ListComp)):
        return _eval_comprehension(node, env, bound, counter, src)
    raise ExprError(f"式 {src!r} に許可されていない構文があります（{type(node).__name__}）")


def _attr_get(obj: Any, name: str, src: str) -> Any:
    if obj is None:
        return None
    if isinstance(obj, list):
        out = []
        for item in obj:
            v = _attr_get(item, name, src)
            if isinstance(v, list):
                out.extend(v)
            else:
                out.append(v)
        return out
    onto_get = getattr(obj, "onto_get", None)
    if callable(onto_get):
        try:
            return onto_get(name)
        except HiddenPropertyError:
            raise ExprError(f"{name} は照会に使えない（非表示のプロパティ）") from None
        except KeyError:
            type_name = getattr(obj, "type", None) or type(obj).__name__
            raise ExprError(f"式 {src!r}: {type_name} に {name} は無い") from None
    if isinstance(obj, Mapping):
        try:
            return obj[name]
        except KeyError:
            raise ExprError(f"式 {src!r}: {name!r} という名前は無い") from None
    raise ExprError(f"式 {src!r} は属性を持たない値 {name!r} を参照しています")


def _compare_one(op: ast.cmpop, left: Any, right: Any, src: str) -> bool:
    if isinstance(op, (ast.Lt, ast.LtE, ast.Gt, ast.GtE)):
        if left is None or right is None:
            return False
        try:
            return _ORDER_OPS[type(op)](left, right)
        except TypeError as e:
            raise ExprError(f"式 {src!r} の比較に失敗しました（{e}）") from e
    if isinstance(op, ast.Eq):
        return left == right
    if isinstance(op, ast.NotEq):
        return left != right
    if isinstance(op, ast.Is):
        return left is right
    if isinstance(op, ast.IsNot):
        return left is not right
    if isinstance(op, (ast.In, ast.NotIn)):
        if left is None or right is None:
            return False
        try:
            contained = left in right
        except TypeError as e:
            raise ExprError(f"式 {src!r} の in に失敗しました（{e}）") from e
        return contained if isinstance(op, ast.In) else not contained
    raise ExprError(f"式 {src!r} は許可されていない比較演算子です")


def _call_builtin(fname: str, args: list, env: Mapping, src: str) -> Any:
    today_override = env.get("__today__") if isinstance(env, Mapping) else None
    if fname == "today":
        if args:
            raise ExprError(f"式 {src!r} の today() は引数を取りません")
        return today_override if today_override is not None else datetime.date.today()
    if fname == "days_since":
        if len(args) != 1:
            raise ExprError(f"式 {src!r} の days_since は引数を 1 つ取ります")
        d = args[0]
        if d is None:
            return None
        base = today_override if today_override is not None else datetime.date.today()
        return (base - d).days
    if fname == "days_between":
        if len(args) != 2:
            raise ExprError(f"式 {src!r} の days_between は引数を 2 つ取ります")
        a, b = args
        if a is None or b is None:
            return None
        return (b - a).days
    func = BUILTINS[fname]
    try:
        return func(*args)
    except ExprError:
        raise
    except Exception as e:
        raise ExprError(f"式 {src!r} の {fname}(...) の評価に失敗しました（{e}）") from e


def _eval_comprehension(node: ast.AST, env: Mapping, bound: dict, counter: list, src: str) -> list:
    results: list = []
    generators = node.generators  # type: ignore[attr-defined]
    elt = node.elt  # type: ignore[attr-defined]

    def rec(gen_index: int, local_bound: dict) -> None:
        if gen_index == len(generators):
            results.append(_eval(elt, env, local_bound, counter, src))
            return
        gen = generators[gen_index]
        iterable = _eval(gen.iter, env, local_bound, counter, src)
        if iterable is None:
            iterable = []
        elif isinstance(iterable, (list, tuple)):
            pass
        elif hasattr(iterable, "onto_get"):
            iterable = [iterable]  # 1 件のリンク（リストでない実体）も回せるようにする
        else:
            raise ExprError(
                f"式 {src!r} の for は反復できない値に使われています（{type(iterable).__name__}）"
            )
        for item in iterable:
            counter[0] += 1
            if counter[0] > _MAX_ITERATIONS:
                raise ExprError(f"式 {src!r} の反復回数が上限（{_MAX_ITERATIONS}）を超えました")
            new_bound = dict(local_bound)
            new_bound[gen.target.id] = item
            ok = True
            for cond in gen.ifs:
                if not _eval(cond, env, new_bound, counter, src):
                    ok = False
                    break
            if ok:
                rec(gen_index + 1, new_bound)

    rec(0, bound)
    return results
