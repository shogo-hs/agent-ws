"""wsonto が利用者に見せるエラー。メッセージは日本語 1 行で、何を直せばよいかを書く。"""
from __future__ import annotations


class OntoError(Exception):
    """wsonto の全エラーの基底。CLI はこれを捕まえて `ws: <message>` と出して終了コード 1。"""


class SchemaError(OntoError):
    """定義（ontology.json）の誤り。problems に 1 件 1 行で全部入れる（最初の 1 件で止めない）。"""

    def __init__(self, problems: list[str], source: str = ""):
        self.problems = list(problems)
        self.source = source
        head = f"{source}: " if source else ""
        super().__init__(head + " / ".join(self.problems))


class ExprError(OntoError):
    """式の構文が許可リストの外、または評価中の誤り（存在しないプロパティ名など）。"""


class StoreError(OntoError):
    """実体の保管（objects.json）の読み書き・ロック・参照の解決の誤り。"""


class HiddenPropertyError(KeyError):
    """`Store.hide_hidden` が立っているときに `agent_visible: false` のプロパティへ触れた合図。

    `KeyError` の子なので既存の `except KeyError` はそのまま拾える。利用者にそのまま
    見せるものではなく、`query.py` の where / select がこれを見て ExprError か
    「（非表示）」に変換してから使う（`OntoError` は継承しない）。
    """
