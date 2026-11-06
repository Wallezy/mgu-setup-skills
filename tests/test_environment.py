# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Wallezy and contributors.

import importlib.util
import pathlib
import subprocess
import unittest
from unittest.mock import patch


PATH = (
    pathlib.Path(__file__).resolve().parents[1]
    / "skills/mgu-setup/scripts/check_environment.py"
)
SPEC = importlib.util.spec_from_file_location("environment", PATH)
ENV = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ENV)


class EnvironmentTests(unittest.TestCase):
    def test_missing_executable_does_not_launch(self):
        with patch.object(ENV.shutil, "which", return_value=None), patch.object(
            ENV.subprocess, "run"
        ) as run:
            result = ENV.probe_tool("node", "--version", r"v(\d+\.\d+\.\d+)", (18, 0, 0))
        self.assertFalse(result["ok"])
        run.assert_not_called()

    def test_old_node_is_not_ready(self):
        completed = subprocess.CompletedProcess([], 0, stdout="v16.20.2\n", stderr="")
        with patch.object(ENV.shutil, "which", return_value="/example/node"), patch.object(
            ENV.subprocess, "run", return_value=completed
        ):
            result = ENV.probe_tool("node", "--version", r"v(\d+\.\d+\.\d+)", (18, 0, 0))
        self.assertFalse(result["ok"])

    def test_openssh_version_on_stderr(self):
        completed = subprocess.CompletedProcess(
            [], 0, stdout="", stderr="OpenSSH_9.9p2, LibreSSL 3.3.6\n"
        )
        with patch.object(ENV.shutil, "which", return_value="/example/ssh"), patch.object(
            ENV.subprocess, "run", return_value=completed
        ):
            result = ENV.probe_tool("ssh", "-V", r"\b(OpenSSH[^\s,]*)")
        self.assertTrue(result["ok"])
        self.assertEqual(result["version"], "OpenSSH_9.9p2")

    def test_unresponsive_tool_is_unverified(self):
        with patch.object(ENV.shutil, "which", return_value="/example/node"), patch.object(
            ENV.subprocess,
            "run",
            side_effect=subprocess.TimeoutExpired("node", 8),
        ):
            result = ENV.probe_tool("node", "--version", r"v(\d+\.\d+\.\d+)")
        self.assertFalse(result["ok"])

    def test_store_profile_does_not_require_crypto_or_claim_vehicle_ready(self):
        available = {"ok": True, "version": "example", "reason": "available"}
        with patch.object(ENV, "probe_crypto", return_value={"ok": False}), patch.object(
            ENV, "probe_tool", return_value=available
        ):
            report = ENV.make_report("store")
            full = ENV.make_report("full")
        self.assertTrue(report["local_requirements_met"])
        self.assertFalse(full["local_requirements_met"])
        self.assertFalse(report["vehicle_checked"])
        self.assertIsNone(report["vehicle_ready"])


if __name__ == "__main__":
    unittest.main()
