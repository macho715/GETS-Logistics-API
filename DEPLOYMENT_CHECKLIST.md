# 🚀 /shipments/verify 배포 체크리스트

## ✅ 완료된 작업

- [x] **Flask 패치 적용**
  - [x] `API_KEY` 설정 및 `require_api_key()` 함수
  - [x] `/shipments/verify` 엔드포인트 구현
  - [x] `index()` endpoints 업데이트

- [x] **OpenAPI 스키마 업데이트**
  - [x] `/shipments/verify` 경로 추가
  - [x] `bearerAuth` security scheme 추가
  - [x] 루트 `openapi-schema.yaml` 동기화

- [x] **테스트 작성 및 통과**
  - [x] `tests/test_shipments_verify.py` 생성
  - [x] 8개 테스트 모두 통과 ✅

- [x] **문서화**
  - [x] 배포 가이드 작성 (`docs/guides/SHIPMENTS_VERIFY_DEPLOYMENT.md`)

## 📋 배포 전 체크리스트

### 1. 코드 검증
- [x] 모든 테스트 통과
- [x] 문법 오류 없음
- [x] OpenAPI 스키마 동기화 완료

### 2. Vercel 환경변수 설정

**필수**:
```
AIRTABLE_API_TOKEN = <your-airtable-pat>
```

**선택** (인증 활성화 시):
```
API_KEY = <your-api-key>
```

### 3. 배포 명령어

```bash
# Vercel CLI 설치 (최초 1회)
npm i -g vercel

# 로그인
vercel login

# 프로젝트 연결
vercel link

# 환경변수 확인
vercel env ls

# 프로덕션 배포
vercel --prod
```

## 🔍 배포 후 검증

### 1. Health Check
```bash
curl https://<your-vercel-domain>/health
```

### 2. Shipments Verify (공개 모드)
```bash
curl "https://<your-vercel-domain>/shipments/verify?shptNo=HE-0512,HE-0513"
```

### 3. Shipments Verify (인증 모드, API_KEY 설정 시)
```bash
curl -H "X-API-Key: <key>" \
  "https://<your-vercel-domain>/shipments/verify?shptNo=HE-0512"
```

### 4. OpenAPI 스키마 확인
```bash
curl "https://<your-vercel-domain>/openapi-schema.yaml" | grep -A 5 "/shipments/verify"
```

## 🤖 GPTs Actions 연결

1. **GPTs 편집기** → **Actions** → **Create new action**
2. **Import from URL**: `https://<your-vercel-domain>/openapi-schema.yaml`
3. **인증 설정** (API_KEY 사용 시):
   - Type: API Key
   - Header: `X-API-Key`
   - Value: Vercel `API_KEY` 환경변수 값

## 📚 참고 문서

- [배포 가이드](docs/guides/SHIPMENTS_VERIFY_DEPLOYMENT.md)
- [Vercel 배포 가이드](docs/guides/VERCEL_DEPLOYMENT_GUIDE.md)
- [테스트 코드](tests/test_shipments_verify.py)

## 🎯 다음 단계

1. ✅ 테스트 실행 완료
2. ✅ 로컬 검증 완료 (문서화)
3. ⏳ **Vercel 배포** (환경변수 설정 후)
4. ⏳ 프로덕션 검증
5. ⏳ GPTs Actions 연결

---

**배포 준비 완료!** Vercel 환경변수 설정 후 배포를 진행하세요.

