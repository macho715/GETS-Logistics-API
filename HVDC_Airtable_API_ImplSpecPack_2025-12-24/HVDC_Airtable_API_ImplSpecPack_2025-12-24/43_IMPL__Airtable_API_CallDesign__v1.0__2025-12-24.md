# HVDC Status Ledger — Airtable API Call Design (Filter/Paging/Batch/Upsert)

> Date: 2025-12-24  
> TZ(work): Asia/Dubai (+04:00)

## 0. Purpose

This document fixes the **implementation spec** for calling Airtable Web API from a Flask service (Status/KPI/Approval engines) with:
- **filterByFormula** (single & multi-key lookups)
- **paging** (offset cursor)
- **batching** (≤10 records/req)
- **upsert** (performUpsert + fieldsToMergeOn) for idempotent ingest

---

## 1. One-time setup (SSOT keys)

### 1.1 Required IDs & Secrets
- `AIRTABLE_PAT` : Personal Access Token (Bearer)
- `AIRTABLE_BASE_ID` : Base id (starts with `app...`)
- `TABLE_ID_*` : Table ids (starts with `tbl...`) — use table IDs for stability against renames

### 1.2 Recommended unique keys (merge fields)
Upsert requires merge fields to be **unique** (1 record match). Create these fields as Single line text.

| Table | Upsert mode | fieldsToMergeOn (recommended) | Notes |
|---|---:|---|---|
| Shipments | YES | [`shptNo`] | master row per shipment |
| Documents | YES | [`docKey`] | `docKey = shptNo + '|' + docType` |
| Approvals | YES | [`approvalKey`] | `approvalKey = shptNo + '|' + approvalType` |
| Evidence | YES | [`evidenceId`] | e.g., `msg_abc`, `sha256:...` |
| Events | OPTIONAL | [`eventKey`] | append-only; use eventKey to dedupe replays |

---

## 2. Base URL + Auth

### 2.1 Endpoint template
```
https://api.airtable.com/v0/{baseId}/{tableIdOrName}
```

### 2.2 Headers
```
Authorization: Bearer {AIRTABLE_PAT}
Content-Type: application/json
```

---

## 3. LIST (paging, filtering, sorting)

### 3.1 Paging rule (offset cursor)
- Always request with `pageSize=100` (max)
- If response contains `offset`, call again with `offset=<value>`
- Stop when response has **no `offset`**

### 3.2 Minimal list request (all rows, paged)
```
GET /v0/{baseId}/{tableId}?pageSize=100
```

### 3.3 “Find by key” using filterByFormula
**Shipment by shptNo**
```
GET /v0/{baseId}/{shipmentsTableId}?filterByFormula=%7BshptNo%7D%3D%27SCT-0143%27
```

**Document by (shptNo + docType)**
```
filterByFormula=AND({shptNo}='SCT-0143',{docType}='BOE')
```

### 3.4 Multi-key fetch (small set)
For <= ~20 keys, you can OR them:
```
filterByFormula=OR({shptNo}='SCT-0143',{shptNo}='SCT-0144')
```

### 3.5 View + filterByFormula combo
Use `view=<viewNameOrId>` to pre-filter (e.g., “OPEN ONLY”) and additionally apply `filterByFormula`.

### 3.6 Sorting
Use:
```
sort[0][field]=ETA
sort[0][direction]=desc
```
Note: If combined with `view`, sort parameter overrides the view’s sort order.

### 3.7 Empty fields are omitted
Airtable list responses omit fields with empty values; your consumer should **default missing fields to null/empty**.

---

## 4. CREATE (batch ≤10)

### 4.1 Create records (bulk)
```
POST /v0/{baseId}/{tableId}
{
  "records": [
    {"fields": {"shptNo":"SCT-0143","site":"TAWEELAH","ETA":"2025-12-26T08:00:00+04:00"}},
    {"fields": {"shptNo":"SCT-0144","site":"RUWAIS","ETA":"2025-12-27T08:00:00+04:00"}}
  ],
  "typecast": true
}
```
- `typecast=true` recommended when writing single/multi-select values from strings.

---

## 5. UPDATE (batch ≤10) and UPSERT (performUpsert)

### 5.1 Update multiple (PATCH, non-destructive)
```
PATCH /v0/{baseId}/{tableId}
{
  "records": [
    {"id":"recXXXXXXXXXXXX","fields":{"boeStatus":"SUBMITTED","updatedAt":"2025-12-24T09:00:00+04:00"}}
  ],
  "typecast": true
}
```

### 5.2 Upsert multiple (PATCH + performUpsert)
Use when you ingest daily reports and want **idempotency**:
```
PATCH /v0/{baseId}/{documentsTableId}
{
  "performUpsert": { "fieldsToMergeOn": ["docKey"] },
  "records": [
    {"fields":{"docKey":"SCT-0143|BOE","shptNo":"SCT-0143","docType":"BOE","status":"SUBMITTED","updatedAt":"2025-12-24T09:00:00+04:00"}},
    {"fields":{"docKey":"SCT-0143|DO","shptNo":"SCT-0143","docType":"DO","status":"NOT_STARTED"}}
  ],
  "typecast": true
}
```

Operational notes:
- If **0 matches** → creates a new record
- If **1 match** → updates that record
- If **>1 matches** → the whole request fails (merge fields must be unique)

---

## 6. Error handling (hard rules)

### 6.1 Rate limit
- Per-base: 5 req/sec
- PAT aggregate: 50 req/sec (all traffic using a PAT)

When exceeded:
- HTTP 429
- wait 30 sec (respect Retry-After header if present)

### 6.2 Typical user errors
- 401 unauthorized → token missing/invalid
- 403 invalid_permissions → token/user lacks access or field/table permissions
- 422 invalid_multiple_choice_options → enable `typecast` or pre-create options
- 422 invalid_request_body → JSON malformed or wrong payload shape

### 6.3 Retry policy
- 429: sleep 30 sec, retry (max 3)
- 503: exponential backoff (1s, 2s, 4s, 8s), retry (max 5)
- 422/403: do NOT retry automatically (fix payload/permissions)

---

## 7. Performance & call reduction (ops)

- Prefer **performUpsert** over (search+create/update) to cut calls.
- Batch always (10 records/req).
- Use `fields[]` to return only required fields to reduce payload.
- Cache reference tables (vendors/sites/status enums) in memory for 10–30 minutes.
- If ingest is CSV-heavy, evaluate Sync API (up to 10,000 rows/req) as an alternative.

---

## 8. Minimal recipes (copy/paste)

### 8.1 Find shipment by shptNo
```
GET /v0/{baseId}/{shipments}?filterByFormula={shptNo}='SCT-0143'&pageSize=1
```

### 8.2 Upsert shipments (by shptNo)
```
PATCH /v0/{baseId}/{shipments}
{
  "performUpsert": {"fieldsToMergeOn":["shptNo"]},
  "records":[{"fields":{"shptNo":"SCT-0143","vendor":"DSV","incoterm":"DAP","hs2":"85","eta":"2025-12-26T08:00:00+04:00"}}],
  "typecast": true
}
```

---

## 9. Compliance notes (HVDC ops)

- Store evidence pointers (email msgId, file sha256, portal screenshot id) for audit.
- Keep `updatedAt` in ISO-8601 with +04:00 for human ops; internally also keep UTC if required.
- Never let LLM write “facts” into Airtable without an evidence id.

