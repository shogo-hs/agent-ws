"""wsonto — agent-ws のオントロジーのエンジン。python3 の標準ライブラリだけで動く（3.9 以上）。

定義（ontology.json）を読み、実体（objects.json）への照会・前提条件の判定・実行・実行待ち・記録を行う。
構成とモジュール間の取り決めは scripts/wsonto/README.md。入口は scripts/ws onto …（cli.py）。
"""
