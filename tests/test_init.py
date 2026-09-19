"""scripts/ws init の自己チェック。  python3 -m unittest tests/test_init.py

同梱の見本（projects/_example/ と repo 直下 knowledges/）は init で消してよいもの（README・ADR 0023）
なので、無ければ（消してある環境なら）skip する。
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
WS = REPO / "scripts" / "ws"
EXAMPLES = REPO / "templates" / "examples.json"
EXAMPLE_ROOTS = ("projects/_example", "knowledges")


def _digest(f: Path) -> str:
    # scripts/ws の _digest と同じ式。拡張子なしのスクリプトは import しにくいのでここでも定義する
    return hashlib.sha256(f.read_text(encoding="utf-8").encode("utf-8")).hexdigest()


@unittest.skipUnless((REPO / "projects/_example").exists(), "同梱の見本が無い（消してある）")
class ManifestTest(unittest.TestCase):
    def test_examples_json_matches_the_shipped_examples(self):
        shipped = {}
        for root_name in EXAMPLE_ROOTS:
            for f in (REPO / root_name).rglob("*"):
                if f.is_file() and "__pycache__" not in f.parts:
                    shipped[f.relative_to(REPO).as_posix()] = _digest(f)
        manifest = json.loads(EXAMPLES.read_text(encoding="utf-8"))
        self.assertEqual(manifest, shipped,
                         "見本と templates/examples.json がずれている。"
                         "見本を直したら scripts/ws init --manifest で一覧を作り直す")


@unittest.skipUnless((REPO / "projects/_example").exists(), "同梱の見本が無い（消してある）")
class InitFlowTest(unittest.TestCase):
    """一時ルートへ同梱の見本を写し、init の挙動を確かめる（tests/test_ws.py の WsFlowTest と同じ型）。"""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="ws-init-test-"))
        shutil.copytree(REPO / "templates", self.root / "templates")
        (self.root / "projects").mkdir()
        shutil.copy(REPO / "projects" / "index.md", self.root / "projects" / "index.md")
        shutil.copytree(REPO / "projects" / "_example", self.root / "projects" / "_example")
        shutil.copytree(REPO / "knowledges", self.root / "knowledges")
        self.env = {**os.environ, "WS_ROOT": str(self.root)}
        for k in ("CLAUDE_CODE_SESSION_ID", "CODEX_THREAD_ID"):  # テストを起こしたエージェントのセッションを持ち込まない
            self.env.pop(k, None)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def ws(self, *args, stdin=None, check=True):
        r = subprocess.run([sys.executable, str(WS), *args], input=stdin, capture_output=True,
                           text=True, env=self.env, cwd=self.root)
        if check and r.returncode != 0:
            self.fail(f"ws {' '.join(args)} failed:\n{r.stderr}")
        return r

    def test_untouched_examples_are_removed_folder_and_all(self):
        self.ws("init")
        self.assertFalse((self.root / "projects" / "_example").exists())
        self.assertFalse((self.root / "knowledges").exists())
        self.assertNotIn("_example", (self.root / "projects" / "index.md").read_text(encoding="utf-8"))
        r2 = self.ws("init", check=False)  # 2 回目も正常終了する
        self.assertEqual(r2.returncode, 0, r2.stderr)

    def test_mixed_state_keeps_edited_and_added_files(self):
        glossary = self.root / "knowledges" / "glossary.md"
        with glossary.open("a", encoding="utf-8") as f:
            f.write("追記した1行\n")
        self.ws("know", "new", "--common", "決裁範囲", "--owner", "総務部")
        added = next((self.root / "knowledges").glob("0*_決裁範囲.md"))

        out = self.ws("init").stdout

        self.assertFalse((self.root / "knowledges" / "001_組織図.md").exists())
        self.assertFalse((self.root / "knowledges" / "ontology").exists())
        self.assertTrue(glossary.exists())
        self.assertIn("追記した1行", glossary.read_text(encoding="utf-8"))
        self.assertTrue(added.exists())
        self.assertIn("knowledges/glossary.md", out)

        idx = (self.root / "knowledges" / "index.md").read_text(encoding="utf-8")
        self.assertIn(added.name, idx)
        self.assertNotIn("001_組織図", idx)

    def test_tried_out_example_project_is_left_with_a_hint(self):
        # 見本を試すとタスクの index.md が書き換わる。中身を見ずには消せないので残し、フォルダごと消してよいと伝える
        task_idx = next((self.root / "projects" / "_example" / "tasks").glob("*/index.md"))
        task_idx.write_text(task_idx.read_text(encoding="utf-8") + "\n試した跡\n", encoding="utf-8")
        out = self.ws("init").stdout
        self.assertTrue(task_idx.exists())
        self.assertIn(task_idx.relative_to(self.root).as_posix(), out)
        self.assertIn("フォルダごと消して", out)
        self.assertFalse((self.root / "projects" / "_example" / "knowledges").exists())

    def test_common_index_is_rebuilt_when_only_user_files_remain(self):
        # know new を通さず手で置いたファイルだと index.md は同梱時のまま（＝消える）。雛形から作り直して一覧に載せる
        mine = self.root / "knowledges" / "002_決裁範囲.md"
        mine.write_text('---\ntitle: "決裁範囲"\nsummary: "自社の決裁範囲"\n---\n本文\n', encoding="utf-8")
        self.ws("init")
        self.assertTrue(mine.exists())
        self.assertIn(mine.name, (self.root / "knowledges" / "index.md").read_text(encoding="utf-8"))

    def test_session_start_mentions_init_only_while_examples_remain(self):
        def additional_context():
            out = self.ws("hook", "session-start",
                          stdin=json.dumps({"session_id": "s1", "source": "startup"})).stdout
            return json.loads(out)["hookSpecificOutput"]["additionalContext"]

        self.assertIn("scripts/ws init", additional_context())
        self.ws("init")
        self.assertNotIn("scripts/ws init", additional_context())

    def test_session_start_silent_without_any_examples(self):
        plain = Path(tempfile.mkdtemp(prefix="ws-init-test-plain-"))
        try:
            shutil.copytree(REPO / "templates", plain / "templates")
            (plain / "projects").mkdir()
            shutil.copy(REPO / "projects" / "index.md", plain / "projects" / "index.md")
            env = {**self.env, "WS_ROOT": str(plain)}
            r = subprocess.run([sys.executable, str(WS), "hook", "session-start"],
                               input=json.dumps({"session_id": "s1", "source": "startup"}),
                               capture_output=True, text=True, env=env, cwd=plain)
            ctx = json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]
            self.assertNotIn("scripts/ws init", ctx)
        finally:
            shutil.rmtree(plain, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
