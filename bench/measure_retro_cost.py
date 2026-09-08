"""Estimate per-session input for a SessionEnd retrospective hook.

usage: uv run python bench/measure_retro_cost.py   (writes bench/results/retro_cost.csv)
"""
import csv, glob, json, math, os, statistics

BASE = os.path.expanduser("~/.claude/projects")
GROUPS = {
    "agent-ws": f"{BASE}/*-poc-agent-ws/*.jsonl",
    "workspace": f"{BASE}/*-workspace/*.jsonl",
}
# system-generated user records (not human speech): shell output, subagent notices
SYSTEM_TAGS = ("<local-command-stdout>", "<bash-stdout>", "<task-notification>")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "retro_cost.csv")


def user_text(o):
    """Human-typed text of a user record, or None if it is not a human turn."""
    if o.get("isMeta") or o.get("isCompactSummary") or o.get("isSidechain"):
        return None
    c = o.get("message", {}).get("content")
    if isinstance(c, str):
        return None if c.lstrip().startswith(SYSTEM_TAGS) else c
    if isinstance(c, list):
        t = [b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text"]
        t = [x for x in t if not x.lstrip().startswith(SYSTEM_TAGS)]
        return "\n".join(t) if t else None  # tool_result-only -> None
    return None


def measure(path):
    a = os.path.getsize(path)
    b = 0; n_asst = 0; c = 0; d = 0; e = 0
    for line in open(path, encoding="utf-8"):
        try:
            o = json.loads(line)
        except json.JSONDecodeError:
            continue
        t = o.get("type"); m = o.get("message")
        if not isinstance(m, dict):
            continue
        if t == "user":
            txt = user_text(o)
            if txt is not None:
                c += 1; e += len(txt); d += len(txt)
        elif t == "assistant" and not o.get("isSidechain"):
            n_asst += 1
            u = m.get("usage") or {}
            if u:
                b = (u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0)
                     + u.get("cache_creation_input_tokens", 0))
            cont = m.get("content")
            if isinstance(cont, list):
                d += sum(len(x.get("text", "")) for x in cont
                         if isinstance(x, dict) and x.get("type") == "text")
    return dict(a_bytes=a, b_ctx_tokens=b, n_assistant=n_asst, c_user_turns=c,
                d_text_chars=d, d_tok_div4=d // 4, d_tok_div2=d // 2,
                e_user_chars=e, e_tok_div4=e // 4, e_tok_div2=e // 2)


def p(xs, q):
    xs = sorted(xs)
    return xs[max(0, math.ceil(q * len(xs)) - 1)]  # nearest-rank


rows = []
for g, pat in GROUPS.items():
    for f in sorted(glob.glob(pat)):
        rows.append(dict(group=g, session=os.path.basename(f)[:-6], **measure(f)))

with open(OUT, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)

cols = ["a_bytes", "b_ctx_tokens", "c_user_turns", "d_text_chars", "d_tok_div4",
        "e_user_chars", "e_tok_div4"]
for g in GROUPS:
    allr = [r for r in rows if r["group"] == g]
    ne = [r for r in allr if r["n_assistant"] > 0]
    print(f"\n== {g}: {len(allr)} sessions, {len(allr)-len(ne)} with no assistant msg (excluded below)")
    print(f"{'metric':14} {'median':>10} {'p90':>10} {'max':>10}")
    for col in cols:
        xs = [r[col] for r in ne]
        print(f"{col:14} {int(statistics.median(xs)):>10} {p(xs,0.9):>10} {max(xs):>10}")
print("\nwrote", OUT)

if __name__ == "__main__":  # self-check on a synthetic transcript
    import tempfile
    rec = [
        {"type": "user", "message": {"content": "hi"}},
        {"type": "assistant", "message": {"usage": {"input_tokens": 1, "cache_read_input_tokens": 2,
         "cache_creation_input_tokens": 3}, "content": [{"type": "text", "text": "abcd"},
         {"type": "tool_use", "input": {"x": "zzzzzzzz"}}]}},
        {"type": "user", "message": {"content": [{"type": "tool_result", "content": "zzz"}]}},
        {"type": "user", "isMeta": True, "message": {"content": "<local-command-caveat>"}},
    ]
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as t:
        for r in rec: t.write(json.dumps(r) + "\n")
    m = measure(t.name); os.unlink(t.name)
    assert (m["b_ctx_tokens"], m["c_user_turns"], m["d_text_chars"], m["e_user_chars"]) == (6, 1, 6, 2), m
