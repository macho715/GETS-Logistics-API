# ARCHITECTURE — GETS Logistics API (HVDC)

## SSOT
- Data: Airtable Base (SSOT)
- API: Vercel Serverless (Flask)
- Schema lock: `schemaVersion = 2025-12-25T00:32:52+0400`

## Key properties
- Rate limit: 5 RPS per base
- Retries: 429/503 with backoff
- Pagination: Airtable `offset`

## Deploy guard
- Mandatory: `scripts/deploy_preflight.sh` checks PROD_URL + /health + schemaVersion
- No blind redeploy: if PROD_URL unknown or schemaVersion mismatch, ZERO stop
