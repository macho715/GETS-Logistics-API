# 🚀 Vercel 배포 가이드

## ✅ 현재 상태

```
✅ GitHub Repository: https://github.com/macho715/GETS-Logistics-API
✅ Branch: main
✅ Files: Updated with production configuration
✅ Ready for Vercel deployment
```

---

## 📋 배포 단계

### 1️⃣ **Vercel 대시보드 접속**

👉 **https://vercel.com/dashboard**

(GitHub 계정으로 로그인 권장)

---

### 2️⃣ **새 프로젝트 Import**

1. **"Add New Project"** 또는 **"Import Project"** 버튼 클릭
2. **"Import Git Repository"** 섹션에서 GitHub 선택
3. `macho715/GETS-Logistics-API` 리포지토리 찾기
4. **"Import"** 클릭

---

### 3️⃣ **프로젝트 설정 (자동 감지됨)**

Vercel이 `vercel.json`을 자동으로 인식합니다:

```json
{
  "version": 2,
  "builds": [{
    "src": "api/document_status.py",
    "use": "@vercel/python"
  }],
  "routes": [{
    "src": "/(.*)",
    "dest": "api/document_status.py"
  }]
}
```

**설정 확인:**
- ✅ Framework Preset: **Other** (자동 선택)
- ✅ Root Directory: **.** (루트)
- ✅ Build Command: (비워두기)
- ✅ Output Directory: (비워두기)
- ✅ Install Command: `pip install -r requirements.txt` (자동)

---

### 4️⃣ **환경변수 설정** ⚠️ 중요!

배포 **전**에 다음 환경변수를 추가하세요:

#### **필수 환경변수:**

| Name | Value | Description |
|------|-------|-------------|
| `AIRTABLE_API_TOKEN` | `your_token_here` | Airtable Personal Access Token |

#### **선택사항 환경변수:**

| Name | Value | Description |
|------|-------|-------------|
| `SLACK_WEBHOOK_URL` | `https://hooks.slack.com/...` | Slack 알림용 (선택사항) |
| `API_KEY` | `your_secret_key_123` | Bearer Token 인증용 (선택사항) |

**환경변수 추가 방법:**
1. Vercel 프로젝트 설정 페이지에서
2. **"Environment Variables"** 탭 클릭
3. Name과 Value 입력
4. Environment 선택: **Production, Preview, Development** 모두 체크
5. **"Save"** 클릭

---

### 5️⃣ **Airtable Token 발급**

1. **https://airtable.com/create/tokens** 접속
2. **"Create new token"** 클릭
3. 토큰 이름: `GETS API Production`
4. **Scopes 선택:**
   - ✅ `data.records:read`
   - ✅ `data.records:write`
   - ✅ `schema.bases:read` (선택사항)
5. **Access 선택:**
   - ✅ Base: `HVDC Logistics (appnLz06h07aMm366)` 선택
6. **"Create token"** 클릭
7. 생성된 토큰 복사 (한 번만 표시됨!)

**⚠️ 보안 주의:**
- 토큰을 안전한 곳에 보관하세요
- 절대 Git에 커밋하지 마세요
- 주기적으로 토큰을 갱신하세요

---

### 6️⃣ **배포 시작!**

1. 환경변수 설정 완료 확인
2. **"Deploy"** 버튼 클릭
3. 약 1-2분 대기 (빌드 + 배포)

**빌드 로그 확인:**
```
Installing Python dependencies...
✓ Installed flask==3.0.0
✓ Installed flask-cors==4.0.0
✓ Installed requests==2.31.0
✓ Installed python-dotenv==1.0.0
✓ Installed pyyaml==6.0.1
...
✓ Build completed successfully!
```

---

## ✅ 배포 완료 후 확인

### **배포 URL 받기**

배포 완료 후 다음과 같은 URL들을 받게 됩니다:

```
✅ Production URL:
   https://gets-logistics-api.vercel.app

✅ Preview URL (각 커밋마다):
   https://gets-logistics-api-git-main-macho715.vercel.app
```

---

### **API 테스트**

#### **1. Health Check**
```bash
curl https://gets-logistics-api.vercel.app/health
```

**예상 응답:**
```json
{
  "status": "healthy",
  "version": "1.8.0",
  "airtable": {
    "configured": true,
    "connected": true,
    "baseId": "appnLz06h07aMm366"
  },
  "lockedConfig": {
    "schemaVersion": "2025-12-25T00:32:52+0400",
    "protectedFields": 20
  }
}
```

#### **2. API Info**
```bash
curl https://gets-logistics-api.vercel.app/
```

#### **3. Status Summary**
```bash
curl https://gets-logistics-api.vercel.app/status/summary
```

#### **4. Document Status (특정 선적)**
```bash
curl https://gets-logistics-api.vercel.app/document/status/SCT-0143
```

---

## 🤖 ChatGPT Actions 연결

### **1️⃣ OpenAPI 스키마 업데이트**

`openapi-schema.yaml` 파일의 `servers` 섹션을 업데이트:

```yaml
servers:
  - url: https://gets-logistics-api.vercel.app
    description: Production server (Vercel)
```

### **2️⃣ ChatGPT Custom GPT 설정**

1. ChatGPT → **Custom GPT** 편집 화면
2. **"Actions"** 탭 클릭
3. **"Create new action"** 선택
4. 업데이트된 `openapi-schema.yaml` 내용 붙여넣기
5. **"Save"** 클릭

### **3️⃣ 인증 설정 (선택사항)**

만약 `API_KEY` 환경변수를 설정했다면:

1. ChatGPT Actions 편집 화면
2. **"Authentication"** 섹션
3. **"Bearer"** 선택
4. Token: `your_secret_key_123`
5. **"Save"**

### **4️⃣ ChatGPT 테스트**

```
/status
```

또는

```
SCT-0143 선적의 문서 상태를 알려줘
```

**예상 응답:**
```
📊 전체 선적: 73건
📈 BOE 41%, DO 52%, COO 70%
⚠️ 병목: FANR_PENDING (15건)
```

---

## 🔧 문제 해결

### **Problem: "Module not found" 오류**

**원인:** `requirements.txt`가 누락되었거나 패키지 이름 오류

**해결:**
```bash
# 로컬에서 테스트
pip install -r requirements.txt
python api/document_status.py
```

---

### **Problem: "Airtable connection failed"**

**원인:** `AIRTABLE_API_TOKEN` 환경변수가 설정되지 않음

**해결:**
1. Vercel Dashboard → 프로젝트 선택
2. **Settings** → **Environment Variables**
3. `AIRTABLE_API_TOKEN` 추가
4. **Redeploy** (Deployments 탭에서 최신 배포의 "..." → "Redeploy")

---

### **Problem: "Schema version mismatch"**

**원인:** `airtable_schema.lock.json`이 오래됨

**해결:**
```bash
# 로컬에서 스키마 재생성
python scripts/lock_schema_and_generate_mapping.py

# Git commit & push
git add airtable_schema.lock.json airtable_locked_config.py
git commit -m "Update schema lock"
git push origin main

# Vercel이 자동으로 재배포됨
```

---

### **Problem: "429 Rate Limit" 오류**

**원인:** Airtable API 요청 제한 (5 req/s per base)

**해결:** 이미 코드에 rate limiting이 내장되어 있습니다. 잠시 후 자동 재시도됩니다.

---

### **Problem: ChatGPT에서 "Unable to connect" 오류**

**원인:** CORS 설정 또는 URL 오류

**해결:**
1. 브라우저에서 직접 URL 접속 테스트
2. `openapi-schema.yaml`의 `servers.url` 확인
3. Vercel 배포 로그 확인

---

## 📊 모니터링

### **Vercel 대시보드에서 확인**

1. **Deployments**: 배포 히스토리
2. **Analytics**: 트래픽, 응답 시간
3. **Logs**: 실시간 로그
4. **Performance**: 성능 지표

### **API 성능 지표**

```bash
# Detailed health check
curl https://gets-logistics-api.vercel.app/health/detailed
```

**응답에 포함:**
- Performance metrics (평균 응답 시간)
- SLA violations (D-5/D-15 위반)
- Error rates

---

## 🔄 업데이트 및 재배포

### **자동 배포 (권장)**

GitHub에 푸시하면 Vercel이 자동으로 배포합니다:

```bash
# 코드 수정
git add .
git commit -m "Update API endpoint"
git push origin main

# Vercel이 자동으로 감지하고 재배포
```

### **수동 재배포**

1. Vercel Dashboard → **Deployments**
2. 최신 배포의 **"..."** 메뉴
3. **"Redeploy"** 클릭

---

## 📚 사용 가능한 엔드포인트

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API 정보 |
| GET | `/health` | 헬스체크 |
| GET | `/health/detailed` | 상세 헬스체크 |
| GET | `/shipments/verify` | Verify shipments (GPTs Action) |
| GET | `/document/status/{shptNo}` | 문서 상태 조회 |
| GET | `/approval/status/{shptNo}` | 승인 상태 조회 |
| GET | `/approval/summary` | 전체 승인 요약 |
| GET | `/document/events/{shptNo}` | 이벤트 히스토리 |
| GET | `/status/summary` | KPI 요약 |
| GET | `/bottleneck/summary` | 병목 분석 |
| POST | `/ingest/events` | 이벤트 수집 (RPA용) |

---

## ✅ 완료 체크리스트

- [ ] Vercel 계정 생성 및 GitHub 연결
- [ ] 프로젝트 Import 완료
- [ ] `AIRTABLE_API_TOKEN` 환경변수 설정
- [ ] 첫 배포 성공
- [ ] `/health` 엔드포인트 테스트 통과
- [ ] `/shipments/verify` 엔드포인트 테스트 통과
- [ ] `/status/summary` 실제 데이터 반환 확인
- [ ] ChatGPT Actions 연결 완료
- [ ] ChatGPT에서 테스트 성공

---

## 🆘 추가 지원

**문제가 발생하면:**

1. **Vercel 로그 확인**: Dashboard → Deployments → 해당 배포 → Logs
2. **GitHub Issues**: https://github.com/macho715/GETS-Logistics-API/issues
3. **AGENTS.md 참조**: 개발 가이드라인 및 규칙

---

**🎉 배포 성공을 축하합니다!**

이제 ChatGPT가 실시간 Airtable 데이터에 접근할 수 있습니다! 🚀

