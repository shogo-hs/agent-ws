"""固定分（1 ターンで必ず送られる分）の内訳を、部品を 1 つずつ外して測る。Claude（sonnet）各 2 回、Codex（gpt-6.1-sol・medium）各 1 回。

  python3 bench/fixed_parts.py                 # このリポジトリで A と 4 変種。結果は results/fixed_parts.jsonl に追記
  python3 bench/fixed_parts.py A --label A2    # 別の版（規約を変えた写しなど）の A だけを測るときは、その写しの中で叩く

差（A − 変種）がその部品のトークン。Claude は 2 回目が cache read で安定する。標準ライブラリだけで動く。
"""
import argparse, json, os, shutil, subprocess, tempfile
from pathlib import Path
import run as R

def no_agents(d): (d / "AGENTS.md").write_text("")
def no_skills(d):
    for p in (d / ".agents" / "skills").iterdir():
        shutil.rmtree(p)
def no_hook(d):
    for f in (d / ".claude" / "settings.json", d / ".codex" / "hooks.json"):
        s = json.loads(f.read_text(encoding="utf-8")); s["hooks"].pop("SessionStart"); f.write_text(json.dumps(s), encoding="utf-8")
def no_researcher(d): shutil.rmtree(d / ".claude" / "agents"); shutil.rmtree(d / ".codex" / "agents")
VARIANTS = {"A": None, "noAGENTS": no_agents, "noSkills": no_skills, "noHook": no_hook, "noResearcher": no_researcher}
PROMPT = "OK とだけ答えて"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("variants", nargs="*", default=list(VARIANTS))
    ap.add_argument("--label", help="結果の variant に書く名前（既定は変種名）")
    args = ap.parse_args()
    out = R.RESULTS / "fixed_parts.jsonl"
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    for name in args.variants:
        d = Path(tempfile.mkdtemp(prefix="fixed-parts-")) / name
        R.build("A", "large", "doing", d)
        if VARIANTS[name]:
            VARIANTS[name](d)
        label = args.label or name
        recs = []
        for i in range(2):
            p = subprocess.run(["claude", "-p", PROMPT, "--model", "sonnet", "--output-format", "json", "--setting-sources", "project",
                                "--strict-mcp-config", "--max-turns", "1", "--allowedTools", R.ALLOWED_TOOLS],
                               cwd=d, env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=300)
            r = json.loads(p.stdout[p.stdout.find("{"):]); u = r["usage"]
            recs.append(dict(agent="claude", variant=label, i=i, cost=r.get("total_cost_usd"),
                             fixed=u["input_tokens"] + u["cache_creation_input_tokens"] + u["cache_read_input_tokens"]))
        res, _, _, _, home = R.run_codex(d, PROMPT, "gpt-6.1-sol", "medium", True)
        u = R.codex_usage(R.find_rollout(home, res["thread_id"]))
        shutil.rmtree(home, ignore_errors=True)
        recs.append(dict(agent="codex", variant=label, i=0, fixed=u["in"], out=u["out"],
                         credits=R.codex_credits("gpt-6.1-sol", u["in"], u["cached"], u["out"])))
        shutil.rmtree(d.parent, ignore_errors=True)
        with out.open("a", encoding="utf-8") as f:
            for rec in recs:
                print(json.dumps(rec, ensure_ascii=False), flush=True)
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    main()
