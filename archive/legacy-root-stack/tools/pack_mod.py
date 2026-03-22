#!/usr/bin/env python3
"""Create deterministic mod zip artifacts."""
from __future__ import annotations

import argparse
import os
import stat
import sys
import zipfile
from pathlib import Path

FIXED_DT = (1980, 1, 1, 0, 0, 0)
EXCLUDED_PARTS = {".git", "dist", "__pycache__", ".artifacts", "tools"}


def is_excluded(path: Path, include_tests: bool) -> bool:
    parts = set(path.parts)
    if parts & EXCLUDED_PARTS:
        return True
    if not include_tests and "tests" in parts:
        return True
    return False


def iter_files(repo_root: Path, include_tests: bool) -> list[Path]:
    out: list[Path] = []
    for path in (repo_root / "mod").rglob("*"):
        if path.is_dir():
            continue
        rel = path.relative_to(repo_root)
        if is_excluded(rel, include_tests=include_tests):
            continue
        out.append(rel)
    return sorted(out, key=lambda p: p.as_posix())


def write_deterministic_zip(repo_root: Path, files: list[Path], out_zip: Path) -> None:
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_zip, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for rel_path in files:
            src = repo_root / rel_path
            zi = zipfile.ZipInfo(rel_path.as_posix(), date_time=FIXED_DT)
            zi.compress_type = zipfile.ZIP_DEFLATED
            # Normalize file mode and host system for reproducible external attrs.
            zi.create_system = 3
            zi.external_attr = (stat.S_IFREG | 0o644) << 16
            data = src.read_bytes()
            zf.writestr(zi, data)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="dev", help="Artifact version")
    parser.add_argument("--include-tests", action="store_true", help="Include tests/ in archive")
    args = parser.parse_args()

    repo_root = Path.cwd()
    files = iter_files(repo_root, include_tests=args.include_tests)
    if not files:
        print("ERROR: no files selected for packaging", file=sys.stderr)
        return 1

    output = repo_root / "dist" / f"mod-{args.version}.zip"
    write_deterministic_zip(repo_root, files, output)
    print(f"Created {output}")
    print(f"Packed files: {len(files)}")
    return 0


if __name__ == "__main__":
    os.umask(0o022)
    sys.exit(main())
