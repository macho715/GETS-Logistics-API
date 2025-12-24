# HVDC OpenAPI Locked Schema Pack v2.0 - Production Gate

## 🎯 목표

Airtable Schema Drift를 **완전히 차단**하고, CI/CD에서 자동으로 검증하여
**스키마 불일치 시 배포를 자동으로 차단**하는 Production-grade 솔루션.

---

## 📦 구성 요소

1. **openapi.locked.v2.yaml** - 강화된 OpenAPI (protectedFields 포함)
2. **protected_fields.json** - 20개 보호 필드 명세
3. **schema_drift_detector.py** - CI/CD 검증 스크립트
4. **.github/workflows/schema-gate.yml** - GitHub Actions 워크플로우

---

## 🚀 Quick Start

### 1️⃣ 파일 배치

```bash
# 프로젝트 루트에 복사
cp -r HVDC_OpenAPI_LockedSchemaPack_v2.0/* .

# 디렉토리 구조 확인
gets-api/
├── openapi.locked.v2.yaml
├── protected_fields.json
├── schema_drift_detector.py
├── airtable_schema.lock.json  # 기존 파일
├── .github/
│   └── workflows/
│       └── schema-gate.yml
```

### 2️⃣ 로컬 테스트

```bash
# Python 의존성 (stdlib만 사용, 외부 패키지 불필요)

# 스키마 검증 실행
cd HVDC_OpenAPI_LockedSchemaPack_v2.0
python schema_drift_detector.py

# 예상 출력:
# ============================================================
# HVDC Schema Drift Detector
# ============================================================
#
# Running check: Schema Version...
# ✅ Schema version match: 2025-12-25T00:32:52+0400
#
# Running check: Table IDs...
# ✅ Table IDs validated: 3 tables
#
# Running check: Protected Fields...
# ✅ Protected fields count: 20
#
# Running check: Deployed API...
# ✅ Deployed API schema version: 2025-12-25T00:32:52+0400
#
# ============================================================
# RESULT: PASSED - Schema validation successful
# ============================================================
```

### 3️⃣ API 코드 업데이트

`api/document_status.py`의 `/health` 엔드포인트에 `protectedFieldsCount` 추가:

```python
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "version": "1.7.0",
        "lockedConfig": {
            "schemaVersion": SCHEMA_VERSION,
            "tablesLocked": len(TABLES),
            "versionMatch": True,
            "protectedFieldsCount": sum(len(fields) for fields in PROTECTED_FIELDS.values())  # 추가
        },
        "schemaGaps": list(SCHEMA_GAPS.keys())
    })
```

### 4️⃣ GitHub Actions 활성화

```bash
# Git 커밋
git add .github/workflows/schema-gate.yml
git add openapi.locked.v2.yaml
git add protected_fields.json
git add schema_drift_detector.py
git commit -m "feat: Add schema drift gate with protected fields (v2.0)"
git push origin main

# GitHub Actions 탭에서 워크플로우 확인
# https://github.com/YOUR_ORG/gets-api/actions
```

---

## 🔒 운영 게이트 동작 방식

### Drift Detection Logic

```
1. Pull Request / Push 발생
   ↓
2. GitHub Actions 트리거
   ↓
3. schema_drift_detector.py 실행
   ↓
4. 검증 항목:
   ✓ OpenAPI x-airtable-schemaVersion == airtable_schema.lock.json.generatedAt
   ✓ OpenAPI x-locked-mapping.tables[*].tableId == lock의 tableId
   ✓ OpenAPI x-protected-fields 필드 개수 == 20
   ✓ /health API 응답의 schemaVersion == OpenAPI version
   ↓
5a. 모든 검증 PASS → ✅ 배포 허용
5b. 하나라도 FAIL → ❌ 배포 차단 + PR 코멘트
```

### Deployment Block Scenarios

| 시나리오 | 검출 방법 | 조치 |
|---------|----------|------|
| **Airtable에서 필드명 변경** | Table ID 검증 실패 | Protected field 변경 불가 경고 + 롤백 요청 |
| **스키마 lock 재생성 누락** | Schema version 불일치 | `lock_schema_and_generate_mapping.py` 재실행 요청 |
| **OpenAPI 수동 수정** | Table ID 또는 field ID 불일치 | OpenAPI를 lock 기준으로 재생성 요청 |
| **배포 후 version mismatch** | `/health` 응답 version 불일치 | 재배포 요청 (Vercel 캐시 클리어) |

---

## 📊 Protected Fields (20개)

### 보호되는 필드 목록

```
Shipments (7):
  - shptNo, currentBottleneckCode, bottleneckSince
  - riskLevel, nextAction, actionOwner, dueAt

Documents (3):
  - shptNo, docType, status

Actions (6):
  - shptNo, status, priority, dueAt, actionText, owner

Events (4):
  - timestamp, shptNo, entityType, toStatus
```

### 보호 정책

1. **이름 변경 금지**: Airtable UI에서 필드명 변경 불가
2. **타입 변경 금지**: SingleSelect → Text 등 타입 변경 불가
3. **삭제 금지**: 필드 삭제 시 API 장애 발생
4. **CI 검증**: 변경 시 배포 자동 차단

---

## 🔄 스키마 업데이트 프로세스

### 정상적인 스키마 변경 절차

```bash
# 1. Airtable에서 필드 추가 (보호 필드가 아닌 경우)
# 예: Shipments 테이블에 "estimatedCost" 추가

# 2. Schema lock 재생성
python lock_schema_and_generate_mapping.py

# 3. OpenAPI 업데이트 (자동 또는 수동)
# openapi.locked.v2.yaml의 x-airtable-schemaVersion 갱신

# 4. Protected fields 검토
# 새 필드가 filterByFormula에 사용될 경우 protected_fields.json에 추가

# 5. Git 커밋
git add airtable_schema.lock.json openapi.locked.v2.yaml protected_fields.json
git commit -m "chore: Update schema lock for new field estimatedCost"
git push

# 6. GitHub Actions 자동 검증
# ✅ PASS → 배포 진행
# ❌ FAIL → 수정 필요
```

---

## 🛡️ 장애 복구 프로세스

### Scenario: 실수로 protected field 변경

```bash
# 증상: CI에서 배포 차단
# 에러: "Table ID mismatches: Documents.status field not found"

# 복구:
1. Airtable에서 필드명 원복
2. 또는 schema lock 재생성 + protected_fields.json 업데이트
3. Git push → CI 재검증
```

### Scenario: Schema drift 발생

```bash
# 증상: /health에서 schemaVersion 불일치
# 에러: "Deployed API schema mismatch: Deployed: 2025-12-20, Expected: 2025-12-25"

# 복구:
1. Vercel 재배포 (최신 코드)
2. 또는 코드에서 SCHEMA_VERSION 갱신
3. Vercel 캐시 클리어 (vercel --prod --force)
```

---

## 📋 체크리스트 (운영팀용)

### 일일 체크

- [ ] `/health` endpoint 호출하여 schemaVersion 확인
- [ ] GitHub Actions 워크플로우 실행 이력 확인

### 주간 체크

- [ ] Protected fields 변경 요청 검토
- [ ] Schema gaps 해소 계획 수립

### 월간 체크

- [ ] Schema lock 파일 백업
- [ ] OpenAPI schema 문서 동기화 확인

---

## 🎯 주요 기능

### 1. Schema Version 추적
- OpenAPI `x-airtable-schemaVersion` 필드로 명시
- Lock 파일의 `generatedAt`와 자동 비교
- Drift 발생 시 즉시 감지

### 2. Protected Fields 명세
- 20개 필드를 `x-protected-fields`로 OpenAPI에 명시
- `protected_fields.json`에 상세 정보 (fieldId, reason, usedIn)
- CI에서 개수 자동 검증

### 3. CI/CD Gate
- GitHub Actions에서 자동 실행
- 4가지 검증: Schema Version, Table IDs, Protected Fields, Deployed API
- 실패 시 배포 자동 차단

### 4. Deployment Safety
- Pre-deployment 체크
- Post-deployment 검증
- Rollback 프로세스 명확화

---

## 🔧 기술 상세

### Schema Drift Detector

**검증 항목**:
1. **Schema Version**: OpenAPI ↔ Lock 파일 version 일치 확인
2. **Table IDs**: OpenAPI ↔ Lock 파일 table ID 일치 확인
3. **Protected Fields**: 선언된 필드 개수 확인 (20개)
4. **Deployed API**: 실제 배포된 API의 `/health` 응답 검증

**Exit Codes**:
- `0`: 모든 검증 통과 (배포 허용)
- `1`: Drift 감지 (배포 차단)
- `2`: 설정 오류

### GitHub Actions Workflow

**Triggers**:
- Push to `main` or `develop`
- Pull Request to `main`

**Jobs**:
1. `schema-validation`: 스키마 검증 실행
2. `pre-deployment-check`: Protected fields 개수 확인

**Artifacts**:
- Validation report 업로드 (실패 시 디버깅용)

---

## 📈 기대 효과

### 안정성
- ✅ 스키마 불일치로 인한 런타임 에러 **사전 차단**
- ✅ Protected fields 변경 시 **자동 감지 및 차단**
- ✅ 배포 전 **자동 검증**으로 장애 예방

### 효율성
- 🚀 수동 검증 불필요 (CI/CD 자동화)
- 🚀 Drift 발생 시 **즉시 알림**
- 🚀 명확한 복구 절차

### 품질
- 📊 Schema version 추적으로 **감사 추적** 강화
- 📊 Protected fields 문서화로 **운영 가시성** 향상
- 📊 OpenAPI에 모든 정보 명시로 **문서 품질** 향상

---

## 🎉 완료!

이제 HVDC API는 **Production-grade Schema Lock**으로 보호됩니다!

**다음 단계**:
- Phase 2.4: Evidence/Incoterm/HS Code 필드 추가
- Phase 3: AI 기반 예측 분석
- Phase 4: RPA 통합 자동화

---

**문서 버전**: v2.0
**작성일**: 2025-12-25
**Schema Version**: 2025-12-25T00:32:52+0400

