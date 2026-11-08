#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Wallezy and contributors.
"""Report local prerequisites without accessing a vehicle or the network."""

import argparse
import importlib
import json
import os
import pathlib
import platform
import re
import shutil
import subprocess
import sys

ROOT_RELEASE = pathlib.Path(__file__).resolve().parents[1] / "references/root-tool.json"


def probe_root_repo(folder):
    policy = json.loads(ROOT_RELEASE.read_text(encoding="utf-8"))
    result = {
        "ok": False,
        "version": None,
        "revision": None,
        "expected_version": policy["version"],
        "expected_revision": policy["commit"],
    }
    repo = pathlib.Path(folder).expanduser().resolve()
    git = shutil.which("git")
    if not git:
        return dict(result, reason="Git is required to verify a source checkout")
    if not (repo / "ssh_enable.py").is_file():
        return dict(result, reason="Root source folder or ssh_enable.py is missing")

    def read_git(*arguments):
        completed = subprocess.run(
            [git, "-C", str(repo), *arguments],
            capture_output=True, text=True, timeout=8, check=False,
            # Avoid refreshing the index in a read-only environment check.
            env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"),
        )
        if completed.returncode:
            raise ValueError("Git checkout could not be verified")
        return completed.stdout.strip()

    try:
        if pathlib.Path(read_git("rev-parse", "--show-toplevel")).resolve() != repo:
            return dict(result, reason="Select the Root repository itself, not a subfolder")
        result["revision"] = read_git("rev-parse", "HEAD")
        if result["revision"] != policy["commit"]:
            return dict(result, reason="Revision differs from the reviewed stable release")
        if read_git("status", "--porcelain", "--untracked-files=no"):
            return dict(result, reason="Tracked source or assets are modified or missing")
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        return dict(result, reason=str(exc) if isinstance(exc, ValueError) else type(exc).__name__)
    return dict(result, ok=True, version=policy["version"], reason="Reviewed source checkout; vehicle not checked")


def probe_tool(name, argument, pattern, minimum=None):
    executable = shutil.which(name)
    if not executable:
        return {"ok": False, "version": None, "reason": "not found on PATH"}
    try:
        result = subprocess.run(
            [executable, argument],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "version": None, "reason": type(exc).__name__}
    match = re.search(pattern, result.stdout + "\n" + result.stderr)
    if result.returncode != 0 or not match:
        return {"ok": False, "version": None, "reason": "version check failed"}
    version = match.group(1)
    parts = tuple(int(x) for x in re.findall(r"\d+", version)[:3])
    ok = minimum is None or parts >= minimum
    return {
        "ok": ok,
        "version": version,
        "reason": "available" if ok else "below the documented minimum",
    }


def probe_crypto():
    try:
        module = importlib.import_module("cryptography")
        version = module.__version__
        major = int(version.split(".")[0])
        return {
            "ok": major >= 41,
            "version": version,
            "reason": "available" if major >= 41 else "requires cryptography >=41",
        }
    except (ImportError, AttributeError, ValueError, OSError) as exc:
        return {"ok": False, "version": None, "reason": type(exc).__name__}


def required_for(profile):
    return {
        "inspect": ["python"],
        "root": ["python", "cryptography", "ssh"],
        "store": ["python", "node", "ssh"],
        "full": ["python", "cryptography", "node", "ssh"],
    }[profile]


def make_report(profile, root_repo=None):
    checks = {
        "python": {
            "ok": sys.version_info >= (3, 9),
            "version": platform.python_version(),
            "reason": "this helper and source workflow use Python 3.9+",
        },
        "cryptography": probe_crypto(),
        "node": probe_tool("node", "--version", r"\bv(\d+\.\d+\.\d+)\b", (18, 0, 0)),
        "ssh": probe_tool("ssh", "-V", r"\b(OpenSSH[^\s,]*)"),
    }
    required = required_for(profile)
    if root_repo is not None:
        checks["root_tool"] = probe_root_repo(root_repo)
        if profile in ("root", "full"):
            required.append("root_tool")
    return {
        "schema": 1,
        "profile": profile,
        "system": platform.system(),
        "machine": platform.machine(),
        "checks": checks,
        "required": required,
        "local_requirements_met": all(checks[key]["ok"] for key in required),
        "vehicle_checked": False,
        "vehicle_ready": None,
        "limits": [
            "No network, interface, administrator, coding-backup or vehicle check.",
            "The root profile checks the Python source route, not a Windows executable.",
            "The store profile checks the direct Node installer, not runtime wrappers.",
            "Root source revision is checked only when --root-repo is supplied; untracked code is not audited.",
            "Recheck current upstream requirements before installing.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit a JSON report")
    parser.add_argument(
        "--root-repo",
        help="verify a local Root source checkout against the reviewed release; no fetch or execution",
    )
    parser.add_argument(
        "--profile",
        choices=["inspect", "root", "store", "full"],
        default="full",
        help="local prerequisites to require (default: full)",
    )
    args = parser.parse_args()
    report = make_report(args.profile, args.root_repo)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("Local environment / 本地环境: " + report["system"])
        for name, check in report["checks"].items():
            mark = "OK" if check["ok"] else "MISSING/UNVERIFIED"
            print("{}: {} ({})".format(name, mark, check["version"] or check["reason"]))
        print("Vehicle not checked / 尚未检查车辆")
        print("Local prerequisites met: " + str(report["local_requirements_met"]))
    return 0 if report["local_requirements_met"] else 1


if __name__ == "__main__":
    sys.exit(main())
