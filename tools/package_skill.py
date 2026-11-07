#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Build a reproducible standalone skill archive; no downloaded assets."""

import hashlib
import pathlib
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]


def main():
    skill = ROOT / "skills/mgu-setup"
    files = sorted(
        p for p in skill.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
        and (p.name == "LICENSE" or p.suffix in (".md", ".py", ".yaml", ".json")
             or (p.relative_to(skill).parts[0] == "assets"
                 and p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".svg")))
    )
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    archive = dist / "mgu-setup.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as output:
        for path in files:
            info = zipfile.ZipInfo(path.relative_to(skill.parent).as_posix(), (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            output.writestr(info, path.read_bytes())
    with zipfile.ZipFile(archive) as output:
        assert output.testzip() is None
        assert output.read("mgu-setup/LICENSE") == (ROOT / "LICENSE").read_bytes()
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (dist / "SHA256SUMS").write_text(digest + "  mgu-setup.zip\n", encoding="utf-8")
    print("Packaged {} files into {}".format(len(files), archive))


if __name__ == "__main__":
    main()
