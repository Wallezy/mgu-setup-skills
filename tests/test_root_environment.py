# SPDX-License-Identifier: GPL-3.0-only
"""Exercise checkout validation without importing or running the Root tool."""

import importlib.util
import json
import pathlib
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

PATH = pathlib.Path(__file__).resolve().parents[1] / "skills/mgu-setup/scripts/check_environment.py"
SPEC = importlib.util.spec_from_file_location("root_environment", PATH)
ENV = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ENV)


@unittest.skipUnless(shutil.which("git"), "Git is needed for source-checkout tests")
class RootEnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = pathlib.Path(self.temp.name)
        self.repo = self.directory / "root"
        self.repo.mkdir()
        (self.repo / "ssh_enable.py").write_text("raise AssertionError('must not execute')\n")
        (self.repo / "requirements.txt").write_text("cryptography>=41.0\n")
        self.git("init", "-q")
        self.git("add", ".")
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                 "-c", "commit.gpgsign=false", "-c", "core.hooksPath=" + str(self.directory / "no-hooks"),
                 "commit", "-qm", "fixture")
        self.commit = self.git("rev-parse", "HEAD").strip()
        self.policy = self.directory / "release.json"
        self.policy.write_text(json.dumps({"version": "v-test", "commit": self.commit}))
        patcher = patch.object(ENV, "ROOT_RELEASE", self.policy)
        patcher.start()
        self.addCleanup(patcher.stop)

    def git(self, *args):
        return subprocess.run(
            [shutil.which("git"), "-C", str(self.repo), *args],
            capture_output=True, text=True, check=True,
        ).stdout

    def test_clean_pinned_checkout_passes_without_executing_source(self):
        (self.repo / "data").mkdir()
        (self.repo / "data/session.txt").write_text("private local placeholder")
        result = ENV.probe_root_repo(self.repo)
        self.assertTrue(result["ok"])
        self.assertEqual(result["revision"], self.commit)
        self.assertEqual(result["version"], "v-test")
        self.assertNotIn("private", json.dumps(result))

    def test_wrong_revision_is_not_accepted_as_latest(self):
        self.policy.write_text(json.dumps({"version": "v-next", "commit": "0" * 40}))
        result = ENV.probe_root_repo(self.repo)
        self.assertFalse(result["ok"])
        self.assertEqual(result["revision"], self.commit)

    def test_changed_and_missing_tracked_files_fail(self):
        requirements = self.repo / "requirements.txt"
        requirements.write_text("unreviewed-dependency\n")
        self.assertFalse(ENV.probe_root_repo(self.repo)["ok"])
        requirements.unlink()
        self.assertFalse(ENV.probe_root_repo(self.repo)["ok"])

    def test_parent_checkout_does_not_certify_nested_tool(self):
        child = self.repo / "nested"
        child.mkdir()
        (child / "ssh_enable.py").write_text("raise AssertionError('must not execute')\n")
        result = ENV.probe_root_repo(child)
        self.assertFalse(result["ok"])
        self.assertIn("subfolder", result["reason"])

    def test_source_archive_without_git_is_unverified(self):
        archive = self.directory / "archive"
        archive.mkdir()
        (archive / "ssh_enable.py").write_text("# no Git metadata\n")
        self.assertFalse(ENV.probe_root_repo(archive)["ok"])

    def test_missing_git_and_timeout_do_not_pass(self):
        with patch.object(ENV.shutil, "which", return_value=None):
            self.assertFalse(ENV.probe_root_repo(self.repo)["ok"])
        with patch.object(ENV.subprocess, "run", side_effect=subprocess.TimeoutExpired("git", 8)):
            self.assertFalse(ENV.probe_root_repo(self.repo)["ok"])

    def test_invalid_root_blocks_root_profile_but_not_store_updates(self):
        available = {"ok": True, "version": "test", "reason": "available"}
        (self.repo / "requirements.txt").unlink()
        with patch.object(ENV, "probe_crypto", return_value=available), patch.object(
            ENV, "probe_tool", return_value=available
        ):
            root = ENV.make_report("root", self.repo)
            store = ENV.make_report("store", self.repo)
        self.assertFalse(root["local_requirements_met"])
        self.assertTrue(store["local_requirements_met"])
        self.assertFalse(root["vehicle_checked"])
        self.assertIsNone(root["vehicle_ready"])


if __name__ == "__main__":
    unittest.main()
