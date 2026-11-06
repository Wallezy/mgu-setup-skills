#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Check local documentation links and the standalone skill's license."""

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]


def main():
    documents = list(ROOT.glob("*.md"))
    for directory in ("skills", "docs", ".github"):
        documents.extend((ROOT / directory).rglob("*.md"))
    errors = []
    links = 0
    for document in documents:
        text = document.read_text(encoding="utf-8")
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if "://" in target or target.startswith("#"):
                continue
            links += 1
            if not (document.parent / target.split("#", 1)[0]).exists():
                errors.append("{}: missing {}".format(document.relative_to(ROOT), target))
        if "[TODO" in text:
            errors.append("{}: unfinished scaffold".format(document.relative_to(ROOT)))
    skill = ROOT / "skills/mgu-setup"
    if (ROOT / "LICENSE").read_bytes() != (skill / "LICENSE").read_bytes():
        errors.append("Root and standalone skill licenses differ")
    entry = (skill / "SKILL.md").read_text(encoding="utf-8")
    for field in ("name: mgu-setup", "description:", "license: GPL-3.0-only"):
        if field not in entry.split("---", 2)[1]:
            errors.append("Missing skill metadata: " + field)
    if errors:
        raise SystemExit("\n".join(errors))
    print("Validated {} Markdown files and {} local links.".format(len(documents), links))


if __name__ == "__main__":
    main()
