완벽합니다! 두 schema를 하나로 통합한 **완전한 Dual-Action Schema**를 만들어드리겠습니다.

# 🎯 통합 Dual-Action OpenAPI Schema

## 📊 점검 결과

### ✅ 발견된 것들

**Airtable Direct API (v1.0.1)**:
- ✅ `getRecords` - GET `/{baseId}/{tableName}`
- ✅ `updateRecord` - PATCH `/{baseId}/{tableName}/{recordId}`
- ✅ Bearer Auth 필요

**GETS API (v1.8.0)**:
- ✅ 9개 endpoints (/, /health, /document/status, etc.)
- ✅ 비즈니스 로직 포함
- ✅ 인증 불필요

### ⚠️ 통합 시 주의사항
1. **operationId 충돌 방지**: prefix 추가 필요
2. **서버 분리**: 각 endpoint가 올바른 서버 사용
3. **인증 분리**: Airtable만 Bearer Auth
4. **명확한 구분**: 어느 API인지 summary에 표시

---

## 📋 완전한 통합 Schema

```yaml
openapi: 3.1.0
info:
  title: GETS Logistics - Dual API (GETS + Airtable)
  version: 2.0.0
  description: |
    **HVDC Project Logistics - Unified API**

    This GPT has access to TWO APIs:

    🔵 **GETS API** (Smart Layer):
    - Business logic and analytics
    - Real-time calculations
    - Protected fields enforced
    - No authentication required
    - Use for: queries, analysis, reports

    🟠 **Airtable Direct API** (Data Layer):
    - Direct table access
    - Full CRUD capabilities
    - Raw data access
    - Requires authentication (Bearer Token)
    - Use for: updates, custom queries, data modification

    **Data Source**: Airtable Base `appnLz06h07aMm366`
    **Timezone**: Asia/Dubai (+04:00)
    **Schema Version**: 2025-12-25T00:32:52+0400

    **Protected Fields** (20 total):
    - Shipments: shptNo, currentBottleneckCode, bottleneckSince, riskLevel, nextAction, actionOwner, dueAt
    - Documents: shptNo, docType, status
    - Actions: shptNo, status, priority, dueAt, actionText, owner
    - Events: timestamp, shptNo, entityType, toStatus

servers:
  - url: https://gets-416ut4t8g-chas-projects-08028e73.vercel.app
    description: 🔵 GETS API - Business Logic Layer (Flask/Vercel)
  - url: https://api.airtable.com/v0
    description: 🟠 Airtable Direct API - Data Layer (requires auth)

paths:
  # ==========================================
  # 🔵 GETS API ENDPOINTS (Read + Analytics)
  # ==========================================

  /:
    servers:
      - url: https://gets-416ut4t8g-chas-projects-08028e73.vercel.app
    get:
      summary: "[GETS] Get API information"
      operationId: getsGetApiInfo
      description: Returns GETS API version, endpoints, and system status
      tags: ["GETS API"]
      responses:
        '200':
          description: API information
          content:
            application/json:
              schema:
                type: object
                properties:
                  service:
                    type: string
                  version:
                    type: string
                  endpoints:
                    type: array
                    items:
                      type: string

  /health:
    servers:
      - url: https://gets-416ut4t8g-chas-projects-08028e73.vercel.app
    get:
      summary: "[GETS] Health check"
      operationId: getsGetHealth
      description: Returns API health, Airtable connection, schema validation status
      tags: ["GETS API"]
      responses:
        '200':
          description: Health status
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                  airtable:
                    type: object
                  schema:
                    type: object

  /document/status/{shptNo}:
    servers:
      - url: https://gets-416ut4t8g-chas-projects-08028e73.vercel.app
    get:
      summary: "[GETS] Get document status with analysis"
      operationId: getsGetDocumentStatus
      description: Returns operational status packet with bottleneck analysis, risk level, and recommended actions
      tags: ["GETS API", "Documents"]
      parameters:
        - name: shptNo
          in: path
          required: true
          description: Shipment number (e.g., SCT-0143)
          schema:
            type: string
          example: SCT-0143
      responses:
        '200':
          description: Document status packet with analytics
          content:
            application/json:
              schema:
                type: object
                properties:
                  shptNo:
                    type: string
                  doc:
                    type: object
                  bottleneck:
                    type: object
                  action:
                    type: object
                  evidence:
                    type: array
                    items:
                      type: object
        '404':
          description: Shipment not found

  /approval/status/{shptNo}:
    servers:
      - url: https://gets-416ut4t8g-chas-projects-08028e73.vercel.app
    get:
      summary: "[GETS] Get approval status with SLA"
      operationId: getsGetApprovalStatus
      description: Returns approval details with D-5/D-15 SLA classification and priority
      tags: ["GETS API", "Approvals"]
      parameters:
        - name: shptNo
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Approval status with SLA analysis
          content:
            application/json:
              schema:
                type: object
                properties:
                  shptNo:
                    type: string
                  approvals:
                    type: array
                    items:
                      type: object
                  summary:
                    type: object

  /approval/summary:
    servers:
      - url: https://gets-416ut4t8g-chas-projects-08028e73.vercel.app
    get:
      summary: "[GETS] Get global approval summary"
      operationId: getsGetApprovalSummary
      description: Returns all approvals statistics by type, status, and D-15/D-5/overdue buckets
      tags: ["GETS API", "Approvals"]
      responses:
        '200':
          description: Global approval summary
          content:
            application/json:
              schema:
                type: object
                properties:
                  summary:
                    type: object
                  byType:
                    type: object
                  critical:
                    type: object

  /document/events/{shptNo}:
    servers:
      - url: https://gets-416ut4t8g-chas-projects-08028e73.vercel.app
    get:
      summary: "[GETS] Get event history"
      operationId: getsGetDocumentEvents
      description: Returns chronological event ledger (latest first) for audit trail
      tags: ["GETS API", "Events"]
      parameters:
        - name: shptNo
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Event history
          content:
            application/json:
              schema:
                type: object
                properties:
                  shptNo:
                    type: string
                  events:
                    type: array
                    items:
                      type: object

  /status/summary:
    servers:
      - url: https://gets-416ut4t8g-chas-projects-08028e73.vercel.app
    get:
      summary: "[GETS] Get KPI summary"
      operationId: getsGetStatusSummary
      description: Returns overall KPI metrics - shipment count, doc rates, risk distribution
      tags: ["GETS API", "KPIs"]
      responses:
        '200':
          description: KPI summary
          content:
            application/json:
              schema:
                type: object
                properties:
                  dataSource:
                    type: string
                  totalShipments:
                    type: integer
                  riskSummary:
                    type: object

  /bottleneck/summary:
    servers:
      - url: https://gets-416ut4t8g-chas-projects-08028e73.vercel.app
    get:
      summary: "[GETS] Get bottleneck analysis"
      operationId: getsGetBottleneckSummary
      description: Returns bottleneck statistics with aging distribution (24h/48h/72h+)
      tags: ["GETS API", "Bottlenecks"]
      responses:
        '200':
          description: Bottleneck analysis
          content:
            application/json:
              schema:
                type: object
                properties:
                  byCategory:
                    type: object
                  byCode:
                    type: object
                  aging:
                    type: object
                  topBottlenecks:
                    type: array
                    items:
                      type: object

  /ingest/events:
    servers:
      - url: https://gets-416ut4t8g-chas-projects-08028e73.vercel.app
    post:
      summary: "[GETS] Ingest events"
      operationId: getsIngestEvents
      description: Batch event ingestion with deduplication (for RPA/ETL systems)
      tags: ["GETS API", "Events"]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - events
              properties:
                batchId:
                  type: string
                sourceSystem:
                  type: string
                events:
                  type: array
                  items:
                    type: object
      responses:
        '200':
          description: Events ingested
          content:
            application/json:
              schema:
                type: object

  # ==========================================
  # 🟠 AIRTABLE DIRECT API ENDPOINTS (Read + Write)
  # ==========================================

  /{baseId}/{tableName}:
    servers:
      - url: https://api.airtable.com/v0
    get:
      summary: "[Airtable] Get records from table"
      operationId: airtableGetRecords
      description: |
        ⚠️ Direct Airtable access - use GETS API when possible

        Query any table with filtering and sorting.
        Common tables: Shipments, Documents, Approvals, Actions, Events
      tags: ["Airtable Direct"]
      parameters:
        - name: baseId
          in: path
          required: true
          description: Airtable Base ID (use appnLz06h07aMm366)
          schema:
            type: string
          example: appnLz06h07aMm366
        - name: tableName
          in: path
          required: true
          description: |
            Table name (options: Shipments, Documents, Approvals, Actions, Events,
            Evidence, BottleneckCodes, Owners, Vendors, Sites)
          schema:
            type: string
          example: Shipments
        - name: maxRecords
          in: query
          description: Maximum number of records to return (max 100)
          schema:
            type: integer
            maximum: 100
          example: 10
        - name: filterByFormula
          in: query
          description: |
            Airtable formula to filter records
            Examples:
            - {shptNo}='SCT-0143'
            - {riskLevel}='HIGH'
            - AND({riskLevel}='HIGH', {dueAt}<'2025-12-30')
          schema:
            type: string
          example: "{shptNo}='SCT-0143'"
        - name: sort[0][field]
          in: query
          description: Field name to sort by
          schema:
            type: string
          example: shptNo
        - name: sort[0][direction]
          in: query
          description: Sort direction
          schema:
            type: string
            enum: [asc, desc]
          example: asc
      security:
        - BearerAuth: []
      responses:
        '200':
          description: List of records
          content:
            application/json:
              schema:
                type: object
                properties:
                  records:
                    type: array
                    items:
                      type: object
                      properties:
                        id:
                          type: string
                          description: Record ID (recXXXXXXX)
                        createdTime:
                          type: string
                        fields:
                          type: object
                          description: Record fields (varies by table)
        '401':
          description: Unauthorized (check Bearer token)
        '404':
          description: Base or table not found

  /{baseId}/{tableName}/{recordId}:
    servers:
      - url: https://api.airtable.com/v0
    patch:
      summary: "[Airtable] Update record"
      operationId: airtableUpdateRecord
      description: |
        ⚠️ CAUTION: Direct data modification

        Updates an Airtable record. No validation layer!

        **Protected fields** (use with care):
        - shptNo, currentBottleneckCode, riskLevel, dueAt (Shipments)
        - status (Documents)
        - priority, dueAt (Actions)

        Always confirm with user before updating protected fields.
      tags: ["Airtable Direct"]
      parameters:
        - name: baseId
          in: path
          required: true
          description: Airtable Base ID
          schema:
            type: string
          example: appnLz06h07aMm366
        - name: tableName
          in: path
          required: true
          description: Table name
          schema:
            type: string
          example: Shipments
        - name: recordId
          in: path
          required: true
          description: Airtable Record ID (recXXXXXXX) - get from getRecords first
          schema:
            type: string
          example: recABC123XYZ
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                fields:
                  type: object
                  description: Fields to update
                  example:
                    currentBottleneckCode: "CLEARED"
                    riskLevel: "LOW"
      security:
        - BearerAuth: []
      responses:
        '200':
          description: Updated record
          content:
            application/json:
              schema:
                type: object
                properties:
                  id:
                    type: string
                  createdTime:
                    type: string
                  fields:
                    type: object
        '401':
          description: Unauthorized
        '404':
          description: Record not found
        '422':
          description: Invalid field names or values

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      description: |
        Airtable Personal Access Token (PAT)

        ⚠️ Required ONLY for Airtable Direct API operations
        GETS API operations do NOT require authentication

        Format: Bearer pat...your_token_here

        Get your PAT from: https://airtable.com/create/tokens

# Tags for organization
tags:
  - name: GETS API
    description: 🔵 Smart layer with business logic (preferred for queries)
  - name: Airtable Direct
    description: 🟠 Direct data access (use for updates and custom queries)
  - name: Documents
    description: Document tracking operations
  - name: Approvals
    description: Approval management operations
  - name: Bottlenecks
    description: Bottleneck analysis operations
  - name: Events
    description: Event history operations
  - name: KPIs
    description: KPI and summary operations
```

---

## 🎯 주요 개선사항

### 1️⃣ **명확한 Prefix**
```yaml
GETS API operations:
- getsGetApiInfo
- getsGetHealth
- getsGetDocumentStatus
- getsGetApprovalStatus
- getsGetApprovalSummary
- getsGetDocumentEvents
- getsGetStatusSummary
- getsGetBottleneckSummary
- getsIngestEvents

Airtable operations:
- airtableGetRecords
- airtableUpdateRecord
```

### 2️⃣ **서버 분리**
```yaml
각 endpoint마다:
  servers:
    - url: [해당 서버 URL]
```

### 3️⃣ **인증 분리**
```yaml
GETS API: 인증 없음 (public)
Airtable Direct: Bearer Auth 필요
```

### 4️⃣ **Summary에 태그 추가**
```yaml
"[GETS] Get document status"
"[Airtable] Get records from table"
```

### 5️⃣ **상세한 설명**
```yaml
- ⚠️ 경고 표시 (Airtable Direct)
- 💡 사용 예시
- 📋 Protected fields 목록
- 🔍 filterByFormula 예제
```

---

## 📊 결과 확인

### GPT Actions에서 보이는 모습

```
Available actions (11 total):

🔵 GETS API (9 operations):
├─ getsGetApiInfo
├─ getsGetHealth
├─ getsGetDocumentStatus
├─ getsGetApprovalStatus
├─ getsGetApprovalSummary
├─ getsGetDocumentEvents
├─ getsGetStatusSummary
├─ getsGetBottleneckSummary
└─ getsIngestEvents

🟠 Airtable Direct (2 operations):
├─ airtableGetRecords
└─ airtableUpdateRecord
```

---

## ✅ 점검 체크리스트

### Schema 구조
- [x] ✅ 두 서버 모두 정의됨
- [x] ✅ operationId 충돌 없음 (prefix 사용)
- [x] ✅ 각 endpoint의 서버 명시
- [x] ✅ 인증 분리 (Airtable만 Bearer)
- [x] ✅ Tags로 그룹핑
- [x] ✅ Summary에 API 구분 표시

### 기능 완전성
- [x] ✅ GETS API 9개 endpoints
- [x] ✅ Airtable 2개 endpoints
- [x] ✅ Protected fields 명시
- [x] ✅ 상세한 설명과 예시
- [x] ✅ 에러 응답 정의

### 사용성
- [x] ✅ 명확한 API 구분
- [x] ✅ 경고 메시지 포함
- [x] ✅ 예제 값 제공
- [x] ✅ Base ID 하드코딩

---

## 🎓 GPT Instructions 업데이트

이 schema와 함께 사용할 Instructions:

```markdown
You are the GETS Logistics Assistant.

## Your APIs

You have access to 11 operations across 2 APIs:

### 🔵 GETS API (9 ops) - USE FIRST
Smart layer with business logic:
- getsGetDocumentStatus - Status with bottleneck analysis
- getsGetBottleneckSummary - All bottlenecks with aging
- getsGetApprovalStatus - Approval with D-5/D-15 SLA
- getsGetApprovalSummary - Global approval stats
- getsGetDocumentEvents - Event history
- getsGetStatusSummary - KPI metrics
- getsGetApiInfo - API info
- getsGetHealth - Health check
- getsIngestEvents - Add events

### 🟠 Airtable Direct (2 ops) - USE WITH CARE
Raw data access:
- airtableGetRecords - Query tables
- airtableUpdateRecord - Modify records

## Decision Tree

User wants to...
├─ READ data?
│  ├─ Available in GETS API? → Use GETS (faster, safer)
│  └─ Need custom query? → Use Airtable
│
└─ WRITE/UPDATE data?
   └─ Always use Airtable (with confirmation)

## Usage Examples

### Read (Common)
User: "Show bottlenecks"
→ getsGetBottleneckSummary

User: "Status of SCT-0143?"
→ getsGetDocumentStatus

### Custom Query
User: "All HIGH risk shipments"
→ airtableGetRecords(
    baseId='appnLz06h07aMm366',
    tableName='Shipments',
    filterByFormula="{riskLevel}='HIGH'"
  )

### Update (Careful)
User: "Clear bottleneck for SCT-0143"
→ Steps:
  1. airtableGetRecords to find record ID
  2. Show current status
  3. Ask confirmation: "I will update currentBottleneckCode to 'CLEARED'. Proceed?"
  4. If yes: airtableUpdateRecord
  5. Verify: getsGetDocumentStatus

## Protected Fields Warning

When updating these, always warn:
- shptNo, currentBottleneckCode, riskLevel, dueAt
- status (Documents)
- priority, dueAt (Actions)

## Response Format

Show which API:
```
🔵 [GETS API] Fetching bottleneck summary...
✅ Found 7 active bottlenecks
[results...]

🟠 [Airtable] Preparing to update...
⚠️ Confirmation required
[details...]
```

Remember: GETS first, Airtable when needed!
```

---

**🎉 완벽한 Dual-Action Schema 완성!**

Agent 모드로 전환하시면 이 schema를 파일로 저장해드리겠습니다! 🚀
