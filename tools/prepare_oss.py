#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Prepare a complete, verified static OSS upload tree from public releases."""

import argparse
import copy
import datetime
import importlib.util
import json
import pathlib
import re
import shutil
import tarfile
import tempfile
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "mirror", ROOT / "skills/mgu-setup/scripts/mirror_resources.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
REPOS = ("mgu-store", "idrive-apps")


def release_asset(repo, release, name, maximum):
    matches = [a for a in release.get("assets", []) if a.get("name") == name]
    if len(matches) != 1:
        raise ValueError("Expected one published release asset: " + name)
    asset = matches[0]
    size, digest = asset.get("size"), asset.get("digest", "")
    url = ("https://github.com/robertnisipeanu/" + repo
           + "/releases/download/catalog/" + name)
    if (asset.get("state") != "uploaded" or asset.get("browser_download_url") != url
            or not isinstance(size, int) or isinstance(size, bool) or not 0 < size <= maximum
            or not re.fullmatch(r"sha256:[a-f0-9]{64}", digest)):
        raise ValueError("Invalid official release asset metadata: " + name)
    return {"url": url, "size": size, "sha256": digest[7:]}


def upstream_catalog(repo, cache):
    if repo not in REPOS:
        raise ValueError("Unsupported upstream repository")
    metadata = cache / (repo + "-release.json")
    M.download("https://api.github.com/repos/robertnisipeanu/" + repo
               + "/releases/tags/catalog", metadata, accept="application/vnd.github+json")
    release = M.load_json(metadata)
    asset = release_asset(repo, release, "catalog.json", M.MAX_FILE)
    path = cache / (repo + "-catalog.json")
    M.download(asset["url"], path, asset["size"], asset["sha256"])
    catalog = M.validate_catalog(M.load_json(path))
    icons = {}
    for entry in catalog["components"]:
        name = entry.get("icon")
        if name:
            M.icon_path(name, "0" * 64)
            icons[name] = release_asset(repo, release, name, M.MAX_ICON)
    return catalog, path, icons


def rewrite_catalog(catalog, icons):
    rewritten = copy.deepcopy(catalog)
    for entry in rewritten["components"]:
        artifact = entry["artifact"]
        artifact["url"] = "packages/" + artifact["sha256"] + "/" + artifact["name"]
        if entry.get("icon"):
            name = entry["icon"]
            entry["icon"] = M.icon_path(name, icons[name]["sha256"])
    return rewritten


def inspect_archive(path):
    with tarfile.open(path, "r:gz") as archive:
        for member in archive:
            name = pathlib.PurePosixPath(member.name)
            if name.is_absolute() or ".." in name.parts:
                raise ValueError("Unsafe archive member: " + member.name)
            if "oap-sdk" in name.parts or name.parts[-2:] == ("javascript", "app.js"):
                raise ValueError("Refusing a bundled SDK or built BMW-linked app: " + member.name)


def prepare(output, cache, upstream=None):
    if output.exists():
        raise ValueError("Use a new output folder; existing snapshots are never overwritten")
    cache.mkdir(parents=True, exist_ok=True)
    originals = upstream if upstream is not None else {
        repo: upstream_catalog(repo, cache) for repo in REPOS}
    M.verify_dependencies([c for c, _, _ in originals.values()])
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = pathlib.Path(tempfile.mkdtemp(prefix=".mgu-oss-", dir=output.parent))
    try:
        provenance = {}
        for repo, (catalog, raw, icons) in originals.items():
            commit = catalog.get("commit", "")
            if not re.fullmatch(r"[a-f0-9]{40}", commit):
                raise ValueError("Published catalog must identify a source commit")
            provenance[repo] = {"upstream": "https://github.com/robertnisipeanu/" + repo,
                                "commit": commit, "catalog_sha256": M.digest(raw),
                                "icons": {}}
            destination = staging / repo
            destination.mkdir()
            shutil.copyfile(raw, destination / "upstream-catalog.json")
            rewritten = rewrite_catalog(catalog, icons)
            for entry in catalog["components"]:
                artifact = entry["artifact"]
                name = artifact["name"]
                rel = "packages/" + artifact["sha256"] + "/" + name
                cached = cache / "packages" / artifact["sha256"] / name
                print("{} {} {}".format(repo, entry["id"], entry["version"]), flush=True)
                M.download(artifact["url"], cached, artifact["size"], artifact["sha256"])
                inspect_archive(cached)
                target = destination / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(cached, target)
            for name, asset in icons.items():
                rel = M.icon_path(name, asset["sha256"])
                cached = cache / rel
                M.download(asset["url"], cached, asset["size"], asset["sha256"])
                M.verify_png(cached)
                target = destination / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(cached, target)
                provenance[repo]["icons"][name] = dict(asset, path=rel)
            M.write_json(destination / "catalog.json", rewritten)
            source = "https://raw.githubusercontent.com/robertnisipeanu/{}/{}/".format(repo, commit)
            for name in ("LICENSE", "README.md"):
                M.download(source + name, destination / name)
            archive = cache / (repo + "-" + commit + ".zip")
            M.download("https://codeload.github.com/robertnisipeanu/{}/zip/{}".format(repo, commit), archive)
            with zipfile.ZipFile(archive) as package:
                if package.testzip() is not None:
                    raise ValueError("Corrupt source ZIP")
                if any("oap-sdk" in pathlib.PurePosixPath(n).parts for n in package.namelist()):
                    raise ValueError("Refusing SDK in source archive")
            source_dest = destination / "source" / (commit + ".zip")
            source_dest.parent.mkdir()
            shutil.copyfile(archive, source_dest)
            if repo == "mgu-store":
                installer = staging / "bootstrap/mgu-install.js"
                M.download(source + "deploy/mgu-install.js", installer)
                if "--from <folder>" not in installer.read_text(encoding="utf-8"):
                    raise ValueError("Upstream installer lacks offline first-install support")
        (staging / "NOTICE.txt").write_text(
            "Community distribution mirror maintained by Wallezy.\n"
            "Packages and icons are byte-for-byte upstream assets; catalogs change artifact and icon URLs only.\n"
            "Original authors, licenses and version/dependency fields are retained.\n"
            "Upstream source archives and LICENSE files are provided beside each catalog.\n"
            "See package notices for third-party licensing/build dependencies.\n"
            "This tree contains no SSH root credentials or vehicle firmware assets.\n"
            "A verified download does not certify vehicle compatibility or installation.\n",
            encoding="utf-8")
        files = [{"path": p.relative_to(staging).as_posix(), "size": p.stat().st_size,
                  "sha256": M.digest(p)}
                 for p in sorted(staging.rglob("*")) if p.is_file()]
        manifest = {"schema": 1, "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "repositories": provenance, "files": files}
        M.write_json(staging / "mirror-manifest.json", manifest)
        M.verify_bundle(staging)
        staging.rename(output)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    print("Verified upload tree: " + str(output), flush=True)
    print("Manifest SHA-256: " + M.digest(output / "mirror-manifest.json"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=pathlib.Path, required=True,
                        help="New folder outside this repository")
    parser.add_argument("--cache", type=pathlib.Path, required=True)
    args = parser.parse_args()
    output, cache = args.output.resolve(), args.cache.resolve()
    if output == ROOT or ROOT in output.parents or cache == ROOT or ROOT in cache.parents:
        parser.error("Keep upload trees and download caches outside the source repository")
    try:
        prepare(output, cache)
    except (OSError, ValueError, KeyError, StopIteration, RuntimeError, tarfile.TarError,
            zipfile.BadZipFile) as error:
        parser.exit(1, "Mirror preparation stopped: {}\n".format(error))


if __name__ == "__main__":
    main()
