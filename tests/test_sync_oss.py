# SPDX-License-Identifier: GPL-3.0-only
import importlib.util
import pathlib
import tempfile
import unittest
import json
import subprocess
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("sync_oss", ROOT / "tools/sync_oss.py")
S = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(S)

PACKAGE = "mgu-store/packages/" + "a" * 64 + "/store@1.0.0.tgz"
ICON = "mgu-store/icons/" + "c" * 64 + "/store.png"
CATALOG = "mgu-store/catalog.json"


def entry(path, digest="b" * 64):
    return {"path": path, "size": 3, "sha256": digest}


class SyncTests(unittest.TestCase):
    def test_custom_domain_is_bound_to_exact_bucket_prefix_and_region(self):
        self.assertEqual(S.validate_target("oss://walle-mgu/mgu", "https://mgu.walle.pw/mgu/"),
                         ("oss://walle-mgu/mgu/", "https://mgu.walle.pw/mgu/"))
        self.assertEqual(S.target_region("oss://walle-mgu/mgu", "https://mgu.walle.pw/mgu/"), "cn-hangzhou")
        for target, base in [
            ("oss://walle-jenkins/mgu", "https://mgu.walle.pw/mgu/"),
            ("oss://walle-mgu/other", "https://mgu.walle.pw/other/"),
            ("oss://walle-mgu/mgu", "https://untrusted.example/mgu/"),
        ]:
            with self.assertRaises(ValueError):
                S.validate_target(target, base)

    def test_custom_binding_requires_live_bucket_domain_and_enabled_certificate(self):
        remote = S.Remote("ossutil", "private-config", "oss://walle-mgu/mgu",
                          "https://mgu.walle.pw/mgu/", pathlib.Path("/unused"))
        valid = {"Bucket": "walle-mgu", "Cname": {
            "Domain": "mgu.walle.pw", "Status": "Enabled", "Certificate": {"Status": "Enabled"}}}
        for value, accepted in [
            (valid, True),
            (dict(valid, Bucket="other"), False),
            (dict(valid, Cname=[]), False),
            (dict(valid, Cname=dict(valid["Cname"], Certificate={})), False),
            (dict(valid, Cname=dict(valid["Cname"], Domain="other.example")), False),
        ]:
            with patch.object(S.subprocess, "run", return_value=subprocess.CompletedProcess(
                    [], 0, json.dumps(value) + "\n0.1(s) elapsed\n", "")):
                if accepted:
                    remote.verify_binding()
                else:
                    with self.assertRaises(ValueError):
                        remote.verify_binding()
        options = remote.cli_options()
        self.assertEqual(options[options.index("--region") + 1], "cn-hangzhou")
        self.assertEqual(options[options.index("--retry-times") + 1], "1")
        self.assertIn("https://oss-cn-hangzhou.aliyuncs.com", options)
        with patch.object(S.subprocess, "run", return_value=subprocess.CompletedProcess([], 1, "", "")):
            with self.assertRaises(RuntimeError):
                remote.verify_binding()

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

    def test_icon_and_reused_package_headers_are_verified(self):
        for path in (ICON, PACKAGE):
            headers = {"cache-control": S.cache_control(path), "content-type": "image/png"}
            self.assertTrue(S.headers_match(path, headers))
            self.assertFalse(S.headers_match(path, {}))
            self.assertFalse(S.headers_match(path, dict(headers, **{"cache-control": "no-cache"})))
        self.assertFalse(S.headers_match(ICON, {
            "cache-control": S.cache_control(ICON), "content-type": "application/gzip"}))
        plan = S.upload_plan({"files": [entry(PACKAGE)]}, {"files": [entry(PACKAGE)]}, [PACKAGE])
        self.assertEqual(plan[0]["phase"], "resources")
        self.assertEqual(plan[0]["path"], PACKAGE)

    def test_retired_package_header_repair_retains_original_bytes(self):
        plan = S.upload_plan({"files": [entry(PACKAGE)]}, {"files": []}, [PACKAGE])
        self.assertEqual(plan, [dict(entry(PACKAGE), phase="resources", historical=True)])

    def test_immutable_path_cannot_be_replaced(self):
        with self.assertRaisesRegex(ValueError, "immutable"):
            S.upload_plan({"files": [entry(ICON)]}, {"files": [entry(ICON, "d" * 64)]})

    def test_public_icon_acceptance_checks_bytes_and_headers(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            remote = S.Remote("unused", "unused", "oss://example-bucket/mgu",
                              "https://example-bucket.oss-cn-beijing.aliyuncs.com/mgu/", root)
            for headers, accepted in [
                ({"cache-control": S.cache_control(ICON), "content-type": "image/png"}, True),
                ({"cache-control": "no-cache", "content-type": "image/png"}, False),
                ({"cache-control": S.cache_control(ICON), "content-type": "text/html"}, False),
            ]:
                with patch.object(S.M, "download") as download, \
                        patch.object(remote, "headers", return_value=headers):
                    if accepted:
                        remote.verify(ICON, entry(ICON), root)
                    else:
                        with self.assertRaisesRegex(RuntimeError, "headers"):
                            remote.verify(ICON, entry(ICON), root)
                    download.assert_called_once_with(remote.base + ICON, root / ICON, 3, "b" * 64)

    def test_lock_refuses_overlap_and_releases(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            with S.lock(root):
                with self.assertRaises(FileExistsError):
                    with S.lock(root):
                        self.fail("overlap allowed")
            self.assertFalse((root / ".sync.lock").exists())

    def exercise_publish(self, fail=None, with_icons=False):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            old_root, new_root = root / "old", root / "new"
            S.M.write_json(old_root / "mirror-manifest.json",
                           {"files": [entry(CATALOG), entry(PACKAGE)]})
            S.M.write_json(new_root / "mirror-manifest.json",
                           {"files": [entry(CATALOG), entry(ICON if with_icons else PACKAGE)]})
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
                    if fail == "headers" and rel == PACKAGE:
                        return {}
                    return {"cache-control": S.cache_control(rel), "content-type": "image/png"}

            def fetch(base, folder, **kwargs):
                events.append(("fetch", folder.name, kwargs.get("manifest_sha256")))
                if fail == "acceptance" and folder.name == "remote-acceptance":
                    raise RuntimeError("simulated acceptance failure")

            plan = [dict(entry(PACKAGE), phase="resources"),
                    dict(entry(CATALOG), phase="metadata")]
            if with_icons:
                plan = [dict(entry(ICON), phase="resources"),
                        dict(entry(PACKAGE), phase="resources", historical=True),
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

    def test_icon_and_historical_header_repair_precede_indexes(self):
        events = self.exercise_publish(with_icons=True)
        self.assertEqual(events[:6], [
            ("put", "new", ICON), ("verify", "resource-check", ICON),
            ("put", "old", PACKAGE), ("verify", "resource-check", PACKAGE),
            ("put", "new", CATALOG), ("verify", "metadata-check", CATALOG)])

    def test_publication_failures_restore_verified_previous_snapshot(self):
        for failure in ("catalog", "acceptance", "headers"):
            events = self.exercise_publish(failure)
            puts = [e for e in events if e[0] == "put"]
            self.assertEqual(puts[-2:], [("put", "old", CATALOG),
                                         ("put", "old", "mirror-manifest.json")])
            self.assertTrue(any(e[:2] == ("fetch", "rollback-acceptance") for e in events))


if __name__ == "__main__":
    unittest.main()
