"""scripts/ws の自己チェック。  python3 -m unittest tests/test_ws.py

一時ディレクトリを WS_ROOT にして、案件作成 → タスク作成 → hook の拒否/許可 →
情報源の保存 → 用語集と正規化 → 完了 の一連を通す。
"""
import http.server
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
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
        ref = next(p for p in (task / "references").glob("*.md") if p.name != "index.md" and not p.name.endswith(".orig.md"))
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
        # 完了したセッションは、他のセッションが .ws/current を書いても拾わない（未設定のまま）
        self.ws("task", "use", f"projects/acme/tasks/{y.name}", env=e2)
        self.assertEqual(self.ws("task", "current", env=e1, check=False).returncode, 1)
        self.assertEqual(self.hook("Read", {"file_path": str(y / "index.md")}, sid=s1), "deny")

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

    def test_docs_snapshots_are_off_limits_while_a_task_is_current(self):
        """規則の根拠（Web ページの原文）は案件の仕事では読まない。台帳（docs/*.md）は読める。"""
        snap = self.root / "docs/snapshots/20260101_0000_page.orig.md"
        snap.parent.mkdir(parents=True)
        snap.write_text("原文\n", encoding="utf-8")
        ledger = self.root / "docs/sources.md"
        ledger.write_text("台帳\n", encoding="utf-8")
        self.assertIsNone(self.hook("Read", {"file_path": str(snap)}))  # タスク未設定なら読める
        self.ws("project", "new", "acme")
        self.ws("task", "new", "acme", "t1")
        self.assertEqual(self.hook("Read", {"file_path": str(snap)}), "deny")
        self.assertEqual(self.hook("Grep", {"pattern": "x", "path": "docs/snapshots"}), "deny")
        self.assertEqual(self.hook("Bash", {"command": "cat docs/snapshots/20260101_0000_page.md"}), "deny")
        self.assertIsNone(self.hook("Read", {"file_path": str(ledger)}))
        # ref add --dir docs/snapshots（scripts/ws 自身の実行）は通す
        self.assertIsNone(self.hook("Bash", {"command": "scripts/ws ref add https://example.org/ --dir docs/snapshots"}))

    def test_bench_is_off_limits_while_a_task_is_current(self):
        self.ws("project", "new", "acme")
        self.ws("task", "new", "acme", "kickoff")
        self.assertEqual(self.hook("Read", {"file_path": "bench/corpus/projects/acme/index.md"}), "deny")
        self.assertEqual(self.hook("Bash", {"command": "grep -r 見積 bench/"}), "deny")
        self.assertEqual(self.hook("Read", {"file_path": str(self.root / "bench/README.md")}), "deny")
        self.assertIsNone(self.hook("Bash", {"command": "ls /var/tmp/agent-ws-bench/runs"}))  # 外のパスは止めない
        self.ws("task", "done")
        self.assertIsNone(self.hook("Read", {"file_path": "bench/corpus/projects/acme/index.md"}))  # 保守中は通す

    def test_hook_is_fail_open_on_garbage(self):
        r = self.ws("hook", "pre-tool-use", stdin="not json")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "")

    def test_ref_add_local_file_has_new_sections_and_via(self):
        self.ws("project", "new", "acme")
        self.ws("task", "new", "acme", "kickoff")
        task = next(p for p in (self.root / "projects/acme/tasks").iterdir() if p.is_dir())
        src = self.root / "note.txt"
        src.write_text("メモ本文", encoding="utf-8")
        self.ws("ref", "add", str(src), "--summary", "メモ")
        ref = next(p for p in (task / "references").glob("*.md") if p.name != "index.md" and not p.name.endswith(".orig.md"))
        orig = ref.with_name(ref.stem + ".orig.md")
        text = ref.read_text(encoding="utf-8")
        self.assertIn("via: local", text)
        self.assertIn("## 引用した記述（原文のまま。要約しない）", text)
        self.assertIn("## このタスクでの使いどころ（使わなかったなら理由）", text)
        self.assertIn("## 原文（改変しない）", text)
        self.assertIn(f"原文: [{orig.name}]", text)  # 要点側は本文を持たずポインタだけ
        self.assertNotIn("メモ本文", text)
        self.assertTrue(orig.is_file())
        self.assertEqual(orig.read_text(encoding="utf-8"), "メモ本文")
        # index.md・references/index.md の一覧には要点ファイルだけが載る（.orig.md は載らない）
        self.assertIn(ref.name, (task / "index.md").read_text(encoding="utf-8"))
        self.assertNotIn(orig.name, (task / "index.md").read_text(encoding="utf-8"))
        self.assertNotIn(orig.name, (task / "references/index.md").read_text(encoding="utf-8"))

    def test_ref_add_summary_optional(self):
        self.ws("project", "new", "acme")
        self.ws("task", "new", "acme", "kickoff")
        task = next(p for p in (self.root / "projects/acme/tasks").iterdir() if p.is_dir())
        src = self.root / "note.txt"
        src.write_text("メモ", encoding="utf-8")
        out = self.ws("ref", "add", str(src)).stdout  # --summary を省略
        self.assertIn("summary が空", out)
        ref = next(p for p in (task / "references").glob("*.md") if p.name != "index.md" and not p.name.endswith(".orig.md"))
        self.assertIn('summary: ""', ref.read_text(encoding="utf-8"))
        # 後から埋められる（frontmatter を書き換えられる）
        text = ref.read_text(encoding="utf-8").replace('summary: ""', 'summary: "後から埋めた"', 1)
        ref.write_text(text, encoding="utf-8")
        self.assertIn('summary: "後から埋めた"', ref.read_text(encoding="utf-8"))

    def test_ref_add_dir_without_current_task(self):
        self.ws("project", "new", "acme")  # 現在のタスクは設定しない
        src = self.root / "note.txt"
        src.write_text("根拠になる記述", encoding="utf-8")
        out_dir = self.root / "docs"
        self.ws("ref", "add", str(src), "--summary", "根拠メモ", "--dir", str(out_dir))
        saved = next(p for p in out_dir.glob("*.md") if not p.name.endswith(".orig.md"))
        orig = saved.with_name(saved.stem + ".orig.md")
        self.assertTrue(orig.is_file())  # --dir 指定でも要点と原文の対ができる
        self.assertIn("根拠になる記述", orig.read_text(encoding="utf-8"))
        self.assertNotIn("根拠になる記述", saved.read_text(encoding="utf-8"))

    def test_doctor_flags_reference_gaps_and_stale_knowledge(self):
        self.ws("project", "new", "acme")
        self.ws("know", "new", "acme", "手順書")
        kfile = next((self.root / "projects/acme/knowledges").glob("001_*.md"))
        kfile.write_text(kfile.read_text(encoding="utf-8").replace(
            'summary: ""', 'summary: "手順の要点"'), encoding="utf-8")
        actual_updated = re.search(r"^updated: (.+)$", kfile.read_text(encoding="utf-8"), re.M).group(1).strip()
        know_line_placeholder = ("（`- knowledges/<file>（updated YYYY-MM-DD）: 使った要点` の書式で 1 件 1 行。"
                                  "updated はナレッジの frontmatter を参照した時点の値のまま書き写す。"
                                  "doctor が古い記録を検出する）")

        # クリーンなタスク: 3節・summary・ナレッジの記録日を全部埋めた → 何も警告されない
        self.ws("task", "new", "acme", "clean")
        clean_task = next(p for p in (self.root / "projects/acme/tasks").iterdir() if p.name.endswith("_clean"))
        src = self.root / "clean.txt"
        src.write_text("クリーンな原文", encoding="utf-8")
        self.ws("ref", "add", str(src), "--summary", "クリーンな要約")
        ref = next(p for p in (clean_task / "references").glob("*.md") if p.name != "index.md" and not p.name.endswith(".orig.md"))
        text = ref.read_text(encoding="utf-8")
        text = text.replace("（このタスクに関係する記述を原文のまま引用する。複数あれば箇条書き）", "「原文からの引用」")
        text = text.replace("（この記述をどう使ったか、使わなかったならその理由）", "このまま使った")
        ref.write_text(text, encoding="utf-8")
        idx = clean_task / "index.md"
        idx.write_text(idx.read_text(encoding="utf-8").replace(
            know_line_placeholder, f"- knowledges/{kfile.name}（updated {actual_updated}）: 手順の要点"),
            encoding="utf-8")

        # 乱れたタスク: 引用未記入・summary 空・原文空・古いナレッジ記録
        self.ws("task", "new", "acme", "stale")
        stale_task = next(p for p in (self.root / "projects/acme/tasks").iterdir() if p.name.endswith("_stale"))
        src2 = self.root / "stale.txt"
        src2.write_text("乱れた原文", encoding="utf-8")
        out = self.ws("ref", "add", str(src2)).stdout  # --summary を省略
        self.assertIn("summary が空", out)
        ref2 = next(p for p in (stale_task / "references").glob("*.md") if p.name != "index.md" and not p.name.endswith(".orig.md"))
        ref2.with_name(ref2.stem + ".orig.md").unlink()  # 原文ファイルが欠落した状態を再現
        idx2 = stale_task / "index.md"
        idx2.write_text(idx2.read_text(encoding="utf-8").replace(
            know_line_placeholder, f"- knowledges/{kfile.name}（updated 2020-01-01）: 古い記録"),
            encoding="utf-8")

        r = self.ws("doctor", check=False)
        self.assertEqual(r.returncode, 1, r.stdout)
        ref2_rel = ref2.relative_to(self.root).as_posix()
        idx2_rel = idx2.relative_to(self.root).as_posix()
        self.assertIn(f"{ref2_rel}: 原文が無い（.orig.md も原文節も空）", r.stdout)
        self.assertIn(f"{ref2_rel}: 「引用した記述」節が未記入のまま", r.stdout)
        self.assertIn(f"{ref2_rel}: frontmatter の summary が空", r.stdout)
        self.assertIn(f"{idx2_rel}: 参照したナレッジ knowledges/{kfile.name} は記録（updated 2020-01-01）より新しい", r.stdout)
        ref_rel = ref.relative_to(self.root).as_posix()
        self.assertNotIn(f"{ref_rel}:", r.stdout)  # クリーンなタスクの reference には出ない

    def test_fetch_direct_with_ws_no_jina(self):
        page = b"<html><head><title>Sample Page</title></head><body><p>Hello agent-ws</p></body></html>"

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):  # noqa: D401 — テスト出力を静かにする
                pass

            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(page)))
                self.end_headers()
                self.wfile.write(page)

        server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            port = server.server_address[1]
            self.ws("project", "new", "acme")
            self.ws("task", "new", "acme", "t1")
            task = next(p for p in (self.root / "projects/acme/tasks").iterdir() if p.is_dir())
            self.ws("ref", "add", f"http://127.0.0.1:{port}/", "--summary", "s", env={"WS_NO_JINA": "1"})
            ref = next(p for p in (task / "references").glob("*.md") if p.name != "index.md" and not p.name.endswith(".orig.md"))
            text = ref.read_text(encoding="utf-8")
            self.assertIn("via: direct", text)
            self.assertIn("Sample Page", text)
            self.assertIn("Hello agent-ws", ref.with_name(ref.stem + ".orig.md").read_text(encoding="utf-8"))
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()

    def test_hook_denies_webfetch_with_current_task(self):
        self.ws("project", "new", "acme")
        self.ws("task", "new", "acme", "t1")
        self.assertEqual(self.hook("WebFetch", {"url": "https://example.com/x"}), "deny")
        r = self.ws("hook", "pre-tool-use",
                    stdin=json.dumps({"tool_name": "WebFetch", "tool_input": {"url": "https://example.com/x"}}))
        reason = json.loads(r.stdout)["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("ref add https://example.com/x", reason)
        self.assertIn("WebFetch", reason)

    def test_hook_pre_tool_use_ignores_web_tools_without_current_task(self):
        self.assertIsNone(self.hook("WebFetch", {"url": "https://example.com/x"}))
        self.assertIsNone(self.hook("Bash", {"command": "curl https://example.com/x"}))

    def test_hook_denies_curl_wget_to_external_host_only(self):
        self.ws("project", "new", "acme")
        self.ws("task", "new", "acme", "t1")
        self.assertEqual(self.hook("Bash", {"command": "curl https://example.com/x"}), "deny")
        self.assertIsNone(self.hook("Bash", {"command": "curl http://127.0.0.1:8000/"}))
        self.assertIsNone(self.hook(
            "Bash", {"command": "python3 scripts/ws ref add https://example.com/x --summary s"}))

    def test_hook_post_tool_use_lists_search_result_urls(self):
        self.ws("project", "new", "acme")
        self.ws("task", "new", "acme", "t1")
        payload = {"tool_name": "WebSearch", "tool_response": {"results": [
            {"content": [{"title": "A", "url": "https://a.example/1"}, {"title": "B", "url": "https://b.example/2"}]},
            "plain string result（無視される）",
        ]}}
        r = self.ws("hook", "post-tool-use", stdin=json.dumps(payload))
        out = json.loads(r.stdout)["hookSpecificOutput"]
        self.assertEqual(out["hookEventName"], "PostToolUse")
        self.assertIn("https://a.example/1", out["additionalContext"])
        self.assertIn("https://b.example/2", out["additionalContext"])
        self.assertIn("ref add", out["additionalContext"])

    def test_hook_post_tool_use_no_output_without_current_task_or_urls(self):
        payload = {"tool_name": "WebSearch", "tool_response": {"results": [{"content": [{"url": "https://a.example/1"}]}]}}
        self.assertEqual(self.ws("hook", "post-tool-use", stdin=json.dumps(payload)).stdout.strip(), "")
        self.ws("project", "new", "acme")
        self.ws("task", "new", "acme", "t1")
        self.assertEqual(self.ws("hook", "post-tool-use",
                                 stdin=json.dumps({"tool_name": "WebSearch", "tool_response": {"results": []}})
                                 ).stdout.strip(), "")

    def test_hook_post_tool_use_is_fail_open_on_garbage(self):
        r = self.ws("hook", "post-tool-use", stdin="not json")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "")

    def test_ref_split_migrates_old_format_and_is_idempotent(self):
        self.ws("project", "new", "acme")
        self.ws("task", "new", "acme", "t1")
        task = next(p for p in (self.root / "projects/acme/tasks").iterdir() if p.is_dir())
        old = task / "references" / "20260101_0000_old.md"
        old.write_text(
            '---\n'
            'title: "旧形式"\n'
            'kind: file\n'
            'source: "x.txt"\n'
            'via: local\n'
            'retrieved_at: 2026-01-01T00:00:00+09:00\n'
            'retrieved_by: unknown\n'
            'summary: "旧形式のテスト"\n'
            '---\n'
            '# 旧形式\n\n'
            '## 引用した記述（原文のまま。要約しない）\n'
            '「原文からの引用」\n\n'
            '## このタスクでの使いどころ（使わなかったなら理由）\n'
            'このまま使った\n\n'
            '## 原文（改変しない）\n'
            '旧形式の本文テキスト\n\n'
            '## 本文の中の見出し（Web ページの Markdown に出る）\n'
            '見出しのあとの本文\n',
            encoding="utf-8")
        # 旧形式（.orig.md 無し・原文節あり）は doctor が通す
        r = self.ws("doctor", check=False)
        self.assertEqual(r.returncode, 0, r.stdout)

        out = self.ws("ref", "split", str(old)).stdout
        self.assertIn("分割", out)
        orig = old.with_name("20260101_0000_old.orig.md")
        self.assertTrue(orig.is_file())
        # 本文中の「## 見出し」で切らず、末尾まで原文側に移る
        self.assertEqual(orig.read_text(encoding="utf-8").strip(),
                         "旧形式の本文テキスト\n\n## 本文の中の見出し（Web ページの Markdown に出る）\n見出しのあとの本文")
        self.assertIn(f"原文: [{orig.name}]", old.read_text(encoding="utf-8"))
        self.assertNotIn("旧形式の本文テキスト", old.read_text(encoding="utf-8"))
        self.assertNotIn("見出しのあとの本文", old.read_text(encoding="utf-8"))
        # references/index.md の一覧に .orig.md は載らない
        self.assertNotIn(orig.name, (task / "references/index.md").read_text(encoding="utf-8"))

        # 2 回目は「済」で変化なし（冪等）
        before = old.read_text(encoding="utf-8")
        out2 = self.ws("ref", "split", str(old)).stdout
        self.assertIn("済", out2)
        self.assertEqual(old.read_text(encoding="utf-8"), before)

    def test_transcript_normalize_reads_orig_file(self):
        self.ws("project", "new", "acme")
        self.ws("task", "new", "acme", "t1")
        task = next(p for p in (self.root / "projects/acme/tasks").iterdir() if p.is_dir())
        self.ws("glossary", "add", "acme", "Kubernetes", "--alias", "クバネティス")
        src = self.root / "meeting.txt"
        src.write_text("クバネティスの話", encoding="utf-8")
        self.ws("ref", "add", str(src), "--summary", "s", "--kind", "transcript")
        ref = next(p for p in (task / "references").glob("*.md")
                   if p.name != "index.md" and not p.name.endswith(".orig.md"))
        orig = ref.with_name(ref.stem + ".orig.md")
        norm = ref.with_name(ref.stem + ".normalized.md")
        # 新形式（要点ファイルを渡す）→ 隣の .orig.md を読んで置換する
        self.ws("transcript", "normalize", str(ref))
        self.assertEqual(norm.read_text(encoding="utf-8"), "Kubernetesの話")
        norm.unlink()
        # .orig.md を直接渡しても出力名は <stem>.normalized.md のまま
        self.ws("transcript", "normalize", str(orig))
        self.assertTrue(norm.is_file())
        self.assertEqual(norm.read_text(encoding="utf-8"), "Kubernetesの話")

    def test_ttl_flag_and_env_override(self):
        def start_with_gap(sid, gap_minutes):
            self.ws("hook", "session-start",
                    stdin=json.dumps({"session_id": sid, "hook_event_name": "SessionStart", "source": "startup"}))
            self.ws("hook", "stop", stdin=json.dumps({"session_id": sid, "hook_event_name": "Stop"}))
            rec = self.root / ".ws/sessions" / f"{sid}.last_stop"
            rec.write_text(str(int(time.time()) - gap_minutes * 60), encoding="utf-8")

        start_with_gap("sess-ttl1", 45)
        r1 = self.ws("hook", "user-prompt-submit", "--ttl", "30",
                     stdin=json.dumps({"session_id": "sess-ttl1", "hook_event_name": "UserPromptSubmit",
                                       "prompt": "続き"}), check=False)
        self.assertEqual(r1.returncode, 2, r1.stderr)
        self.assertIn("30 分", r1.stderr)

        # 環境変数 WS_CACHE_TTL_MIN があれば --ttl より優先される
        start_with_gap("sess-ttl2", 45)
        r2 = self.ws("hook", "user-prompt-submit", "--ttl", "30",
                     stdin=json.dumps({"session_id": "sess-ttl2", "hook_event_name": "UserPromptSubmit",
                                       "prompt": "続き"}), env={"WS_CACHE_TTL_MIN": "60"}, check=False)
        self.assertEqual(r2.returncode, 0, r2.stderr)

    def test_pre_tool_use_reads_back_normalized_transcript(self):
        self.ws("project", "new", "acme")
        self.ws("task", "new", "acme", "t1")
        task = next(p for p in (self.root / "projects/acme/tasks").iterdir() if p.is_dir())
        self.ws("glossary", "add", "acme", "Kubernetes", "--alias", "クバネティス")
        src = self.root / "meeting.txt"
        src.write_text("クバネティスの話", encoding="utf-8")
        self.ws("ref", "add", str(src), "--summary", "s", "--kind", "transcript")
        ref = next(p for p in (task / "references").glob("*.md")
                   if p.name != "index.md" and not p.name.endswith(".orig.md"))
        orig = ref.with_name(ref.stem + ".orig.md")
        self.ws("transcript", "normalize", str(ref))
        norm = ref.with_name(ref.stem + ".normalized.md")
        self.assertTrue(norm.is_file())

        # Read で原文（.orig.md）を指すと、正規化版へ読み替える（updatedInput）
        r = self.ws("hook", "pre-tool-use",
                    stdin=json.dumps({"tool_name": "Read", "tool_input": {"file_path": str(orig)}}))
        out = json.loads(r.stdout)["hookSpecificOutput"]
        self.assertEqual(out["permissionDecision"], "allow")
        self.assertEqual(out["updatedInput"]["file_path"], str(norm))

        # 要点ファイル（隣に .orig.md がある。小さいので読ませてよい）は出力なし
        self.assertIsNone(self.hook("Read", {"file_path": str(ref)}))

        # Bash 越しに原文を読もうとすると deny。理由に正規化版のパスを示す
        r2 = self.ws("hook", "pre-tool-use",
                     stdin=json.dumps({"tool_name": "Bash", "tool_input": {"command": f"cat {orig}"}}))
        out2 = json.loads(r2.stdout)["hookSpecificOutput"]
        self.assertEqual(out2["permissionDecision"], "deny")
        self.assertIn(norm.name, out2["permissionDecisionReason"])

        # 他タスクの .orig.md は従来どおり deny（allow で抜けない）
        other = "projects/acme/tasks/20200101_other"
        self.assertEqual(
            self.hook("Read", {"file_path": str(self.root / other / "references/x.orig.md")}), "deny")

    def test_ref_split_keeps_headings_inside_original_text(self):
        """Web ページの本文には「## 見出し」が入る。原文節は最後の節なので末尾まで丸ごと移す。"""
        self.ws("project", "new", "acme")
        self.ws("task", "new", "acme", "t1")
        task = next(p for p in (self.root / "projects/acme/tasks").iterdir() if p.is_dir())
        old = task / "references" / "20260101_0000_web.md"
        body = "前置き\n\n## 本文の見出し 1\n段落 A\n\n## 本文の見出し 2\n段落 B\n"
        old.write_text(
            '---\ntitle: "web"\nkind: web\nsource: "https://example.org/"\nvia: jina\n'
            'retrieved_at: 2026-01-01T00:00:00+09:00\nretrieved_by: unknown\nsummary: "s"\n---\n'
            '# web\n\n## 引用した記述（原文のまま。要約しない）\n「段落 B」\n\n'
            '## このタスクでの使いどころ（使わなかったなら理由）\n使った\n\n'
            '## 原文（改変しない）\n' + body, encoding="utf-8")
        self.ws("ref", "split", str(old))
        orig = old.with_name("20260101_0000_web.orig.md")
        self.assertEqual(orig.read_text(encoding="utf-8"), body)
        front = old.read_text(encoding="utf-8")
        self.assertNotIn("段落 A", front)  # 段落 B は「引用した記述」に引用として残る
        self.assertIn("## 原文（改変しない）\n原文: [" + orig.name + "]", front)

    def test_ref_split_refuses_derived_files_and_new_format(self):
        """must: 派生ファイルと新形式の要点ファイルに ref split をかけても壊さない。ROOT 外でも落ちない。"""
        self.ws("project", "new", "acme")
        self.ws("task", "new", "acme", "t1")
        task = next(p for p in (self.root / "projects/acme/tasks").iterdir() if p.is_dir())
        src = self.root / "m.txt"
        src.write_text("本文\n", encoding="utf-8")
        self.ws("ref", "add", str(src), "--kind", "transcript", "--summary", "s")
        front = next(p for p in (task / "references").glob("*.md")
                     if p.name != "index.md" and not p.name.endswith(".orig.md"))
        orig = front.with_name(front.stem + ".orig.md")
        self.ws("transcript", "normalize", str(front))
        norm = front.with_name(front.stem + ".normalized.md")
        # 派生ファイルは拒否（中身は変わらない）
        for derived in (orig, norm):
            before = derived.read_text(encoding="utf-8")
            r = self.ws("ref", "split", str(derived), check=False)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("派生ファイル", r.stderr)
            self.assertEqual(derived.read_text(encoding="utf-8"), before)
            self.assertFalse(derived.with_name(derived.stem + ".orig.md").exists())
        # .orig.md を失った新形式の要点ファイルに当てても、ポインタ行を原文にした偽の .orig.md を作らない
        orig.unlink()
        r = self.ws("ref", "split", str(front))
        self.assertIn("済", r.stdout)
        self.assertFalse(orig.exists())
        self.assertIn("原文が無い", self.ws("doctor", check=False).stdout)  # doctor の検査が黙らない
        # ROOT 外の旧形式でも traceback にならない
        outside = Path(tempfile.mkdtemp(prefix="ws-outside-")) / "o.md"
        outside.write_text("---\ntitle: \"o\"\nsummary: \"o\"\n---\n# o\n\n## 原文（改変しない）\n外の本文\n", encoding="utf-8")
        r = self.ws("ref", "split", str(outside))
        self.assertIn("分割", r.stdout)
        self.assertEqual(outside.with_name("o.orig.md").read_text(encoding="utf-8").strip(), "外の本文")
        shutil.rmtree(outside.parent)

    def test_ref_add_source_named_orig_md_is_still_listed(self):
        """情報源のファイル名が *.orig.md（スナップショットの原文など）でも、要点ファイルが index と doctor から消えない。"""
        self.ws("project", "new", "acme")
        self.ws("task", "new", "acme", "t1")
        task = next(p for p in (self.root / "projects/acme/tasks").iterdir() if p.is_dir())
        src = self.root / "snap.orig.md"
        src.write_text("原文です\n", encoding="utf-8")
        out = self.ws("ref", "add", str(src), "--summary", "スナップショット").stdout
        front = next(p for p in (task / "references").glob("*.md")
                     if p.name != "index.md" and not p.name.endswith(".orig.md"))
        self.assertTrue(front.name.endswith("_orig.md"), front.name)
        self.assertTrue(front.with_name(front.stem + ".orig.md").is_file())
        self.assertIn(front.name, (task / "references/index.md").read_text(encoding="utf-8"))
        self.assertIn("保存:", out)
        # .normalized.md / .summary.md を情報源にしても同じ（doctor がその reference を検査対象にする）
        for name in ("n.normalized.md", "s.summary.md"):
            (self.root / name).write_text("本文\n", encoding="utf-8")
            self.ws("ref", "add", str(self.root / name), "--summary", "x")
        fronts = sorted(p.name for p in (task / "references").glob("*.md")
                        if p.name != "index.md" and not p.name.endswith(".orig.md"))
        self.assertEqual(len(fronts), 3, fronts)
        self.assertTrue(all(n.endswith(("_orig.md", "_normalized.md", "_summary.md")) for n in fronts), fronts)
        r = self.ws("doctor", check=False)
        self.assertEqual(r.stdout.count("「引用した記述」節が未記入のまま"), 3, r.stdout)

    def test_pre_tool_use_reads_back_grep_old_format_and_relative_paths(self):
        """Grep も読み替える。旧形式（.orig.md 無し・.normalized.md あり）と相対パスでも効く。"""
        self.ws("project", "new", "acme")
        self.ws("task", "new", "acme", "t1")
        task = next(p for p in (self.root / "projects/acme/tasks").iterdir() if p.is_dir())
        old = task / "references" / "20260101_0000_old.md"
        old.write_text("---\ntitle: \"旧\"\nkind: transcript\nsummary: \"旧\"\n---\n# 旧\n\n## 原文（改変しない）\n久保ネティス\n", encoding="utf-8")
        old.with_name("20260101_0000_old.normalized.md").write_text("Kubernetes\n", encoding="utf-8")
        norm = str(old.with_name("20260101_0000_old.normalized.md"))
        sid = "s1"
        # Grep（絶対パス）
        r = self.ws("hook", "pre-tool-use", stdin=json.dumps(
            {"session_id": sid, "tool_name": "Grep", "tool_input": {"pattern": "K", "path": str(old)}}))
        out = json.loads(r.stdout)["hookSpecificOutput"]
        self.assertEqual(out["permissionDecision"], "allow")
        self.assertEqual(out["updatedInput"]["path"], norm)
        self.assertEqual(out["updatedInput"]["pattern"], "K")
        # Read（旧形式・相対パス）
        r = self.ws("hook", "pre-tool-use", stdin=json.dumps(
            {"session_id": sid, "tool_name": "Read", "tool_input": {"file_path": str(old.relative_to(self.root))}}))
        self.assertEqual(json.loads(r.stdout)["hookSpecificOutput"]["updatedInput"]["file_path"], norm)
        # Grep でディレクトリを指すときは読み替えない（素通し）
        r = self.ws("hook", "pre-tool-use", stdin=json.dumps(
            {"session_id": sid, "tool_name": "Grep", "tool_input": {"pattern": "K", "path": str(task / "references")}}))
        self.assertEqual(r.stdout.strip(), "")

    # ---- 第 6 弾: SessionStart の全文注入・横断検索の拒否・重複取得の検出・statusline ----

    def _task(self):
        self.ws("project", "new", "acme")
        self.ws("task", "new", "acme", "t1")
        return next(p for p in (self.root / "projects/acme/tasks").iterdir() if p.is_dir())

    def test_session_start_injects_index_and_knowledge_list(self):
        task = self._task()
        idx = task / "index.md"
        idx.write_text(idx.read_text(encoding="utf-8").replace(
            "（次のセッションが最初にやること。hook が起動時にここを読み上げる）", "顧客に見積の前提を確認する"), encoding="utf-8")
        self.ws("know", "new", "acme", "移行方針")
        out = json.loads(self.ws("hook", "session-start", stdin="{}").stdout)["hookSpecificOutput"]["additionalContext"]
        # index.md の全文（節見出しごと）とナレッジの一覧が入り、Read を促す文は無い
        self.assertIn("## 次の一手", out)
        self.assertIn("顧客に見積の前提を確認する", out)
        self.assertIn("001_移行方針.md", out)
        self.assertIn("読み直さない", out)
        self.assertNotIn("まず projects/acme/tasks", out)
        # 長すぎる index.md は従来どおりパスだけ示す（hook の出力は 10,000 字で切られる）
        idx.write_text(idx.read_text(encoding="utf-8") + "x" * 7000, encoding="utf-8")
        out = json.loads(self.ws("hook", "session-start", stdin="{}").stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn(f"まず {task.relative_to(self.root).as_posix()}/index.md を読む", out)
        self.assertNotIn("## 次の一手", out)
        self.assertIn("次の一手（index.md より）: 顧客に見積の前提を確認する", out)

    def test_hook_denies_cross_task_scans_only_with_current_task(self):
        task = self._task()
        rel = task.relative_to(self.root).as_posix()
        deny = [("Grep", {"pattern": "単価"}),                                  # path 無し = ルート全体
                ("Grep", {"pattern": "単価", "path": str(self.root / "projects/acme")}),
                ("Glob", {"pattern": "**/index.md"}),
                ("Bash", {"command": "find projects -maxdepth 3 | head -100"}),
                ("Bash", {"command": "ls -la projects/acme/tasks/"}),
                ("Bash", {"command": "ls projects/acme/tasks"}),
                ("Bash", {"command": f"grep -rn 単価 {self.root}/projects/acme"}),
                ("Bash", {"command": "rg 単価 ."}),
                ("Bash", {"command": "tree projects/"})]
        for tool, inp in deny:
            self.assertEqual(self.hook(tool, inp), "deny", (tool, inp))
        allow = [("Grep", {"pattern": "単価", "path": str(self.root / "projects/acme/knowledges")}),
                 ("Grep", {"pattern": "単価", "path": str(task)}),
                 ("Bash", {"command": "cat projects/acme/tasks/index.md"}),
                 ("Bash", {"command": "cat projects/index.md projects/acme/index.md"}),
                 ("Bash", {"command": "grep -rn 単価 projects/acme/knowledges"}),
                 ("Bash", {"command": f"ls {rel}/references/"}),
                 ("Bash", {"command": f"cd {rel} && find . -name '*.md'"}),
                 ("Bash", {"command": "ls scripts templates"}),
                 ("Bash", {"command": "echo projects"})]
        for tool, inp in allow:
            self.assertIsNone(self.hook(tool, inp), (tool, inp))
        # 現在のタスクが無ければ横断は止めない（agent-ws 自体を直すときの grep を邪魔しない）
        self.ws("task", "done")
        self.assertIsNone(self.hook("Grep", {"pattern": "単価"}))
        self.assertIsNone(self.hook("Bash", {"command": "find projects -maxdepth 3"}))

    def test_ref_add_skips_same_source_unless_forced(self):
        task = self._task()
        src = self.root / "memo.txt"
        src.write_text("単価は 10 万円", encoding="utf-8")
        self.ws("ref", "add", str(src), "--summary", "メモ")
        refs = lambda: [p for p in (task / "references").glob("*.md") if p.name != "index.md" and not p.name.endswith(".orig.md")]  # noqa: E731
        self.assertEqual(len(refs()), 1)
        out = self.ws("ref", "add", str(src), "--summary", "メモ").stdout
        self.assertIn("既にある", out)
        self.assertIn(refs()[0].name, out)
        self.assertEqual(len(refs()), 1)
        time.sleep(1)  # 同じ分に撮ると _SS が付くだけなので、秒違いの名前になるのを待つ
        self.ws("ref", "add", str(src), "--summary", "メモ", "--force")
        self.assertEqual(len(refs()), 2)

    def test_statusline_shows_task_context_and_cost(self):
        task = self._task()
        payload = json.dumps({"session_id": "s1", "model": {"display_name": "Sonnet 5"},
                              "context_window": {"used_percentage": 34.6}, "cost": {"total_cost_usd": 0.4171}})
        out = self.ws("statusline", stdin=payload).stdout.strip()
        self.assertEqual(out, f"agent-ws {task.name} | Sonnet 5 | ctx 35% | $0.42")
        # 値が無くても落ちない（セッション冒頭は used_percentage が null）
        out = self.ws("statusline", stdin='{"context_window": {"used_percentage": null}}').stdout.strip()
        self.assertEqual(out, f"agent-ws {task.name} | ctx - | $0.00")


if __name__ == "__main__":
    unittest.main()