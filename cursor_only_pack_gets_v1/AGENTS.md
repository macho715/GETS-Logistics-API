# AGENTS.md — Cursor/Codex Agent Operating Rules (GETS Logistics API)
Project: GETS Logistics API (HVDC) — Vercel Serverless + Airtable SSOT
Timezone: Asia/Dubai (+04:00)
Doc-Version: v1.0
Last-Update: 2025-12-25

> You are an AI coding agent running inside Cursor IDE / Codex.
> Follow this file strictly. If a required input is missing or any rule is ambiguous → STOP (ZERO mode).

---

## 0) ZERO Fail-safe (Hard Stop)
If ANY of the following is true, output only a STOP table and do not proceed:
- Production URL is unknown or cannot be validated via `/health`
- `schemaVersion` mismatch vs lock (`2025-12-25T00:32:52+0400`)
- Deployment target cannot be proven (you are unsure which Vercel project / URL is active)
- You are asked to deploy without running **Deploy Preflight** (§6)

**STOP Template**
| 단계 | 이유 | 위험 | 요청데이터 | 다음조치 |
|---|---|---|---|---|
| ZERO | <why> | <impact> | <what you need> | <what to do next> |

---

## 1) System Overview (SSOT)
- Architecture: **Vercel Serverless (Flask)** → **Airtable Base (SSOT)** with schema lock + protected fields.
- Core modules (expected): `api/document_status.py`, `airtable_client.py`, `schema_validator.py`, `monitoring.py`, `utils.py`
- Rate limiting: **5 RPS per base**, retry on **429/503**, pagination via `offset`
- Schema lock:
  - `SCHEMA_VERSION = 2025-12-25T00:32:52+0400`
  - Protected fields are rename-forbidden
- Core endpoints (examples): `/`, `/health`, `/status/summary`, `/approval/summary`, etc.

Reference: ARCHITECTURE.md (single source of truth for system design).

---

## 2) Working Style (Small diffs, Reproducible)
- Make the **smallest diff** that meets the DoD.
- Prefer **file-scoped checks** over full rebuild.
- Keep changes deterministic: avoid “magic” constants; read from config.
- No silent behavior change without test evidence.

---

## 3) Code Conventions (Python / Flask)
- Python 3.11 runtime (Vercel)
- No hard-coded secrets: tokens only from env vars:
  - `AIRTABLE_API_TOKEN` (required)
  - `AIRTABLE_BASE_ID` (optional override)
  - `API_KEY` (optional bearer auth)
- Logging: no PII in logs (mask emails/phones if they appear).
- Airtable calls must respect:
  - page_size ≤ 100
  - max records safety cap
  - 5 RPS enforcement (client-side)

---

## 4) Allowed / Ask-First Permissions
**Allowed without asking**
- Read/list files, grep, search within repo
- Run local unit tests / lint (no network secrets exposed)
- Run curl to `/health` and read public JSON from the API URL

**Ask-first (require explicit human approval)**
- `vercel --prod` deployment
- Changing Vercel env vars / Airtable token scopes
- Deleting files, moving modules, mass refactor
- Adding new dependency packages

---

## 5) Test Gates (Local)
Run at least one gate before proposing merge-ready change:
- Unit: `pytest -q` (if tests exist)
- Basic import check: `python -c "import api.document_status"`
- Smoke server (local):
  - `flask --app api.document_status run --port 5000`
  - `curl -s http://127.0.0.1:5000/health`

If these commands are not present/working in repo, do not invent them—STOP and request the correct commands.

---

## 6) Deployment Rules (Mandatory Preflight)
### 6.1 Deploy Preflight (MUST PASS)
Before any deploy action, the agent MUST:
1) Determine the **current Production URL** (PROD_URL) from one of:
   - Repo config (README/ARCHITECTURE.md), or
   - Vercel project settings, or
   - `vercel project ls` / `vercel env pull` output (human can provide)
2) Validate PROD_URL health:
   - `curl -sS ${PROD_URL}/health`
   - Response MUST be HTTP 200 and JSON
3) Validate schema lock:
   - Health/metadata response must include `schemaVersion` OR
   - Another endpoint returning `schemaVersion`
   - Must equal: `2025-12-25T00:32:52+0400`
4) Validate “wrong-target deploy” prevention:
   - Compare PROD_URL host with intended deploy host
   - If mismatch/unknown → STOP

### 6.2 Deploy Guard (Prevent Blind Redeploy)
If preflight shows:
- PROD_URL is healthy AND
- schemaVersion matches AND
- code change is only docs/comment/no runtime impact
→ Do NOT deploy automatically. Recommend “no deploy needed”.

If deploy is requested, require human confirmation after showing:
- PROD_URL
- health check status
- schemaVersion check result
- intended Vercel project name (if known)

### 6.3 Post-Deploy Verification (MUST)
After deploy (only after approval):
- Run the same `/health` check on the new deployment URL
- Verify schemaVersion unchanged unless intentionally updated
- Verify at least one critical endpoint (`/approval/summary`) returns 200

---

## 7) Known Gotchas (Vercel cache / stale code)
- If production behaves like old code:
  - Recommend “Clear Build Cache” and redeploy with cache disabled
  - Prefer `vercel --prod --force` only after approval
- If signature mismatch occurs (`unexpected keyword argument ...`):
  - Suspect stale lambda layer / cached build

---

## 8) Output Requirements (When you respond in chat)
- Be explicit about evidence: command outputs, endpoint JSON snippets, or file paths.
- If you did not run a check, say so.
- If any critical data is missing: use ZERO STOP table.

---

## 9) Quick Checklist (Agent)
- [ ] Identify scope & smallest diff
- [ ] Update code + tests
- [ ] Run Test Gates (§5)
- [ ] If deploy requested: run Deploy Preflight (§6.1) and show results
- [ ] Only then propose deploy steps

---

## 10) Optional Repo Add-ons
- `scripts/deploy_preflight.sh` (curl 기반, PROD_URL·schemaVersion 강제 체크)
- `CODEOWNERS` rules: changes to `AGENTS.md`, `vercel.json`, schema-lock files require mandatory review
