from __future__ import annotations

import argparse
from pathlib import Path

from app.core.secret_store import LocalSecretStore


def main() -> int:
    parser = argparse.ArgumentParser(description="Rotate Boss Key local secret store encryption key.")
    parser.add_argument("--path", required=True, help="Path to secrets.json")
    parser.add_argument("--old-key", required=True, help="Current secret store key")
    parser.add_argument("--new-key", required=True, help="New secret store key")
    args = parser.parse_args()

    count = LocalSecretStore.rotate_file_key(
        file_path=Path(args.path),
        old_key=args.old_key,
        new_key=args.new_key,
    )
    print(f"Rotated {count} secret entries in {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
