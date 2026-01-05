# /shipments/verify 엔드포인트 배포 가이드

## 개요

`/shipments/verify` 엔드포인트는 GPTs Actions를 위한 읽기 전용 검증 API입니다. 여러 shipment 번호를 한 번에 조회하여 운영 상태를 확인할 수 있습니다.

## 기능

- **다중 shipment 조회**: 쉼표로 구분된 최대 50개의 shptNo 조회
- **중복 탐지**: 동일한 shptNo가 여러 번 나타나는 경우 자동 감지
- **선택적 인증**: `API_KEY` 환경변수 설정 시 Bearer/X-API-Key 인증 강제
- **Airtable 통합**: 실시간 Airtable 데이터 조회

## 배포 전 체크리스트

### 1. 코드 검증

- [x] Flask 패치 적용 완료
  - [x] `API_KEY` 설정 (line 69-72)
  - [x] `require_api_key()` 함수 (line 75-92)
  - [x] `/shipments/verify` 엔드포인트 (line 627-745)
  - [x] `index()` endpoints 업데이트 (line 419)

- [x] OpenAPI 스키마 동기화
  - [x] `openapi-schema.yaml`에 `/shipments/verify` 경로 추가
  - [x] `components.securitySchemes`에 `bearerAuth` 추가
  - [x] `docs/openapi/openapi-gets-api.yaml`과 동기화

- [x] 테스트 통과
  - [x] `pytest tests/test_shipments_verify.py -v` ✅ 8/8 통과

### 2. Vercel 환경변수 설정

Vercel Dashboard → Settings → Environment Variables:

```
AIRTABLE_API_TOKEN = <your-airtable-pat>  # 필수
API_KEY = <your-optional-api-key>          # 선택 (설정하면 인증 강제)
```

**참고**:
- `API_KEY`를 설정하지 않으면 엔드포인트는 공개적으로 접근 가능합니다
- `API_KEY`를 설정하면 Bearer 또는 X-API-Key 헤더가 필요합니다

### 3. 로컬 검증 (선택)

```bash
# Flask 서버 실행
flask --app api.app run --port 5000

# 다른 터미널에서 테스트
# Health check
curl http://localhost:5000/health

# Shipments verify (공개 모드)
curl "http://localhost:5000/shipments/verify?shptNo=HE-0512,HE-0513"

# Shipments verify (인증 모드, API_KEY 설정 시)
curl -H "X-API-Key: your-key" "http://localhost:5000/shipments/verify?shptNo=HE-0512"
curl -H "Authorization: Bearer your-key" "http://localhost:5000/shipments/verify?shptNo=HE-0512"

# OpenAPI 스키마 확인
curl "http://localhost:5000/openapi-schema.yaml" | grep -A 5 "/shipments/verify"
```

## Vercel 배포

### 1. 배포 명령어

```bash
# Vercel CLI 로그인 (최초 1회)
vercel login

# 프로젝트 연결 (최초 1회)
vercel link

# 환경변수 설정 확인
vercel env ls

# 배포
vercel --prod
```

### 2. 환경변수 확인

```bash
# 환경변수 목록 확인
vercel env ls

# 환경변수 추가 (필요 시)
vercel env add AIRTABLE_API_TOKEN production
vercel env add API_KEY production
```

## 배포 후 검증

### 1. Health Check

```bash
PROD_URL="https://<your-vercel-domain>"
curl "${PROD_URL}/health"
```

예상 응답:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-06T...",
  "version": "1.7.0",
  "airtable": {
    "configured": true,
    "connected": true,
    ...
  }
}
```

### 2. Shipments Verify 테스트

```bash
# 공개 모드 (API_KEY 미설정 시)
curl "${PROD_URL}/shipments/verify?shptNo=HE-0512,HE-0513"

# 인증 모드 (API_KEY 설정 시)
curl -H "X-API-Key: <your-key>" \
  "${PROD_URL}/shipments/verify?shptNo=HE-0512,HE-0513"

# Bearer 토큰 방식
curl -H "Authorization: Bearer <your-key>" \
  "${PROD_URL}/shipments/verify?shptNo=HE-0512,HE-0513"
```

예상 응답:
```json
{
  "items": [
    {
      "shptNo": "HE-0512",
      "site": "MIR",
      "eta": "2025-12-18T00:00:00Z",
      "nextAction": "POD 서명본(수령일시) 텍스트 필요(Closed 전환)",
      "riskLevel": "HIGH",
      "currentBottleneckCode": "INSPECT_RED"
    }
  ],
  "meta": {
    "count": 1,
    "duplicates": [],
    "timestamp": "2026-01-06T00:00:00+04:00",
    "schemaVersion": "2025-12-25T00:32:52+0400"
  }
}
```

### 3. OpenAPI 스키마 확인

```bash
curl "${PROD_URL}/openapi-schema.yaml" | grep -A 5 "/shipments/verify"
```

## GPTs Actions 연결

### 1. OpenAPI 스키마 가져오기

1. GPTs 편집기 열기
2. **Actions** → **Create new action**
3. **Import from URL** 선택
4. URL 입력:
   ```
   https://<your-vercel-domain>/openapi-schema.yaml
   ```

### 2. 인증 설정 (API_KEY 사용 시)

1. **Authentication** 섹션에서:
   - **Type**: API Key
   - **Header name**: `X-API-Key` (또는 `Authorization`)
   - **Key**: Vercel 환경변수 `API_KEY` 값

2. 또는 Bearer 토큰 사용:
   - **Type**: HTTP Bearer
   - **Token**: Vercel 환경변수 `API_KEY` 값

### 3. 테스트 호출

GPTs에서 테스트:
```
"Verify shipments HE-0512, HE-0513, SCT-0151"
```

예상 동작:
- GPTs가 `/shipments/verify?shptNo=HE-0512,HE-0513,SCT-0151` 호출
- 결과를 표 형식으로 표시
- 중복이 있으면 경고 표시

## 트러블슈팅

### 문제: 503 Service Unavailable

**원인**: Airtable 연결 실패

**해결**:
1. `AIRTABLE_API_TOKEN` 환경변수 확인
2. Airtable Base ID 확인 (`appnLz06h07aMm366`)
3. Vercel 로그 확인: `vercel logs`

### 문제: 401 Unauthorized

**원인**: `API_KEY`가 설정되었지만 헤더가 없거나 잘못됨

**해결**:
1. `API_KEY` 환경변수 확인
2. 헤더 형식 확인:
   - `X-API-Key: <key>` 또는
   - `Authorization: Bearer <key>`

### 문제: 400 Bad Request

**원인**:
- `shptNo` 파라미터 누락
- 50개 이상의 shptNo 제공

**해결**:
- `shptNo` 파라미터 확인
- 최대 50개 제한 준수

### 문제: OpenAPI 스키마가 업데이트되지 않음

**원인**: `openapi-schema.yaml` 파일이 동기화되지 않음

**해결**:
```bash
# 동기화 스크립트 실행
./scripts/sync_openapi.sh
# 또는
python scripts/sync_openapi.py
```

## API 엔드포인트 사양

### GET /shipments/verify

**Query Parameters**:
- `shptNo` (required): 쉼표로 구분된 shipment 번호 (최대 50개)

**Headers** (선택, API_KEY 설정 시 필수):
- `X-API-Key: <key>` 또는
- `Authorization: Bearer <key>`

**Response 200**:
```json
{
  "items": [
    {
      "shptNo": "string",
      "site": "string",
      "eta": "string (ISO 8601)",
      "nextAction": "string",
      "riskLevel": "LOW|MEDIUM|HIGH|CRITICAL",
      "currentBottleneckCode": "string"
    }
  ],
  "meta": {
    "count": 0,
    "duplicates": ["string"],
    "timestamp": "string (ISO 8601)",
    "schemaVersion": "string"
  }
}
```

**Error Responses**:
- `400`: Bad request (빈 shptNo 또는 50개 초과)
- `401`: Unauthorized (API_KEY 설정 시 인증 실패)
- `502`: Airtable upstream error
- `503`: Service unavailable (Airtable 연결 실패)

## 참고 자료

- [OpenAPI 스키마](../openapi/openapi-gets-api.yaml)
- [테스트 코드](../../tests/test_shipments_verify.py)
- [Vercel 배포 가이드](./VERCEL_DEPLOYMENT_GUIDE.md)

