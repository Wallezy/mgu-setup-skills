# SPDX-License-Identifier: GPL-3.0-only
import importlib.util
import pathlib
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("sync_oss", ROOT / "tools/sync_oss.py")
S = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(S)

PACKAGE = "mgu-store/packages/" + "a" * 64 + "/store@1.0.0.tgz"
CATALOG = "mgu-store/catalog.json"


def entry(path, digest="b" * 64):
    return {"path": path, "size": 3, "sha256": digest}


class SyncTests(unittest.TestCase):
    def test_destination_must_match_public_prefix(self):
        destination = "oss://example-bucket/mgu"
        base = "https://example-bucket.oss-cn-beijing.aliyuncs.com/mgu/"
        self.assertEqual(S.validate_target(destination, base), (destination + "/", base))
        for wrong in ("https://other.oss-cn-beijing.aliyuncs.com/mgu/",
                      "https://example-bucket.oss-cn-beijing.aliyuncs.com/other/",
                      "https://example-bucket.oss-cn-beijing.aliyuncs.com:8443/mgu/"):
            with self.assertRaises(ValueError):
                S.validate_target(destination, wrong)
        with self.assertRaises(ValueError):
            S.validate_target("oss://example-bucket/", base)

    def test_delta_reuses_bytes_and_repairs_mutable_headers(self):
        old = {"files": [entry(CATALOG), entry(PACKAGE)]}
        new = {"files": [entry(CATALOG, "c" * 64), entry(PACKAGE),
                         entry("idrive-apps/README.md")]}
        plan = S.upload_plan(old, new)
        self.assertEqual({e["path"] for e in plan}, {CATALOG, "idrive-apps/README.md"})
        self.assertEqual(len(S.upload_plan(old, old, [CATALOG])), 1)
        self.assertEqual(S.cache_control(CATALOG), "no-cache")
        self.assertIn("immutable", S.cache_control(PACKAGE))
        self.assertEqual(S.cache_control("mgu-store/packages/latest.tgz"), "no-cache")
        self.assertTrue(S.no_cache({"cache-control": "public, no-cache"}))
        self.assertFalse(S.no_cache({"cache-control": "no-cache-for-something"}))

    def test_lock_refuses_overlap_and_releases(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            with S.lock(root):
                with self.assertRaises(FileExistsError):
                    with S.lock(root):
                        self.fail("overlap allowed")
            self.assertFalse((root / ".sync.lock").exists())

    def exercise_publish(self, fail=None):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            old_root, new_root = root / "old", root / "new"
            for folder in (old_root, new_root):
                S.M.write_json(folder / "mirror-manifest.json",
                               {"files": [entry(CATALOG), entry(PACKAGE)]})
            events = []

            class Remote:
                base = "https://example-bucket.oss-cn-beijing.aliyuncs.com/mgu/"

                def put(self, folder, rel):
                    events.append(("put", folder.name, rel))
                    if fail == "catalog" and folder == new_root and rel == CATALOG:
                        raise RuntimeError("simulated catalog failure")

                def verify(self, rel, artifact, folder):
                    events.append(("verify", folder.name, rel))
                    if fail == "resource" and rel == PACKAGE:
                        raise RuntimeError("simulated corrupt resource")

                def headers(self, rel):
                    return {"cache-control": "no-cache"}

            def fetch(base, folder, **kwargs):
                events.append(("fetch", folder.name, kwargs.get("manifest_sha256")))
                if fail == "acceptance" and folder.name == "remote-acceptance":
                    raise RuntimeError("simulated acceptance failure")

            plan = [dict(entry(PACKAGE), phase="resources"),
                    dict(entry(CATALOG), phase="metadata")]
            with patch.object(S.M, "fetch_remote", side_effect=fetch):
                if fail:
                    with self.assertRaises(RuntimeError):
                        S.publish(Remote(), old_root, new_root, plan, root)
                else:
                    S.publish(Remote(), old_root, new_root, plan, root)
            return events

    def test_resource_verified_before_catalog_and_manifest_last(self):
        events = self.exercise_publish()
        self.assertEqual(events[:4], [
            ("put", "new", PACKAGE), ("verify", "resource-check", PACKAGE),
            ("put", "new", CATALOG), ("verify", "metadata-check", CATALOG)])
        self.assertEqual([e for e in events if e[0] == "put"][-1],
                         ("put", "new", "mirror-manifest.json"))
        self.assertTrue(any(e[:2] == ("fetch", "remote-acceptance") for e in events))

    def test_bad_resource_never_replaces_indexes(self):
        puts = [e for e in self.exercise_publish("resource") if e[0] == "put"]
        self.assertEqual(puts, [("put", "new", PACKAGE)])

    def test_publication_failures_restore_verified_previous_snapshot(self):
        for failure in ("catalog", "acceptance"):
            events = self.exercise_publish(failure)
            puts = [e for e in events if e[0] == "put"]
            self.assertEqual(puts[-2:], [("put", "old", CATALOG),
                                         ("put", "old", "mirror-manifest.json")])
            self.assertTrue(any(e[:2] == ("fetch", "rollback-acceptance") for e in events))


if __name__ == "__main__":
    unittest.main()
