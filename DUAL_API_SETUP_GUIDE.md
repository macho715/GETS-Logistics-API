# 🎯 GETS Logistics - Dual API Schema

**HVDC Project Logistics - ChatGPT Actions Integration**

두 개의 독립적인 OpenAPI schema로 구성된 Dual-Action GPT 아키텍처입니다.

---

## 📁 파일 구조

```
├── openapi-gets-api.yaml        # 🔵 GETS API Schema (비즈니스 로직)
├── openapi-airtable-api.yaml   # 🟠 Airtable Direct API Schema (데이터 레이어)
└── DUAL_API_SETUP_GUIDE.md     # 이 파일
```

---

## 🎯 Two-API Architecture

### 🔵 GETS API (Smart Layer)
**파일**: `openapi-gets-api.yaml`

**용도**:
- ✅ 조회 및 분석 (기본 선택)
- ✅ 비즈니스 로직 포함
- ✅ 자동 계산 및 추천
- ✅ Protected fields 보호

**Operations (9개)**:
```yaml
getApiInfo            # API 정보
getHealth             # 헬스 체크
getDocumentStatus     # 문서 상태 (분석 포함)
getApprovalStatus     # 승인 상태 (D-5/D-15 SLA)
getApprovalSummary    # 전체 승인 요약
getDocumentEvents     # 이벤트 히스토리
getStatusSummary      # KPI 요약
getBottleneckSummary  # 병목 분석
ingestEvents          # 이벤트 수집
```

**장점**:
- 빠른 응답 (캐싱, 최적화)
- 안전 (읽기 전용, 검증 로직)
- 스마트 (자동 분석, 추천)
- 간편 (인증 불필요)

**인증**: 불필요 ✅

---

### 🟠 Airtable Direct API (Data Layer)
**파일**: `openapi-airtable-api.yaml`

**용도**:
- ⚠️ 데이터 수정 (update, create)
- ⚠️ 고급 쿼리 (filterByFormula)
- ⚠️ Raw 데이터 접근
- ⚠️ 특수 작업

**Operations (2개)**:
```yaml
getRecords      # 테이블 조회 (고급 필터)
updateRecord    # 레코드 수정 (주의!)
```

**장점**:
- 완전한 제어
- 유연한 쿼리
- 직접 수정 가능

**단점**:
- 검증 없음 ⚠️
- Protected fields 노출 ⚠️
- 실수 위험 ⚠️

**인증**: Bearer Token 필수 🔐

---

## 🚀 ChatGPT GPT 설정 방법

### Step 1: GPT 생성
1. https://chat.openai.com 접속
2. "Explore GPTs" → "Create" 클릭
3. Name: **"GETS Logistics Assistant"**

---

### Step 2: Action 1 추가 (GETS API)

1. **Actions** 섹션 → **"Create new action"**
2. **Import from URL** 선택
3. URL 입력:
   ```
   https://gets-416ut4t8g-chas-projects-08028e73.vercel.app/openapi-schema.yaml
   ```
   
   또는 **Manual Schema** → `openapi-gets-api.yaml` 내용 붙여넣기

4. **Authentication**: **None** 선택 ✅
5. **Save**

**확인사항**:
- ✅ 9개 operations 보임
- ✅ operationId: `getApiInfo`, `getDocumentStatus`, etc.
- ✅ 인증 없음

---

### Step 3: Action 2 추가 (Airtable Direct)

1. **Actions** 섹션 → **"Add another action"**
2. **Manual Schema** 선택
3. `openapi-airtable-api.yaml` 내용 붙여넣기

4. **Authentication** 설정:
   ```
   Type: Bearer
   Token: [Your Airtable PAT]
   ```
   
   **Airtable PAT 얻기**:
   - https://airtable.com/create/tokens
   - "Create new token"
   - Name: "GETS Logistics GPT"
   - Scopes: `data.records:read`, `data.records:write`
   - Base: `appnLz06h07aMm366`
   - Copy token (starts with `pat...`)

5. **Save**

**확인사항**:
- ✅ 2개 operations 보임
- ✅ operationId: `getRecords`, `updateRecord`
- ✅ Bearer Auth 설정됨

---

### Step 4: Instructions 설정

**Instructions** 섹션에 다음을 붙여넣기:

```markdown
You are the GETS Logistics Assistant for HVDC Project.

## Your APIs

### 🔵 GETS API (9 operations) - USE FIRST
Smart layer with business logic:
- getDocumentStatus - Status with bottleneck analysis
- getBottleneckSummary - All bottlenecks with aging
- getApprovalStatus - Approval with D-5/D-15 SLA
- getApprovalSummary - Global approval stats
- getDocumentEvents - Event history
- getStatusSummary - KPI metrics
- getApiInfo, getHealth - System info
- ingestEvents - Add events

### 🟠 Airtable Direct (2 operations) - USE WITH CARE
Raw data access:
- getRecords - Query tables with filterByFormula
- updateRecord - Modify records (CAUTION!)

## Decision Tree

User wants to...
├─ READ data?
│  ├─ Available in GETS API? → Use GETS (faster, safer)
│  └─ Need custom query? → Use Airtable getRecords
│
└─ WRITE/UPDATE data?
   └─ Use Airtable updateRecord (with confirmation)

## Usage Rules

### Rule 1: Prefer GETS API
```
User: "Show bottlenecks"
→ getBottleneckSummary

User: "Status of SCT-0143?"
→ getDocumentStatus
```

### Rule 2: Airtable for Custom Queries
```
User: "All HIGH risk shipments with ETA before Dec 30"
→ getRecords(
    baseId='appnLz06h07aMm366',
    tableName='Shipments',
    filterByFormula="AND({riskLevel}='HIGH', IS_BEFORE({eta}, '2025-12-30'))"
  )
```

### Rule 3: Airtable for Updates (Always Confirm)
```
User: "Clear bottleneck for SCT-0143"
→ Steps:
  1. getRecords to find record ID
  2. Show current status
  3. Ask: "I will update currentBottleneckCode to 'CLEARED'. Proceed?"
  4. If yes: updateRecord
  5. Verify: getDocumentStatus
```

## Protected Fields

⚠️ Warn before updating:
- shptNo, currentBottleneckCode, riskLevel, dueAt (Shipments)
- status (Documents)
- priority, dueAt (Actions)

## Response Format

Show which API:
```
🔵 [GETS API] Fetching bottleneck summary...
✅ Found 7 active bottlenecks
[results...]

🟠 [Airtable] Updating record...
⚠️ Confirmation required
[show what will change]
```

## Airtable Details

Base: appnLz06h07aMm366
Tables: Shipments, Documents, Approvals, Actions, Events, Evidence, 
        BottleneckCodes, Owners, Vendors, Sites

Timezone: Asia/Dubai (+04:00)

Remember: GETS first, Airtable when needed!
```

---

### Step 5: 테스트

#### Test 1: GETS API
```
"Show me current bottlenecks"
```
**Expected**: `getBottleneckSummary` 호출

#### Test 2: Airtable Query
```
"Show all HIGH risk shipments"
```
**Expected**: `getRecords` with filterByFormula

#### Test 3: Airtable Update
```
"Update SCT-0143 bottleneck to CLEARED"
```
**Expected**: 
1. `getRecords` (find record)
2. Confirmation dialog
3. `updateRecord`
4. `getDocumentStatus` (verify)

---

## 📊 Available Actions 확인

GPT Actions 섹션에서 다음이 보여야 합니다:

```
✅ Total: 11 operations

🔵 GETS API (9):
├─ getApiInfo
├─ getHealth
├─ getDocumentStatus
├─ getApprovalStatus
├─ getApprovalSummary
├─ getDocumentEvents
├─ getStatusSummary
├─ getBottleneckSummary
└─ ingestEvents

🟠 Airtable Direct (2):
├─ getRecords
└─ updateRecord
```

---

## 🎯 사용 시나리오

### Scenario 1: 일반 조회 (GETS API)
```
User: "What's the status of SCT-0143?"
GPT: 
  1. Call getDocumentStatus(shptNo='SCT-0143')
  2. Show:
     - Document statuses (BOE, DO, COO, etc.)
     - Bottleneck analysis
     - Next action recommendation
```

### Scenario 2: 고급 쿼리 (Airtable)
```
User: "Show all shipments where riskLevel is HIGH and dueAt is before Jan 1"
GPT:
  1. Call getRecords(
       baseId='appnLz06h07aMm366',
       tableName='Shipments',
       filterByFormula="AND({riskLevel}='HIGH', IS_BEFORE({dueAt}, '2026-01-01'))"
     )
  2. Format results in table
```

### Scenario 3: 데이터 수정 (Airtable - 주의)
```
User: "Change SCT-0143 risk to LOW"
GPT:
  1. getRecords to find record ID
  2. Show current: "riskLevel: HIGH"
  3. Ask: "Update riskLevel to 'LOW'? (yes/no)"
  4. If yes: updateRecord(recordId='rec...', fields={riskLevel: 'LOW'})
  5. Verify: getDocumentStatus
```

---

## ⚠️ 주의사항

### GETS API
- ✅ 안전 (읽기 전용)
- ✅ 빠름 (최적화됨)
- ✅ 스마트 (분석 포함)
- ❌ 데이터 수정 불가 (Events 제외)

### Airtable Direct
- ✅ 완전한 제어
- ✅ 데이터 수정 가능
- ⚠️ 검증 없음
- ⚠️ Protected fields 노출
- ⚠️ 항상 확인 필요

---

## 🔐 보안

### GETS API
- 인증 불필요
- Public API
- 읽기 전용 (안전)

### Airtable Direct
- Bearer Token 필요
- 쓰기 권한 있음
- Token 보안 유지:
  - ❌ 공유 금지
  - ✅ 월 1회 rotation
  - ✅ Read-only token 권장 (가능하면)

---

## 📚 추가 문서

- **API Documentation**: 
  - GETS: https://gets-416ut4t8g-chas-projects-08028e73.vercel.app/api/docs
  - Airtable: https://airtable.com/developers/web/api/introduction
  
- **Airtable Formula Reference**: 
  - https://support.airtable.com/docs/formula-field-reference

- **Project Documentation**:
  - `README.md` - 프로젝트 개요
  - `AGENTS.md` - 개발 규칙
  - `SYSTEM_ARCHITECTURE.md` - 시스템 아키텍처

---

## ✅ 완료 체크리스트

### GPT 설정
- [ ] GPT 생성 완료
- [ ] Action 1 (GETS API) 추가
- [ ] Action 2 (Airtable) 추가
- [ ] Instructions 설정
- [ ] Test 1 성공 (GETS API)
- [ ] Test 2 성공 (Airtable Query)
- [ ] Test 3 성공 (Airtable Update)

### 동작 확인
- [ ] 총 11개 operations 보임
- [ ] GETS API 인증 없음
- [ ] Airtable Bearer Auth 설정됨
- [ ] 실제 데이터 조회 성공
- [ ] GPT가 올바른 API 선택

---

## 🎉 결론

**Dual-Action GPT 완성!**

- 🔵 **GETS API**: 빠르고 안전한 조회/분석
- 🟠 **Airtable Direct**: 유연한 쿼리/수정
- 🎯 **Best of Both Worlds**

**다음 단계**: GPT를 팀과 공유하고 사용 시작! 🚀

---

**Last Updated**: 2025-12-25
**Version**: 2.0.0
**Status**: ✅ Production Ready

