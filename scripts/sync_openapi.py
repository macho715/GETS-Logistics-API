#!/usr/bin/env python3
"""
Sync OpenAPI schema from docs to repo root.
"""

import os
import shutil
import sys
from pathlib import Path

SOURCE = "docs/openapi/openapi-gets-api.yaml"
TARGET = "openapi-schema.yaml"


def main() -> None:
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    os.chdir(repo_root)

    source_path = repo_root / SOURCE
    target_path = repo_root / TARGET

    if not source_path.exists():
        print(f"ERROR: Source file not found: {SOURCE}", file=sys.stderr)
        sys.exit(1)

    shutil.copy2(source_path, target_path)

    if not target_path.exists():
        print(f"ERROR: Failed to create target file: {TARGET}", file=sys.stderr)
        sys.exit(1)

    with target_path.open("r", encoding="utf-8") as handle:
        line_count = sum(1 for _ in handle)
    file_size_kb = target_path.stat().st_size / 1024

    print(f"Synced {SOURCE} -> {TARGET}")
    print(f"Lines: {line_count}")
    print(f"Size: {file_size_kb:.2f} KB")


if __name__ == "__main__":
    main()
