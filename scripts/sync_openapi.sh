#!/usr/bin/env bash
# Sync OpenAPI schema from docs to repo root.

set -euo pipefail

SOURCE="docs/openapi/openapi-gets-api.yaml"
TARGET="openapi-schema.yaml"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

if [ ! -f "$SOURCE" ]; then
  echo "ERROR: Source file not found: $SOURCE" >&2
  exit 1
fi

cp "$SOURCE" "$TARGET"

if [ ! -f "$TARGET" ]; then
  echo "ERROR: Failed to create target file: $TARGET" >&2
  exit 1
fi

LINE_COUNT=$(wc -l < "$TARGET" 2>/dev/null || echo "unknown")
FILE_SIZE=$(du -h "$TARGET" 2>/dev/null | cut -f1 || echo "unknown")

echo "Synced $SOURCE -> $TARGET"
echo "Lines: $LINE_COUNT"
echo "Size: $FILE_SIZE"
