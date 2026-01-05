# 🎯 GETS Logistics API - OpenAPI Schema for ChatGPT Actions

## 📋 Schema URL

**Production Schema**:
```
https://gets-logistics-api.vercel.app/openapi-schema.yaml
```

## 📊 Schema Overview

### API Information
- **Version**: 1.8.0
- **Base URL**: https://gets-logistics-api.vercel.app
- **Schema Version**: 2025-12-25T00:32:52+0400
- **Airtable Base**: appnLz06h07aMm366

### Available Endpoints (9 total)

#### 1. GET / - API Information
Returns API version, available endpoints, and system status.

#### 2. GET /health - Health Check
Returns API health status, configuration, and schema validation info.

#### 3. GET /document/status/{shptNo}
Operational status for BOE, DO, COO, HBL, CIPL with bottleneck, action, evidence.
- **Parameters**: shptNo (required)
- **Example**: `/document/status/SCT-0143`
- **404**: Shipment not found

#### 4. GET /approval/status/{shptNo}
Approval details with D-5/D-15 SLA, priority (OVERDUE/CRITICAL/HIGH/NORMAL).
- **Parameters**: shptNo (required)
- **Example**: `/approval/status/SCT-0143`
- **200**: Returns empty array if no approvals
- **404**: Shipment not found

#### 5. GET /approval/summary
All approvals stats by type, status, D-15/D-5/overdue buckets.
- **Returns**: Global statistics for all approvals

#### 6. GET /document/events/{shptNo}
Chronological event ledger (latest first) for audit trail.
- **Parameters**: shptNo (required)
- **Example**: `/document/events/SCT-0143`
- **404**: Shipment not found

#### 7. GET /status/summary
KPI metrics - shipment count, doc rates, risk distribution, top bottlenecks.

#### 8. GET /bottleneck/summary
Bottleneck stats by code/category with aging (24h/48h/72h+) and shipment lists.

#### 9. POST /ingest/events
Batch event ingestion with deduplication and rate-limiting. For RPA/ETL systems.

---

## 🔐 Protected Fields (20 fields)

### Shipments (7 fields)
- shptNo
- currentBottleneckCode
- bottleneckSince
- riskLevel
- nextAction
- actionOwner
- dueAt

### Documents (3 fields)
- shptNo
- docType
- status

### Actions (6 fields)
- shptNo
- status
- priority
- dueAt
- actionText
- owner

### Events (4 fields)
- timestamp
- shptNo
- entityType
- toStatus

---

## 🚀 ChatGPT Actions Setup Guide

### Prerequisites
- **ChatGPT Plus subscription** (required for GPTs feature)
- **Access to GPT Builder** (ChatGPT → Explore GPTs → Create)

### Step 1: Create New GPT
1. Go to ChatGPT
2. Click "Explore GPTs" in left sidebar
3. Click "Create a GPT" or "My GPTs" → "Create"
4. Choose "Configure" tab (manual configuration)

### Step 2: Import Schema
1. In GPT Builder, scroll to "Actions" section
2. Click "Create new action"
3. Click "Import from URL"
4. Paste: `https://gets-logistics-api.vercel.app/openapi-schema.yaml`
5. Wait for schema import to complete

### Step 3: Configure Authentication
1. In Actions section, find "Authentication"
2. Select "Bearer" authentication type
3. Enter your Airtable Personal Access Token (PAT)
   - **Never share this token** - It's securely stored by OpenAI
   - Token scopes required: `data.records:read`, `data.records:write`
4. Test connection if available

### Step 4: Verify Import
Check that all 10 operations are loaded:
- ✅ getApiInfo
- ✅ getHealth
- ✅ verifyShipments
- ✅ getDocumentStatus
- ✅ getApprovalStatus
- ✅ getApprovalSummary
- ✅ getDocumentEvents
- ✅ getStatusSummary
- ✅ getBottleneckSummary
- ✅ ingestEvents

### Step 5: Upload Knowledge Files
1. Scroll to "Knowledge" section
2. Click "Upload files"
3. Upload the following files:
   - `Excel_Batch_Upload_Workflow.md`
   - `Common_Workflows.md`
   - `CHATGPT_SCHEMA_GUIDE.md` (optional, already in Instructions)
4. Wait for processing to complete

### Step 6: Configure Instructions
1. Scroll to "Instructions" field
2. Copy content from `GPT_INSTRUCTIONS.md` (ensure within 8,000 character limit)
3. Paste into Instructions field

### Step 7: Set Conversation Starters
1. Scroll to "Conversation starters" section
2. Add 4 conversation starters (see `GPT_CONVERSATION_STARTERS.md`)
3. Example:
   - 📊 현재 병목(bottleneck) 상황을 요약해줘
   - 🚢 SCT-0143 선적 상태를 자세히 보여줘
   - ⏰ D-5 또는 초과된 승인 건이 있어?
   - 📈 오늘의 KPI 대시보드를 보여줘

### Step 8: Test Endpoints
Try these queries in your GPT preview:
```
"Show me current bottlenecks"
"What's the status of SCT-0143?"
"Show all pending approvals"
"Give me KPI summary"
"Show approval status for SCT-0143"
```

### Step 9: Save and Publish
1. Click "Save" button (top right)
2. Choose visibility:
   - **Only me** - Private GPT
   - **Anyone with a link** - Shareable link
   - **Public** - Available in GPT Store (requires review)
3. Click "Confirm" to save

---

## 📈 Features

### v1.8.0 Updates
- ✅ Approval summary endpoint with D-5/D-15 SLA classification
- ✅ Bottleneck analysis with aging distribution
- ✅ Document event history tracking
- ✅ rename-safe fieldId parsing
- ✅ Z/UTC timezone support
- ✅ Duplicate endpoint definitions removed
- ✅ x-airtable metadata added
- ✅ x-protected-fields added (20 fields)

### Technical Features
- 🔄 Offset paging (automatic pagination)
- ⚡ Rate limiting (5 rps per base)
- 🔁 Retry logic (429, 503)
- 📦 Batch operations (≤10 records/req)
- 🔒 Upsert support (idempotent ingest)

---

## 🔐 Security & Authentication

### Actions Authentication Setup

**Recommended Authentication Method:**
- **Bearer Token** (for Airtable Personal Access Token)
- **API Key** (for custom API authentication)

**Security Best Practices:**
1. **Never hardcode tokens** - Use ChatGPT Actions authentication settings
2. **Token scopes** - Use minimal required scopes for Airtable PAT
   - Required: `data.records:read`, `data.records:write`
   - Optional: `schema.bases:read`
3. **Token rotation** - Rotate tokens periodically for security
4. **Environment separation** - Use different tokens for production and development
5. **Secure storage** - OpenAI securely stores authentication tokens, never expose in Instructions

### OpenAPI 3.1 Requirements

**GPTs Actions Requirements:**
- ✅ OpenAPI 3.1 schema format (current schema compliant)
- ✅ HTTPS endpoints only (all endpoints use HTTPS)
- ✅ Proper authentication configuration (Bearer token configured)
- ✅ Clear operation descriptions (all operations documented)
- ✅ Error response schemas (comprehensive error handling)

**Current Schema Compliance:**
- ✅ OpenAPI 3.1.0 format
- ✅ All endpoints use HTTPS
- ✅ Bearer token authentication configured
- ✅ Comprehensive error handling
- ✅ Schema version pinned in metadata (2025-12-25T00:32:52+0400)

### Privacy & Data Protection

**Important Considerations:**
- All API calls are logged by OpenAI for service improvement
- User inputs may be used to improve GPTs (can be disabled in settings)
- Airtable data is accessed in real-time, not stored by GPT
- Protected fields require explicit confirmation before modification

---

## 🎓 GPT Instructions (Recommended)

```markdown
You are the GETS Logistics Assistant for the HVDC Project.

## Capabilities
- Track shipment documents (BOE, DO, COO, HBL, CIPL)
- Monitor approvals (FANR, MOEI, MOIAT) with D-5/D-15 SLA
- Analyze bottlenecks and delays
- Provide real-time KPI metrics

## Data Source
- Real-time from Airtable
- Timezone: Asia/Dubai (+04:00)
- Schema Version: 2025-12-25T00:32:52+0400

## Endpoint Selection

For overview queries:
- "Show bottlenecks" → /bottleneck/summary
- "Approval status?" → /approval/summary
- "KPI summary?" → /status/summary

For specific shipments:
- "Status of SCT-0143?" → /document/status/{shptNo}
- "Approval for SCT-0143?" → /approval/status/{shptNo}
- "History of SCT-0143?" → /document/events/{shptNo}

## Response Format

Always highlight:
- 🔴 CRITICAL/OVERDUE items (D-0 or past due)
- 🟠 HIGH risk shipments (D-5 or less)
- ⚠️ Bottlenecks >48h

Format responses with:
1. **Summary**: Quick overview with key numbers
2. **Details**: Table format for clarity
3. **Highlights**: Call out urgent items
4. **Actions**: What needs to be done next

Example:
"📊 Bottleneck Summary (as of [time] GST)

📈 Overview: 7 active bottlenecks
🔴 CRITICAL: 1 shipment (use actual shipment number from response)
🟠 HIGH: 5 shipments (4 INSPECT_RED, 1 FANR_PENDING)

⚠️ Urgent Actions:
1. Use actual shptNo from API response: FANR approval due in 1h
2. Use actual shptNo from API response: Correct details immediately"

Use tables for multi-item data.
Always provide timestamps in GST (Dubai time).
Suggest follow-up queries when relevant.
```

---

## 🧪 Test Results

### Production Tests (2025-12-25)
```
✅ / - API Info (200 OK)
✅ /health - Health Check (200 OK)
✅ /bottleneck/summary - Real data (7 bottlenecks)
✅ /status/summary - KPI metrics (21 shipments)
✅ /document/status/SCT-0143 - Document tracking
✅ /approval/status/SCT-0143 - Approval status
✅ /document/events/SCT-0143 - Event history
✅ /openapi-schema.yaml - Schema accessible
```

**Success Rate**: 8/9 (88.9%) - Only /api/docs returning 404 (Swagger UI, not critical)

---

## 📝 Changelog

### v1.8.0 (2025-12-25)
- Added x-airtable-baseId and x-airtable-schemaVersion metadata
- Added x-protected-fields (20 fields across 4 tables)
- Removed duplicate endpoint definitions
- Added / and /health endpoint documentation
- Improved descriptions for ChatGPT compatibility
- Consistent response schemas across all endpoints

### v1.7.0 (2025-12-24)
- Added /approval/status/{shptNo}
- Added /approval/summary
- Added /bottleneck/summary
- Added /document/events/{shptNo}
- Implemented rename-safe parsing
- Added D-5/D-15 SLA classification

### v1.6.0 (2025-12-23)
- Enhanced /document/status with evidence and boeRedRisk
- Added monitoring and logging
- Improved error handling

---

## 🔗 Resources

- **API Base**: https://gets-logistics-api.vercel.app
- **OpenAPI Schema**: https://gets-logistics-api.vercel.app/openapi-schema.yaml
- **Health Check**: https://gets-logistics-api.vercel.app/health
- **GitHub**: https://github.com/macho715/GETS-Logistics-API

---

## ✅ Status

**API**: ✅ Production Ready
**Schema**: ✅ v1.8.0 Deployed
**ChatGPT Actions**: ✅ Fully Compatible
**Protected Fields**: ✅ 20 fields pinned
**Schema Version**: ✅ 2025-12-25T00:32:52+0400

**Ready to import! 🚀**

