#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Configure and verify HTTPS mirror resources locally; never contact a car."""

import argparse
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile
import urllib.parse

CONFIG = pathlib.Path(__file__).resolve().parents[1] / "references/network-sources.json"
MAX_FILE = 512 << 20


def load_json(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def https_url(value):
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Use an absolute HTTPS URL without credentials")
    if parsed.query or parsed.fragment:
        raise ValueError("Use a stable URL without a query or fragment")
    return value.rstrip("/") + "/"


def relative_path(value):
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("Invalid relative resource path")
    path = pathlib.PurePosixPath(value)
    if (path.is_absolute() or any(p in ("", ".", "..") for p in value.split("/"))
            or any(c in value for c in ":?#%")):
        raise ValueError("Unsafe relative resource path: " + value)
    return path


def digest(path):
    result = hashlib.sha256()
    with pathlib.Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def checked(path, size, sha256):
    if not isinstance(size, int) or isinstance(size, bool) or not 0 < size <= MAX_FILE:
        raise ValueError("Invalid resource size")
    if not isinstance(sha256, str) or not re.fullmatch(r"[a-f0-9]{64}", sha256):
        raise ValueError("Invalid SHA-256")
    return pathlib.Path(path).is_file() and pathlib.Path(path).stat().st_size == size and digest(path) == sha256


def download(url, destination, size=None, sha256=None, accept=None):
    # Curl uses the platform certificate store; TLS verification stays enabled.
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.username or parsed.password or not parsed.hostname:
        raise ValueError("HTTPS downloads without embedded credentials only")
    destination = pathlib.Path(destination)
    if size is not None and sha256 is not None and checked(destination, size, sha256):
        return
    if not shutil.which("curl"):
        raise RuntimeError("curl is required for HTTPS resource downloads")
    destination.parent.mkdir(parents=True, exist_ok=True)
    part = destination.with_name(destination.name + ".part")
    if destination.is_symlink() or part.is_symlink():
        raise ValueError("Refusing a symlink destination")
    command = ["curl", "--fail", "--location", "--silent", "--show-error",
               "--proto", "=https", "--proto-redir", "=https",
               "--connect-timeout", "15", "--max-time", "180",
               "--retry", "2", "--max-filesize", str(size or MAX_FILE)]
    if accept:
        command += ["--header", "Accept: " + accept]
    command += ["--output", str(part), url]
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError("Download failed: " + result.stderr.strip()[-500:])
        if size is not None and sha256 is not None and not checked(part, size, sha256):
            raise ValueError("Size/SHA-256 mismatch: " + destination.name)
        if part.stat().st_size > MAX_FILE:
            raise ValueError("Download exceeds size limit")
        part.replace(destination)
    finally:
        part.unlink(missing_ok=True)


def validate_catalog(catalog):
    if catalog.get("schema") not in (1, 2) or not isinstance(catalog.get("components"), list):
        raise ValueError("Unsupported catalog")
    seen = set()
    for entry in catalog["components"]:
        identity = entry.get("id", "")
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", identity) or identity in seen:
            raise ValueError("Invalid/duplicate component id")
        seen.add(identity)
        if not re.fullmatch(r"\d+\.\d+\.\d+", entry.get("version", "")):
            raise ValueError("Invalid version: " + identity)
        artifact = entry["artifact"]
        name = relative_path(artifact["name"])
        if len(name.parts) != 1:
            raise ValueError("Artifact name must be a filename")
        if not isinstance(artifact.get("size"), int) or not 0 < artifact["size"] <= MAX_FILE:
            raise ValueError("Invalid artifact size")
        if not re.fullmatch(r"[a-f0-9]{64}", artifact.get("sha256", "")):
            raise ValueError("Missing upstream SHA-256: " + identity)
    return catalog


def verify_dependencies(catalogs):
    entries = {}
    for catalog in catalogs:
        for entry in catalog["components"]:
            if entry["id"] in entries:
                raise ValueError("Duplicate component across catalogs: " + entry["id"])
            entries[entry["id"]] = entry
    for entry in entries.values():
        for identity, minimum in entry.get("requires", {}).items():
            partner = entries.get(identity)
            version = lambda v: tuple(int(n) for n in v.split("."))
            if partner is None or version(partner["version"]) < version(minimum):
                raise ValueError("Unmet dependency: {} requires {} >= {}".format(entry["id"], identity, minimum))
    return entries


def verify_bundle(root):
    root = pathlib.Path(root)
    manifest = load_json(root / "mirror-manifest.json")
    if manifest.get("schema") != 1 or not isinstance(manifest.get("files"), list):
        raise ValueError("Unsupported mirror manifest")
    inventory = {}
    for entry in manifest["files"]:
        rel = str(relative_path(entry["path"]))
        if rel in inventory:
            raise ValueError("Duplicate file: " + rel)
        inventory[rel] = entry
        if not checked(root / rel, entry["size"], entry["sha256"]):
            raise ValueError("Missing/corrupt resource: " + rel)
    catalogs = []
    for repo in ("mgu-store", "idrive-apps"):
        catalog_name = repo + "/catalog.json"
        if catalog_name not in inventory:
            raise ValueError("Catalog absent from manifest")
        catalog = validate_catalog(load_json(root / catalog_name))
        catalogs.append(catalog)
        for component in catalog["components"]:
            artifact = component["artifact"]
            rel = repo + "/" + str(relative_path(artifact.get("url", artifact["name"])))
            if rel not in inventory or not checked(root / rel, artifact["size"], artifact["sha256"]):
                raise ValueError("Catalog artifact mismatch: " + rel)
    verify_dependencies(catalogs)
    if "bootstrap/mgu-install.js" not in inventory:
        raise ValueError("Missing upstream installer")
    return manifest, catalogs


def assert_plan_matches(catalogs, plan):
    entries = verify_dependencies(catalogs)
    for identity, expected in plan.get("components", {}).items():
        entry = entries.get(identity)
        if (entry is None or entry["version"] != expected["version"]
                or entry["artifact"]["sha256"] != expected["sha256"]):
            raise ValueError("Selected version/hash changed: " + identity)


def fetch_remote(base, output, manifest_sha256=None, plan=None):
    base = https_url(base)
    output = pathlib.Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="mgu-mirror-index-") as temporary:
        index = pathlib.Path(temporary) / "manifest.json"
        download(base + "mirror-manifest.json", index)
        if manifest_sha256 and digest(index) != manifest_sha256:
            raise ValueError("Mirror manifest differs from the locally prepared snapshot")
        manifest = load_json(index)
        if manifest.get("schema") != 1:
            raise ValueError("Unsupported mirror manifest")
        # Check pinned selections before downloading the rest of the snapshot.
        if plan is not None:
            catalogs = []
            for repo in ("mgu-store", "idrive-apps"):
                rel = repo + "/catalog.json"
                entry = next(f for f in manifest["files"] if f["path"] == rel)
                local = pathlib.Path(temporary) / (repo + ".json")
                download(base + rel, local, entry["size"], entry["sha256"])
                catalogs.append(validate_catalog(load_json(local)))
            assert_plan_matches(catalogs, plan)
        for entry in manifest["files"]:
            rel = str(relative_path(entry["path"]))
            target = output / rel
            if output not in target.resolve().parents:
                raise ValueError("Resource escapes output folder")
            print("Verify/download " + rel, flush=True)
            download(base + urllib.parse.quote(rel, safe="/@"), target,
                     entry["size"], entry["sha256"])
        # Publish the local index only after the download set is complete.
        shutil.copyfile(index, output / "mirror-manifest.json")
    verify_bundle(output)
    return output


def source_order(preference):
    if preference not in ("auto", "upstream-first", "domestic-first"):
        raise ValueError("Unknown source preference")
    return ["domestic", "upstream"] if preference == "domestic-first" else ["upstream", "domestic"]


def plan_sources(config, preference=None):
    """Probe catalogs only. Artifact verification remains a separate prerequisite."""
    attempts = []
    with tempfile.TemporaryDirectory(prefix="mgu-source-check-") as directory:
        root = pathlib.Path(directory)
        for source in source_order(preference or config.get("preference", "auto")):
            try:
                catalogs, urls = [], []
                if source == "domestic":
                    base = config.get("oss_base_url")
                    if not base:
                        raise ValueError("OSS URL has not been configured")
                    base = https_url(base)
                    index = root / "mirror-manifest.json"
                    download(base + "mirror-manifest.json", index)
                    manifest = load_json(index)
                    if manifest.get("schema") != 1:
                        raise ValueError("Invalid mirror manifest")
                    indexed = {f["path"]: f for f in manifest["files"]}
                    for repo in ("mgu-store", "idrive-apps"):
                        rel = repo + "/catalog.json"
                        entry = indexed[rel]
                        url = base + rel
                        local = root / (repo + ".json")
                        download(url, local, entry["size"], entry["sha256"])
                        catalogs.append(validate_catalog(load_json(local)))
                        urls.append(url)
                else:
                    for repo in ("mgu-store", "idrive-apps"):
                        release = root / (repo + "-release.json")
                        download("https://api.github.com/repos/robertnisipeanu/" + repo
                                 + "/releases/tags/catalog", release,
                                 accept="application/vnd.github+json")
                        asset = next(a for a in load_json(release)["assets"] if a["name"] == "catalog.json")
                        local = root / (repo + ".json")
                        download(asset["url"], local, accept="application/octet-stream")
                        catalogs.append(validate_catalog(load_json(local)))
                        urls.append(asset["browser_download_url"])
                entries = verify_dependencies(catalogs)
                return {"selected_source": source, "preference": preference or config.get("preference", "auto"),
                        "catalog_urls": urls, "failed_attempts": attempts,
                        "verification": "Catalogs only; verify all selected packages before vehicle writes.",
                        "components": {k: {"version": v["version"], "sha256": v["artifact"]["sha256"]}
                                       for k, v in entries.items()}}
            except (OSError, ValueError, KeyError, StopIteration, TypeError, RuntimeError) as error:
                attempts.append({"source": source, "reason": str(error)})
    raise ValueError("No usable source catalog: " + json.dumps(attempts, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    configure = sub.add_parser("configure", help="Set a stable domestic HTTPS base URL")
    configure.add_argument("--base-url", required=True)
    configure.add_argument("--config", type=pathlib.Path, default=CONFIG)
    configure.add_argument("--preference", choices=("auto", "upstream-first", "domestic-first"))
    plan = sub.add_parser("plan", help="Resolve preferred source and lock catalog versions; no installation")
    plan.add_argument("--config", type=pathlib.Path, default=CONFIG)
    plan.add_argument("--preference", choices=("auto", "upstream-first", "domestic-first"))
    plan.add_argument("--output", type=pathlib.Path, required=True)
    verify = sub.add_parser("verify", help="Verify a local complete mirror snapshot")
    verify.add_argument("directory", type=pathlib.Path)
    fetch = sub.add_parser("fetch", help="Download and verify an entire mirror snapshot; no installation")
    fetch.add_argument("--base-url")
    fetch.add_argument("--config", type=pathlib.Path, default=CONFIG)
    fetch.add_argument("--output", type=pathlib.Path, required=True)
    fetch.add_argument("--manifest-sha256", help="Pin a known snapshot for upload acceptance")
    fetch.add_argument("--plan", type=pathlib.Path, help="Require the versions/hashes in a saved source plan")
    args = parser.parse_args()
    try:
        if args.command == "configure":
            config = load_json(args.config)
            config["oss_base_url"] = https_url(args.base_url)
            if args.preference:
                config["preference"] = args.preference
            write_json(args.config, config)
            print("Configured domestic mirror: " + config["oss_base_url"])
        elif args.command == "plan":
            report = plan_sources(load_json(args.config), args.preference)
            write_json(args.output, report)
            print("Selected {}; recorded catalog versions in {}. Packages not verified.".format(
                report["selected_source"], args.output))
        elif args.command == "verify":
            manifest, catalogs = verify_bundle(args.directory)
            print("Verified {} files / {} components; vehicle not checked.".format(
                len(manifest["files"]), sum(len(c["components"]) for c in catalogs)))
        else:
            base = args.base_url or load_json(args.config).get("oss_base_url")
            if not base:
                raise ValueError("OSS base URL is not configured; do not substitute an unverified source")
            path = fetch_remote(base, args.output, args.manifest_sha256,
                                load_json(args.plan) if args.plan else None)
            print("Verified local resources: {}; not installed or vehicle-ready.".format(path))
    except (OSError, ValueError, KeyError, StopIteration, TypeError, RuntimeError) as error:
        parser.exit(1, "Resource preparation stopped: {}\n".format(error))


if __name__ == "__main__":
    main()
