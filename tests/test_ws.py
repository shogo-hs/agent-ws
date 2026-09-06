"""scripts/ws の自己チェック。  python3 -m unittest tests/test_ws.py

一時ディレクトリを WS_ROOT にして、案件作成 → タスク作成 → hook の拒否/許可 →
情報源の保存 → 用語集と正規化 → 完了 の一連を通す。
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
WS = REPO / "scripts" / "ws"


class WsFlowTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="ws-test-"))
        shutil.copytree(REPO / "templates", self.root / "templates")
        (self.root / "projects").mkdir()
        shutil.copy(REPO / "projects" / "index.md", self.root / "projects" / "index.md")
        self.env = {**os.environ, "WS_ROOT": str(self.root)}
        for k in ("CLAUDE_CODE_SESSION_ID", "CODEX_THREAD_ID"):  # テストを起こしたエージェントのセッションを持ち込まない
            self.env.pop(k, None)

    def tearDown(self):
        shutil.rmtree(self.root)

    def ws(self, *args, stdin=None, check=True, env=None):
        r = subprocess.run([sys.executable, str(WS), *args], input=stdin, capture_output=True,
                           text=True, env={**self.env, **(env or {})}, cwd=self.root)
        if check and r.returncode != 0:
            self.fail(f"ws {' '.join(args)} failed:\n{r.stderr}")
        return r

    def hook(self, tool, tool_input, sid=None):
        r = self.ws("hook", "pre-tool-use",
                    stdin=json.dumps({"session_id": sid, "tool_name": tool, "tool_input": tool_input}))
        if not r.stdout.strip():
            return None
        return json.loads(r.stdout)["hookSpecificOutput"]["permissionDecision"]

    def test_flow(self):
        # 案件とタスク
        self.ws("project", "new", "acme")
        self.assertTrue((self.root / "projects/acme/knowledges/glossary.md").exists())
        self.assertIn("acme/", (self.root / "projects/index.md").read_text(encoding="utf-8"))
        self.ws("task", "new", "acme", "kickoff", "--title", "キックオフ準備")
        task = next(p for p in (self.root / "projects/acme/tasks").iterdir() if p.is_dir())
        self.assertTrue(task.name.endswith("_kickoff"))
        self.assertTrue((task / "references/index.md").exists())
        self.assertIn(task.name, (self.root / ".ws/current").read_text(encoding="utf-8"))
        self.assertIn("キックオフ準備", self.ws("task", "current").stdout)

        # hook: 他タスクは拒否、自タスクと一覧と ws 自身は許可
        other = f"projects/acme/tasks/20200101_other"
        self.assertEqual(self.hook("Read", {"file_path": str(self.root / other / "index.md")}), "deny")
        self.assertEqual(self.hook("Bash", {"command": f"cat {other}/notes.md"}), "deny")
        self.assertEqual(self.hook("Grep", {"pattern": "x", "path": str(self.root / other)}), "deny")
        self.assertIsNone(self.hook("Read", {"file_path": str(task / "index.md")}))
        self.assertIsNone(self.hook("Read", {"file_path": str(self.root / "projects/acme/tasks/index.md")}))
        self.assertIsNone(self.hook("Bash", {"command": f"scripts/ws task use {other}"}))
        self.assertIsNone(self.hook("Read", {"file_path": str(self.root / "projects/acme/knowledges/index.md")}))

        # 情報源の保存と index.md への反映
        src = self.root / "meeting.txt"
        src.write_text("クバネティスの久保ネティス移行はポックで進める。担当は山田。", encoding="utf-8")
        self.ws("ref", "add", str(src), "--summary", "週次定例の文字起こし", "--kind", "transcript")
        ref = next(p for p in (task / "references").glob("*.md") if p.name != "index.md")
        text = ref.read_text(encoding="utf-8")
        self.assertIn("retrieved_at:", text)
        self.assertIn("kind: transcript", text)
        self.assertIn(ref.name, (task / "index.md").read_text(encoding="utf-8"))

        # 用語集と正規化
        self.ws("glossary", "add", "acme", "Kubernetes", "--reading", "くばねてぃす",
                "--alias", "クバネティス, 久保ネティス", "--desc", "コンテナ基盤")
        self.ws("glossary", "add", "acme", "PoC", "--alias", "ポック")
        out = self.ws("transcript", "normalize", str(ref)).stdout
        norm = ref.with_name(ref.stem + ".normalized.md").read_text(encoding="utf-8")
        self.assertIn("KubernetesのKubernetes移行はPoCで進める", norm)
        self.assertIn("クバネティス → Kubernetes: 1", out)
        self.assertIn("ポック → PoC: 1", out)
        self.assertIn("文字・", out)  # 長さを出して、長い文字起こしを分けて読ませる判断材料にする

        # ナレッジの昇格、点検、完了
        self.ws("know", "new", "acme", "移行方針")
        self.assertTrue((self.root / "projects/acme/knowledges/001_移行方針.md").exists())
        self.assertIn("001_移行方針.md", (self.root / "projects/acme/knowledges/index.md").read_text(encoding="utf-8"))
        r = self.ws("doctor", check=False)
        self.assertEqual(r.returncode, 1, r.stdout)  # 昇格したナレッジの summary が空なので 1 件
        self.assertIn("summary が空", r.stdout)
        self.ws("task", "done")
        self.assertFalse((self.root / ".ws/current").exists())
        self.assertIn("[done]", (self.root / "projects/acme/tasks/index.md").read_text(encoding="utf-8"))
        self.assertIn("未設定", self.ws("hook", "session-start", stdin="{}").stdout)

    def test_session_start_reads_next_step(self):
        self.ws("project", "new", "acme")
        self.ws("task", "new", "acme", "t1")
        task = next(p for p in (self.root / "projects/acme/tasks").iterdir() if p.is_dir())
        idx = task / "index.md"
        idx.write_text(idx.read_text(encoding="utf-8").replace(
            "（次のセッションが最初にやること。hook が起動時にここを読み上げる）", "顧客に見積の前提を確認する"),
            encoding="utf-8")
        pidx = self.root / "projects/acme/index.md"
        pidx.write_text(pidx.read_text(encoding="utf-8").replace(
            "（成果物の置き場所、使う言語、連絡手段など。長くなるなら knowledges/ に移す）",
            "成果物は共有ドライブの ACME フォルダに置く"), encoding="utf-8")
        out = self.ws("hook", "session-start", stdin="{}").stdout
        self.assertIn(task.name, out)
        self.assertIn("顧客に見積の前提を確認する", out)
        # 案件の決まりごとは index.md に書く場所だけあって読まれなかったので、hook が差し込む
        self.assertIn("成果物は共有ドライブの ACME フォルダに置く", out)
        pidx.unlink()
        self.assertIn("決まりごと（projects/acme/index.md より）: （未記入）",
                      self.ws("hook", "session-start", stdin="{}").stdout)
        # Codex は JSON の additionalContext しか文脈に足さない（素のテキストだと落ちる）
        self.assertIn("additionalContext", json.loads(out)["hookSpecificOutput"])

    def test_lessons_are_kept_and_injected(self):
        self.ws("project", "new", "acme")
        text = "報告は結論を先に書く（読む人はチャットしか見ない）"
        self.assertIn("追加", self.ws("lesson", "add", text).stdout)
        self.assertIn("既にある", self.ws("lesson", "add", text).stdout)
        self.assertEqual((self.root / "LESSONS.md").read_text(encoding="utf-8").count(text), 1)
        # 案件固有の指摘は案件の決まりごとへ。雛形の括弧書きは消える
        self.ws("lesson", "add", "週次定例の文字起こしは当日のタスクに置く", "--project", "acme")
        pidx = (self.root / "projects/acme/index.md").read_text(encoding="utf-8")
        self.assertIn("- 週次定例の文字起こしは当日のタスクに置く", pidx)
        self.assertNotIn("（成果物の置き場所", pidx)
        # タスク未設定でも、設定後でも hook が差し込む
        self.assertIn(text, self.ws("hook", "session-start", stdin="{}").stdout)
        self.ws("task", "new", "acme", "t1")
        out = self.ws("hook", "session-start", stdin="{}").stdout
        self.assertIn(text, out)
        self.assertIn("週次定例の文字起こしは当日のタスクに置く", out)
        # 20 行を超えたら doctor が減らせと報告する
        for i in range(20):
            self.ws("lesson", "add", f"教訓 {i}")
        self.assertIn("LESSONS.md が 21 行", self.ws("doctor", check=False).stdout)

    def test_sessions_keep_their_own_current_task(self):
        """同じ clone の 2 セッション。片方の task use がもう片方の現在のタスクを変えない（issue #1）。"""
        self.ws("project", "new", "acme")
        self.ws("task", "new", "acme", "y")
        self.ws("task", "new", "acme", "x")
        tasks = self.root / "projects/acme/tasks"
        x, y = (next(tasks.glob(f"*_{s}")) for s in ("x", "y"))
        s1, s2 = "sess-1", "sess-2"
        e1, e2 = {"CLAUDE_CODE_SESSION_ID": s1}, {"CODEX_THREAD_ID": s2}

        def ev(name, sid, **kw):
            return json.dumps({"session_id": sid, "hook_event_name": name, **kw})

        # セッション 1 が X で起動すると写しができる。その後セッション 2 が Y に切り替える
        self.assertIn(x.name, self.ws("hook", "session-start", stdin=ev("SessionStart", s1, source="startup")).stdout)
        self.assertEqual((self.root / ".ws/sessions" / f"{s1}.current").read_text(encoding="utf-8").strip(),
                         f"projects/acme/tasks/{x.name}")
        self.hook("Bash", {"command": f"scripts/ws task use projects/acme/tasks/{y.name}"}, sid=s2)
        self.ws("task", "use", f"projects/acme/tasks/{y.name}", env=e2)
        # セッション 1 の hook と CLI は X のまま。セッション 2 と端末（環境変数なし）は Y
        self.assertIsNone(self.hook("Read", {"file_path": str(x / "index.md")}, sid=s1))
        self.assertEqual(self.hook("Read", {"file_path": str(y / "index.md")}, sid=s1), "deny")
        self.assertEqual(self.hook("Read", {"file_path": str(x / "index.md")}, sid=s2), "deny")
        out = self.ws("hook", "session-start", stdin=ev("SessionStart", s1, source="compact")).stdout
        self.assertIn(x.name, out)
        self.assertNotIn(y.name, out)
        self.assertIn(x.name, self.ws("task", "current", env=e1).stdout)
        self.assertIn(y.name, self.ws("task", "current", env=e2).stdout)
        self.assertIn(y.name, self.ws("task", "current").stdout)
        (self.root / "memo.txt").write_text("メモ", encoding="utf-8")
        self.ws("ref", "add", str(self.root / "memo.txt"), "--summary", "s", env=e1)
        self.assertTrue(list((x / "references").glob("*_memo.md")))
        (self.root / ".ws/sessions" / f"{s1}.last_stop").write_text(str(int(time.time()) - 61 * 60), encoding="utf-8")
        r = self.ws("hook", "user-prompt-submit", stdin=ev("UserPromptSubmit", s1, prompt="続き"), check=False)
        self.assertIn(x.name, r.stderr)
        self.assertNotIn(y.name, r.stderr)
        # セッション 1 自身の切り替えは効く。CLI がセッションを知らなくても（環境変数なし）hook が写しを捨てるので追いつく
        self.hook("Bash", {"command": f"scripts/ws task use projects/acme/tasks/{y.name}"}, sid=s1)
        self.ws("task", "use", f"projects/acme/tasks/{y.name}")
        self.assertIsNone(self.hook("Read", {"file_path": str(y / "index.md")}, sid=s1))
        # /clear で写しが消え、最後に設定したタスク（.ws/current）から始まる
        self.ws("task", "use", f"projects/acme/tasks/{x.name}", env=e2)
        self.assertIn(x.name, self.ws("hook", "session-start", stdin=ev("SessionStart", s1, source="clear")).stdout)
        # セッション 1 が完了にしても、セッション 2 の現在のタスクは残る
        self.ws("task", "use", f"projects/acme/tasks/{y.name}", env=e2)
        self.hook("Bash", {"command": "scripts/ws task done"}, sid=s1)
        self.ws("task", "done", env=e1)
        self.assertIn("status: done", (x / "index.md").read_text(encoding="utf-8"))
        self.assertNotIn("status: done", (y / "index.md").read_text(encoding="utf-8"))
        self.assertIn(y.name, self.ws("task", "current", env=e2).stdout)
        self.assertEqual(self.ws("task", "current", env=e1, check=False).returncode, 1)

    def test_gap_guard_blocks_first_prompt_after_cache_ttl(self):
        sid = "sess-1"
        def ev(name, **kw):
            return json.dumps({"session_id": sid, "hook_event_name": name, **kw})
        self.ws("hook", "session-start", stdin=ev("SessionStart", source="startup"))
        self.ws("hook", "stop", stdin=ev("Stop"))
        # 直後の送信は通る
        r = self.ws("hook", "user-prompt-submit", stdin=ev("UserPromptSubmit", prompt="続き"), check=False)
        self.assertEqual(r.returncode, 0)
        # 前回の応答を 61 分前に偽装 → 止まる。本文は保存される
        rec = self.root / ".ws/sessions" / f"{sid}.last_stop"
        rec.write_text(str(int(time.time()) - 61 * 60), encoding="utf-8")
        r = self.ws("hook", "user-prompt-submit", stdin=ev("UserPromptSubmit", prompt="続きをやって"), check=False)
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("/clear", r.stderr)
        self.assertEqual((self.root / ".ws/sessions" / f"{sid}.blocked_prompt").read_text(encoding="utf-8"), "続きをやって")
        # 10 分以内の再送は通す
        r = self.ws("hook", "user-prompt-submit", stdin=ev("UserPromptSubmit", prompt="続きをやって"), check=False)
        self.assertEqual(r.returncode, 0)
        # /clear（source=clear）で記録が消え、以後は通る
        rec.write_text(str(int(time.time()) - 61 * 60), encoding="utf-8")
        self.ws("hook", "session-start", stdin=ev("SessionStart", source="clear"))
        r = self.ws("hook", "user-prompt-submit", stdin=ev("UserPromptSubmit", prompt="x"), check=False)
        self.assertEqual(r.returncode, 0)
        # compact 直後はタイマーが今からになる
        self.ws("hook", "stop", stdin=ev("Stop"))
        rec.write_text(str(int(time.time()) - 61 * 60), encoding="utf-8")
        self.ws("hook", "session-start", stdin=ev("SessionStart", source="compact"))
        r = self.ws("hook", "user-prompt-submit", stdin=ev("UserPromptSubmit", prompt="x"), check=False)
        self.assertEqual(r.returncode, 0)

    def test_hook_is_fail_open_on_garbage(self):
        r = self.ws("hook", "pre-tool-use", stdin="not json")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
