# AGENTS.md — GETS Logistics API (Cursor Agent Codex)

> **Authority**: This file is the **single source of truth** for Cursor Agent rules in this repo.
> Place in **project root** as `AGENTS.md`.

## 0) Mission
Build and operate **GETS Logistics API** for HVDC Project Logistics:
- SSOT: **Airtable** (10 tables) + **Schema Lock** (pinned)
- API: Flask on Vercel (serverless)
- Consumers: ChatGPT Actions (OpenAPI), Dashboard/BI, Ops bots
- Timezone: **Asia/Dubai (+04:00)**

## 1) Non‑negotiables (Hard Gates)
1. **No hallucinations**: if data/paths/commands are unknown, **inspect repo first** and report `MISSING:` explicitly.
2. **Schema Lock pinned**: use `airtable_schema.lock.json` as SSOT.
3. **Rename protection**: protected field names **MUST NOT** be renamed (Airtable `filterByFormula` dependency).
4. **Ops Gate**: if schema drift is detected, **STOP** (do not merge/deploy).
5. **Numbers**: 2 decimals for ratios/days/hours; currency specify AED/USD when relevant.
6. **Timezone**: normalize all date-times to `Asia/Dubai` and ISO-8601 with offset.

## 2) Repo SSOT: Airtable Lock Metadata
- Airtable Base ID: `appnLz06h07aMm366`
- Schema Lock Version (`generatedAt`): `2025-12-25T00:32:52+0400`
- Tables (10):
  - Shipments: `tbl4NnKYx1ECKmaaC`
  - Documents: `tblbA8htgQSd2lOPO`
  - Approvals: `tblJh4z49DbjX7cyb`
  - Actions: `tblkDpCWYORAPqxhw`
  - Events: `tblGw5wKFQhR9FBRR`
  - Evidence: `tbljDDDNyvZY1sORx`
  - BottleneckCodes: `tblMad2YVdiN8WAYx`
  - Owners: `tblAjPArtKVBsShfE`
  - Vendors: `tblZ6Kc9EQP7Grx3B`
  - Sites: `tblSqSRWCe1IxCIih`

### Protected fields (rename‑protected) — total 20
```json
{
  "Shipments": [
    "shptNo",
    "currentBottleneckCode",
    "bottleneckSince",
    "riskLevel",
    "nextAction",
    "actionOwner",
    "dueAt"
  ],
  "Documents": [
    "shptNo",
    "docType",
    "status"
  ],
  "Actions": [
    "shptNo",
    "status",
    "priority",
    "dueAt",
    "actionText",
    "owner"
  ],
  "Events": [
    "timestamp",
    "shptNo",
    "entityType",
    "toStatus"
  ]
}
```

### Known schema gaps (Phase 2.4 targets)
- Evidence links: Documents/Approvals/Actions/Events currently have no canonical Evidence reference field.
- eventKey: Events has `eventId` autoNumber; **no eventKey** for strict idempotency.
- Incoterm/HS: Shipments has no Incoterm/HS fields (limits BOE RED risk rules).

## 3) Setup / Run / Test commands (Agent must confirm in repo)
> **Rule**: Before running commands, check whether this repo uses `requirements.txt`, `pyproject.toml`, or both.

### Install
- If `requirements.txt` exists:
  - `python -m pip install -r requirements.txt`
- If `pyproject.toml` exists:
  - use the project’s documented tool (`pip`, `uv`, `poetry`) — do not guess.

### Tests (TDD)
- Unit tests:
  - `pytest -q`
- Coverage (target ≥ 80.00% for new modules):
  - `pytest --cov=api --cov-report=term-missing`

### Ops Gate (must pass on PR)
- Schema drift check:
  - `python scripts/check_schema_drift.py`

### Local run (choose correctly)
- If Vercel project present:
  - `vercel dev`
- Else:
  - `flask --app api.document_status run --port 8000`

(If neither works, report `MISSING:` with discovered entrypoints.)

## 4) Development workflow (RED → GREEN → REFACTOR)
When adding/modifying endpoints:
1. **RED**: write tests first (pytest).
2. **GREEN**: minimal implementation to pass.
3. **REFACTOR**: extract services, ensure timezone, pagination, error handling, and docs updated.
4. **Update OpenAPI**: keep pinned:
   - `info.x-airtable-baseId = appnLz06h07aMm366`
   - `info.x-airtable-schemaVersion = 2025-12-25T00:32:52+0400`
   - `x-protected-fields = (20 fields)`
5. **Update /health** to expose:
   - `openapi.schemaVersion`
   - `openapi.protectedFieldsCount`
   - `openapi.protectedFields`
6. **Run Ops Gate** locally before commit.

## 5) API contract rules (Operational packets)
### /document/status/{shptNo}
- Must return operational packet:
  - doc statuses (BOE/DO/COO/HBL/CIPL)
  - bottleneck code/since/riskLevel
  - next action (owner/dueAt)
- If document row missing: return status `UNKNOWN` for that docType.
- If Shipments not found: return **404**.

### /approval/status/{shptNo}
- Must distinguish:
  - **404**: shipment not found (Shipments missing)
  - **200 + approvals=[]**: shipment exists but approvals not started

### /approval/summary
- Must paginate Airtable list records (offset loop).
- Must compute D-15/D-5/overdue buckets for pending approvals.

### /bottleneck/summary
- Must compute:
  - byCategory (join BottleneckCodes.category)
  - byCode (count + avg aging hours)
  - aging distribution (24h/48h/72h+)

### /document/events/{shptNo}
- Sort by timestamp desc (latest first).
- Events is append-only ledger.

## 6) Airtable access rules (Performance + Safety)
- Enforce Airtable limits:
  - **5.00 req/s per base**, **50.00 req/s per PAT**
  - On 429, backoff and retry (cooldown 30.00s recommended)
- Always implement:
  - pagination via `offset`
  - optional caching for summary endpoints (1–5 minutes) to reduce RPS
- Prefer tableId in API paths (rename-safe).

## 7) Error handling & observability
- Always return JSON error payloads with:
  - `error` code, `message`, `timestamp` (Dubai), and `schemaVersion` when relevant
- `/health` must include:
  - app version, schema lock version, and whether schema matches pinned OpenAPI

## 8) Documentation & changelog discipline
- Any API contract change requires:
  - OpenAPI update
  - Tests update
  - `PHASE_*.md` / `README.md` update
- Keep decisions in a short `CHANGELOG` section per phase doc.

## 9) Security / PII / secrets
- Never print or commit:
  - Airtable PATs, headers, raw env dumps
- Mask any PII in logs and sample payloads.

## 10) Definition of DONE (DoD)
A task is DONE only if:
- Tests pass (including new tests)
- Ops gate passes (schema drift check)
- OpenAPI pinned + `x-protected-fields` correct
- `/health` exposes schemaVersion + protected fields summary
- No unexplained TODOs left in code paths touched

## 11) Deployment Preflight (ZERO Fail-safe)
**Before any production deployment:**
1. **Set PROD_URL explicitly**:
   ```bash
   export PROD_URL="https://gets-logistics-api.vercel.app"
   ```
2. **Run preflight script**:
   ```bash
   chmod +x scripts/deploy_preflight.sh
   ./scripts/deploy_preflight.sh
   ```
3. **Preflight must pass** (exit 0):
   - `/health` returns HTTP 200
   - `schemaVersion` matches `2025-12-25T00:32:52+0400`
   - PROD_URL is valid HTTPS URL

**If preflight fails**: STOP. Do not deploy. Fix the issue first.

**ZERO STOP Rule**: If Agent cannot validate PROD_URL or schemaVersion, output STOP table:

| 단계 | 이유 | 위험 | 요청데이터 | 다음조치 |
|------|------|------|-----------|----------|
| ZERO | PROD_URL unknown | Wrong deploy target | Production URL | Provide PROD_URL |
