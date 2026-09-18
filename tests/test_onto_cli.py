"""cli.py / govern.py の適合テスト。標準ライブラリだけで動く（unittest）。

実体・定義を変えるテストは fixture を一時ディレクトリに写してから行う（取り決め通り）。
"""
from __future__ import annotations

import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from wsonto import cli, engine  # noqa: E402

FIXTURE_BASE = Path(__file__).resolve().parent / "fixtures" / "onto_case"


def _base_estimate_args(**overrides) -> list:
    params = {
        "title": "運用の見積", "sizing": "SD-2", "items": "pi-node,pi-monitor",
        "months": "12", "approver": "sato",
    }
    params.update(overrides)
    return [f"{k}={v}" for k, v in params.items()]


class CliCaseTest(unittest.TestCase):
    """common / project の fixture を一時ディレクトリに写して Ctx を組む。"""

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.common_dir = self.root / "knowledges" / "ontology"
        self.project_dir = self.root / "projects" / "acme" / "knowledges" / "ontology"
        shutil.copytree(FIXTURE_BASE / "common", self.common_dir)
        shutil.copytree(FIXTURE_BASE / "project", self.project_dir)

        self.agent_ctx = cli.Ctx(
            root=self.root, current_project="acme",
            current_task="projects/acme/tasks/20260916_estimate",
            session="s1", is_tty=False, user="reviewer",
        )
        self.human_ctx = cli.Ctx(
            root=self.root, current_project="acme",
            current_task="projects/acme/tasks/20260916_estimate",
            session=None, is_tty=True, user="reviewer",
        )
        self.common_agent_ctx = cli.Ctx(
            root=self.root, current_project=None, current_task=None,
            session="s1", is_tty=False, user="reviewer",
        )

    def _run(self, argv: list, ctx=None) -> "tuple[int, str, str]":
        ctx = ctx or self.agent_ctx
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli.main(argv, ctx)
        return code, out.getvalue(), err.getvalue()

    def _write_patch(self, patch: dict) -> str:
        path = self.root / f"patch_{uuid.uuid4().hex}.json"
        path.write_text(json.dumps(patch, ensure_ascii=False), encoding="utf-8")
        return str(path)


# --- types / describe ---------------------------------------------------


class TypesDescribeTest(CliCaseTest):
    def test_types_lists_object_and_actions(self) -> None:
        code, out, _err = self._run(["types"])
        self.assertEqual(code, 0)
        self.assertIn("IssueEstimate", out)
        self.assertIn("SizingDecision", out)

    def test_types_common_scope_has_no_project_actions(self) -> None:
        code, out, _err = self._run(["types"], self.common_agent_ctx)
        self.assertEqual(code, 0)
        self.assertIn("Person", out)
        self.assertNotIn("IssueEstimate", out)

    def test_describe_action_shows_criteria_and_message(self) -> None:
        code, out, _err = self._run(["describe", "IssueEstimate"])
        self.assertEqual(code, 0)
        self.assertIn("sizing.status == 'active'", out)
        self.assertIn("置き換え済みの決定", out)

    def test_describe_type_shows_props_and_inverse_link(self) -> None:
        code, out, _err = self._run(["describe", "SizingDecision"])
        self.assertEqual(code, 0)
        self.assertIn("nodes", out)
        self.assertIn("superseded_by", out)


# --- query / show ---------------------------------------------------------


class QueryShowTest(CliCaseTest):
    def test_query_where_finds_tanaka(self) -> None:
        code, out, _err = self._run(["query", "Person", "--where", "any('IdP' in w.name for w in leads)"])
        self.assertEqual(code, 0)
        self.assertIn("tanaka", out)

    def test_query_select_hides_for_agent(self) -> None:
        code, out, _err = self._run(["query", "Person", "--select", "name,email"])
        self.assertEqual(code, 0)
        self.assertIn("（非表示）", out)
        self.assertNotIn("sato@example.com", out)

    def test_query_select_shows_for_human(self) -> None:
        ctx = cli.Ctx(
            root=self.root, current_project="acme", current_task=None,
            session=None, is_tty=True, user="reviewer",
        )
        code, out, _err = self._run(["query", "Person", "--select", "name,email"], ctx)
        self.assertEqual(code, 0)
        self.assertIn("sato@example.com", out)

    def test_query_count(self) -> None:
        code, out, _err = self._run(["query", "Person", "--count"])
        self.assertEqual(code, 0)
        self.assertEqual(int(out.strip()), 6)  # common Person 4 件 + Stakeholder 2 件

    def test_show_without_type_finds_sd1(self) -> None:
        code, out, _err = self._run(["show", "SD-1"])
        self.assertEqual(code, 0)
        self.assertIn("SizingDecision:SD-1", out)


# --- act -------------------------------------------------------------------


class ActTest(CliCaseTest):
    def test_sd1_rejected(self) -> None:
        code, out, _err = self._run(["act", "IssueEstimate"] + _base_estimate_args(sizing="SD-1"))
        self.assertEqual(code, 4)
        self.assertIn("拒否", out)
        self.assertIn("置き換え済みの決定", out)

    def test_sd2_committed_with_next_and_task(self) -> None:
        code, out, _err = self._run(["act", "IssueEstimate"] + _base_estimate_args())
        self.assertEqual(code, 0)
        self.assertIn("反映", out)
        self.assertIn("次:", out)
        entries = engine.read_log(self.project_dir)
        self.assertEqual(entries[-1]["task"], self.agent_ctx.current_task)

    def test_months_24_staged(self) -> None:
        code, out, _err = self._run(["act", "IssueEstimate"] + _base_estimate_args(months="24"))
        self.assertEqual(code, 3)
        self.assertIn("実行待ち P-0001", out)
        self.assertTrue((self.project_dir / "proposals" / "P-0001.json").exists())

    def test_dry_run_writes_nothing(self) -> None:
        before = (self.project_dir / "objects.json").read_bytes()
        code, _out, _err = self._run(["act", "IssueEstimate"] + _base_estimate_args() + ["--dry-run"])
        self.assertEqual(code, 0)
        self.assertEqual((self.project_dir / "objects.json").read_bytes(), before)
        self.assertFalse((self.project_dir / "proposals").exists())

    def test_json_output_parses(self) -> None:
        code, out, _err = self._run(["act", "IssueEstimate"] + _base_estimate_args() + ["--json"])
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data["status"], "committed")

    def test_human_ctx_long_estimate_still_requires_approval(self) -> None:
        # 「実行者が人なら承認を省く」を engine.act 側から削る担当と同時作業。
        # 直り待ちなら code は 0（素通り）になり、ここだけ失敗してよい（報告に書く）。
        code, out, _err = self._run(["act", "IssueEstimate"] + _base_estimate_args(months="24"), self.human_ctx)
        self.assertEqual(code, 3)
        self.assertIn("実行待ち", out)

    def test_transfer_person_common_action_stages_in_common(self) -> None:
        code, out, _err = self._run(["act", "TransferPerson", "person=suzuki", "to=tech"])
        self.assertEqual(code, 3)
        self.assertIn("実行待ち", out)
        hits = list((self.common_dir / "proposals").glob("P-*.json"))
        self.assertEqual(len(hits), 1)
        self.assertFalse((self.project_dir / "proposals").exists())


# --- approve / reject（人だけ）------------------------------------------------


class ApproveRejectTest(CliCaseTest):
    def test_agent_cannot_approve(self) -> None:
        code, _out, _err = self._run(["act", "IssueEstimate"] + _base_estimate_args(months="24"))
        self.assertEqual(code, 3)
        code, _out, err = self._run(["approve", "P-0001"], self.agent_ctx)
        self.assertEqual(code, 1)
        self.assertIn("人だけ", err)

    def test_agent_cannot_reject(self) -> None:
        code, _out, _err = self._run(["act", "IssueEstimate"] + _base_estimate_args(months="24"))
        self.assertEqual(code, 3)
        code, _out, err = self._run(["reject", "P-0001", "--reason", "x"], self.agent_ctx)
        self.assertEqual(code, 1)
        self.assertIn("人だけ", err)

    def test_human_approves_via_cli(self) -> None:
        code, _out, _err = self._run(["act", "IssueEstimate"] + _base_estimate_args(months="24"))
        self.assertEqual(code, 3)
        code, out, _err = self._run(["approve", "P-0001"], self.human_ctx)
        self.assertEqual(code, 0)
        self.assertIn("反映", out)


# --- handle_prompt（UserPromptSubmit の承認・却下）---------------------------


class HandlePromptTest(CliCaseTest):
    def test_approve_creates_estimate_with_total(self) -> None:
        code, _out, _err = self._run(["act", "IssueEstimate"] + _base_estimate_args(months="24"))
        self.assertEqual(code, 3)
        msg = cli.handle_prompt("承認 P-0001", self.agent_ctx)
        self.assertIsNotNone(msg)
        self.assertIn("P-0001", msg)
        self.assertIn("9840000", msg)

    def test_reject_records_reason(self) -> None:
        code, _out, _err = self._run(["act", "IssueEstimate"] + _base_estimate_args(months="24"))
        self.assertEqual(code, 3)
        msg = cli.handle_prompt("却下 P-0001 金額が違う", self.agent_ctx)
        self.assertIsNotNone(msg)
        prop = json.loads((self.project_dir / "proposals" / "P-0001.json").read_text(encoding="utf-8"))
        self.assertEqual(prop["status"], "rejected")
        self.assertEqual(prop["reason"], "金額が違う")

    def test_no_match_returns_none(self) -> None:
        self.assertIsNone(cli.handle_prompt("見積を作って", self.agent_ctx))

    def test_not_found(self) -> None:
        msg = cli.handle_prompt("承認 P-9999", self.agent_ctx)
        self.assertIsNotNone(msg)
        self.assertIn("見つからない", msg)

    def test_ambiguous_scope_then_disambiguated(self) -> None:
        code, _out, _err = self._run(["act", "TransferPerson", "person=suzuki", "to=tech"])
        self.assertEqual(code, 3)
        code, _out, _err = self._run(["act", "IssueEstimate"] + _base_estimate_args(months="24"))
        self.assertEqual(code, 3)

        msg = cli.handle_prompt("承認 P-0001", self.agent_ctx)
        self.assertIsNotNone(msg)
        self.assertIn("複数の範囲", msg)

        msg2 = cli.handle_prompt("承認 common/P-0001", self.agent_ctx)
        self.assertIsNotNone(msg2)
        self.assertNotIn("複数の範囲", msg2)


# --- define apply（govern.propose 経由）--------------------------------------


class DefineApplyTest(CliCaseTest):
    def test_add_type_staged_and_ontology_unchanged(self) -> None:
        before = (self.project_dir / "ontology.json").read_bytes()
        patch = {"object_types": {"Note": {"label": "メモ", "properties": {"body": {"type": "text", "label": "本文"}}}}}
        code, out, _err = self._run(["define", "apply", self._write_patch(patch)])
        self.assertEqual(code, 3)
        self.assertIn("実行待ち S-0001", out)
        self.assertEqual((self.project_dir / "ontology.json").read_bytes(), before)

    def test_approve_schema_bumps_version_and_rewrites_index(self) -> None:
        patch = {"object_types": {"Note": {"label": "メモ", "properties": {"body": {"type": "text", "label": "本文"}}}}}
        code, _out, _err = self._run(["define", "apply", self._write_patch(patch)])
        self.assertEqual(code, 3)

        msg = cli.handle_prompt("承認 S-0001", self.agent_ctx)
        self.assertIsNotNone(msg)

        doc = json.loads((self.project_dir / "ontology.json").read_text(encoding="utf-8"))
        self.assertEqual(doc["version"], 2)
        self.assertIn("Note", doc["object_types"])
        self.assertTrue((self.project_dir / "index.md").exists())

        lines = (self.project_dir / "log.jsonl").read_text(encoding="utf-8").splitlines()
        last = json.loads(lines[-1])
        self.assertEqual(last["kind"], "schema")

    def test_set_action_warnings(self) -> None:
        patch = {"action_types": {
            "SetStatus": {
                "label": "状態を直接変える", "description": "宿題の状態を直接書き換える操作（lint の検収を確かめるための例）。",
                "parameters": {"item": {"object_type": "ActionItem", "required": True}},
                "rules": [{"modify": "item", "set": {"state": "'done'"}}], "approval": "auto",
            },
            "SetReason": {
                "label": "出所を直接変える", "description": "決定の出所を直接書き換える操作（lint の検収を確かめるための例）。",
                "parameters": {"item": {"object_type": "Decision", "required": True}},
                "rules": [{"modify": "item", "set": {"source": "'x'"}}], "approval": "auto",
            },
            "SetTitle": {
                "label": "題を直接変える", "description": "会議の題を直接書き換える操作（lint の検収を確かめるための例）。",
                "parameters": {"item": {"object_type": "Meeting", "required": True}},
                "rules": [{"modify": "item", "set": {"title": "'x'"}}], "approval": "auto",
            },
            "UpdateAddress": {
                "label": "名前を直接変える", "description": "作業領域の名前を直接書き換える操作（lint の検収を確かめるための例）。",
                "parameters": {"item": {"object_type": "Workstream", "required": True}},
                "rules": [{"modify": "item", "set": {"name": "'x'"}}], "approval": "auto",
            },
        }}
        code, out, _err = self._run(["define", "apply", self._write_patch(patch)])
        self.assertEqual(code, 3)
        self.assertEqual(out.count("SET_ACTION"), 4)

    def test_misnomer_warning_for_date_property(self) -> None:
        patch = {"object_types": {"Meeting": {"properties": {"date": {"type": "string", "label": "日付"}}}}}
        code, out, _err = self._run(["define", "apply", self._write_patch(patch)])
        self.assertEqual(code, 3)
        self.assertIn("MISNOMER", out)

    def test_conflicting_common_type_rejected(self) -> None:
        patch = {"object_types": {"Person": {"label": "重複", "properties": {}}}}
        code, out, _err = self._run(["define", "apply", self._write_patch(patch)])
        self.assertEqual(code, 4)
        self.assertIn("拒否", out)
        self.assertIn("Person", out)

    def test_existing_entities_violate_patch_rejected(self) -> None:
        patch = {"object_types": {"Decision": {"properties": {"status": {"values": ["active"]}}}}}
        code, out, _err = self._run(["define", "apply", self._write_patch(patch)])
        self.assertEqual(code, 4)
        self.assertIn("拒否", out)
        self.assertIn("status", out)

    def test_governance_patch_always_staged_for_agent(self) -> None:
        patch = {"governance": {"schema_changes": "auto"}}
        code, out, _err = self._run(["define", "apply", self._write_patch(patch)])
        self.assertEqual(code, 3)
        self.assertIn("実行待ち", out)

    def test_human_define_apply_also_stages_when_governance_stage(self) -> None:
        # 「実行者が人なら承認を省く」はやらない。人が define apply を叩いても
        # governance が stage（fixture の既定）なら実行待みになり、反映は approve だけがする。
        before = (self.project_dir / "ontology.json").read_bytes()
        patch = {"object_types": {"Note": {"label": "メモ", "properties": {"body": {"type": "text", "label": "本文"}}}}}
        code, out, _err = self._run(["define", "apply", self._write_patch(patch)], self.human_ctx)
        self.assertEqual(code, 3)
        self.assertIn("実行待ち S-0001", out)
        self.assertEqual((self.project_dir / "ontology.json").read_bytes(), before)

        code2, out2, _err = self._run(["approve", "S-0001"], self.human_ctx)
        self.assertEqual(code2, 0)
        self.assertIn("反映", out2)
        doc = json.loads((self.project_dir / "ontology.json").read_text(encoding="utf-8"))
        self.assertEqual(doc["version"], 2)

    def test_human_define_apply_commits_when_governance_auto(self) -> None:
        auto_dir = self.root / "projects" / "autogov" / "knowledges" / "ontology"
        auto_dir.mkdir(parents=True)
        doc = {
            "ontology": "autogov", "version": 1, "governance": {"schema_changes": "auto"},
            "object_types": {}, "link_types": {}, "action_types": {},
        }
        (auto_dir / "ontology.json").write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
        ctx = cli.Ctx(
            root=self.root, current_project="autogov", current_task=None,
            session=None, is_tty=True, user="reviewer",
        )
        patch = {"object_types": {"Note": {"label": "メモ", "properties": {"body": {"type": "text", "label": "本文"}}}}}
        code, out, _err = self._run(["define", "apply", self._write_patch(patch)], ctx)
        self.assertEqual(code, 0)
        self.assertIn("反映", out)


# --- validate / lint / eval / export / log ----------------------------------


class ValidateLintEvalExportLogTest(CliCaseTest):
    def test_validate_clean(self) -> None:
        code, out, _err = self._run(["validate"])
        self.assertEqual(code, 0)
        self.assertIn("問題なし", out)

    def test_lint_clean(self) -> None:
        code, out, _err = self._run(["lint"])
        self.assertEqual(code, 0)
        self.assertIn("問題なし", out)

    def test_eval_all_ok(self) -> None:
        code, out, _err = self._run(["eval"])
        self.assertEqual(code, 0)
        self.assertIn("10/10 ok", out)

    def test_eval_all_ok_for_human_ctx(self) -> None:
        # eval は固定の実行者で判定する（叩く人で expect.status の判定が変わらないように）
        code, out, _err = self._run(["eval"], self.human_ctx)
        self.assertEqual(code, 0)
        self.assertIn("10/10 ok", out)

    def test_export_turtle_has_range_includes(self) -> None:
        code, out, _err = self._run(["export", "--format", "turtle"])
        self.assertEqual(code, 0)
        self.assertIn("schema:rangeIncludes", out)

    def test_export_jsonschema_parses(self) -> None:
        code, out, _err = self._run(["export", "--format", "jsonschema"])
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertIn("IssueEstimate", data["actions"])

    def test_export_mermaid_has_erdiagram(self) -> None:
        code, out, _err = self._run(["export", "--format", "mermaid"])
        self.assertEqual(code, 0)
        self.assertIn("erDiagram", out)

    def test_export_markdown_to_file(self) -> None:
        out_path = self.root / "onto.md"
        code, _out, _err = self._run(["export", "--format", "markdown", "--out", str(out_path)])
        self.assertEqual(code, 0)
        self.assertTrue(out_path.exists())
        self.assertIn("## 型", out_path.read_text(encoding="utf-8"))

    def test_log_filters_by_object(self) -> None:
        code, _out, _err = self._run(["act", "IssueEstimate"] + _base_estimate_args())
        self.assertEqual(code, 0)
        code, out, _err = self._run(["log", "--object", "SizingDecision:SD-2"])
        self.assertEqual(code, 0)
        self.assertIn("IssueEstimate", out)


# --- doctor / alias_pairs / pending_count -----------------------------------


class DoctorAliasPendingTest(CliCaseTest):
    def test_doctor_clean(self) -> None:
        self.assertEqual(cli.doctor_problems(self.agent_ctx), [])

    def test_doctor_clean_for_human_ctx(self) -> None:
        # eval と同じ固定の実行者で判定する（人の端末から doctor を叩いても結果は変わらない）
        self.assertEqual(cli.doctor_problems(self.human_ctx), [])

    def test_doctor_detects_hash_mismatch_and_violation(self) -> None:
        code, _out, _err = self._run(["act", "IssueEstimate"] + _base_estimate_args())
        self.assertEqual(code, 0)
        doc = json.loads((self.project_dir / "objects.json").read_text(encoding="utf-8"))
        doc["SizingDecision"]["SD-2"]["status"] = "unknown"
        (self.project_dir / "objects.json").write_text(
            json.dumps(doc, sort_keys=True, indent=1, ensure_ascii=False) + "\n", encoding="utf-8",
        )
        problems = cli.doctor_problems(self.agent_ctx)
        self.assertTrue(any("記録に無い形で書き換えられている" in p for p in problems))
        self.assertTrue(any("status" in p and "SD-2" in p for p in problems))

    def test_alias_pairs(self) -> None:
        pairs = cli.alias_pairs(self.agent_ctx, "acme")
        self.assertEqual(pairs.get("サトウハナコ"), "佐藤花子")
        self.assertEqual(pairs.get("キンタイ"), "KinTai")
        self.assertEqual(pairs.get("ヤマダタロウ"), "山田太郎")

    def test_pending_count(self) -> None:
        self.assertEqual(cli.pending_count(self.root), 0)
        code, _out, _err = self._run(["act", "TransferPerson", "person=suzuki", "to=tech"])
        self.assertEqual(code, 3)
        code, _out, _err = self._run(["act", "IssueEstimate"] + _base_estimate_args(months="24"))
        self.assertEqual(code, 3)
        self.assertEqual(cli.pending_count(self.root), 2)


# --- 想定外の例外（Y-4）------------------------------------------------------


class InternalErrorHandlingTest(CliCaseTest):
    def test_types_with_unreadable_objects_json_exits_1_without_traceback(self) -> None:
        (self.project_dir / "objects.json").write_text("{not json", encoding="utf-8")
        code, _out, err = self._run(["types"])
        self.assertEqual(code, 1)
        self.assertNotIn("Traceback", err)
        self.assertLessEqual(len(err.strip().splitlines()), 2)

    def test_doctor_reports_other_scope_when_one_scope_is_broken(self) -> None:
        # common 側に実体の違反を作り、project 側の objects.json を壊す。
        # project は common 抜きでは読めないので project 側はエラー 1 行になるが、
        # common 側の違反は消えずに残る（doctor 全体は落ちない）。
        doc = json.loads((self.common_dir / "objects.json").read_text(encoding="utf-8"))
        del doc["Person"]["sato"]["name"]
        (self.common_dir / "objects.json").write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
        (self.project_dir / "objects.json").write_text("{not json", encoding="utf-8")

        problems = cli.doctor_problems(self.agent_ctx)
        self.assertTrue(any("Person:sato" in p and "MIN_COUNT" in p for p in problems))
        self.assertTrue(any("acme" in p or "projects" in p for p in problems))

    def test_doctor_validate_internal_error_does_not_stop_other_checks(self) -> None:
        with mock.patch.object(cli, "validate", side_effect=RuntimeError("boom")):
            problems = cli.doctor_problems(self.agent_ctx)
        self.assertTrue(any("validate で内部エラー（RuntimeError: boom）" in p for p in problems))
        # validate だけ落ちて lint は普通に走った（他の検査が続いている証拠。fixture は lint 0 件）
        self.assertFalse(any("lint で内部エラー" in p for p in problems))
        self.assertFalse(any(" lint " in p for p in problems))

    def test_main_reports_unexpected_exception_as_one_line_without_traceback(self) -> None:
        with mock.patch.object(cli.lint_mod, "lint", side_effect=RuntimeError("boom")):
            code, _out, err = self._run(["lint"])
        self.assertEqual(code, 1)
        self.assertIn("内部エラー", err)
        self.assertIn("RuntimeError", err)
        self.assertNotIn("Traceback", err)
        self.assertLessEqual(len(err.strip().splitlines()), 2)


# --- init / 範囲の決め方 -------------------------------------------------------


class InitScopeTest(CliCaseTest):
    def test_init_project_creates_then_noop(self) -> None:
        code, out, _err = self._run(["init", "--project", "newcase"], self.agent_ctx)
        self.assertEqual(code, 0)
        self.assertIn("作成", out)
        newcase_dir = self.root / "projects" / "newcase" / "knowledges" / "ontology"
        self.assertTrue((newcase_dir / "ontology.json").exists())
        self.assertTrue((newcase_dir / "index.md").exists())
        doc = json.loads((newcase_dir / "ontology.json").read_text(encoding="utf-8"))
        self.assertEqual(doc["object_types"], {})

        before = (newcase_dir / "ontology.json").read_bytes()
        code2, out2, _err = self._run(["init", "--project", "newcase"], self.agent_ctx)
        self.assertEqual(code2, 0)
        self.assertEqual((newcase_dir / "ontology.json").read_bytes(), before)

    def test_scope_defaults_to_common_without_current_project(self) -> None:
        ctx = cli.Ctx(root=self.root, current_project=None, current_task=None, session="s1", is_tty=False, user="reviewer")
        code, out, _err = self._run(["types"], ctx)
        self.assertEqual(code, 0)
        self.assertIn("Person", out)
        self.assertNotIn("IssueEstimate", out)

        code, out, _err = self._run(["types", "--project", "acme"], ctx)
        self.assertEqual(code, 0)
        self.assertIn("IssueEstimate", out)


if __name__ == "__main__":
    unittest.main()
