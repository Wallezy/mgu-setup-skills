#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""One-way, non-destructive synchronization of the four configured Git mirrors."""

import argparse
import datetime
import json
import os
import pathlib
import subprocess
import tempfile

REPOSITORIES = {
    "mgu-setup-skills": "Wallezy/mgu-setup-skills",
    "mgu-store": "robertnisipeanu/mgu-store",
    "idrive-apps": "robertnisipeanu/idrive-apps",
    "idrive7-8-ssh-root": "cauliflowermossgrape/idrive7-8-ssh-root",
}
ROOT = pathlib.Path(__file__).resolve().parents[1]


def git(folder, *args, allow_failure=False):
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0",
               GIT_SSH_COMMAND="ssh -o BatchMode=yes -o ConnectTimeout=15 -o StrictHostKeyChecking=yes")
    command = ["git", "-c", "core.hooksPath=/dev/null", "-c", "protocol.file.allow=never"]
    if folder:
        command += ["-C", str(folder)]
    result = subprocess.run(command + list(args), env=env, capture_output=True,
                            text=True, timeout=600)
    if result.returncode and not allow_failure:
        raise RuntimeError("git {} failed: {}".format(args[0], result.stderr.strip()[-1500:]))
    return result


def refs(folder, namespace):
    output = git(folder, "for-each-ref", "--format=%(objectname) %(refname)",
                 "refs/" + namespace + "/").stdout
    return {name.replace("refs/" + namespace + "/", "refs/", 1): sha
            for sha, name in (line.split() for line in output.splitlines())}


def remote_refs(url):
    output = git(None, "ls-remote", "--refs", url, "refs/heads/*", "refs/tags/*").stdout
    return {name: sha for sha, name in (line.split() for line in output.splitlines())}


def default_branch(url):
    output = git(None, "ls-remote", "--symref", url, "HEAD").stdout
    branches = [line.split()[1] for line in output.splitlines()
                if line.startswith("ref: refs/heads/") and line.endswith("\tHEAD")]
    if len(branches) != 1:
        raise RuntimeError("Cannot determine source default branch")
    return branches[0]


def synchronize(folder, source, target, publish=False, all_branches=False):
    """Only Git objects enter the fresh bare repository; no checkout or hooks."""
    git(None, "init", "--bare", str(folder))
    git(folder, "fetch", "--no-tags", source,
        "+refs/heads/*:refs/source/heads/*", "+refs/tags/*:refs/source/tags/*")
    git(folder, "fetch", "--no-tags", target,
        "+refs/heads/*:refs/target/heads/*", "+refs/tags/*:refs/target/tags/*")
    upstream, destination = refs(folder, "source"), refs(folder, "target")
    if not upstream:
        raise RuntimeError("Source has no branches or tags")
    main = default_branch(source)
    if main not in upstream:
        raise RuntimeError("Source default branch changed during preparation")
    managed = {name: sha for name, sha in upstream.items()
               if all_branches or name == main or name.startswith("refs/tags/")}
    changes, conflicts = [], []
    for name, sha in sorted(managed.items()):
        old = destination.get(name)
        if old == sha:
            continue
        if old and (name.startswith("refs/tags/") or
                    git(folder, "merge-base", "--is-ancestor", old, sha,
                        allow_failure=True).returncode != 0):
            conflicts.append({"ref": name, "source": sha, "target": old})
        else:
            changes.append({"ref": name, "before": old, "after": sha})
    report = {"source": source, "target": target, "changes": changes,
              "conflicts": conflicts, "target_only": sorted(set(destination) - set(upstream)),
              "scope": "all-branches-and-tags" if all_branches else "default-branch-and-tags",
              "default_branch": main, "managed_source_refs": managed,
              "preserved_refs": {k: v for k, v in destination.items() if k not in managed},
              "preserved_differences": [
                  {"ref": k, "source": upstream[k], "target": v}
                  for k, v in sorted(destination.items())
                  if k not in managed and k in upstream and upstream[k] != v],
              "excluded_source_refs": sorted(set(upstream) - set(managed)),
              "source_refs": upstream, "target_before": destination,
              "status": "blocked" if conflicts else "prepared" if changes else "unchanged"}
    if conflicts:
        return report
    if publish and changes:
        # Require the target snapshot to still match before the atomic, non-force push.
        if remote_refs(target) != destination:
            raise RuntimeError("Target changed during preparation; no push attempted")
        specifications = [c["ref"].replace("refs/", "refs/source/", 1) + ":" + c["ref"]
                          for c in changes]
        git(folder, "push", "--atomic", target, *specifications)
        report["status"] = "published"
    if publish or not changes:
        actual = remote_refs(target)
        expected = dict(destination)
        expected.update(managed)
        if actual != expected:
            raise RuntimeError("Remote acceptance differs from expected refs; inspect target before retrying")
        report["remote_verified"] = True
    return report


def write_json(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", required=True, type=pathlib.Path)
    parser.add_argument("--repo", action="append", choices=sorted(REPOSITORIES))
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--all-branches", action="store_true",
                        help="Strict full-branch sync; any rewritten branch blocks this repository")
    args = parser.parse_args()
    base = args.work_dir.expanduser().resolve()
    if base == ROOT or ROOT in base.parents:
        parser.error("Run records and bare repositories must stay outside the source checkout")
    base.mkdir(parents=True, exist_ok=True)
    lock = base / ".sync.lock"
    try:
        descriptor = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        parser.exit(1, "Synchronization lock exists; inspect the running task before retrying\n")
    try:
        with os.fdopen(descriptor, "w") as stream:
            stream.write(str(os.getpid()))
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run = pathlib.Path(tempfile.mkdtemp(prefix=stamp + "-", dir=base))
        results = {}
        for name in args.repo or REPOSITORIES:
            source = "git@github.com:" + REPOSITORIES[name] + ".git"
            target = "git@gitee.com:walle7/" + name + ".git"
            print("Checking " + name, flush=True)
            try:
                results[name] = synchronize(run / (name + ".git"), source, target,
                                            args.publish, args.all_branches)
            except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
                results[name] = {"status": "failed", "error": str(error),
                                 "source": source, "target": target}
            write_json(run / (name + ".json"), results[name])
            print(name + ": " + results[name]["status"], flush=True)
        success = all(r["status"] in ("published", "unchanged") for r in results.values())
        report = {"checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  "work_dir": str(run), "published_requested": args.publish,
                  "repositories": results, "success": success}
        write_json(run / "result.json", report)
        write_json(base / "latest-check.json", report)
        if success:
            write_json(base / "latest-success.json", report)
        print("Report: " + str(run / "result.json"))
        if any(r["status"] in ("blocked", "failed") for r in results.values()):
            return 1
        return 0
    finally:
        lock.unlink()


if __name__ == "__main__":
    raise SystemExit(main())
