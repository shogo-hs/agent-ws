"""bench/run.py の Codex 対応（--agent codex）の自己チェック。  python3 -m unittest tests.test_bench_codex -v

codex exec を実際には呼ばない。rollout の形を architecture 通りに模した
fixture（tests/fixtures/codex_rollout_min.jsonl・架空）だけで数え方を検証する。
"""
import argparse
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parent.parent
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "codex_rollout_min.jsonl"


def _load_run_module():
    spec = importlib.util.spec_from_file_location("bench_run", REPO / "bench" / "run.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


RUN = _load_run_module()


class AnalyzeCodexTest(unittest.TestCase):
    """fixture: token_usage_record 3 件（1 件は response_id 重複）、
    CommandExecution 2 件（現在のタスクの参照を cat / 他タスクのファイルを cat）、
    FileChange 1 件（現在のタスクへの書き込み）、拒否の custom_tool_call_output 1 件。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="bench-codex-test-"))
        self.rundir = self.tmp / "rundir"
        self.rundir.mkdir()
        text = FIXTURE.read_text(encoding="utf-8").replace("__RUNDIR__", str(self.rundir))
        self.rollout = self.tmp / "rollout.jsonl"
        self.rollout.write_text(text, encoding="utf-8")

    def is_other(self, p: str) -> bool:
        return "other_task" in p

    def test_counts(self):
        m = RUN.analyze_codex(self.rollout, self.rundir, self.is_other)
        # token_usage_record: resp_1 が重複、resp_2 で新規 -> turns は重複を除いた件数
        self.assertEqual(m["turns"], 2)
        self.assertEqual(m["in_total"], 1000 + 2000)
        self.assertEqual(m["cached_in"], 200 + 500)
        self.assertEqual(m["out_total"], 50 + 80)
        self.assertEqual(m["reasoning_out"], 10 + 20)
        self.assertEqual(m["ctx_final"], 2000)  # 最後の input_tokens
        self.assertEqual(m["model"], "gpt-6.1-sol")
        # CommandExecution 2 件とも cat = read。2 件目は他タスクのパス
        self.assertEqual(m["reads"], 2)
        self.assertEqual(m["searches"], 1)  # 拒否された ls projects/ も Claude 側と同じく検索に数える
        # FileChange 1 件（現在のタスクへの書き込みなので other_task は増えない）
        self.assertEqual(m["writes"], 1)
        self.assertEqual(m["other_task"], 1)
        # 拒否の custom_tool_call_output 1 件
        self.assertEqual(m["denied"], 1)


class CodexCreditsTest(unittest.TestCase):
    def test_known_model(self):
        # ((1,000,000-200,000)*2.5 + 200,000*0.25 + 100,000*12.5) / 1e6 = 3.3
        self.assertAlmostEqual(RUN.codex_credits("gpt-6-luna", 1_000_000, 200_000, 100_000), 3.3)

    def test_unknown_model(self):
        self.assertIsNone(RUN.codex_credits("no-such-model", 1, 1, 1))


class CodexHelpersTest(unittest.TestCase):
    def test_codex_usage_dedups_and_reads_model(self):
        u = RUN.codex_usage(FIXTURE)
        self.assertEqual((u["in"], u["cached"], u["out"], u["model"]), (3000, 700, 130, "gpt-6.1-sol"))

    def test_tilde_str(self):
        self.assertEqual(RUN.tilde_str(f"cat {Path.home()}/x"), "cat ~/x")


class FollowupTest(unittest.TestCase):
    def test_claude_resume_flag(self):
        cmd = RUN.build_claude_cmd("答え", "sonnet", 30, resume="sid-1")
        self.assertEqual(cmd[-2:], ["--resume", "sid-1"])

    def test_summary_labels_do_not_look_like_successes(self):
        tmp = Path(tempfile.mkdtemp(prefix="bench-codex-test-"))
        results = tmp / "runs.jsonl"
        base = {"exp": "trap", "stage": None, "scale": "large", "model": "m", "cond": "B", "rundir": "x", "agent": "codex"}
        rows = [dict(base, verdict="none", task_pick="asked"), dict(base, verdict="correct", task_pick="estimate", followup=True)]
        results.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
        with mock.patch.object(RUN, "RESULTS", tmp):
            RUN.cmd_summary(argparse.Namespace(results=str(results), tag=None))
        md = (tmp / "summary.md").read_text(encoding="utf-8")
        self.assertIn("聞き返し（未着手）×1", md)
        self.assertIn("correct（2 往復）×1", md)


class CmdSummaryRobustnessTest(unittest.TestCase):
    """chain_id が無い（None）行で --tag を付けても落ちないこと。"""

    def test_missing_chain_id_with_tag(self):
        tmp = Path(tempfile.mkdtemp(prefix="bench-codex-test-"))
        results = tmp / "runs.jsonl"
        rec = {"exp": "trap", "stage": None, "scale": "small", "model": "sonnet", "cond": "A",
               "rundir": str(tmp / "somewhere"), "chain_id": None}
        results.write_text(json.dumps(rec) + "\n", encoding="utf-8")
        args = argparse.Namespace(results=str(results), tag="does-not-match")
        with mock.patch.object(RUN, "RESULTS", tmp):  # summary.md / summary.json をリポジトリの bench/results/ に書かせない
            RUN.cmd_summary(args)  # 例外を投げなければ OK
        self.assertTrue((tmp / "summary.md").exists())  # 書き出し先は RESULTS（ここでは tmp）


class BuildClaudeCmdTest(unittest.TestCase):
    """既定（agent 未指定）の run は claude を呼ぶ組み立てになること。subprocess は呼ばない。"""

    def test_default_agent_is_claude(self):
        parser = RUN.build_parser()
        args = parser.parse_args(["run", "--exp", "trap"])
        self.assertEqual(args.agent, "claude")

    def test_codex_agent_can_be_selected(self):
        parser = RUN.build_parser()
        args = parser.parse_args(["run", "--exp", "trap", "--agent", "codex", "--model", "gpt-6.1-sol"])
        self.assertEqual(args.agent, "codex")

    def test_build_claude_cmd(self):
        cmd = RUN.build_claude_cmd("続きをやって", "sonnet", 30, delegate=False, advisor=None, effort=None)
        self.assertEqual(cmd[0], "claude")
        self.assertIn("続きをやって", cmd)
        self.assertIn("--model", cmd)
        self.assertIn("sonnet", cmd)
        self.assertNotIn("Agent", ",".join(cmd))  # delegate=False なら allowedTools に Agent が無い

    def test_build_claude_cmd_delegate_adds_agent_tool(self):
        cmd = RUN.build_claude_cmd("x", "sonnet", 30, delegate=True, advisor=None, effort=None)
        i = cmd.index("--allowedTools")
        self.assertIn("Agent", cmd[i + 1])


if __name__ == "__main__":
    unittest.main()
