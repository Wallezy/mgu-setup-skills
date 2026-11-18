#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Publish the official mirror directly to verified self-hosted origins."""
import argparse
import datetime
import json
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import prepare_oss as P
import publication_transport as T
M = P.M
BASE = "https://mgu.walle.pw/mgu/"


def catalogs_match(root, upstream):
    return all(
        M.digest(root / repo / "upstream-catalog.json") == M.digest(raw)
        and M.load_json(root / repo / "catalog.json") == P.rewrite_catalog(catalog, icons)
        for repo, (catalog, raw, icons) in upstream.items()
    )


def synchronize(args, work):
    tx = T.Transaction("mgu/", work)
    prior = work / "live-before"
    expected = tx.files["mgu/mirror-manifest.json"]["sha256"]
    M.fetch_remote(BASE, prior, manifest_sha256=expected)
    old, _ = M.verify_bundle(prior)
    upstream = {repo: P.upstream_catalog(repo, args.cache) for repo in P.REPOS}
    M.verify_dependencies([catalog for catalog, _, _ in upstream.values()])
    if catalogs_match(prior, upstream):
        prepared = prior
    elif args.prepared:
        prepared = args.prepared
        M.verify_bundle(prepared)
        if not catalogs_match(prepared, upstream):
            raise ValueError("Prepared snapshot differs from current official catalogs")
    else:
        prepared = work / "mirror-snapshot"
        P.prepare(prepared, args.cache, upstream=upstream)
    manifest, _ = M.verify_bundle(prepared)
    old_files = {e["path"]: e for e in old["files"]}
    changed = []
    for entry in manifest["files"]:
        if old_files.get(entry["path"]) != entry:
            tx.put(entry["path"], prepared)
            changed.append(entry["path"])
    tx.put("mirror-manifest.json", prepared)
    result = {
        "status": "prepared", "backend": "self-hosted", "oss_used": False,
        "manifest_sha256": M.digest(prepared / "mirror-manifest.json"),
        "changes": changed, "remote_verified": False,
        "versions": {repo: {c["id"]: c["version"] for c in
                           M.load_json(prepared / repo / "catalog.json")["components"]}
                     for repo in P.REPOS},
    }
    M.write_json(work / "plan.json", result)
    if args.publish:
        result["status"] = "published" if changed else "unchanged"
        result = T.replicate(result, work, tx)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", required=True, type=pathlib.Path)
    parser.add_argument("--cache", required=True, type=pathlib.Path)
    parser.add_argument("--prepared", type=pathlib.Path)
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    if not T.self_hosted():
        parser.error("Enable the private self-hosted publication transport first")
    repo = pathlib.Path(__file__).resolve().parents[1]
    for key in ("work_dir", "cache", "prepared"):
        value = getattr(args, key)
        if value is None:
            continue
        value = value.expanduser().resolve()
        if value == repo or repo in value.parents:
            parser.error("Generated publication resources belong outside this repository")
        setattr(args, key, value)
    args.work_dir.mkdir(parents=True, exist_ok=True)
    args.cache.mkdir(parents=True, exist_ok=True)
    work = pathlib.Path(tempfile.mkdtemp(prefix=datetime.datetime.now(
        datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ-"), dir=args.work_dir))
    try:
        with T.lock(True):
            result = synchronize(args, work)
        M.write_json(work / "result.json", result)
        M.write_json(args.work_dir / ("latest-success.json" if args.publish else "latest-prepared.json"),
                     dict(result, work_dir=str(work)))
        print(json.dumps({"status": result["status"], "result": str(work / "result.json")}))
    except (OSError, ValueError, RuntimeError) as error:
        if not (work / "result.json").exists():
            M.write_json(work / "result.json", {"status": "failed", "error": str(error)})
        parser.exit(1, "Self-hosted mirror stopped: " + str(error) + "\n")


if __name__ == "__main__":
    main()
