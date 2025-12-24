# 🚀 GETS Action API for ChatGPT

ChatGPT Custom GPT Actions를 위한 물류 현황 조회 API 서버
**Vercel 무료 배포** | **고정 URL** | **24시간 유지** | **보안 인증 지원**

---

## 📋 목차

1. [프로젝트 개요](#-프로젝트-개요)
2. [API 엔드포인트](#-api-엔드포인트)
3. [Vercel 배포 방법](#-vercel-배포-방법)
4. [ChatGPT Actions 연결](#-chatgpt-actions-연결)
5. [보안 설정](#-보안-설정)
6. [로컬 개발](#-로컬-개발)

---

## 🎯 프로젝트 개요

**목적**: ChatGPT가 외부 물류 시스템(GETS)의 선적 문서 상태를 조회할 수 있도록 API 제공

**주요 기능**:
- ✅ 특정 선적번호(SHPT NO)의 문서 상태 조회
- ✅ 전체 선적 KPI 요약 정보 제공
- ✅ Bearer Token 인증 지원 (선택사항)
- ✅ Vercel 자동 배포 및 무중단 운영

**기술 스택**:
- Backend: Python Flask
- Hosting: Vercel (Serverless)
- API: RESTful JSON API
- Schema: OpenAPI 3.1.0

---

## 🔌 API 엔드포인트

### 1️⃣ 문서 상태 조회

```http
GET /document/status/{shptNo}
```

**응답 예시**:
```json
{
  "shptNo": "HVDC-ADOPT-SIM-0065",
  "boeStatus": "Released",
  "doStatus": "Issued",
  "cooReady": "Ready",
  "hblReady": "Ready",
  "ciplValid": "Valid",
  "lastUpdated": "2025-12-24T19:30:00Z"
}
```

### 2️⃣ 전체 현황 요약

```http
GET /status/summary
```

**응답 예시**:
```json
{
  "totalShipments": 73,
  "ciplRate": 0.88,
  "hblRate": 0.75,
  "cooRate": 0.70,
  "doRate": 0.52,
  "boeRate": 0.41,
  "pendingBOE": ["HVDC-ADOPT-SIM-0065", "HVDC-ADOPT-SCT-0041"],
  "upcomingRisk": ["HVDC-ADOPT-SCT-0058"],
  "lastUpdated": "2025-12-24T19:30:00Z"
}
```

---

## 🚀 Vercel 배포 방법

### 사전 준비

- ✅ [Vercel 계정](https://vercel.com) (GitHub 연동 가능)
- ✅ [GitHub 계정](https://github.com)
- ✅ Git 설치

### 배포 단계

#### 1️⃣ GitHub 리포지토리 생성

1. GitHub에서 새 리포지토리 생성 (예: `GETS-Logistics-API`)
2. 로컬에서 프로젝트를 Git으로 초기화:

```bash
git init
git add .
git commit -m "Initial commit - GETS API for ChatGPT"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/GETS-Logistics-API.git
git push -u origin main
```

#### 2️⃣ Vercel에 배포

1. [Vercel Dashboard](https://vercel.com/dashboard) 접속
2. **"Add New Project"** 클릭
3. **"Import Git Repository"** 선택
4. GitHub에서 방금 만든 리포지토리 선택
5. **"Deploy"** 클릭 ✅

**완료!** 몇 초 후 아래와 같은 고정 URL이 생성됩니다:

```
https://gets-logistics.vercel.app
```

#### 3️⃣ 배포 확인

브라우저에서 접속:
```
https://YOUR-PROJECT.vercel.app/
```

응답 예시:
```json
{
  "status": "online",
  "message": "GETS Action API for ChatGPT",
  "version": "1.2.0"
}
```

---

## 🤖 ChatGPT Actions 연결

### 1️⃣ OpenAPI 스키마 복사

`openapi-schema.yaml` 파일의 내용을 복사합니다.

### 2️⃣ ChatGPT Actions 설정

1. ChatGPT Custom GPT 편집 화면 이동
2. **"Actions (작업)"** 탭 클릭
3. **"Create new action"** 선택
4. 스키마 입력란에 `openapi-schema.yaml` 내용 붙여넣기
5. `servers` 부분을 Vercel URL로 수정:

```yaml
servers:
  - url: https://YOUR-PROJECT.vercel.app
```

### 3️⃣ 테스트

ChatGPT 미리보기에서 다음과 같이 테스트:

```
/status
```

**응답 예시**:
```
📊 전체 선적: 73건
📈 BOE 41%, DO 52%, COO 70%
⚠️ BOE 대기: HVDC-ADOPT-SIM-0065, HVDC-ADOPT-SCT-0041
```

---

## 🔒 보안 설정

### Bearer Token 인증 추가

#### 1️⃣ Vercel 환경변수 설정

1. Vercel Dashboard → 프로젝트 선택
2. **Settings** → **Environment Variables**
3. 새 변수 추가:
   - **Name**: `API_KEY`
   - **Value**: `your-secret-key-here-123456`
4. **Save** 클릭
5. **Redeploy** (자동 재배포됨)

#### 2️⃣ ChatGPT Actions 인증 설정

1. ChatGPT Actions 편집 화면
2. **"Authentication"** 섹션
3. **"API Key"** 또는 **"Bearer Token"** 선택
4. Header Name: `Authorization`
5. Value: `Bearer your-secret-key-here-123456`
6. **Save**

이제 API 키 없이는 접근할 수 없습니다! 🔐

---

## 💻 로컬 개발

### 설치

```bash
# 가상환경 생성 (선택사항)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 실행

```bash
# Flask 서버 시작
cd api
python document_status.py
```

또는:

```bash
export FLASK_APP=api/document_status.py
export FLASK_ENV=development
flask run
```

### 테스트

브라우저에서:
```
http://localhost:5000/status/summary
```

cURL로:
```bash
curl http://localhost:5000/document/status/HVDC-ADOPT-SIM-0065
```

---

## 📂 프로젝트 구조

```
GETS-API/
├── api/
│   └── document_status.py     # Flask API 코드
├── vercel.json                # Vercel 배포 설정
├── requirements.txt           # Python 패키지 목록
├── openapi-schema.yaml        # ChatGPT Actions용 스키마
├── .gitignore                 # Git 제외 파일 목록
└── README.md                  # 이 문서
```

---

## 🔄 실시간 데이터 연동 (다음 단계)

현재는 샘플 데이터를 반환합니다. 실제 데이터 연동을 위해 다음을 추가할 수 있습니다:

### Airtable 연동 예시

```python
import requests

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")

def fetch_from_airtable(shptNo):
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/Shipments"
    headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}
    params = {"filterByFormula": f"{{SHPT NO}}='{shptNo}'"}

    response = requests.get(url, headers=headers, params=params)
    return response.json()
```

### 데이터베이스 연동

PostgreSQL, MySQL, MongoDB 등 원하는 데이터베이스를 연결할 수 있습니다.

---

## 🆘 문제 해결

### Vercel 배포 실패

- `vercel.json` 파일 확인
- `requirements.txt`에 flask 포함 여부 확인
- Vercel 로그에서 에러 메시지 확인

### ChatGPT에서 연결 안 됨

- Vercel URL이 정확한지 확인
- 브라우저에서 직접 URL 접속해보기
- OpenAPI 스키마 문법 오류 확인

### 인증 오류

- Vercel 환경변수가 올바르게 설정되었는지 확인
- ChatGPT Actions에서 Bearer Token 형식 확인
- 재배포 후 테스트

---

## 📞 지원

문제가 발생하면:
1. Vercel 대시보드에서 로그 확인
2. GitHub Issues에 문의
3. 삼성물산 프로젝트 팀에 문의

---

## 📄 라이선스

MIT License - 자유롭게 사용하세요!

---

**Made with ❤️ for Samsung C&T Project Logistics Team**

