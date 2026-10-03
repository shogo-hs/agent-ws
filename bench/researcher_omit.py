"""調査係（researcher）に omitClaudeMd を付けるかを決めるための実測（ADR 0024）。

本線（sonnet）に、researcher_effort.py と同じ架空の文字起こしから決定事項と宿題を researcher に抜かせる。
researcher.md に `omitClaudeMd: true` が無い条件（base）と有る条件（omit）を交互に走らせ、
researcher 側の transcript（<session>/subagents/*.jsonl）から 1 リクエスト目の入力（固定分）・処理した入力の合計・
cache 作成・出力と、out.md の正答率を `bench/results/runs_omit.jsonl` に残す。python3 の標準ライブラリだけで動く。

  python3 bench/researcher_effort.py gen     # 材料（transcript.md・truth.json）が無ければ先に作る
  python3 bench/researcher_omit.py run 3     # base / omit を各 3 回
  python3 bench/researcher_omit.py summary
"""
import json, os, statistics, subprocess, sys, tarfile, tempfile, io
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from researcher_effort import E, PROMPT, score  # noqa: E402

RUNS = Path(E).parent / "omit"
RESULTS = HERE / "results" / "runs_omit.jsonl"
MAIN = ("researcher サブエージェントに次の仕事を 1 回で渡してください。あなた自身は transcript.md を読みません。"
        "終わったら researcher の返答の件数だけを返してください。\n---\n" + PROMPT)


def build(cond: str, i: int) -> Path:
    d = Path(tempfile.mkdtemp(prefix=f"{cond}-{i}-", dir=RUNS))
    tar = subprocess.run(["git", "-C", str(HERE.parent), "archive", "HEAD"], capture_output=True, check=True).stdout
    tarfile.open(fileobj=io.BytesIO(tar)).extractall(d, filter="data")
    agent = d / ".claude/agents/researcher.md"
    text = agent.read_text(encoding="utf-8")
    text = text.replace("\nomitClaudeMd: true\n", "\n")  # HEAD に入った後でも base を作れるように
    if cond == "omit":
        text = text.replace("\nmodel: haiku\n", "\nmodel: haiku\nomitClaudeMd: true\n", 1)
    agent.write_text(text, encoding="utf-8")
    (d / "transcript.md").write_text(Path(E, "transcript.md").read_text(encoding="utf-8"), encoding="utf-8")
    return d


def usage(path: Path) -> dict:
    seen, reqs, out, cc = set(), [], 0, 0
    for line in path.read_text(encoding="utf-8").splitlines():
        o = json.loads(line)
        msg = o.get("message") or {}
        if o.get("type") != "assistant" or msg.get("id") in seen:
            continue  # content block ごとに同じ usage が繰り返し入るので id で重複除去
        seen.add(msg.get("id"))
        u = msg.get("usage") or {}
        reqs.append(u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0))
        out += u.get("output_tokens", 0); cc += u.get("cache_creation_input_tokens", 0)
    return {"first_in": reqs[0] if reqs else 0, "in_total": sum(reqs), "cache_create": cc, "out": out, "turns": len(reqs)}


def one(cond: str, i: int, truth: dict) -> dict:
    d = build(cond, i)
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    p = subprocess.run(["claude", "-p", MAIN, "--model", "sonnet", "--output-format", "json", "--setting-sources", "project",
                        "--strict-mcp-config", "--max-turns", "10", "--allowedTools", "Agent,Read,Grep,Glob,Bash,Write,Edit"],
                       cwd=d, env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=1200)
    try:
        res = json.loads(p.stdout)
    except ValueError:
        res = {}
    sid = res.get("session_id", "")
    subs = list(Path.home().glob(f".claude/projects/*/{sid}/subagents/*.jsonl")) if sid else []
    u = usage(subs[0]) if len(subs) == 1 else {}
    return {"cond": cond, "i": i, "rc": p.returncode, "subagents": len(subs), **u, "main_cost": res.get("total_cost_usd"),
            "score": score(str(d / "out.md"), truth), "dir": d.name}


def run():
    n = int(sys.argv[2])
    truth = json.load(open(f"{E}/truth.json"))
    RUNS.mkdir(parents=True, exist_ok=True); RESULTS.parent.mkdir(exist_ok=True)
    with open(RESULTS, "a") as f:
        for i in range(n):
            for cond in ("base", "omit"):  # 交互に走らせて時間帯の差を均す
                r = one(cond, i, truth)
                f.write(json.dumps(r, ensure_ascii=False) + "\n"); f.flush()
                print(cond, i, r.get("first_in"), r.get("in_total"), r.get("cache_create"), r["score"], flush=True)


def summary():
    rows = [json.loads(l) for l in open(RESULTS) if l.strip()]
    print("| 条件 | n | 1 リクエスト目の入力 | 処理した入力の合計 | cache 作成 | 出力 | 正答率 | 全問正解 |")
    print("|---|---|---|---|---|---|---|---|")
    for c in ("base", "omit"):
        g = [r for r in rows if r["cond"] == c and r.get("first_in")]
        if not g:
            continue
        med = lambda k: int(statistics.median(r[k] for r in g))
        acc = [r["score"]["acc"] if r.get("score") else 0 for r in g]
        print(f"| {c} | {len(g)} | {med('first_in')} | {med('in_total')} | {med('cache_create')} | {med('out')} "
              f"| {statistics.median(acc):.3f} | {sum(a == 1.0 for a in acc)}/{len(g)} |")


if __name__ == "__main__":
    {"run": run, "summary": summary}[sys.argv[1]]()
