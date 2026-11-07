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


def upstream_catalog(repo, cache):
    metadata = cache / (repo + "-release.json")
    M.download("https://api.github.com/repos/robertnisipeanu/" + repo
               + "/releases/tags/catalog", metadata, accept="application/vnd.github+json")
    assets = M.load_json(metadata).get("assets", [])
    asset = next(a for a in assets if a["name"] == "catalog.json")
    path = cache / (repo + "-catalog.json")
    M.download(asset["url"], path, accept="application/octet-stream")
    return M.validate_catalog(M.load_json(path)), path


def inspect_archive(path):
    with tarfile.open(path, "r:gz") as archive:
        for member in archive:
            name = pathlib.PurePosixPath(member.name)
            if name.is_absolute() or ".." in name.parts:
                raise ValueError("Unsafe archive member: " + member.name)
            if "oap-sdk" in name.parts or name.parts[-2:] == ("javascript", "app.js"):
                raise ValueError("Refusing a bundled SDK or built BMW-linked app: " + member.name)


def prepare(output, cache):
    if output.exists():
        raise ValueError("Use a new output folder; existing snapshots are never overwritten")
    cache.mkdir(parents=True, exist_ok=True)
    originals = {}
    for repo in REPOS:
        originals[repo] = upstream_catalog(repo, cache)
    M.verify_dependencies([c for c, _ in originals.values()])
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = pathlib.Path(tempfile.mkdtemp(prefix=".mgu-oss-", dir=output.parent))
    try:
        provenance = {}
        for repo, (catalog, raw) in originals.items():
            commit = catalog.get("commit", "")
            if not re.fullmatch(r"[a-f0-9]{40}", commit):
                raise ValueError("Published catalog must identify a source commit")
            provenance[repo] = {"upstream": "https://github.com/robertnisipeanu/" + repo,
                                "commit": commit, "catalog_sha256": M.digest(raw)}
            destination = staging / repo
            destination.mkdir()
            shutil.copyfile(raw, destination / "upstream-catalog.json")
            rewritten = copy.deepcopy(catalog)
            for entry in rewritten["components"]:
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
                artifact["url"] = rel
                if entry.get("icon"):
                    raise ValueError("New external icon field needs explicit mirroring before publishing")
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
            "Installation packages are byte-for-byte upstream releases; catalogs change artifact URLs only.\n"
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
