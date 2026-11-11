# SPDX-License-Identifier: GPL-3.0-only
"""Exercise real Git ref histories in isolated local repositories, without networks."""
import importlib.util
import pathlib
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "sync_gitee", pathlib.Path(__file__).resolve().parents[1] / "tools/sync_gitee.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class MirrorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.source = self.root / "source"
        self.target = self.root / "target.git"
        self.local(None, "init", "-b", "main", str(self.source))
        self.local(None, "init", "--bare", str(self.target))
        self.local(self.source, "config", "user.name", "Mirror test")
        self.local(self.source, "config", "user.email", "test@example.invalid")
        self.commit("first")
        self.local(self.source, "push", str(self.target), "main")
        self.count = 0
        self.addCleanup(patch.stopall)
        patch.object(M, "git", self.local).start()

    def local(self, folder, *args, allow_failure=False):
        command = ["git", "-c", "core.hooksPath=/dev/null", "-c", "protocol.file.allow=always"]
        if folder:
            command += ["-C", str(folder)]
        result = subprocess.run(command + list(args), capture_output=True, text=True, timeout=20)
        if result.returncode and not allow_failure:
            raise RuntimeError(result.stderr)
        return result

    def commit(self, text):
        (self.source / "file.txt").write_text(text, encoding="utf-8")
        self.local(self.source, "add", "file.txt")
        self.local(self.source, "commit", "-m", text)

    def sync(self, publish=True, all_branches=False):
        self.count += 1
        return M.synchronize(self.root / ("run%d.git" % self.count),
                             str(self.source), str(self.target), publish, all_branches)

    def test_fast_forward_and_annotated_tag_then_unchanged(self):
        self.commit("second")
        self.local(self.source, "tag", "-a", "v1", "-m", "release")
        result = self.sync()
        self.assertEqual(result["status"], "published")
        self.assertTrue(result["remote_verified"])
        self.assertEqual(M.remote_refs(str(self.source)), M.remote_refs(str(self.target)))
        self.assertEqual(self.sync()["status"], "unchanged")

    def test_prepare_does_not_push(self):
        old = M.remote_refs(str(self.target))
        self.commit("second")
        self.assertEqual(self.sync(False)["status"], "prepared")
        self.assertEqual(old, M.remote_refs(str(self.target)))

    def test_divergence_blocks_entire_repository(self):
        self.commit("target-only commit")
        self.local(self.source, "push", str(self.target), "main")
        self.local(self.source, "switch", "-c", "alternate", "HEAD~1")
        self.commit("upstream change")
        self.local(self.source, "branch", "-f", "main", "HEAD")
        self.local(self.source, "switch", "main")
        self.local(self.source, "tag", "new-tag")
        old = M.remote_refs(str(self.target))
        result = self.sync()
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["conflicts"][0]["ref"], "refs/heads/main")
        self.assertEqual(old, M.remote_refs(str(self.target)))

    def test_changed_tag_blocks_and_target_only_branch_survives(self):
        self.local(self.source, "tag", "v1")
        self.local(self.source, "push", str(self.target), "v1", "main:refs/heads/local-note")
        self.commit("second")
        self.local(self.source, "tag", "-f", "v1")
        old = M.remote_refs(str(self.target))
        result = self.sync()
        self.assertEqual(result["status"], "blocked")
        self.assertIn("refs/heads/local-note", result["target_only"])
        self.assertEqual(old, M.remote_refs(str(self.target)))

    def test_target_only_branch_is_not_deleted(self):
        self.local(self.source, "push", str(self.target), "main:refs/heads/local-note")
        old = M.remote_refs(str(self.target))["refs/heads/local-note"]
        self.commit("second")
        self.assertEqual(self.sync()["status"], "published")
        self.assertEqual(M.remote_refs(str(self.target))["refs/heads/local-note"], old)

    def test_rewritten_work_branch_preserved_while_main_and_tags_update(self):
        self.local(self.source, "switch", "-c", "safe-mode")
        self.commit("old experiment")
        self.local(self.source, "push", str(self.target), "safe-mode")
        old = M.remote_refs(str(self.target))["refs/heads/safe-mode"]
        self.local(self.source, "switch", "main")
        self.commit("new release")
        self.local(self.source, "branch", "-f", "safe-mode", "HEAD")
        self.local(self.source, "branch", "new-experiment")
        self.local(self.source, "tag", "v2")
        strict = self.sync(all_branches=True)
        self.assertEqual(strict["status"], "blocked")
        result = self.sync()
        self.assertEqual(result["status"], "published")
        self.assertTrue(result["remote_verified"])
        self.assertEqual(result["scope"], "default-branch-and-tags")
        self.assertEqual(result["preserved_differences"][0]["ref"], "refs/heads/safe-mode")
        target = M.remote_refs(str(self.target))
        source = M.remote_refs(str(self.source))
        self.assertEqual(target["refs/heads/main"], source["refs/heads/main"])
        self.assertEqual(target["refs/tags/v2"], source["refs/tags/v2"])
        self.assertEqual(target["refs/heads/safe-mode"], old)
        self.assertNotIn("refs/heads/new-experiment", target)
        self.assertEqual(self.sync()["status"], "unchanged")

    def test_source_default_branch_is_discovered_not_assumed(self):
        self.local(self.source, "branch", "-m", "main", "trunk")
        self.commit("trunk release")
        result = self.sync()
        self.assertEqual(result["default_branch"], "refs/heads/trunk")
        self.assertIn("refs/heads/main", result["preserved_refs"])
        self.assertTrue(result["remote_verified"])

    def test_target_race_stops_before_push(self):
        self.commit("second")
        with patch.object(M, "remote_refs", return_value={}):
            with self.assertRaisesRegex(RuntimeError, "no push attempted"):
                self.sync()
        self.assertNotEqual(M.remote_refs(str(self.source)), M.remote_refs(str(self.target)))


if __name__ == "__main__":
    unittest.main()
