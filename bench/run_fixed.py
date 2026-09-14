"""固定分（1 ターンで必ず送られる分）を変種ごとに測る。各 2 回（2 回目は cache read で安定する）。

  uv run bench/run.py build --cond A --scale large --state doing --out bench/fixed/A
  uv run bench/run_fixed.py [変種名 ...]     # 省略時は全部。結果は results/fixed_v3.jsonl に追記
  RUNDIR=<dir> uv run bench/run_fixed.py default   # 別のディレクトリ（settings.json を変えた写しなど）で測る

標準ライブラリだけで動く。表にしたものは results/fixed_v3.md。
"""
import json, os, subprocess, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
RUNDIR = Path(os.environ.get("RUNDIR") or HERE / "fixed" / "A")  # bench/run.py build --cond A --scale large --state doing --out bench/fixed/A
BASE = ["claude", "-p", "OK とだけ答えて", "--model", "sonnet", "--output-format", "json",
        "--setting-sources", "project", "--strict-mcp-config", "--max-turns", "1",
        "--allowedTools", "Read,Grep,Glob,Bash,Write,Edit"]
VARIANTS = {
    "default": [],
    "effort_low": ["--effort", "low"],
    "effort_high": ["--effort", "high"],
    "disallow": ["--disallowedTools", "WebSearch,WebFetch,NotebookEdit,Agent,TodoWrite,KillShell,BashOutput,ExitPlanMode,EnterPlanMode,ToolSearch,AskUserQuestion,Skill"],
    "bare": ["--bare"],
    "disallow_noTS": ["--disallowedTools", "WebSearch,WebFetch,NotebookEdit,Agent,TodoWrite,KillShell,BashOutput,ExitPlanMode,EnterPlanMode,AskUserQuestion,Skill"],
    "disallow_min": ["--disallowedTools", "WebSearch,WebFetch,NotebookEdit"],
    "disallow_TSonly": ["--disallowedTools", "ToolSearch"],
    "tools6": ["--tools", "Read,Grep,Glob,Bash,Write,Edit"],
    "haiku": ["--model", "haiku"],
    "tools8": ["--tools", "Read,Grep,Glob,Bash,Write,Edit,Agent,Skill"],
    "tools_default": ["--tools", "default"],
    "tools6_haiku": ["--tools", "Read,Grep,Glob,Bash,Write,Edit", "--model", "haiku"],
    "disallow_eager": ["--disallowedTools", "ListAgents,ReportFindings,ScheduleWakeup,Workflow"],
    "disallow_eager_AS": ["--disallowedTools", "ListAgents,ReportFindings,ScheduleWakeup,Workflow,Agent,Skill"],
    "tools7_skill": ["--tools", "Read,Grep,Glob,Bash,Write,Edit,Skill"],
    "tools7_agent": ["--tools", "Read,Grep,Glob,Bash,Write,Edit,Agent"],
}
env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
out = HERE / "results" / "fixed_v3.jsonl"
sel = sys.argv[1:] or list(VARIANTS)
for name in sel:
    for i in range(2):
        t0 = time.time()
        p = subprocess.run(BASE + VARIANTS[name], cwd=RUNDIR, env=env, stdin=subprocess.DEVNULL,
                           capture_output=True, text=True, timeout=300)
        try:
            r = json.loads(p.stdout[p.stdout.find("{"):])
        except Exception:
            print(name, i, "ERR", p.returncode, p.stderr[-300:], p.stdout[:300]); continue
        u = r.get("usage", {})
        fixed = u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0)
        rec = dict(variant=name, i=i, fixed=fixed, input=u.get("input_tokens"), cc=u.get("cache_creation_input_tokens"),
                   cc5=(u.get("cache_creation") or {}).get("ephemeral_5m_input_tokens"), cc1h=(u.get("cache_creation") or {}).get("ephemeral_1h_input_tokens"),
                   cr=u.get("cache_read_input_tokens"), out=u.get("output_tokens"), think=(u.get("output_tokens_details") or {}).get("thinking_tokens"),
                   cost=r.get("total_cost_usd"), turns=r.get("num_turns"), result=(r.get("result") or "")[:40], sec=round(time.time()-t0,1))
        print(json.dumps(rec, ensure_ascii=False), flush=True)
        with out.open("a") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")
