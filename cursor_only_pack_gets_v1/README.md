# GETS Logistics API — Cursor-Only Starter Pack

## What this pack enforces
- **ZERO Fail-safe**: no blind deploy; validate PROD_URL + `schemaVersion` lock first
- Airtable SSOT with schema lock: `2025-12-25T00:32:52+0400`
- CI quality gates: coverage ≥ 85.00, ruff/black/isort 0 warn, bandit High=0, pip-audit --strict

## Quick start
```bash
python -m venv .venv && . .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -U pip pre-commit pytest pytest-cov ruff black isort bandit pip-audit

python tools/init_settings.py --git --precommit

pytest -q
ruff check . && ruff format --check . && black --check . && isort --check-only .
```

## Deploy preflight (mandatory)
```bash
export PROD_URL="https://<your-prod-app>.vercel.app"
./scripts/deploy_preflight.sh
```

If preflight fails, STOP and do not deploy.
