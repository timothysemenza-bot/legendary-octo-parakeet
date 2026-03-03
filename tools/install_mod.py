#!/usr/bin/env python3
"""Install mod directory into a game mods folder."""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path


def default_mod_name() -> str:
    name = Path.cwd().name.strip()
    return name or "BossKeyMod"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mod-dir", default="mod", help="Source mod folder")
    parser.add_argument("--mods-dir", default=os.environ.get("ISAAC_MODS_DIR", ""), help="Target game mods directory")
    parser.add_argument("--name", default=default_mod_name(), help="Folder name for installed mod")
    args = parser.parse_args()

    mod_dir = Path(args.mod_dir)
    mods_dir = Path(args.mods_dir) if args.mods_dir else None

    if not mod_dir.exists():
        print(f"ERROR: source mod directory not found: {mod_dir}")
        return 1
    if mods_dir is None:
        print("ERROR: missing --mods-dir (or ISAAC_MODS_DIR env var)")
        return 1

    mods_dir.mkdir(parents=True, exist_ok=True)
    target = mods_dir / args.name

    if target.exists():
        shutil.rmtree(target)

    shutil.copytree(mod_dir, target)
    print(f"Installed mod to: {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
