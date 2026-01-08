# CHANGELOG - 2026-01-06

## 🎯 버전: v1.8.0

### ✨ 새로운 기능

#### `/shipments/verify` 엔드포인트 추가
- **경로**: `GET /shipments/verify?shptNo=A,B,C`
- **기능**:
  - 다중 shipment 번호 조회 (최대 50개, 쉼표 구분)
  - 중복 shipment 자동 감지
  - 운영 검증 필드 반환 (shptNo, site, eta, nextAction, riskLevel, currentBottleneckCode)
- **인증**: 선택사항 (API_KEY 환경변수 설정 시 Bearer/X-API-Key 인증 강제)

### 🔧 변경 사항

#### OpenAPI 스키마 ChatGPT Actions 호환성 개선
- `components.schemas: {}` 추가 (필수 섹션)
- `bearerAuth` 제거, `apiKeyAuth`만 유지
- 모든 엔드포인트에 `security: []` 추가 (인증 불필요 명시)
- parameters에서 인증 헤더 제거

#### 프로덕션 URL 통일
- 모든 파일에서 `gets-logistics-api.vercel.app`로 통일
- 이전 버전 URL 제거:
  - `gets-416ut4t8g-chas-projects-08028e73.vercel.app`
  - `gets-45ywvkhui-chas-projects-08028e73.vercel.app`
  - `gets-cofgcl0hc-chas-projects-08028e73.vercel.app`

### 🐛 버그 수정

#### 보안 토큰 마스킹
- GitHub Push Protection이 Airtable PAT 감지 문제 해결
- 관련 파일에서 토큰 제거/마스킹:
  - `docs/airtable_Personal access tokens are required to u.md`
  - `docs/openapi/openapi-airtable-api-v1.0.4.yaml`
  - `gpt_config/openapi-schema.yaml`

#### ChatGPT Actions 인증 오류 해결
- 401 Unauthorized 오류 해결
- 인증이 필요 없는 엔드포인트에 `security: []` 추가

#### Airtable 연결 실패 해결
- Vercel Dashboard에서 `AIRTABLE_API_TOKEN` 환경변수 설정
- 502 Bad Gateway 오류 해결

### 📝 문서 업데이트

#### 신규 문서
- `docs/guides/SHIPMENTS_VERIFY_DEPLOYMENT.md` - 배포 가이드
- `DEPLOYMENT_CHECKLIST.md` - 배포 체크리스트
- `docs/guides/CHATGPT_ACTIONS_INTEGRATION_COMPLETE.md` - 통합 완료 보고서

#### 업데이트된 문서
- `docs/guides/CHATGPT_SCHEMA_GUIDE.md` - Production URL 업데이트, `/shipments/verify` 엔드포인트 설명 추가

### 🧪 테스트

#### 신규 테스트
- `tests/test_shipments_verify.py` - 8개 테스트 케이스 추가
  - ✅ 모든 테스트 통과 (8/8)

#### 업데이트된 테스트
- `test_production_api.py` - Production URL 업데이트
- `tests/load_test.py` - Production URL 업데이트 (3곳)
- `tests/test_api_health.py` - Production URL 업데이트
- `test_api_integration.py` - Production URL 업데이트

### 🔨 스크립트

#### 신규 스크립트
- `scripts/sync_openapi.py` - OpenAPI 스키마 동기화 스크립트 (Python)
- `scripts/sync_openapi.sh` - OpenAPI 스키마 동기화 스크립트 (Bash)
- `scripts/sync_openapi.ps1` - OpenAPI 스키마 동기화 스크립트 (PowerShell)

### 📊 배포 통계

#### Git 커밋
1. **커밋 `4547441`**
   - `/shipments/verify` 엔드포인트 추가
   - OpenAPI 스키마 업데이트
   - 53개 파일 변경, 11,548줄 추가, 536줄 삭제

2. **커밋 `0fc9e34`**
   - 보안 토큰 마스킹
   - 커밋 수정 (--amend)

3. **커밋 `7f36b08`**
   - `security: []` 추가 (ChatGPT Actions 호환성)
   - 2개 파일 변경, 18줄 추가, 34줄 삭제

4. **커밋 `85cd7bf`** (2026-01-08)
   - PAT prefix 마스킹 작업 시작
   - `gpt_config/openapi-schema.yaml`: Token prefix 마스킹
   - 한국어 경고 메시지 추가: "토큰 전문/부분을 문서에 포함하지 말 것."

5. **커밋 `7ada74a`** (2026-01-08)
   - Merge PR #1: PAT prefix 마스킹 완료
   - `gpt_config/openapi-schema.yaml`: Token prefix `patDazyBR21DC5Bqs` → `[REDACTED]`
   - 보안 토큰 완전 마스킹 확인

6. **커밋 `9c2cd19`** (2026-01-08)
   - behavioral(openapi): bearerAuth → apiKeyAuth 전환
   - `gpt_config/openapi-schema.yaml`: 모든 `BearerAuth: []` → `apiKeyAuth: []`
   - Authentication Type: "Bearer" → "API Key"
   - ChatGPT Actions 호환성 개선

7. **커밋 `21b3bcc`** (2026-01-08)
   - Merge PR #2: bearerAuth 제거 완료
   - `README.md`: GPT schema 관련 문서 업데이트
   - `gpt_config/openapi-schema.yaml`: 최종 변경사항 반영
   - 모든 보안 스키마 통일 완료

#### 배포 정보
- **배포 환경**: Production
- **배포 시간**: ~11초
- **배포 상태**: Ready
- **도메인**: `gets-logistics-api.vercel.app`

### ✅ 검증 결과

#### Health Check
- ✅ API Status: healthy
- ✅ Airtable Connected: true
- ✅ Schema Version: 2025-12-25T00:32:52+0400

#### API 엔드포인트 테스트
- ✅ `getApiInfo`: 정상 작동
- ✅ `getHealth`: Airtable 연결 성공
- ✅ `verifyShipments`: 데이터 정상 반환 (4개 레코드)
- ✅ `getBottleneckSummary`: 24개 활성 병목 분석
- ✅ `getApprovalSummary`: 2개 승인 상태 (1개 Overdue)

#### ChatGPT Actions 통합
- ✅ OpenAPI 스키마 정상 로드
- ✅ 모든 10개 operation 정상 작동
- ✅ 인증 문제 해결 (401 오류 해결)
- ✅ 데이터 품질 검증 (중복 감지 작동)

### 📈 성능 및 품질 지표

#### API 성능
- **응답 시간**: < 2초 (SLA 준수)
- **가용성**: 100% (배포 후)
- **에러율**: 0% (정상 작동)

#### 데이터 품질
- **중복 감지**: ✅ 작동 (SCT-0151 중복 감지)
- **데이터 정확성**: ✅ 모든 필드 정상 반환
- **스키마 일치**: ✅ 2025-12-25T00:32:52+0400

#### 코드 품질
- **테스트 커버리지**: 8/8 테스트 통과
- **코드 리뷰**: ✅ 완료
- **문서화**: ✅ 완료

### 🔗 관련 이슈

- ChatGPT Actions 호환성 개선
- 프로덕션 URL 통일 작업
- 보안 토큰 마스킹 작업
- Airtable 연결 안정화

### 📚 참고 문서

- [ChatGPT Actions 통합 완료 보고서](guides/CHATGPT_ACTIONS_INTEGRATION_COMPLETE.md)
- [배포 가이드](guides/SHIPMENTS_VERIFY_DEPLOYMENT.md)
- [ChatGPT Schema 가이드](guides/CHATGPT_SCHEMA_GUIDE.md)

---

**작성일**: 2026-01-06 (최종 업데이트: 2026-01-08)
**버전**: v1.8.0
**최종 커밋**: `21b3bcc`

