#!/usr/bin/env python3
"""bench の結果（runs*.jsonl）の transcript から、1 セッションの費用を費目に分解して tag ごとの中央値を出す。

  uv run bench/cost_breakdown.py bench/results/runs_v3.jsonl [--group tag|exp]

費目は input / cache 作成 5m / cache 作成 1h / cache 読み / 出力（thinking 込み）。単価は PRICES（$/MTok）。
Claude Code の cost_usd はこの積の和と一致する（ts8 の 40 セッションで差ゼロを確認）。標準ライブラリだけで動く。
"""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

PRICES = {  # $/MTok。docs/snapshots の Pricing を参照
    "claude-sonnet-5": dict(input=2.0, cc5=2.5, cc1h=4.0, cr=0.2, out=10.0),
    "claude-haiku-4-5": dict(input=1.0, cc5=1.25, cc1h=2.0, cr=0.1, out=5.0),
}


def usage_of(tpath: Path) -> dict:
    seen, u = set(), dict(input=0, cc5=0, cc1h=0, cr=0, out=0, think=0, turns=0, model="")
    for line in tpath.read_text(encoding="utf-8").splitlines():
        try:
            o = json.loads(line)
        except json.JSONDecodeError:
            continue
        if o.get("type") != "assistant" or o.get("isSidechain"):
            continue
        msg = o.get("message", {})
        mid, us = msg.get("id"), msg.get("usage") or {}
        if not mid or mid in seen or not us:
            continue
        seen.add(mid)
        u["turns"] += 1
        u["model"] = msg.get("model", u["model"])
        u["input"] += us.get("input_tokens", 0)
        cc = us.get("cache_creation") or {}
        u["cc5"] += cc.get("ephemeral_5m_input_tokens", 0)
        u["cc1h"] += cc.get("ephemeral_1h_input_tokens", 0)
        if not cc:
            u["cc5"] += us.get("cache_creation_input_tokens", 0)
        u["cr"] += us.get("cache_read_input_tokens", 0)
        u["out"] += us.get("output_tokens", 0)
        u["think"] += (us.get("output_tokens_details") or {}).get("thinking_tokens", 0)
    return u


def cost_of(u: dict) -> dict:
    key = next((k for k in PRICES if u["model"].startswith(k)), "claude-sonnet-5")
    p = PRICES[key]
    return {k: u[k] * p[k] / 1e6 for k in ("input", "cc5", "cc1h", "cr", "out")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--group", default="tag", choices=["tag", "exp"])
    a = ap.parse_args()
    groups: dict[str, list[dict]] = {}
    for line in Path(a.results).read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if not r.get("transcript"):
            continue
        t = Path(r["transcript"].replace("~", str(Path.home()), 1))
        if not t.exists():
            continue
        u = usage_of(t)
        c = cost_of(u)
        key = Path(r["rundir"]).parts[-2] if a.group == "tag" else f"{r['exp']}/S{r['stage']}" if r.get("stage") else r["exp"]
        groups.setdefault(key, []).append(dict(u=u, c=c, total=sum(c.values()), rec=r["cost_usd"]))
    med = lambda xs: statistics.median(xs) if xs else 0
    print("| 条件 | n | ターン | 入力 tok | cache 作成 tok | cache 読み tok | 出力 tok（thinking） | 費用 $ | 内 cache 作成 | 内 cache 読み | 内 出力 |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for k, rs in groups.items():
        tot = med([r["total"] for r in rs])
        cc = med([r["c"]["cc5"] + r["c"]["cc1h"] for r in rs]); cr = med([r["c"]["cr"] for r in rs]); out = med([r["c"]["out"] for r in rs])
        print(f"| {k} | {len(rs)} | {med([r['u']['turns'] for r in rs]):.0f} | {med([r['u']['input'] for r in rs]):,.0f} | "
              f"{med([r['u']['cc5'] + r['u']['cc1h'] for r in rs]):,.0f} | {med([r['u']['cr'] for r in rs]):,.0f} | "
              f"{med([r['u']['out'] for r in rs]):,.0f}（{med([r['u']['think'] for r in rs]):,.0f}） | {tot:.3f} | "
              f"{100 * cc / tot:.0f}% | {100 * cr / tot:.0f}% | {100 * out / tot:.0f}% |")
    worst = max((abs(r["total"] - r["rec"]) / r["rec"] for rs in groups.values() for r in rs), default=0)
    print(f"\n記録の cost_usd との最大差: {100 * worst:.2f}%")


if __name__ == "__main__":
    main()
