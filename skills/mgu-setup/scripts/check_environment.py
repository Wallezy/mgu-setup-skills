#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Wallezy and contributors.
"""Report local prerequisites without accessing a vehicle or the network."""

import argparse
import importlib
import json
import platform
import re
import shutil
import subprocess
import sys


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


def make_report(profile):
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
            "Recheck current upstream requirements before installing.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit a JSON report")
    parser.add_argument(
        "--profile",
        choices=["inspect", "root", "store", "full"],
        default="full",
        help="local prerequisites to require (default: full)",
    )
    args = parser.parse_args()
    report = make_report(args.profile)
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
