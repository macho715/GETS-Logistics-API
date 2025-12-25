#!/usr/bin/env bash
# ------------------------------------------------------------
# Deploy Preflight Guard (Cursor/Codex)
# - Enforces PROD_URL validation
# - Enforces schemaVersion lock
# - Fails fast (ZERO mode) on any ambiguity
# ------------------------------------------------------------

set -euo pipefail

# CONFIG (LOCKED)
REQUIRED_SCHEMA_VERSION="2025-12-25T00:32:52+0400"
HEALTH_PATH="/health"
TIMEOUT_SEC=10

# INPUT
# PROD_URL must be provided explicitly to avoid blind deploy
PROD_URL="${PROD_URL:-}"

fail() {
  echo "PRECHECK FAILED: $1" >&2
  exit 1
}

info() {
  echo "INFO: $1" >&2
}

# CHECK 0: PROD_URL existence
if [[ -z "$PROD_URL" ]]; then
  fail "PROD_URL is not set. Example: export PROD_URL=https://your-app.vercel.app"
fi

# Basic sanity
if [[ "$PROD_URL" != https://* ]]; then
  fail "PROD_URL must start with https://"
fi

info "Using PROD_URL: $PROD_URL"

# CHECK 1: Health endpoint reachable
HEALTH_URL="${PROD_URL}${HEALTH_PATH}"
info "Checking health endpoint: $HEALTH_URL"

HTTP_RESPONSE="$(curl -sS --max-time ${TIMEOUT_SEC} -w 'HTTPSTATUS:%{http_code}' "$HEALTH_URL" || true)"
HTTP_BODY="$(echo "$HTTP_RESPONSE" | sed -e 's/HTTPSTATUS:.*//g')"
HTTP_STATUS="$(echo "$HTTP_RESPONSE" | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')"

if [[ "$HTTP_STATUS" != "200" ]]; then
  fail "Health check failed. HTTP status=${HTTP_STATUS}"
fi

# CHECK 2: schemaVersion existence (expects JSON containing "schemaVersion")
if ! echo "$HTTP_BODY" | grep -q ""schemaVersion""; then
  fail "schemaVersion not found in /health response"
fi

# Extract schemaVersion (best-effort; expects JSON string value)
ACTUAL_SCHEMA_VERSION="$(echo "$HTTP_BODY" | sed -n 's/.*"schemaVersion"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1)"

if [[ -z "$ACTUAL_SCHEMA_VERSION" ]]; then
  fail "schemaVersion key exists but value could not be parsed"
fi

info "Detected schemaVersion: $ACTUAL_SCHEMA_VERSION"

# CHECK 3: schemaVersion lock match
if [[ "$ACTUAL_SCHEMA_VERSION" != "$REQUIRED_SCHEMA_VERSION" ]]; then
  fail "schemaVersion mismatch. expected=${REQUIRED_SCHEMA_VERSION}, actual=${ACTUAL_SCHEMA_VERSION}"
fi

# PASS SUMMARY
echo "------------------------------------------------------------"
echo "DEPLOY PREFLIGHT PASSED"
echo "PROD_URL      : $PROD_URL"
echo "Health        : OK"
echo "schemaVersion : $ACTUAL_SCHEMA_VERSION"
echo "------------------------------------------------------------"
echo "Proceed with deployment ONLY after explicit human approval."
