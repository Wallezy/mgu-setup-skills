# SPDX-License-Identifier: GPL-3.0-only
import copy
import hashlib
import importlib.util
import pathlib
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "mirror", ROOT / "skills/mgu-setup/scripts/mirror_resources.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def component(identity, data=b"package", requires=None):
    return {"id": identity, "version": "1.0.0", "kind": "tool",
            "requires": requires or {},
            "artifact": {"name": identity + "@1.0.0.tgz", "url": "packages/" + identity + ".tgz",
                         "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}}


class MirrorTests(unittest.TestCase):
    def make_bundle(self, root):
        for repo, entry in (("mgu-store", component("mgu-deploy")),
                            ("idrive-apps", component("map", requires={"mgu-deploy": "1.0.0"}))):
            target = root / repo / entry["artifact"]["url"]
            target.parent.mkdir(parents=True)
            target.write_bytes(b"package")
            M.write_json(root / repo / "catalog.json", {"schema": 2, "components": [entry]})
        (root / "bootstrap").mkdir()
        (root / "bootstrap/mgu-install.js").write_text("offline", encoding="utf-8")
        manifest = {"schema": 1, "files": [
            {"path": p.relative_to(root).as_posix(), "size": p.stat().st_size, "sha256": M.digest(p)}
            for p in root.rglob("*") if p.is_file()]}
        M.write_json(root / "mirror-manifest.json", manifest)
        return manifest

    def test_full_bundle_and_tampered_package(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            self.make_bundle(root)
            M.verify_bundle(root)
            (root / "idrive-apps/packages/map.tgz").write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "corrupt"):
                M.verify_bundle(root)

    def test_catalog_cannot_point_back_to_upstream_or_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            manifest = self.make_bundle(root)
            path = root / "idrive-apps/catalog.json"
            catalog = M.load_json(path)
            catalog["components"][0]["artifact"]["url"] = "https://github.com/file.tgz"
            M.write_json(path, catalog)
            entry = next(f for f in manifest["files"] if f["path"] == "idrive-apps/catalog.json")
            entry.update(size=path.stat().st_size, sha256=M.digest(path))
            M.write_json(root / "mirror-manifest.json", manifest)
            with self.assertRaisesRegex(ValueError, "Unsafe"):
                M.verify_bundle(root)

    def test_dependencies_are_checked_across_repositories(self):
        catalog = {"schema": 2, "components": [component("map", requires={"renderer": "1.0.1"})]}
        with self.assertRaisesRegex(ValueError, "Unmet dependency"):
            M.verify_dependencies([catalog, {"components": [component("renderer")]}])

    def test_fallback_cannot_change_pinned_version_or_bytes(self):
        entry = component("map")
        plan = {"components": {"map": {"version": "1.0.0", "sha256": entry["artifact"]["sha256"]}}}
        M.assert_plan_matches([{"components": [entry]}], plan)
        for field in ("version", "sha256"):
            changed = copy.deepcopy(entry)
            if field == "version":
                changed["version"] = "1.0.1"
            else:
                changed["artifact"]["sha256"] = "a" * 64
            with self.assertRaisesRegex(ValueError, "changed"):
                M.assert_plan_matches([{"components": [changed]}], plan)

    def test_invalid_paths_and_expiring_or_credential_urls(self):
        for value in ("../key", "/absolute", "folder/../key", "a\\b", "a%2fb", "https://host/file"):
            with self.assertRaises(ValueError):
                M.relative_path(value)
        for value in ("http://example.com", "https://user:pass@example.com", "https://example.com/?token=x"):
            with self.assertRaises(ValueError):
                M.https_url(value)

    def test_failed_download_does_not_replace_valid_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "artifact"
            path.write_bytes(b"old")
            def fake_download(command, **kwargs):
                destination = pathlib.Path(command[command.index("--output") + 1])
                destination.write_bytes(b"wrong")
                return type("Result", (), {"returncode": 0})()
            with patch.object(M.shutil, "which", return_value="/curl"), patch.object(
                    M.subprocess, "run", side_effect=fake_download):
                with self.assertRaisesRegex(ValueError, "mismatch"):
                    M.download("https://example.com/pkg", path, 3, hashlib.sha256(b"new").hexdigest())
            self.assertEqual(path.read_bytes(), b"old")
            self.assertFalse(path.with_name("artifact.part").exists())

    def test_explicit_preference_and_fallback_are_recorded(self):
        self.assertEqual(M.source_order("domestic-first"), ["domestic", "upstream"])
        self.assertEqual(M.source_order("auto"), ["upstream", "domestic"])
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            self.make_bundle(root)
            def download(url, destination, *args, **kwargs):
                if "api.github.com" in url:
                    raise RuntimeError("unreachable")
                relative = url.split("https://mirror.example/", 1)[1]
                pathlib.Path(destination).write_bytes((root / relative).read_bytes())
            with patch.object(M, "download", side_effect=download):
                plan = M.plan_sources({"oss_base_url": "https://mirror.example/", "preference": "auto"})
            self.assertEqual(plan["selected_source"], "domestic")
            self.assertEqual(plan["failed_attempts"][0]["source"], "upstream")

    def test_catalog_timeout_falls_back_without_weakening_package_downloads(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            self.make_bundle(root)
            commands = []

            def curl(command, **kwargs):
                commands.append(command)
                url = command[-1]
                if "api.github.com" in url:
                    return type("Result", (), {"returncode": 28, "stderr": "timeout"})()
                destination = pathlib.Path(command[command.index("--output") + 1])
                relative = url.split("https://mirror.example/", 1)[1]
                destination.write_bytes((root / relative).read_bytes())
                return type("Result", (), {"returncode": 0})()

            with patch.object(M.shutil, "which", return_value="/curl"), patch.object(
                    M.subprocess, "run", side_effect=curl):
                plan = M.plan_sources({"oss_base_url": "https://mirror.example/", "preference": "auto"})
                self.assertEqual(plan["selected_source"], "domestic")
                self.assertIn("timeout", plan["failed_attempts"][0]["reason"])
                self.assertEqual(len(commands), 4)
                for command in commands:
                    self.assertLessEqual(int(command[command.index("--max-time") + 1]), 20)
                    self.assertEqual(command[command.index("--retry") + 1], "0")

                target = root / "downloaded-package"
                url = "https://mirror.example/mgu-store/packages/mgu-deploy.tgz"
                M.download(url, target, 7, hashlib.sha256(b"package").hexdigest())
                self.assertEqual(target.read_bytes(), b"package")
                command = commands[-1]
                self.assertEqual(command[command.index("--max-time") + 1], "180")
                self.assertEqual(command[command.index("--retry") + 1], "2")
                with self.assertRaisesRegex(ValueError, "mismatch"):
                    M.download(url, target, 7, "a" * 64)
                self.assertEqual(target.read_bytes(), b"package")


if __name__ == "__main__":
    unittest.main()
