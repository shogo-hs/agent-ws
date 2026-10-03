"""scripts/ws update とローカル運用の push 止め（ADR 0032）の自己チェック。  python3 -m unittest tests/test_update.py

テンプレートの代わりに一時の bare リポジトリを WS_TEMPLATE_URL に置き、本物の git で取り込みと push の拒否を確かめる。
"""
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
GIT_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
           "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}


@unittest.skipUnless(shutil.which("git"), "git が無い")
class UpdateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="ws-update-test-"))
        self.env = {**os.environ, **GIT_ENV, "WS_TEMPLATE_URL": str(self.tmp / "tpl.git")}
        for k in ("CLAUDE_CODE_SESSION_ID", "CODEX_THREAD_ID"):
            self.env.pop(k, None)
        self.git("init", "-q", "--bare", "-b", "main", str(self.tmp / "tpl.git"))
        self.dev = self.tmp / "dev"  # テンプレートを開発する側の clone
        self.git("clone", "-q", str(self.tmp / "tpl.git"), str(self.dev))
        (self.dev / "LESSONS.md").write_text("# 教訓\n", encoding="utf-8")
        (self.dev / "a.md").write_text("1\n", encoding="utf-8")
        self.commit_push("最初")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def git(self, *args, cwd=None, check=True):
        r = subprocess.run(["git", *args], cwd=cwd or self.tmp, capture_output=True, text=True, env=self.env)
        if check and r.returncode != 0:
            self.fail(f"git {' '.join(args)}: {r.stderr}")
        return r

    def commit_push(self, msg):
        self.git("add", "-A", cwd=self.dev)
        self.git("commit", "-q", "-m", msg, cwd=self.dev)
        self.git("push", "-q", "origin", "HEAD:main", cwd=self.dev)

    def ws(self, root, *args, stdin=None, check=True):
        r = subprocess.run([sys.executable, str(WS), *args], input=stdin, capture_output=True, text=True,
                           env={**self.env, "WS_ROOT": str(root)}, cwd=root)
        if check and r.returncode != 0:
            self.fail(f"ws {' '.join(args)} failed:\n{r.stdout}\n{r.stderr}")
        return r

    def hook(self, root, tool, tool_input, cwd=None):
        r = self.ws(root, "hook", "pre-tool-use", stdin=json.dumps(
            {"tool_name": tool, "tool_input": tool_input, "cwd": str(cwd or root)}))
        return json.loads(r.stdout)["hookSpecificOutput"]["permissionDecision"] if r.stdout.strip() else None

    def test_local_only_pulls_keeps_own_work_and_blocks_push(self):
        ws_root = self.tmp / "ws"
        self.git("clone", "-q", str(self.tmp / "tpl.git"), str(ws_root))
        self.assertIsNone(self.hook(ws_root, "Bash", {"command": "git push origin main"}))  # 印が付くまでは止めない
        with (ws_root / "LESSONS.md").open("a", encoding="utf-8") as f:
            f.write("- 自分の教訓\n")
        (ws_root / "mine.md").write_text("自分のファイル\n", encoding="utf-8")
        (self.dev / "a.md").write_text("2\n", encoding="utf-8")
        self.commit_push("テンプレートの更新")

        out = self.ws(ws_root, "update").stdout
        self.assertIn("テンプレートの更新", out)
        self.assertEqual((ws_root / "a.md").read_text(encoding="utf-8"), "2\n")
        self.assertIn("自分の教訓", (ws_root / "LESSONS.md").read_text(encoding="utf-8"))
        self.assertTrue((ws_root / "mine.md").exists())
        # push は宛先（no_push）でも pre-push フックでも止まる
        self.assertEqual(self.git("remote", "get-url", "--push", "origin", cwd=ws_root).stdout.strip(), "no_push")
        self.git("commit", "-qam", "x", cwd=ws_root)
        self.assertNotEqual(self.git("push", "origin", "main", cwd=ws_root, check=False).returncode, 0)
        r = self.git("push", str(self.tmp / "tpl.git"), "HEAD:main", cwd=ws_root, check=False)  # URL を直接書いても
        self.assertIn("pre-push", r.stderr)
        # エージェントの hook
        for cmd in ("git push origin main", "scripts/ws index; git push", "git remote set-url --push origin x",
                    "git config --unset remote.origin.pushurl", "git push --no-verify", "rm .git/hooks/pre-push",
                    "git reset --hard", "git checkout .", "git clean -fd", "git restore LESSONS.md"):
            self.assertEqual(self.hook(ws_root, "Bash", {"command": cmd}), "deny", cmd)
        self.assertEqual(self.hook(ws_root, "Write", {"file_path": str(ws_root / ".git/hooks/pre-push"), "content": ""}), "deny")
        for cmd in ("git status", "git stash push", "git reset", "git restore --staged .", "git log --oneline",
                    "cd repos/app && git push", "scripts/ws update"):
            self.assertIsNone(self.hook(ws_root, "Bash", {"command": cmd}), cmd)
        self.assertIsNone(self.hook(ws_root, "Bash", {"command": "git push"}, cwd=ws_root / "repos" / "app"))
        self.assertIsNone(self.hook(ws_root, "Read", {"file_path": str(ws_root / ".git/config")}))

    def test_local_only_conflict_is_listed_and_own_change_survives_in_stash(self):
        ws_root = self.tmp / "ws"
        self.git("clone", "-q", str(self.tmp / "tpl.git"), str(ws_root))
        (ws_root / "a.md").write_text("手元\n", encoding="utf-8")
        (self.dev / "a.md").write_text("テンプレート\n", encoding="utf-8")
        self.commit_push("同じ行を変える")
        out = self.ws(ws_root, "update").stdout
        self.assertIn("衝突したファイル", out)
        self.assertIn("a.md", out)
        text = (ws_root / "a.md").read_text(encoding="utf-8")
        self.assertIn("手元", text)
        self.assertIn("テンプレート", text)
        self.assertTrue(self.git("stash", "list", cwd=ws_root).stdout.strip())  # 手元の変更は stash にも残る
        r = self.ws(ws_root, "update", check=False)  # 衝突を直す前の 2 回目は止まる
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("衝突が残っている", r.stderr)

    def test_fork_merges_remote_template(self):
        fork = self.tmp / "fork"  # 自分のリポジトリ（origin はテンプレートではない）
        self.git("init", "-q", "--bare", "-b", "main", str(self.tmp / "mine.git"))
        self.git("clone", "-q", str(self.tmp / "tpl.git"), str(fork))
        self.git("remote", "set-url", "origin", str(self.tmp / "mine.git"), cwd=fork)
        (fork / "mine.md").write_text("x\n", encoding="utf-8")
        self.git("add", "-A", cwd=fork)
        self.git("commit", "-qm", "自分の作業", cwd=fork)
        (self.dev / "a.md").write_text("2\n", encoding="utf-8")
        self.commit_push("テンプレートの更新")

        out = self.ws(fork, "update").stdout
        self.assertIn("テンプレートの更新", out)
        self.assertEqual((fork / "a.md").read_text(encoding="utf-8"), "2\n")
        self.assertIn("を取り込む", self.git("log", "-1", "--format=%s", cwd=fork).stdout)
        self.assertNotEqual(self.git("remote", "get-url", "--push", "origin", cwd=fork).stdout.strip(), "no_push")
        self.assertIsNone(self.hook(fork, "Bash", {"command": "git push origin main"}))
        self.assertIn("取り込む更新は無い", self.ws(fork, "update").stdout)


if __name__ == "__main__":
    unittest.main()
