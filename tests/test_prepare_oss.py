# SPDX-License-Identifier: GPL-3.0-only
import copy
import hashlib
import importlib.util
import io
import json
import pathlib
import struct
import tarfile
import tempfile
import unittest
import zipfile
import zlib
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("sync", ROOT / "tools/sync_oss.py")
S = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(S)
P, M = S.P, S.M


def png(width=1):
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, 1, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(b"\0\xff\0\0\xff"))
            + chunk(b"IEND", b""))


class PrepareTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.cache = self.root / "cache"
        self.cache.mkdir()
        self.payloads = {}
        self.releases = {}
        self.catalogs = {}
        self.requests = []
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode="w:gz") as archive:
            info = tarfile.TarInfo("README")
            info.size = 4
            archive.addfile(info, io.BytesIO(b"test"))
        package = stream.getvalue()
        for repo, identity in (("mgu-store", "mgu-deploy"), ("idrive-apps", "map")):
            commit = ("a" if repo == "mgu-store" else "b") * 40
            artifact_url = "https://github.com/robertnisipeanu/" + repo + "/releases/download/v1/pkg.tgz"
            self.payloads[artifact_url] = package
            catalog = {"schema": 2, "commit": commit, "components": [{
                "id": identity, "version": "1.0.0", "kind": "tool", "icon": identity + ".png",
                "requires": {} if repo == "mgu-store" else {"mgu-deploy": "1.0.0"},
                "artifact": {"url": artifact_url, "name": identity + ".tgz",
                             "sha256": hashlib.sha256(package).hexdigest(), "size": len(package)}}]}
            self.catalogs[repo] = catalog
            assets = []
            for name, data in (("catalog.json", json.dumps(catalog).encode()), (identity + ".png", png())):
                url = "https://github.com/robertnisipeanu/" + repo + "/releases/download/catalog/" + name
                self.payloads[url] = data
                assets.append({"name": name, "state": "uploaded", "size": len(data),
                               "digest": "sha256:" + hashlib.sha256(data).hexdigest(),
                               "browser_download_url": url})
            self.releases[repo] = {"assets": assets}
            source = "https://raw.githubusercontent.com/robertnisipeanu/" + repo + "/" + commit + "/"
            for name in ("README.md", "LICENSE"):
                self.payloads[source + name] = b"test fixture"
            self.payloads[source + "deploy/mgu-install.js"] = b"// supports --from <folder>"
            stream = io.BytesIO()
            with zipfile.ZipFile(stream, "w") as archive:
                archive.writestr(repo + "-" + commit + "/README.md", "fixture")
            self.payloads["https://codeload.github.com/robertnisipeanu/" + repo + "/zip/" + commit] = stream.getvalue()
        self.mock = patch.object(M, "download", side_effect=self.download)
        self.mock.start()
        self.addCleanup(self.mock.stop)

    def download(self, url, destination, size=None, sha256=None, **kwargs):
        self.requests.append(url)
        if url.startswith("https://api.github.com/"):
            repo = url.split("/")[5]
            data = json.dumps(self.releases[repo]).encode()
        else:
            data = self.payloads[url]
        if size is not None and (size != len(data) or hashlib.sha256(data).hexdigest() != sha256):
            raise ValueError("Size/SHA-256 mismatch")
        destination = pathlib.Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)

    def prepare(self):
        output = self.root / "upload"
        upstream = {r: P.upstream_catalog(r, self.cache) for r in P.REPOS}
        P.prepare(output, self.cache, upstream=upstream)
        return output, upstream

    def test_complete_icon_snapshot_has_no_runtime_external_urls(self):
        output, upstream = self.prepare()
        manifest, catalogs = M.verify_bundle(output)
        self.assertTrue(S.same_catalogs(output, upstream))
        inventory = {e["path"]: e for e in manifest["files"]}
        for repo, catalog in zip(P.REPOS, catalogs):
            original = self.catalogs[repo]["components"][0]
            actual = catalog["components"][0]
            self.assertEqual(actual["requires"], original["requires"])
            self.assertEqual(actual["version"], original["version"])
            icon = repo + "/" + actual["icon"]
            self.assertIn(icon, inventory)
            self.assertEqual((output / icon).read_bytes(), png())
            self.assertNotIn("https:", actual["icon"])
            self.assertTrue(S.immutable(icon))
        self.assertEqual(sum("/releases/tags/catalog" in u for u in self.requests), 2)

    def test_changed_icon_digest_invalidates_unchanged_catalog(self):
        output, upstream = self.prepare()
        changed = copy.deepcopy(upstream)
        changed["mgu-store"][2]["mgu-deploy.png"]["sha256"] = "c" * 64
        self.assertFalse(S.same_catalogs(output, changed))

    def test_missing_or_untrusted_icon_metadata_is_rejected(self):
        original = copy.deepcopy(self.releases["mgu-store"]["assets"])
        for alteration in ("missing", "digest", "host", "size", "duplicate"):
            self.releases["mgu-store"]["assets"] = copy.deepcopy(original)
            assets = self.releases["mgu-store"]["assets"]
            if alteration == "missing":
                assets.pop()
            elif alteration == "duplicate":
                assets.append(copy.deepcopy(assets[-1]))
            elif alteration == "digest":
                assets[-1].pop("digest")
            elif alteration == "host":
                assets[-1]["browser_download_url"] = "https://untrusted.invalid/icon.png"
            else:
                assets[-1]["size"] = M.MAX_ICON + 1
            with self.subTest(alteration=alteration), self.assertRaises(ValueError):
                P.upstream_catalog("mgu-store", self.cache)

    def test_corrupt_icon_or_catalog_digest_stops_preparation(self):
        for name in ("mgu-deploy.png", "catalog.json"):
            url = "https://github.com/robertnisipeanu/mgu-store/releases/download/catalog/" + name
            original = self.payloads[url]
            self.payloads[url] = b"tampered"
            with self.subTest(asset=name), self.assertRaisesRegex(ValueError, "mismatch"):
                self.prepare()
            self.assertFalse((self.root / "upload").exists())
            self.payloads[url] = original

    def test_png_type_dimensions_crc_and_truncation(self):
        p = self.root / "icon.png"
        p.write_bytes(png())
        M.verify_png(p)
        for data in (b"<svg/>", png(4096), png()[:-1], png()[:-5] + b"xxxxx"):
            p.write_bytes(data)
            with self.assertRaises(ValueError):
                M.verify_png(p)
        for name in ("../x.png", "/x.png", "https://host/x.png", "x.svg", "x%2epng"):
            with self.assertRaises(ValueError):
                M.icon_path(name, "a" * 64)

    def test_missing_icon_manifest_and_external_icon_fail_local_acceptance(self):
        output, _ = self.prepare()
        manifest = M.load_json(output / "mirror-manifest.json")
        original = copy.deepcopy(manifest)
        manifest["files"] = [e for e in manifest["files"] if "/icons/" not in e["path"]]
        M.write_json(output / "mirror-manifest.json", manifest)
        with self.assertRaisesRegex(ValueError, "absent from manifest"):
            M.verify_bundle(output)
        catalog_path = output / "mgu-store/catalog.json"
        catalog = M.load_json(catalog_path)
        catalog["components"][0]["icon"] = "https://github.com/icon.png"
        M.write_json(catalog_path, catalog)
        entry = next(e for e in original["files"] if e["path"] == "mgu-store/catalog.json")
        entry.update(size=catalog_path.stat().st_size, sha256=M.digest(catalog_path))
        M.write_json(output / "mirror-manifest.json", original)
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            M.verify_bundle(output)


if __name__ == "__main__":
    unittest.main()
