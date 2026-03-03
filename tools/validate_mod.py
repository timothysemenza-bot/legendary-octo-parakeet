#!/usr/bin/env python3
"""Validate mod skeleton content and references."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        raise
    except Exception as exc:  # pragma: no cover - explicit message path
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mod-dir", default="mod", help="Path to mod directory")
    args = parser.parse_args()

    mod_dir = Path(args.mod_dir)
    errors: list[str] = []

    required = [
        mod_dir / "main.lua",
        mod_dir / "manifest.json",
        mod_dir / "config.json",
        mod_dir / "content" / "items.json",
        mod_dir / "content" / "asset_refs.json",
    ]

    for path in required:
        if not path.exists():
            errors.append(f"missing required file: {path}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    manifest_path = mod_dir / "manifest.json"
    try:
        manifest = load_json(manifest_path)
        for key in ("id", "name", "version", "entrypoint"):
            if not manifest.get(key):
                errors.append(f"manifest missing required key: {key}")
        entry = manifest.get("entrypoint")
        if entry and not (mod_dir / entry).exists():
            errors.append(f"manifest entrypoint does not exist: {entry}")
    except Exception as exc:
        errors.append(str(exc))

    items_path = mod_dir / "content" / "items.json"
    try:
        items_doc = load_json(items_path)
        items = items_doc.get("items", [])
        if not isinstance(items, list):
            errors.append("content/items.json field 'items' must be a list")
        else:
            seen: set[str] = set()
            for idx, item in enumerate(items):
                item_id = item.get("id") if isinstance(item, dict) else None
                if not item_id:
                    errors.append(f"content/items.json item at index {idx} missing id")
                    continue
                if item_id in seen:
                    errors.append(f"duplicate content id found: {item_id}")
                seen.add(item_id)
    except Exception as exc:
        errors.append(str(exc))

    refs_path = mod_dir / "content" / "asset_refs.json"
    try:
        refs_doc = load_json(refs_path)
        refs = refs_doc.get("assets", [])
        if not isinstance(refs, list):
            errors.append("content/asset_refs.json field 'assets' must be a list")
        else:
            for ref in refs:
                if not isinstance(ref, str):
                    errors.append("content/asset_refs.json contains non-string asset reference")
                    continue
                asset_path = mod_dir / ref
                if not asset_path.exists():
                    errors.append(f"missing referenced asset: {ref}")
    except Exception as exc:
        errors.append(str(exc))

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("Validation successful.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
