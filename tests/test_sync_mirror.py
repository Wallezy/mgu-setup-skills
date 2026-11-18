import contextlib
import importlib.util
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("sync_mirror", ROOT / "tools/sync_mirror.py")
S = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(S)


class DirectSyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.args = types.SimpleNamespace(cache=self.root / "cache", prepared=None, publish=True)
        self.tx = mock.Mock()
        self.tx.files = {"mgu/mirror-manifest.json": {"sha256": "a" * 64}}
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.transaction = self.stack.enter_context(mock.patch.object(S.T, "Transaction", return_value=self.tx))
        self.fetch = self.stack.enter_context(mock.patch.object(S.M, "fetch_remote"))
        self.stack.enter_context(mock.patch.object(S.P, "upstream_catalog", return_value=({}, self.root, {})))
        self.stack.enter_context(mock.patch.object(S.M, "verify_dependencies"))
        self.stack.enter_context(mock.patch.object(S.M, "verify_bundle", return_value=({"files": []}, None)))
        self.match = self.stack.enter_context(mock.patch.object(S, "catalogs_match", return_value=True))
        self.stack.enter_context(mock.patch.object(S.M, "digest", return_value="b" * 64))
        self.stack.enter_context(mock.patch.object(S.M, "load_json", return_value={"components": []}))
        self.prepare = self.stack.enter_context(mock.patch.object(S.P, "prepare"))
        self.replicate = self.stack.enter_context(mock.patch.object(S.T, "replicate", side_effect=lambda r, w, t: r))

    def test_unchanged_revalidates_root_without_new_packages(self):
        result = S.synchronize(self.args, self.root)
        self.transaction.assert_called_once_with("mgu/", self.root)
        self.fetch.assert_called_once_with(S.BASE, self.root / "live-before", manifest_sha256="a" * 64)
        self.tx.put.assert_called_once_with("mirror-manifest.json", self.root / "live-before")
        self.prepare.assert_not_called()
        self.assertEqual(result["status"], "unchanged")
        self.assertFalse(result["oss_used"])

    def test_prepare_does_not_commit(self):
        self.args.publish = False
        result = S.synchronize(self.args, self.root)
        self.replicate.assert_not_called()
        self.assertFalse(result["remote_verified"])

    def test_failed_publication_propagates_without_success_pointer(self):
        self.replicate.side_effect = RuntimeError("origin unavailable")
        with self.assertRaisesRegex(RuntimeError, "origin unavailable"):
            S.synchronize(self.args, self.root)
        self.assertFalse((self.root / "latest-success.json").exists())

    def test_prepared_snapshot_must_match_current_upstream(self):
        self.args.prepared = self.root / "supplied"
        self.match.return_value = False
        with self.assertRaisesRegex(ValueError, "current official"):
            S.synchronize(self.args, self.root)
        self.replicate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
