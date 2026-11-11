#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Publish verified upstream snapshots with ossutil; never delete old objects."""

import argparse
import contextlib
import datetime
import importlib.util
import json
import os
import pathlib
import re
import subprocess
import tempfile
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("prepare_oss", ROOT / "tools/prepare_oss.py")
P = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P)
M = P.M
CUSTOM_TARGETS = {
    "https://mgu.walle.pw/mgu/": ("oss://walle-mgu/mgu/", "cn-hangzhou"),
}


def validate_target(destination, base):
    base = M.https_url(base)
    target = urllib.parse.urlsplit(destination)
    public = urllib.parse.urlsplit(base)
    if (target.scheme != "oss" or not target.netloc or target.query or target.fragment
            or target.username or target.password):
        raise ValueError("Use oss://bucket/prefix as destination")
    prefix = target.path.strip("/")
    M.relative_path(prefix)
    expected = re.fullmatch(re.escape(target.netloc) + r"\.oss-[a-z0-9-]+\.aliyuncs\.com",
                            public.hostname or "")
    custom = CUSTOM_TARGETS.get(base)
    if custom and custom[0] != destination.rstrip("/") + "/":
        raise ValueError("Custom domain does not match its configured OSS destination")
    if (not expected and not custom) or public.port or public.path != "/" + prefix + "/":
        raise ValueError("Public OSS URL must match the destination bucket and prefix")
    return destination.rstrip("/") + "/", base


def target_region(destination, base):
    _, base = validate_target(destination, base)
    if base in CUSTOM_TARGETS:
        return CUSTOM_TARGETS[base][1]
    return re.search(r"\.oss-([a-z0-9-]+)\.aliyuncs\.com", urllib.parse.urlsplit(base).hostname)[1]


def immutable(rel):
    parts = pathlib.PurePosixPath(rel).parts
    return (len(parts) == 4 and parts[0] in P.REPOS and parts[1] in ("packages", "icons")
            and re.fullmatch(r"[a-f0-9]{64}", parts[2])) or (
        len(parts) == 3 and parts[0] in P.REPOS and parts[1] == "source"
        and re.fullmatch(r"[a-f0-9]{40}\.zip", parts[2]))


def cache_control(rel):
    return "public, max-age=31536000, immutable" if immutable(rel) else "no-cache"


def no_cache(headers):
    return "no-cache" in [v.strip().lower() for v in headers.get("cache-control", "").split(",")]


def headers_match(rel, headers):
    directives = {v.strip().lower() for v in headers.get("cache-control", "").split(",")}
    if immutable(rel):
        cache_ok = ({"public", "max-age=31536000", "immutable"} <= directives
                    and not directives.intersection({"no-cache", "no-store", "private"}))
    else:
        cache_ok = no_cache(headers)
    return cache_ok and (not rel.endswith(".png")
                         or headers.get("content-type", "").split(";", 1)[0].strip().lower() == "image/png")


def same_catalogs(local, upstream):
    for repo, (catalog, raw, icons) in upstream.items():
        if M.digest(local / repo / "upstream-catalog.json") != M.digest(raw):
            return False
        mirrored = M.load_json(local / repo / "catalog.json")
        expected = P.rewrite_catalog(catalog, icons)
        if mirrored != expected:
            return False
    return True


def versions(root):
    return {repo: {c["id"]: c["version"] for c in M.load_json(root / repo / "catalog.json")["components"]}
            for repo in P.REPOS}


def upload_plan(old, new, header_repairs=()):
    prior = {f["path"]: f for f in old["files"]}
    current = {f["path"] for f in new["files"]}
    plan = []
    for entry in new["files"]:
        rel = str(M.relative_path(entry["path"]))
        if rel in prior and immutable(rel) and prior[rel] != entry:
            raise ValueError("Refusing replacement of immutable resource: " + rel)
        if prior.get(rel) != entry or rel in header_repairs:
            plan.append(dict(entry, phase="resources" if immutable(rel) else "metadata"))
    for rel in header_repairs:
        if rel not in current and rel in prior and immutable(rel):
            plan.append(dict(prior[rel], phase="resources", historical=True))
    return sorted(plan, key=lambda e: (e["phase"] != "resources", e["path"]))


@contextlib.contextmanager
def lock(directory):
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / ".sync.lock"
    fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(fd, "w") as out:
            out.write(str(os.getpid()) + "\n")
        yield
    finally:
        path.unlink()


class Remote:
    def __init__(self, cli, config, destination, base, work):
        self.cli, self.config = cli, config
        self.destination, self.base = validate_target(destination, base)
        self.region = target_region(destination, base)
        self.work = work

    def cli_options(self):
        # ossutil 2.2.0 can panic with zero attempts; explicitly request one.
        return ["--config-file", str(self.config), "--region", self.region,
                "--endpoint", "https://oss-" + self.region + ".aliyuncs.com",
                "--retry-times", "1"]

    def verify_binding(self):
        if self.base not in CUSTOM_TARGETS:
            return
        bucket = urllib.parse.urlsplit(self.destination).netloc
        result = subprocess.run(
            [str(self.cli), "api", "list-cname", "--bucket", bucket,
             "--output-format", "json"] + self.cli_options(),
            capture_output=True, text=True, timeout=60)
        if result.returncode:
            raise RuntimeError("Cannot verify custom domain binding on destination bucket")
        record = json.JSONDecoder().raw_decode(result.stdout.lstrip())[0]
        entries = record.get("Cname", [])
        if isinstance(entries, dict):
            entries = [entries]
        hostname = urllib.parse.urlsplit(self.base).hostname
        if record.get("Bucket") != bucket or not any(
                e.get("Domain") == hostname and e.get("Status") == "Enabled"
                and e.get("Certificate", {}).get("Status") == "Enabled"
                for e in entries):
            raise ValueError("Custom domain or HTTPS certificate is not enabled on destination bucket")

    def headers(self, rel):
        M.relative_path(rel)
        header_file = self.work / "response-headers.txt"
        result = subprocess.run(
            ["curl", "--fail", "--silent", "--show-error", "--head",
             "--proto", "=https", "--connect-timeout", "10", "--max-time", "30",
             "--dump-header", str(header_file), "--output", os.devnull,
             "--write-out", "%{http_code}", self.base + rel],
            capture_output=True, text=True, timeout=40)
        if result.returncode or result.stdout.strip() != "200":
            raise RuntimeError("Public HEAD failed: " + rel)
        return {k.lower(): v.strip() for line in header_file.read_text().splitlines()
                if ":" in line for k, v in [line.split(":", 1)]}

    def put(self, root, rel):
        M.relative_path(rel)
        content_type = ("application/json" if rel.endswith(".json") else
                        "text/plain; charset=utf-8" if rel.endswith((".md", ".txt")) else
                        "application/javascript" if rel.endswith(".js") else
                        "image/png" if rel.endswith(".png") else
                        "application/zip" if rel.endswith(".zip") else "application/gzip")
        result = subprocess.run(
            [str(self.cli), "cp", str(root / rel), self.destination + rel,
             "--force", "--no-progress",
             "--cache-control", cache_control(rel), "--content-type", content_type,
             "--output-dir", str(self.work / "ossutil-output")] + self.cli_options(),
            capture_output=True, text=True, timeout=300)
        if result.returncode:
            # Do not copy CLI diagnostics into public logs; they may contain signed URLs.
            raise RuntimeError("ossutil upload failed for {} (exit {})".format(rel, result.returncode))

    def verify(self, rel, entry, folder):
        M.download(self.base + rel, folder / rel, entry["size"], entry["sha256"])
        if not headers_match(rel, self.headers(rel)):
            raise RuntimeError("Unexpected public cache/content headers: " + rel)


def publish(remote, old_root, new_root, plan, work):
    old = {e["path"]: e for e in M.load_json(old_root / "mirror-manifest.json")["files"]}
    changed_fixed = []
    try:
        for entry in plan:
            if entry["phase"] != "resources":
                continue
            remote.put(old_root if entry.get("historical") else new_root, entry["path"])
            remote.verify(entry["path"], entry, work / "resource-check")
        # Reused resources were verified from live OSS before reaching this point.
        for entry in plan:
            if entry["phase"] != "metadata":
                continue
            changed_fixed.append(entry["path"])
            remote.put(new_root, entry["path"])
            remote.verify(entry["path"], entry, work / "metadata-check")
        changed_fixed.append("mirror-manifest.json")
        remote.put(new_root, "mirror-manifest.json")
        M.fetch_remote(remote.base, work / "remote-acceptance",
                       manifest_sha256=M.digest(new_root / "mirror-manifest.json"))
        manifest = M.load_json(new_root / "mirror-manifest.json")
        for rel in [e["path"] for e in manifest["files"]] + ["mirror-manifest.json"]:
            if not headers_match(rel, remote.headers(rel)):
                raise RuntimeError("Unexpected public cache/content headers: " + rel)
    except Exception as original:
        errors = []
        # Restore existing mutable objects and commit the prior manifest last.
        for rel in [p for p in changed_fixed if p != "mirror-manifest.json"]:
            if rel not in old:
                continue
            try:
                remote.put(old_root, rel)
                remote.verify(rel, old[rel], work / "rollback-check")
            except Exception:
                errors.append(rel)
        if changed_fixed:
            try:
                remote.put(old_root, "mirror-manifest.json")
                M.fetch_remote(remote.base, work / "rollback-acceptance",
                               manifest_sha256=M.digest(old_root / "mirror-manifest.json"))
            except Exception:
                errors.append("mirror-manifest.json or rollback acceptance")
        outcome = "previous snapshot restored" if changed_fixed and not errors else (
            "rollback incomplete: " + ", ".join(errors) if errors else "live indexes untouched")
        raise RuntimeError(str(original) + "; " + outcome) from original


def synchronize(args, work):
    destination, base = validate_target(args.destination, args.base_url)
    remote = Remote(args.ossutil, args.config, destination, base, work)
    remote.verify_binding()
    # Full public acceptance protects both delta reuse and a possible rollback.
    old_root = work / "live-before"
    M.fetch_remote(base, old_root)
    old, _ = M.verify_bundle(old_root)
    upstream = {repo: P.upstream_catalog(repo, args.cache) for repo in P.REPOS}
    M.verify_dependencies([c for c, _, _ in upstream.values()])
    repairs = [rel for rel in [f["path"] for f in old["files"]] + ["mirror-manifest.json"]
               if not headers_match(rel, remote.headers(rel))]
    if same_catalogs(old_root, upstream):
        if not repairs:
            return {"status": "unchanged", "manifest_sha256": M.digest(old_root / "mirror-manifest.json"),
                    "uploaded": [], "remote_verified": True, "versions": versions(old_root)}
        new_root = old_root
    elif args.prepared:
        new_root = args.prepared
        M.verify_bundle(new_root)
        if not same_catalogs(new_root, upstream):
            raise ValueError("Prepared snapshot no longer matches published upstream catalogs")
    else:
        new_root = work / "oss-upload"
        P.prepare(new_root, args.cache, upstream=upstream)
    new, _ = M.verify_bundle(new_root)
    plan = upload_plan(old, new, repairs)
    report = {"status": "prepared", "destination": destination,
              "manifest_sha256": M.digest(new_root / "mirror-manifest.json"),
              "changes": plan, "header_repairs": repairs,
              "versions": versions(new_root)}
    M.write_json(work / "plan.json", report)
    if args.publish:
        publish(remote, old_root, new_root, plan, work)
        report.update(status="published", remote_verified=True,
                      uploaded=[e["path"] for e in plan] + ["mirror-manifest.json"])
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ossutil", type=pathlib.Path, required=True)
    parser.add_argument("--config", type=pathlib.Path, required=True,
                        help="Private ossutil config outside this repository")
    parser.add_argument("--destination", required=True, help="oss://bucket/prefix")
    parser.add_argument("--base-url", required=True, help="Matching public OSS prefix or explicitly configured HTTPS domain")
    parser.add_argument("--work-dir", type=pathlib.Path, required=True)
    parser.add_argument("--cache", type=pathlib.Path, required=True)
    parser.add_argument("--prepared", type=pathlib.Path, help="Previously verified complete snapshot")
    parser.add_argument("--publish", action="store_true", help="Upload and verify; otherwise prepare only")
    args = parser.parse_args()
    for key in ("ossutil", "config", "work_dir", "cache", "prepared"):
        value = getattr(args, key)
        if value is not None:
            value = value.expanduser().resolve()
            setattr(args, key, value)
            if key != "ossutil" and (value == ROOT or ROOT in value.parents):
                parser.error("Credentials, cache and generated resources must stay outside the repository")
    if not args.config.is_file() or not args.ossutil.is_file():
        parser.error("Private config and ossutil must exist")
    if os.name != "nt" and args.config.stat().st_mode & 0o077:
        parser.error("ossutil configuration must be readable by its owner only")
    try:
        with lock(args.work_dir):
            stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            work = pathlib.Path(tempfile.mkdtemp(prefix=stamp + "-", dir=args.work_dir))
            try:
                report = synchronize(args, work)
            except Exception as error:
                M.write_json(work / "result.json", {"status": "failed", "error": str(error)})
                raise
            M.write_json(work / "result.json", report)
            latest = "latest-success.json" if report["status"] != "prepared" else "latest-prepared.json"
            M.write_json(args.work_dir / latest, dict(report, work_dir=str(work)))
            print("OSS sync {}. Report: {}".format(report["status"], work / "result.json"))
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        parser.exit(1, "OSS sync stopped: {}\n".format(error))


if __name__ == "__main__":
    main()
