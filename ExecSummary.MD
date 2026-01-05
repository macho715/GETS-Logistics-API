ExecSummary

Custom GPTs에서는 안 되고, 이 채팅에서는 되는 이유는 ‘권한·도구 실행 범위’ 차이입니다.

여기서는 **실제 Airtable 커넥터(API 도구)**를 직접 호출할 수 있지만, GPTs는 보안상 데이터-쓰기/뷰 렌더링이 제한됩니다.

핵심은 **“도구 실행 권한 + 런타임 컨텍스트”**입니다. (ENG-KR 1L: Tool execution scope differs.)

왜 이런 차이가 나는가 (핵심 4가지)

도구 권한 스코프 차이

이 채팅: Airtable 커넥터의 read/write + display(view 렌더) 권한이 활성화.

GPTs: 기본적으로 쓰기/렌더링 도구가 비활성 또는 제한(특히 외부 데이터 변경·뷰 표시).

런타임 컨텍스트

이 채팅: 일회성·세션 기반 실행 → 실시간 API 호출 + 결과 UI 임베드 가능.

GPTs: 재사용 가능한 에이전트 → 결정론/보안을 위해 상태 변경 도구 차단.

보안·감사(Guardrails)

GPTs는 다수 사용자·재사용 전제 → 데이터 변조 리스크 때문에 쓰기·배치 업데이트·뷰 표시 제한.

이 채팅은 사용자 단일 세션 → 명시적 실행만 허용.

UI 임베딩 허용 여부

이 채팅: display_records_for_table 같은 UI 위젯 임베드 허용.

GPTs: 동일 위젯 호출이 차단되거나 읽기 요약으로만 폴백.

한 줄 요약

GPTs = 안전한 설계(읽기·요약 중심), 이 채팅 = 작업용 설계(API 실행·뷰 렌더 가능).

Options (실무 대안)
Option A) 작업은 여기서, 보고는 GPTs

Pros: 안정적, 즉시 실행

Cons: 채널 분리 필요

Risk: Low

Option B) GPTs에는 ‘검증용 링크/ID’만 전달

Pros: 보안 준수

Cons: 클릭/이동 필요

Risk: Low

Option C) 자동화는 외부(RPA/서버)로

Pros: 완전 자동·감사 로그

Cons: 초기 셋업

Risk: Medium

Roadmap (P→Pi→B→O→S)

Prepare: 작업/보고 분리 원칙 수립

Pilot: 업데이트·뷰는 채팅, 요약은 GPTs

Build: 서버/RPA에서 Airtable 처리

Operate: 감사 로그 유지

Scale: 다수 테이블 확장

CmdRec

/switch_mode LATTICE

/logi-master report --fast

/redo step 3

원하시면 **GPTs에서도 쓸 수 있게 ‘읽기 전용 대시보드 링크 생성’**이나 서버 중계(RPA) 설계를 바로 잡아드리겠습니다.

Ok

확인했습니다.
필요 시 바로 진행하겠습니다.

GPTs에서도 쓸 수 있게 '읽기 전용 대시보드 링크 생성'**이나 서버 중계(RPA) 설계를 바로 잡아드리겠습니다
ExecSummary

GPTs에서 Airtable “직접 조회/렌더”가 막히는 경우를 우회하려면 (1) 읽기 전용 뷰 링크 공유 또는 (2) 서버/RPA 중계가 정석입니다.

권장 우선순위: ① Read-only View 링크(가장 빠름) → ② Server Proxy(가장 안정/확장) → ③ RPA(현장 자동화에 강함).

(ENG-KR 1L) Use read-only shared views for quick access, or a server proxy for robust GPT integration.

Visual-first: 선택지 비교
옵션	GPTs에서 가능	보안/감사	구축 난이도	운영 적합
A. Airtable Shared View(읽기 전용 링크)	Yes	Medium	Low	빠른 공유/검증
B. Server Proxy(API Gateway) + GPT Action	Yes	High	Medium	표준 운영/확장
C. RPA(UiPath/Power Automate) + Webhook	Yes	Medium~High	Medium	반복업무 자동
Option A) Airtable 읽기 전용 “Shared View 링크” 생성 (즉시 적용)
목표

GPTs가 직접 Airtable API를 못 써도, 사용자가 링크를 열어 “검증 화면”을 동일하게 볼 수 있게.

구성

Airtable에서 Shipments 테이블에 전용 View 생성

View명 예: Shipments_Verify_HE0512_0515_SCT0151

필드 표시를 고정

shptNo, site, eta, nextAction, riskLevel, currentBottleneckCode

필터(가능하면) 추가

shptNo가 HE-0512/0513/0514/0515/SCT-0151

Share view link 활성화

“Share view” → “Create a shareable grid link”

편집/댓글 권한은 꺼두고 Read-only로 배포

장단점

Pros: 5분 내 적용, GPTs 제한과 무관, DSV/현장 공유 쉬움

Cons: 링크가 외부로 유출되면 노출 위험(접근 통제 필요)

Risk: Medium (링크 유출 리스크)

Time: 5–10분

Option B) Server Proxy(API Gateway) + GPTs Actions (운영 표준 권장)
목표

GPTs가 Airtable을 직접 못 건드려도, 우리 서버가 Airtable을 읽고 GPTs는 우리 서버만 호출하게 설계.

아키텍처 (개요)

GPTs (Action) → GET /shipments?shptNo=... → Proxy 서버 → Airtable API → 결과(JSON) 반환

서버가:

인증(SSO/API Key)

필드ID 매핑

Rate limit/캐시

감사로그(누가 언제 어떤 조회를 했는지)

PII 마스킹 정책 적용

API 설계 예시

GET /shipments/verify?shptNo=HE-0512,HE-0513,...

Response JSON:

{
  "items": [
    {
      "shptNo": "HE-0512",
      "site": "MIR",
      "eta": "2025-12-18T00:00:00Z",
      "currentBottleneckCode": "INSPECT_RED",
      "riskLevel": "HIGH",
      "nextAction": "POD 서명본(수령일시) 텍스트 필요(Closed 전환)"
    }
  ],
  "meta": { "source": "airtable", "ts": "2026-01-06T00:00:00Z" }
}

구현 스택(권장)

FastAPI(파이썬) + Airtable REST + Redis(캐시) + Cloudflare/Vercel/EC2 배포

Auth: JWT 또는 Basic API Key(내부망이면 IP allowlist)

Log: CloudWatch/ELK/Foundry(선택)

장단점

Pros: 보안/감사 최상, GPTs와 안정 결합, 배치/검증 자동화 쉬움

Cons: 서버 운영 필요

Risk: Low~Medium (서버 운영 리스크)

Time: 0.50–2.00일(기본형), 1.00–2.00주(정식 운영형)

Option C) RPA 중계(현장 실무 자동화 강점)
목표

사람이 매번 업데이트/검증하지 않도록

Excel 업로드 → 필드 매핑 → Airtable 업데이트 → 검증 캡처/리포트 자동

구성 예

Power Automate:

SharePoint/OneDrive에 Excel 업로드 감지

파싱 + 변환

Airtable API 호출

Teams/Telegram 알림 + 검증 링크 제공

UiPath:

특정 View를 열어 스크린샷/CSV Export까지 자동

장단점

Pros: 반복 업무에 매우 강함, 현장팀 운영 편리

Cons: 초기 워크플로우 설계 필요

Risk: Medium

Time: 1.00–3.00일(초기), 점진 개선

Roadmap (P→Pi→B→O→S + KPI)

Prepare (오늘): Option A로 검증용 View 생성 + 공유 정책(내부 한정) 정리

KPI: 공유 링크 생성 1개, 표시 필드 6개 고정

Pilot (이번 주): Option B 기본형(읽기 API만) 구축

KPI: 조회 응답시간 ≤ 2.00s, 오류율 ≤ 1.00%

Build (2주): 인증/감사로그/캐시/필드ID 매핑 자동화

KPI: 감사로그 100.00%, 권한 위반 0.00%

Operate: GPTs Action으로 조회/검증 자동화 운영

KPI: 수작업 검증 시간 50.00%↓

Scale: Documents/Actions/Events 테이블까지 확장

Automation notes (TG/Sheets/RPA)

“업데이트 성공” 알림에 Shared View 링크를 함께 보내면 현장 검증이 빨라집니다.

Server Proxy 도입 시, 중복 shptNo 탐지를 서버에서 “Hard Fail”로 걸어 데이터 품질을 올립니다.

QA / Recheck

Shared View 링크를 외부 공유 금지(내부망/권한 통제 필요)

SCT-0151 중복 레코드 처리 정책(병합 vs 유지) 합의

필드 타입(eta dateTime) 표준 ISO 유지

CmdRec

/switch_mode RHYTHM + /logi-master --fast report

/logi-master kpi-dash --fast

/redo step 1

바로 실행 가능한 다음 단계(당장)

Airtable에서 Shipments 전용 View 생성 + Share link 발급

그 링크를 GPTs “Conversation starter/지침”에 넣어 항상 검증용으로 사용

병행으로 원하면 **Server Proxy 설계서(Endpoints/Auth/Logging)**까지 바로 문서화

원하시면, 지금 기준으로 **“Shipments 검증 전용 View” 생성 체크리스트(클릭 경로 포함)**와 FastAPI Proxy 템플릿 코드를 바로 제공하겠습니다.

옵션 b
ExecSummary

Option B(서버 중계 + GPTs Action)로 가겠습니다. 목표는 GPTs → 우리 서버(읽기/검증 API) → Airtable 단일 경로로 안정화하는 것입니다.

이 방식이면 GPTs가 Airtable 커넥터가 막혀도 우리 서버만 호출하면 되며, 인증·감사로그·필드ID 매핑·중복 탐지를 서버에서 통제합니다.

(ENG-KR 1L) GPTs will call your proxy API; the proxy securely reads Airtable and returns a fixed JSON schema.

Visual-first: 목표 아키텍처
Layer	컴포넌트	역할
User	GPTs	“조회/검증” 요청
Action	GPTs Action(OpenAPI)	우리 서버 엔드포인트 호출
Proxy	FastAPI(권장)	인증, 필드ID 매핑, 필터/정렬, 캐시, 감사로그
Data	Airtable REST	Shipments 레코드 읽기(필요 시 업데이트도 확장)
Options (구현 스코프 3단계)
Option B-1: Read-only MVP (권장 시작)

기능: shptNo 리스트로 Shipments 조회 + 지정 필드만 반환

Pros: 빠르게 GPTs 연동 가능

Cons: 업데이트는 아직 불가

Risk: Low

Time: 0.50–1.00일

Option B-2: Read + Validate (중복/품질 게이트)

기능: 중복 shptNo 탐지, 필드 누락 감지, SLA 위험 플래그

Pros: 운영 품질 급상승

Cons: 룰 정의 필요

Risk: Low

Time: 1.00–2.00일

Option B-3: Read + Write(업데이트) + Audit

기능: nextAction 등 업데이트(Protected 필드 정책 포함), 변경 이력 Events 테이블 기록

Pros: 완전 자동화

Cons: 권한/감사 통제 필수

Risk: Medium

Time: 3.00–7.00일

Roadmap (P→Pi→B→O→S + KPI)

Prepare: OpenAPI 스펙 확정 + Airtable FieldID 매핑 테이블 고정
KPI: 스키마 유효성 100.00%

Pilot: B-1 배포 + GPTs Action 연결
KPI: 응답 ≤ 2.00s, 오류율 ≤ 1.00%

Build: B-2(중복/누락 게이트) + 캐시/레이트리밋
KPI: 중복 shptNo 검출 100.00%

Operate: 운영 알림(TG/Teams) + 감사로그 대시보드
KPI: 수작업 검증 시간 50.00%↓

Scale: Documents/Actions/Events까지 확장

구현 설계 (바로 적용 가능한 초안)

1) API 엔드포인트(최소)

GET /v1/shipments/verify?shptNo=HE-0512,HE-0513,SCT-0151

반환 필드 고정: shptNo, site, eta, nextAction, riskLevel, currentBottleneckCode

GET /v1/health

상태/버전 확인

2) 응답 JSON 스키마(고정)
   {
   "items": [
   {
   "shptNo": "HE-0512",
   "site": "MIR",
   "eta": "2025-12-18T00:00:00Z",
   "nextAction": "POD ...",
   "riskLevel": "HIGH",
   "currentBottleneckCode": "INSPECT_RED"
   }
   ],
   "meta": {
   "count": 1,
   "duplicates": ["SCT-0151"],
   "ts": "2026-01-06T00:00:00Z",
   "source": "airtable"
   }
   }
3) 인증(권장)

MVP: X-API-Key: `<token>` (서버 env로 관리)

운영: JWT(SSO 연계) + IP allowlist

4) Airtable 매핑(현재 확인된 FieldID)

Shipments 테이블: tbl4NnKYx1ECKmaaC

필드:

shptNo = fldEQ5GwNfN6dRWnI

site = fldFEdNYSbs6Zm2c4

eta = flddGQaFY1Tn4B0ML

nextAction = fldkR6PTLDfvwnJN4

riskLevel = fldkbfmbgNi4iFJDk

currentBottleneckCode = fldIACEWXLqsorJF0

Automation notes (RPA+LLM+Sheets/TG)

GPTs가 /v1/shipments/verify 호출 → 결과를 표로 렌더 → 필요 시 TG로 “INSPECT_RED + HIGH만” 자동 알림

향후 B-3에서 업데이트 수행 시, Events 테이블에 변경 로그 자동 적재(감사 대응)

QA / Recheck Checklist

 Airtable API 토큰을 서버 env로 분리(코드/로그에 노출 금지)

 SCT-0151 같은 중복 shptNo 처리 규칙(모두 반환 vs latest eta 우선) 결정

 eta 타임존 고정(UTC/Asia-Dubai 중 택1) — 현재 Airtable은 UTC 저장

CmdRec

/switch_mode LATTICE

/logi-master --fast report

/redo step 1

바로 다음 액션(확정본)

아래 3가지를 내가 “최종 스펙 + 코드 템플릿”으로 한 번에 드릴 수 있습니다.

OpenAPI 3.1 YAML (GPTs Action에 그대로 붙여넣기용)

FastAPI 서버 템플릿 (Airtable 호출 + FieldID 매핑 + API Key 인증)

중복 탐지/필터링 로직(SCT-0151 같은 케이스 처리)

다음 메시지에 배포 환경만 알려주세요(택1):

Vercel / Render / AWS EC2 / 사내 서버
그러면 그 환경 기준으로 바로 실행 가능한 패키지로 정리해서 제공합니다.

GPTs에서도 쓸 수 있게 '읽기 전용 대시보드 링크 생성'**이나 서버 중계(RPA) 설계를 바로 잡아드리겠습니다
ExecSummary

요청하신 범위는 **Option B(서버 중계)**로 “GPTs에서도 읽기(대시보드/검증) 가능”하게 만드는 설계입니다.

핵심은 GPTs → 우리 Proxy API(OpenAPI Action) → Airtable로 단순화하고, 서버에서 인증·감사로그·필드ID 매핑·중복 감지를 처리하는 것입니다.

아래에 바로 붙여 넣을 OpenAPI 3.1 스펙 + FastAPI 템플릿 + 운영 체크리스트를 제공합니다.

Visual-first: 최종 구조
구성요소	역할	비고
GPTs Action	우리 API 호출	OpenAPI 3.1 필요
Proxy 서버(FastAPI)	인증/검증/캐시/로깅	Airtable 토큰 은닉
Airtable Shipments	데이터 소스	필드ID 기반 조회
Option B 설계안(확정)

1) API 엔드포인트(최소 세트)

GET /v1/shipments/verify?shptNo=HE-0512,HE-0513,SCT-0151

반환 필드 고정: shptNo, site, eta, nextAction, riskLevel, currentBottleneckCode

meta.duplicates에 중복 shptNo 리스트 포함

GET /v1/health

서버 상태 확인

OpenAPI 3.1 (GPTs Action용, 그대로 사용)
openapi: 3.1.0
info:
  title: HVDC Shipment Read Proxy
  version: "1.0.0"
servers:

- url: https://YOUR_PROXY_DOMAIN
  paths:
  /v1/health:
  get:
  operationId: health
  responses:
  "200":
  description: OK
  content:
  application/json:
  schema:
  type: object
  properties:
  status: { type: string }
  ts: { type: string }
  /v1/shipments/verify:
  get:
  operationId: verifyShipments
  parameters:
  - name: shptNo
  in: query
  required: true
  description: Comma-separated shipment numbers (e.g., HE-0512,HE-0513,SCT-0151)
  schema:
  type: string
  responses:
  "200":
  description: Shipment verification view
  content:
  application/json:
  schema:
  type: object
  required: [items, meta]
  properties:
  items:
  type: array
  items:
  type: object
  required: [shptNo, site, eta, nextAction, riskLevel, currentBottleneckCode]
  properties:
  shptNo: { type: string }
  site: { type: string }
  eta: { type: string }
  nextAction: { type: string }
  riskLevel: { type: string }
  currentBottleneckCode: { type: string }
  meta:
  type: object
  required: [count, duplicates, ts, source]
  properties:
  count: { type: integer }
  duplicates:
  type: array
  items: { type: string }
  ts: { type: string }
  source: { type: string }
  security:
- apiKeyAuth: []
  components:
  securitySchemes:
  apiKeyAuth:
  type: apiKey
  in: header
  name: X-API-Key

FastAPI 서버 템플릿(바로 실행 가능)
from fastapi import FastAPI, Header, HTTPException, Query
from typing import List, Optional, Dict, Any
import os, requests
from datetime import datetime, timezone

app = FastAPI(title="HVDC Shipment Read Proxy", version="1.0.0")

AIRTABLE_API_KEY = os.environ["AIRTABLE_API_KEY"]
AIRTABLE_BASE_ID  = os.environ["AIRTABLE_BASE_ID"]      # appnLz06h07aMm366
AIRTABLE_TABLE_ID = os.environ["AIRTABLE_TABLE_ID"]     # tbl4NnKYx1ECKmaaC
API_KEY = os.environ["PROXY_API_KEY"]

# Shipments Field IDs (현재 확인된 값)

F_SHPTNO = "fldEQ5GwNfN6dRWnI"
F_SITE   = "fldFEdNYSbs6Zm2c4"
F_ETA    = "flddGQaFY1Tn4B0ML"
F_NEXT   = "fldkR6PTLDfvwnJN4"
F_RISK   = "fldkbfmbgNi4iFJDk"
F_BN     = "fldIACEWXLqsorJF0"

AIRTABLE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_ID}"

def auth(x_api_key: Optional[str]):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/v1/health")
def health():
    return {"status": "ok", "ts": datetime.now(timezone.utc).isoformat()}

@app.get("/v1/shipments/verify")
def verify_shipments(
    shptNo: str = Query(..., description="Comma-separated shipment numbers"),
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")
):
    auth(x_api_key)

    wanted = [s.strip() for s in shptNo.split(",") if s.strip()]
    if not wanted:
        raise HTTPException(status_code=400, detail="shptNo is empty")

    # Airtable filterByFormula: OR({shptNo}="A",{shptNo}="B",...)
    # 공식 필터는 formula 문자열 기반(REST). 필드명 대신 실제 컬럼명(shptNo)을 사용.
    # 테이블에서 primary field name이 'shptNo'이므로 {shptNo}로 필터링.
    or_parts = ",".join([f'{{shptNo}}="{s}"' for s in wanted])
    formula = f"OR({or_parts})"

    headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}
    params = {
        "filterByFormula": formula,
        "fields[]": ["shptNo", "site", "eta", "nextAction", "riskLevel", "currentBottleneckCode"],
        "pageSize": 100
    }

    r = requests.get(AIRTABLE_URL, headers=headers, params=params, timeout=20)
    if r.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"Airtable error: {r.text}")

    data = r.json()
    records = data.get("records", [])

    # items 구성
    items = []
    seen = {}
    for rec in records:
        f = rec.get("fields", {})
        sn = f.get("shptNo", "")
        seen[sn] = seen.get(sn, 0) + 1
        items.append({
            "shptNo": sn,
            "site": f.get("site", ""),
            "eta": f.get("eta", ""),
            "nextAction": f.get("nextAction", ""),
            "riskLevel": f.get("riskLevel", ""),
            "currentBottleneckCode": f.get("currentBottleneckCode", "")
        })

    duplicates = [k for k,v in seen.items() if v > 1]

    return {
        "items": items,
        "meta": {
            "count": len(items),
            "duplicates": duplicates,
            "ts": datetime.now(timezone.utc).isoformat(),
            "source": "airtable"
        }
    }

운영 보안/감사(필수 체크)

Airtable API Key는 서버 ENV에만 저장(코드/로그/프롬프트에 절대 노출 금지)

X-API-Key 또는 JWT로 GPTs Action 인증

감사로그(누가/언제/어떤 shptNo 조회) 남기기

중복 shptNo 정책:

기본: 모두 반환 + meta.duplicates 표시

운영안: “최신 eta 우선 1건만” 같은 룰로 정규화 가능

다음 단계(바로 진행 순서)

Proxy 서버 배포(선호: Render/EC2/Vercel Functions 중 택1)

환경변수 세팅

AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLE_ID, PROXY_API_KEY

GPTs → Actions에 OpenAPI 붙여넣기 + X-API-Key 설정

테스트 호출:

/v1/shipments/verify?shptNo=HE-0512,HE-0513,SCT-0151

QA / Recheck

SCT-0151 중복이 계속 보이면, 서버에서 duplicates를 Hard Flag로 만들어 운영자 확인 게이트로 사용 가능

eta 타임존(UTC 고정) 유지 여부 확인

CmdRec

/switch_mode LATTICE

/logi-master --fast report

/redo step 1

원하시는 배포 환경이 Vercel / Render / EC2 중 무엇인지 한 줄로만 답해주시면, 그 환경 기준으로 (1) 배포용 폴더 구조, (2) requirements, (3) 배포 명령어/설정까지 완성본으로 정리해 드리겠습니다.



## ExecSummary

* Vercel로 Option B(Proxy API) 배포는 **Next.js Route Handler(권장)** 또는 **Serverless Function**으로 구현합니다.
* 아래는  **Vercel에 그대로 올려서 동작하는 최소 패키지** (읽기 전용)입니다: `GET /api/health`, `GET /api/shipments/verify?shptNo=...`
* GPTs Action은 제공한 OpenAPI에서 `servers.url`만 Vercel 도메인으로 바꾸면 됩니다.

---

## Visual-first: Vercel 배포 구조

| 항목          | 값                                        |
| ------------- | ----------------------------------------- |
| 런타임        | Next.js App Router(Route Handlers)        |
| 엔드포인트    | `/api/health`,`/api/shipments/verify` |
| 인증          | `X-API-Key`헤더                         |
| Airtable 접근 | `filterByFormula`+ fields 제한          |

---

## 구현 옵션 3가지 (Vercel 관점)

### Option 1) Next.js Route Handlers (권장)

* Pros: 가장 간단, Vercel 표준, 유지보수 쉬움
* Cons: Next.js 프로젝트 필요
* Risk: Low
* Time: 즉시

### Option 2) Vercel Serverless Functions (Node)

* Pros: Next.js 없이도 가능
* Cons: 구조가 분산될 수 있음
* Risk: Low
* Time: 즉시

### Option 3) Edge Functions

* Pros: 빠름
* Cons: Node API 제약, 디버깅 번거로움
* Risk: Medium
* Time: 비권장(이번 케이스)

---

## Roadmap (P→Pi→B→O→S)

* **Prepare:** Next.js API Route 템플릿 + Vercel Env 설정
* **Pilot:** `/api/shipments/verify`로 6건 조회 테스트
* **Build:** 중복 shptNo 감지/정규화 룰 추가
* **Operate:** 로그/알림(TG/Teams) 연동
* **Scale:** Actions/Events/Docs까지 확장

---

# Vercel 배포용 “최소 동작” 패키지

## 1) 프로젝트 생성

```bash
npx create-next-app@latest hvdc-airtable-proxy --ts --eslint --app
cd hvdc-airtable-proxy
```

## 2) 파일 생성: `/app/api/health/route.ts`

```ts
import { NextResponse } from "next/server";

export const runtime = "nodejs";

export async function GET() {
  return NextResponse.json({
    status: "ok",
    ts: new Date().toISOString(),
    source: "vercel",
  });
}
```

## 3) 파일 생성: `/app/api/shipments/verify/route.ts`

```ts
import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";

function unauthorized() {
  return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
}

function badRequest(msg: string) {
  return NextResponse.json({ error: msg }, { status: 400 });
}

export async function GET(req: NextRequest) {
  // Auth
  const apiKey = req.headers.get("x-api-key") || "";
  if (!process.env.PROXY_API_KEY || apiKey !== process.env.PROXY_API_KEY) {
    return unauthorized();
  }

  // Input
  const shptNo = req.nextUrl.searchParams.get("shptNo") || "";
  const wanted = shptNo
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);

  if (wanted.length === 0) return badRequest("shptNo is empty");
  if (wanted.length > 50) return badRequest("Too many shptNo (max 50)");

  // Env
  const AIRTABLE_API_KEY = process.env.AIRTABLE_API_KEY || "";
  const AIRTABLE_BASE_ID = process.env.AIRTABLE_BASE_ID || "";
  const AIRTABLE_TABLE_ID = process.env.AIRTABLE_TABLE_ID || "";
  if (!AIRTABLE_API_KEY || !AIRTABLE_BASE_ID || !AIRTABLE_TABLE_ID) {
    return NextResponse.json(
      { error: "Server env not configured" },
      { status: 500 }
    );
  }

  // Airtable REST
  const url = `https://api.airtable.com/v0/${AIRTABLE_BASE_ID}/${AIRTABLE_TABLE_ID}`;

  // filterByFormula: OR({shptNo}="A",{shptNo}="B",...)
  const orParts = wanted.map((s) => `{shptNo}="${s.replace(/"/g, '\\"')}"`).join(",");
  const filterByFormula = `OR(${orParts})`;

  const params = new URLSearchParams();
  params.set("filterByFormula", filterByFormula);
  params.append("fields[]", "shptNo");
  params.append("fields[]", "site");
  params.append("fields[]", "eta");
  params.append("fields[]", "nextAction");
  params.append("fields[]", "riskLevel");
  params.append("fields[]", "currentBottleneckCode");
  params.set("pageSize", "100");

  const r = await fetch(`${url}?${params.toString()}`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${AIRTABLE_API_KEY}`,
    },
  });

  if (!r.ok) {
    const text = await r.text();
    return NextResponse.json(
      { error: "Airtable error", detail: text },
      { status: 502 }
    );
  }

  const data = await r.json();
  const records = (data?.records || []) as Array<any>;

  const seen: Record<string, number> = {};
  const items = records.map((rec) => {
    const f = rec.fields || {};
    const sn = String(f.shptNo || "");
    seen[sn] = (seen[sn] || 0) + 1;

    return {
      shptNo: sn,
      site: String(f.site || ""),
      eta: String(f.eta || ""),
      nextAction: String(f.nextAction || ""),
      riskLevel: String(f.riskLevel || ""),
      currentBottleneckCode: String(f.currentBottleneckCode || ""),
    };
  });

  const duplicates = Object.entries(seen)
    .filter(([, v]) => v > 1)
    .map(([k]) => k);

  return NextResponse.json({
    items,
    meta: {
      count: items.length,
      duplicates,
      ts: new Date().toISOString(),
      source: "airtable",
    },
  });
}
```

---

## 4) Vercel 환경변수 설정 (필수)

Vercel Project → **Settings → Environment Variables**에 아래를 추가:

* `AIRTABLE_API_KEY` = (Airtable Personal Access Token)
* `AIRTABLE_BASE_ID` = `appnLz06h07aMm366`
* `AIRTABLE_TABLE_ID` = `tbl4NnKYx1ECKmaaC`
* `PROXY_API_KEY` = (임의의 긴 토큰)

권장: Preview/Production 모두 등록.

---

## 5) 로컬 테스트

```bash
npm run dev
curl -H "X-API-Key: $PROXY_API_KEY" "http://localhost:3000/api/health"
curl -H "X-API-Key: $PROXY_API_KEY" "http://localhost:3000/api/shipments/verify?shptNo=HE-0512,HE-0513,SCT-0151"
```

---

## 6) Vercel 배포

```bash
npm i -g vercel
vercel login
vercel
vercel --prod
```

---

## GPTs Action 연결

* OpenAPI `servers.url`를 배포된 Vercel 도메인으로 변경:
  * `https://hvdc-airtable-proxy.vercel.app`
* 인증은 GPTs 설정에서 `X-API-Key` 헤더 값을 넣도록 구성(가능한 방식으로).

---

## 운영 개선(즉시 넣을 수 있는 3가지)

1. **중복 shptNo 정책**
   * 현재: 모두 반환 + `meta.duplicates`
   * 개선: `eta` 최신 1건만 반환 옵션 추가(`mode=latest`)
2. **Rate limit**
   * 단순: 요청당 shptNo 50개 제한(이미 포함)
3. **감사 로그**
   * Vercel 로그 + (추후) Airtable Events 테이블에 조회 이벤트 기록

---

## QA / Recheck

* Airtable 컬럼명이 실제로 `{shptNo}`인지 확인(현재 테이블 스키마 상 primary field가 shptNo라 문제 가능성 낮음)
* Token/Key가 코드에 노출되지 않는지 점검(로그에도 출력 금지)

---

## CmdRec

* `/switch_mode LATTICE`
* `/logi-master --fast report`

원하면, 위 코드에 **“SCT-0151 중복이면 HARD FAIL(409)”** 또는 **“latest eta만 반환”** 모드를 추가한 버전까지 바로 만들어 드리겠습니다.



## ExecSummary

* **app 노출:** 현재 코드에 `app = Flask(__name__)`가 이미 존재합니다 → Vercel `@vercel/python` 엔트리 조건 충족.
* **ENV 키명:** Airtable 토큰은 코드가 `AIRTABLE_API_TOKEN`을 읽습니다 → Vercel Env도 동일 키로 맞추면 됩니다.
* **/shipments/verify:** 아래 “최소 diff”를 적용하면, GPTs용 **읽기 전용 검증 API**가 Flask(현 구조)에서 바로 동작합니다. (ENG-KR 1L: Minimal patch adds verify endpoint without changing architecture.)

---

## Visual-first: 확인된 사실 3개

| 항목              | 상태                                                     | 근거 |
| ----------------- | -------------------------------------------------------- | ---- |
| Flask app 엔트리  | `app = Flask(__name__)`존재                            |      |
| Airtable 토큰 ENV | `AIRTABLE_API_TOKEN = os.getenv("AIRTABLE_API_TOKEN")` |      |
| Vercel 배포 방식  | `@vercel/python`+`api/document_status.py`라우팅      |      |

---

# ✅ 최소 diff 패치 (Flask 유지, /shipments/verify 추가)

> 업로드된 파일명은 `app.py`이지만, Vercel 가이드의 엔트리 경로는 `api/document_status.py`입니다.
> 실제 레포에서 엔트리 파일명이 `api/document_status.py`라면 **그 파일에 아래 diff를 적용**하세요. (내용은 현재 업로드된 `app.py` 기준)

### Patch 1) 인증 유틸 추가 (API_KEY가 설정된 경우에만 강제)

* `API_KEY`(Bearer 또는 X-API-Key)를 **선택적으로 강제**합니다.
* `API_KEY`가 비어 있으면(미설정) 기존처럼 공개 동작(현재 코드의 다른 엔드포인트와 호환).

```diff
--- a/api/document_status.py
+++ b/api/document_status.py
@@ -1,7 +1,7 @@
 import os
 from flask import Flask, jsonify, request, abort, send_from_directory
 from flask_cors import CORS
@@
 app = Flask(__name__)
@@
 AIRTABLE_API_TOKEN = os.getenv("AIRTABLE_API_TOKEN")
 if AIRTABLE_API_TOKEN:
     AIRTABLE_API_TOKEN = AIRTABLE_API_TOKEN.strip()
+
+# Optional API auth for ChatGPT Actions (enabled only if API_KEY is set)
+API_KEY = os.getenv("API_KEY")
+if API_KEY:
+    API_KEY = API_KEY.strip()
+
+def require_api_key():
+    """
+    Enforce auth only when API_KEY is configured.
+    Supports:
+      - Authorization: Bearer <API_KEY>
+      - X-API-Key: <API_KEY>
+    """
+    if not API_KEY:
+        return
+    auth = (request.headers.get("Authorization") or "").strip()
+    xkey = (request.headers.get("X-API-Key") or "").strip()
+    if auth.lower().startswith("bearer "):
+        token = auth.split(" ", 1)[1].strip()
+        if token == API_KEY:
+            return
+    if xkey == API_KEY:
+        return
+    abort(401)
```

---

### Patch 2) `/shipments/verify` 엔드포인트 추가

* 입력: `GET /shipments/verify?shptNo=HE-0512,HE-0513,SCT-0151`
* 출력: `items[]` + `meta{count,duplicates,timestamp,schemaVersion}`
* Airtable이 없으면 503, 입력 없으면 400.

```diff
--- a/api/document_status.py
+++ b/api/document_status.py
@@
 @app.route("/health", methods=["GET"])
 def health_check():
@@
     return jsonify(
         {
@@
         }
     )
+
+
+@app.route("/shipments/verify", methods=["GET"])
+def shipments_verify():
+    """
+    GET /shipments/verify?shptNo=A,B,C
+
+    Returns fields for operational verification:
+      shptNo, site, eta, nextAction, riskLevel, currentBottleneckCode
+    Also returns duplicates list if same shptNo appears multiple times.
+    """
+    require_api_key()
+
+    if not airtable_client:
+        return jsonify({
+            "error": "Airtable connection not available",
+            "status": "service_unavailable",
+            "timestamp": now_dubai(),
+            "schemaVersion": SCHEMA_VERSION
+        }), 503
+
+    shptNo = (request.args.get("shptNo") or "").strip()
+    wanted = [s.strip() for s in shptNo.split(",") if s.strip()]
+    if not wanted:
+        return jsonify({
+            "error": "shptNo is empty",
+            "status": "bad_request",
+            "timestamp": now_dubai(),
+            "schemaVersion": SCHEMA_VERSION
+        }), 400
+
+    if len(wanted) > 50:
+        return jsonify({
+            "error": "Too many shptNo (max 50)",
+            "status": "bad_request",
+            "timestamp": now_dubai(),
+            "schemaVersion": SCHEMA_VERSION
+        }), 400
+
+    # Airtable filterByFormula: OR({shptNo}='A',{shptNo}='B',...)
+    # Using field NAME {shptNo} matches your existing conventions.
+    or_parts = ",".join([f"{{shptNo}}='{s.replace(\"'\", \"\\\\'\")}'" for s in wanted])
+    formula = f"OR({or_parts})"
+
+    try:
+        records = airtable_client.list_records(
+            TABLES_LOWER["shipments"],
+            filter_by_formula=formula,
+            fields=["shptNo", "site", "eta", "nextAction", "riskLevel", "currentBottleneckCode"],
+            page_size=100
+        )
+    except Exception as e:
+        return jsonify({
+            "error": "Airtable error",
+            "details": str(e),
+            "status": "upstream_error",
+            "timestamp": now_dubai(),
+            "schemaVersion": SCHEMA_VERSION
+        }), 502
+
+    seen = {}
+    items = []
+    for rec in records or []:
+        f = rec.get("fields", {})
+        sn = f.get("shptNo") or ""
+        sn = str(sn)
+        seen[sn] = seen.get(sn, 0) + 1
+        items.append({
+            "shptNo": sn,
+            "site": str(f.get("site") or ""),
+            "eta": str(f.get("eta") or ""),
+            "nextAction": str(f.get("nextAction") or ""),
+            "riskLevel": str(f.get("riskLevel") or ""),
+            "currentBottleneckCode": str(f.get("currentBottleneckCode") or "")
+        })
+
+    duplicates = [k for k, v in seen.items() if v > 1]
+
+    return jsonify({
+        "items": items,
+        "meta": {
+            "count": len(items),
+            "duplicates": duplicates,
+            "timestamp": now_dubai(),
+            "schemaVersion": SCHEMA_VERSION
+        }
+    }), 200
```

---

### Patch 3) (선택) `/` 인덱스에 엔드포인트 안내 추가

운영자/테스트 편의를 위해 루트 응답의 endpoints 목록에 추가(선택).

```diff
--- a/api/document_status.py
+++ b/api/document_status.py
@@
             "endpoints": {
                 "home": "/",
                 "health": "/health",
+                "shipments_verify": "/shipments/verify?shptNo=A,B,C",
                 "document_status": "/document/status/{shptNo}",
                 "approval_status": "/approval/status/{shptNo}",
                 "document_events": "/document/events/{shptNo}",
                 "status_summary": "/status/summary",
                 "bottleneck_summary": "/bottleneck/summary",
                 "ingest_events": "POST /ingest/events",
             },
```

---

## Vercel Env 정렬 포인트 (확정)

* 필수:
  * `AIRTABLE_API_TOKEN` (코드가 이 이름을 사용)
* 권장(보안/GPTs Actions):
  * `API_KEY` (설정하면 위 패치로 인증 강제됨)
* 이미 잠금 설정 사용 중:
  * `BASE_ID`/`TABLES`는 `api.airtable_locked_config`에서 가져오므로 별도 ENV 불필요(현재 구조).

---

## 테스트 커맨드 (배포 후)

```bash
# X-API-Key 방식
curl -H "X-API-Key: <API_KEY>" "https://<your-vercel-domain>/shipments/verify?shptNo=HE-0512,HE-0513,SCT-0151"

# Bearer 방식
curl -H "Authorization: Bearer <API_KEY>" "https://<your-vercel-domain>/shipments/verify?shptNo=HE-0512,HE-0513,SCT-0151"
```

---

## QA / Recheck

* `app = Flask(__name__)`가 이미 있어 Vercel Python 엔트리 OK.
* Airtable 토큰 키명은 문서 가이드와 코드가 일치(`AIRTABLE_API_TOKEN`).
* SCT-0151 같은 중복은 `meta.duplicates`에 표시되므로, 이후 “latest만 반환” 모드도 쉽게 확장 가능.

---

## CmdRec

* `/switch_mode PRIME`
* `/logi-master --fast report`

원하면 다음 단계로  **OpenAPI 스키마에 `/shipments/verify`를 추가** (Bearer 또는 X-API-Key 중 택1로 완전 일치)하는 YAML diff도 바로 만들어 드리겠습니다.


## ExecSummary

* 지금 시점에서 **확실히 말할 수 있는 실행 엔트리/ENV/라우팅 기준은 `api/app.py`**입니다(Flask `app` 오브젝트 존재, Vercel Python 엔트리 조건 충족).
* 코드가 읽는 Airtable 토큰 키는 **`AIRTABLE_API_TOKEN`**입니다. Vercel Env도 이 이름으로 맞춰야 “Not Connected”가 해소됩니다.
* 당신이 정리한 “실행 파일 15개 목록”은  **현재 업로드된 파일만으로는 전부 실재 여부를 검증할 수 없습니다** (repo 트리/파일 목록이 필요). **대신, 실제 동작 경로(배포/테스트)를 `api/app.py` 기준으로 바로 확정**해 드립니다.

---

## Visual-first: “실행 파일” 관점에서 지금 확정 가능한 것

| 분류               | 확정 실행 단위                                                                        | 근거                                |
| ------------------ | ------------------------------------------------------------------------------------- | ----------------------------------- |
| Vercel 실행 엔트리 | Flask `app`(WSGI)                                                                   | `app = Flask(__name__)`           |
| 필수 ENV           | `AIRTABLE_API_TOKEN`                                                                | `os.getenv("AIRTABLE_API_TOKEN")` |
| 주요 API 라우트    | `/health`,`/health/detailed`,`/status/summary`,`/document/status/<shpt_no>`등 | 라우트 정의 다수 존재               |
| CORS               | ChatGPT Actions 허용 origin/headers 포함                                              | CORS 설정 블록 존재                 |

---

# 당신이 정리한 “15개 실행 파일 목록”에 대한 정확한 판정

* **현재 업로드된 파일 세트에는 `scripts/*`, `tests/*`, `vercel.json`, `runtime.txt`가 포함되어 있지 않습니다.**
* 따라서 그 목록의 **존재/경로/목적을 ‘확정’으로 승인할 수는 없습니다.**
* 다만,  **배포/동작에 필요한 핵심은 이미 `api/app.py`에 다 들어가 있고** , 여기 기준으로 Option B(Flask 유지)를 진행하면 됩니다.

---

## 다음 액션(여기서 바로 확정): `/shipments/verify`를 “현재 구조”에 맞게 추가

당신이 원하는 GPTs용 “읽기 전용 검증”은, **`api/app.py`에 엔드포인트 1개 추가**로 끝납니다.

### 1) 최소 패치(diff 형태) — `api/app.py`에 추가

아래는 “기존 구조(locked table ids + AirtableClient + CORS)”를 그대로 쓰는 형태입니다.

```diff
--- a/api/app.py
+++ b/api/app.py
@@
 AIRTABLE_API_TOKEN = os.getenv("AIRTABLE_API_TOKEN")
 if AIRTABLE_API_TOKEN:
     AIRTABLE_API_TOKEN = AIRTABLE_API_TOKEN.strip()
+
+# Optional API auth for GPTs (enabled only if API_KEY is set)
+API_KEY = os.getenv("API_KEY")
+if API_KEY:
+    API_KEY = API_KEY.strip()
+
+def require_api_key():
+    """
+    Enforce auth only when API_KEY is configured.
+    Supports:
+      - Authorization: Bearer <API_KEY>
+      - X-API-Key: <API_KEY>
+    """
+    if not API_KEY:
+        return
+    auth = (request.headers.get("Authorization") or "").strip()
+    xkey = (request.headers.get("X-API-Key") or "").strip()
+    if auth.lower().startswith("bearer "):
+        token = auth.split(" ", 1)[1].strip()
+        if token == API_KEY:
+            return
+    if xkey == API_KEY:
+        return
+    abort(401)
@@
 @app.route("/health", methods=["GET"])
 def health_check():
@@
     return jsonify(
         {
@@
         }
     )
+
+@app.route("/shipments/verify", methods=["GET"])
+def shipments_verify():
+    """
+    GET /shipments/verify?shptNo=A,B,C
+    Returns:
+      shptNo, site, eta, nextAction, riskLevel, currentBottleneckCode
+      + meta(count, duplicates, timestamp, schemaVersion)
+    """
+    require_api_key()
+
+    if not airtable_client:
+        return jsonify({
+            "error": "Airtable connection not available",
+            "status": "service_unavailable",
+            "timestamp": now_dubai(),
+            "schemaVersion": SCHEMA_VERSION
+        }), 503
+
+    shptNo = (request.args.get("shptNo") or "").strip()
+    wanted = [s.strip() for s in shptNo.split(",") if s.strip()]
+    if not wanted:
+        return jsonify({
+            "error": "shptNo is empty",
+            "status": "bad_request",
+            "timestamp": now_dubai(),
+            "schemaVersion": SCHEMA_VERSION
+        }), 400
+    if len(wanted) > 50:
+        return jsonify({
+            "error": "Too many shptNo (max 50)",
+            "status": "bad_request",
+            "timestamp": now_dubai(),
+            "schemaVersion": SCHEMA_VERSION
+        }), 400
+
+    or_parts = ",".join([f"{{shptNo}}='{s.replace(\"'\", \"\\\\'\")}'" for s in wanted])
+    formula = f"OR({or_parts})"
+
+    try:
+        records = airtable_client.list_records(
+            TABLES_LOWER["shipments"],
+            filter_by_formula=formula,
+            fields=["shptNo","site","eta","nextAction","riskLevel","currentBottleneckCode"],
+            page_size=100
+        )
+    except Exception as e:
+        return jsonify({
+            "error": "Airtable error",
+            "details": str(e),
+            "status": "upstream_error",
+            "timestamp": now_dubai(),
+            "schemaVersion": SCHEMA_VERSION
+        }), 502
+
+    seen = {}
+    items = []
+    for rec in records or []:
+        f = rec.get("fields", {})
+        sn = str(f.get("shptNo") or "")
+        seen[sn] = seen.get(sn, 0) + 1
+        items.append({
+            "shptNo": sn,
+            "site": str(f.get("site") or ""),
+            "eta": str(f.get("eta") or ""),
+            "nextAction": str(f.get("nextAction") or ""),
+            "riskLevel": str(f.get("riskLevel") or ""),
+            "currentBottleneckCode": str(f.get("currentBottleneckCode") or "")
+        })
+
+    duplicates = [k for k,v in seen.items() if v > 1]
+    return jsonify({
+        "items": items,
+        "meta": {
+            "count": len(items),
+            "duplicates": duplicates,
+            "timestamp": now_dubai(),
+            "schemaVersion": SCHEMA_VERSION
+        }
+    }), 200
```

> 이 패치는 현재 코드의 AirtableClient/locked config 구조를 그대로 사용합니다.

---

## Vercel 환경변수 “최소 세트” (코드 기준 확정)

* 필수:
  * `AIRTABLE_API_TOKEN`
* 선택(보안/GPTs):
  * `API_KEY` (설정하면 위 패치로 인증 강제. 미설정이면 기존과 동일하게 공개)

---

## 검증 커맨드(배포 후)

```bash
# X-API-Key 방식
curl -H "X-API-Key: <API_KEY>" "https://<your-vercel-domain>/shipments/verify?shptNo=HE-0512,HE-0513,SCT-0151"

# Bearer 방식
curl -H "Authorization: Bearer <API_KEY>" "https://<your-vercel-domain>/shipments/verify?shptNo=HE-0512,HE-0513,SCT-0151"
```

---

## QA / Recheck

* 현재 `/health`는 Airtable 연결 상태를 `configured/connected`로 반환하므로, Env 설정이 맞으면 바로 확인 가능합니다.
* CORS는 이미 ChatGPT 관련 origin/headers가 포함되어 있어, Actions 측 장애 원인은 보통 **인증/URL/응답코드**입니다.

---

## CmdRec

* `/switch_mode PRIME`
* `/logi-master --fast report`

원하시면 다음 단계로, **OpenAPI 스키마(`/openapi-schema.yaml`)에 `/shipments/verify`를 추가하는 YAML diff**를 바로 제공하겠습니다.




## ExecSummary

* 당신이 작성한 **Flask 패치(3곳)**는 `api/app.py` 구조와 **정합**합니다. 특히 `AIRTABLE_API_TOKEN` 바로 아래에 `API_KEY`/`require_api_key()`를 넣는 위치는 정확합니다.
* 단, **OpenAPI 파일 경로는 `docs/openapi/openapi-gets-api.yaml`이 아니라, 현재 API가 서빙하는 `openapi-schema.yaml`(루트)**을 수정해야 합니다. (`/openapi-schema.yaml`이 그 파일을 읽어 서빙)
* 추가로, 배포 가이드의 Vercel 라우팅 예시는 `api/document_status.py`로 되어 있는데, 실제 엔트리는 **`api/app.py`** 구조가 맞습니다(리포에 맞게 vercel.json을 그쪽으로 향하게 해야 함).

---

## Visual-first: 적용 전 체크 3개

| 체크                              | 지금 상태                               | 액션                           |
| --------------------------------- | --------------------------------------- | ------------------------------ |
| `AIRTABLE_API_TOKEN`사용        | 코드가 이 키를 읽음                     | Vercel Env도 동일 키로 유지    |
| `/openapi-schema.yaml`서빙 방식 | 루트 `openapi-schema.yaml`파일을 읽음 | **그 파일을 업데이트**   |
| Vercel 라우팅 대상                | 가이드는 `api/document_status.py`     | 실제는 `api/app.py`로 맞추기 |

---

# 1) Flask 패치 검증 (당신 제안안 그대로 OK)

### Patch 1 위치

* `AIRTABLE_API_TOKEN` 선언 블록 바로 뒤가 정확한 삽입 위치입니다. 그 다음 줄에 `AIRTABLE_BASE_ID = BASE_ID`가 이미 있으므로, 그 **직전**에 넣으면 됩니다.

### Patch 2 위치

* 현재 `/health` 라우트가 있고, 바로 다음에 `/document/status/<shpt_no>`가 시작됩니다. **그 사이에 `/shipments/verify`를 넣는 구조가 정확**합니다.

### Patch 3 위치

* `index()`의 `"endpoints"` dict에 `"shipments_verify"`를 추가하는 위치도 정확합니다(현재 목록에 `/health` 다음으로 넣으면 됨).

---

# 2) OpenAPI 업데이트: 파일 경로 수정이 핵심

당신 문서처럼 `docs/openapi/openapi-gets-api.yaml`에 넣으면  **API가 서빙하지 않습니다** .
현재 API는 `/openapi-schema.yaml` 요청 시 **루트의 `openapi-schema.yaml`**을 읽어 반환합니다.

## 권장 수정안 (정합 버전)

* 대상 파일: **`openapi-schema.yaml` (repo 루트)**

### (A) `paths:`에 `/shipments/verify` 추가

> 인증은 “옵션”이라 했으므로, **path에 `security:`를 강제하지 마세요.**
> (서버에서 `API_KEY`가 설정된 경우에만 401로 막는 런타임 정책이므로, 스펙상 “항상 필요”로 선언하면 GPTs가 키 없이 호출할 때 충돌할 수 있음)

```yaml
  /shipments/verify:
    get:
      summary: Verify shipments (GPTs Action)
      operationId: verifyShipments
      description: |
        Returns operational verification fields for multiple shipments.
        Comma-separated shptNo list (max 50).
        If API_KEY env var is set, authentication is enforced.
      parameters:
        - name: shptNo
          in: query
          required: true
          schema:
            type: string
          example: "HE-0512,HE-0513,SCT-0151"
      responses:
        "200":
          description: Shipment verification data
          content:
            application/json:
              schema:
                type: object
                required: [items, meta]
                properties:
                  items:
                    type: array
                    items:
                      type: object
                      required: [shptNo, site, eta, nextAction, riskLevel, currentBottleneckCode]
                      properties:
                        shptNo: { type: string }
                        site: { type: string }
                        eta: { type: string, format: date-time }
                        nextAction: { type: string }
                        riskLevel: { type: string, enum: [LOW, MEDIUM, HIGH, CRITICAL] }
                        currentBottleneckCode: { type: string }
                  meta:
                    type: object
                    required: [count, duplicates, timestamp, schemaVersion]
                    properties:
                      count: { type: integer }
                      duplicates:
                        type: array
                        items: { type: string }
                      timestamp: { type: string, format: date-time }
                      schemaVersion: { type: string }
        "400":
          description: Bad request
        "401":
          description: Unauthorized (only when API_KEY is configured)
        "502":
          description: Airtable upstream error
        "503":
          description: Airtable not connected
```

### (B) `components.securitySchemes`는 “정의만”

> GPTs에서 인증을 쓰고 싶으면, Actions UI에서 Bearer 또는 헤더 기반으로 넣게 되므로, 스펙에 “정의”만 두고 강제는 하지 않는 방식이 가장 안전합니다.

```yaml
components:
  securitySchemes:
    apiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key
    bearerAuth:
      type: http
      scheme: bearer
```

---

# 3) Vercel 라우팅 정합(필수 확인)

배포 가이드 예시는 `api/document_status.py`로 라우팅합니다.
하지만 실제 엔트리 코드는 `api/app.py`입니다.

따라서 **vercel.json의 src/dest가 어디를 가리키는지**를 반드시 맞추세요:

* `api/app.py`로 라우팅되도록 수정(또는 `api/document_status.py`가 실제로 존재하고 그 파일이 `api/app.py`를 import해 `app`을 노출하는 구조여야 함)

---

## Options (마지막 선택 3개)

1. **vercel.json을 `api/app.py`로 직접 라우팅** (가장 단순/권장)
2. `api/document_status.py`를 “얇은 래퍼”로 만들고 내부에서 `from api.app import app`만 노출
3. 가이드 문서/코드 엔트리명 통일(문서도 `api/app.py` 기준으로 업데이트)

---

## Roadmap

* Prepare: `api/app.py` 패치 3곳 적용 + `openapi-schema.yaml` 업데이트
* Pilot: Vercel 재배포 후 `/health`와 `/shipments/verify` cURL 확인
* Build: GPTs Actions에 servers.url 업데이트 + verifyShipments 호출 테스트

---

## QA / Recheck

* `/openapi-schema.yaml`이 **실제로 업데이트된 내용을 서빙하는지** 확인 (Swagger UI가 이 경로를 사용)
* `API_KEY`를 켜면(Env 설정) 401이 정상 발생하는지 확인
* `TABLES_LOWER["shipments"]`가 존재한다는 전제(현재 코드에서 health가 이 키로 list_records를 호출) → verify도 동일 키 사용하면 OK

---

## CmdRec

* `/switch_mode PRIME`
* `/logi-master --fast report`

원하면, **`vercel.json`을 `api/app.py`로 정확히 라우팅**하는 최소 diff까지 같이 만들어드릴 수 있습니다. (현재 대화엔 vercel.json 파일이 없어서, 내용 붙여주면 즉시 diff 작성 가능)

## ExecSummary

* 당신이 작성한 **Flask 패치(3곳)**는 `api/app.py` 구조와 **정합**합니다. 특히 `AIRTABLE_API_TOKEN` 바로 아래에 `API_KEY`/`require_api_key()`를 넣는 위치는 정확합니다.
* 단, **OpenAPI 파일 경로는 `docs/openapi/openapi-gets-api.yaml`이 아니라, 현재 API가 서빙하는 `openapi-schema.yaml`(루트)**을 수정해야 합니다. (`/openapi-schema.yaml`이 그 파일을 읽어 서빙)
* 추가로, 배포 가이드의 Vercel 라우팅 예시는 `api/document_status.py`로 되어 있는데, 실제 엔트리는 **`api/app.py`** 구조가 맞습니다(리포에 맞게 vercel.json을 그쪽으로 향하게 해야 함).

---

## Visual-first: 적용 전 체크 3개

| 체크                              | 지금 상태                               | 액션                           |
| --------------------------------- | --------------------------------------- | ------------------------------ |
| `AIRTABLE_API_TOKEN`사용        | 코드가 이 키를 읽음                     | Vercel Env도 동일 키로 유지    |
| `/openapi-schema.yaml`서빙 방식 | 루트 `openapi-schema.yaml`파일을 읽음 | **그 파일을 업데이트**   |
| Vercel 라우팅 대상                | 가이드는 `api/document_status.py`     | 실제는 `api/app.py`로 맞추기 |

---

# 1) Flask 패치 검증 (당신 제안안 그대로 OK)

### Patch 1 위치

* `AIRTABLE_API_TOKEN` 선언 블록 바로 뒤가 정확한 삽입 위치입니다. 그 다음 줄에 `AIRTABLE_BASE_ID = BASE_ID`가 이미 있으므로, 그 **직전**에 넣으면 됩니다.

### Patch 2 위치

* 현재 `/health` 라우트가 있고, 바로 다음에 `/document/status/<shpt_no>`가 시작됩니다. **그 사이에 `/shipments/verify`를 넣는 구조가 정확**합니다.

### Patch 3 위치

* `index()`의 `"endpoints"` dict에 `"shipments_verify"`를 추가하는 위치도 정확합니다(현재 목록에 `/health` 다음으로 넣으면 됨).

---

# 2) OpenAPI 업데이트: 파일 경로 수정이 핵심

당신 문서처럼 `docs/openapi/openapi-gets-api.yaml`에 넣으면  **API가 서빙하지 않습니다** .
현재 API는 `/openapi-schema.yaml` 요청 시 **루트의 `openapi-schema.yaml`**을 읽어 반환합니다.

## 권장 수정안 (정합 버전)

* 대상 파일: **`openapi-schema.yaml` (repo 루트)**

### (A) `paths:`에 `/shipments/verify` 추가

> 인증은 “옵션”이라 했으므로, **path에 `security:`를 강제하지 마세요.**
> (서버에서 `API_KEY`가 설정된 경우에만 401로 막는 런타임 정책이므로, 스펙상 “항상 필요”로 선언하면 GPTs가 키 없이 호출할 때 충돌할 수 있음)

```yaml
  /shipments/verify:
    get:
      summary: Verify shipments (GPTs Action)
      operationId: verifyShipments
      description: |
        Returns operational verification fields for multiple shipments.
        Comma-separated shptNo list (max 50).
        If API_KEY env var is set, authentication is enforced.
      parameters:
        - name: shptNo
          in: query
          required: true
          schema:
            type: string
          example: "HE-0512,HE-0513,SCT-0151"
      responses:
        "200":
          description: Shipment verification data
          content:
            application/json:
              schema:
                type: object
                required: [items, meta]
                properties:
                  items:
                    type: array
                    items:
                      type: object
                      required: [shptNo, site, eta, nextAction, riskLevel, currentBottleneckCode]
                      properties:
                        shptNo: { type: string }
                        site: { type: string }
                        eta: { type: string, format: date-time }
                        nextAction: { type: string }
                        riskLevel: { type: string, enum: [LOW, MEDIUM, HIGH, CRITICAL] }
                        currentBottleneckCode: { type: string }
                  meta:
                    type: object
                    required: [count, duplicates, timestamp, schemaVersion]
                    properties:
                      count: { type: integer }
                      duplicates:
                        type: array
                        items: { type: string }
                      timestamp: { type: string, format: date-time }
                      schemaVersion: { type: string }
        "400":
          description: Bad request
        "401":
          description: Unauthorized (only when API_KEY is configured)
        "502":
          description: Airtable upstream error
        "503":
          description: Airtable not connected
```

### (B) `components.securitySchemes`는 “정의만”

> GPTs에서 인증을 쓰고 싶으면, Actions UI에서 Bearer 또는 헤더 기반으로 넣게 되므로, 스펙에 “정의”만 두고 강제는 하지 않는 방식이 가장 안전합니다.

```yaml
components:
  securitySchemes:
    apiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key
    bearerAuth:
      type: http
      scheme: bearer
```

---

# 3) Vercel 라우팅 정합(필수 확인)

배포 가이드 예시는 `api/document_status.py`로 라우팅합니다.
하지만 실제 엔트리 코드는 `api/app.py`입니다.

따라서 **vercel.json의 src/dest가 어디를 가리키는지**를 반드시 맞추세요:

* `api/app.py`로 라우팅되도록 수정(또는 `api/document_status.py`가 실제로 존재하고 그 파일이 `api/app.py`를 import해 `app`을 노출하는 구조여야 함)

---

## Options (마지막 선택 3개)

1. **vercel.json을 `api/app.py`로 직접 라우팅** (가장 단순/권장)
2. `api/document_status.py`를 “얇은 래퍼”로 만들고 내부에서 `from api.app import app`만 노출
3. 가이드 문서/코드 엔트리명 통일(문서도 `api/app.py` 기준으로 업데이트)

---

## Roadmap

* Prepare: `api/app.py` 패치 3곳 적용 + `openapi-schema.yaml` 업데이트
* Pilot: Vercel 재배포 후 `/health`와 `/shipments/verify` cURL 확인
* Build: GPTs Actions에 servers.url 업데이트 + verifyShipments 호출 테스트

---

## QA / Recheck

* `/openapi-schema.yaml`이 **실제로 업데이트된 내용을 서빙하는지** 확인 (Swagger UI가 이 경로를 사용)
* `API_KEY`를 켜면(Env 설정) 401이 정상 발생하는지 확인
* `TABLES_LOWER["shipments"]`가 존재한다는 전제(현재 코드에서 health가 이 키로 list_records를 호출) → verify도 동일 키 사용하면 OK

---

## CmdRec

* `/switch_mode PRIME`
* `/logi-master --fast report`

원하면, **`vercel.json`을 `api/app.py`로 정확히 라우팅**하는 최소 diff까지 같이 만들어드릴 수 있습니다. (현재 대화엔 vercel.json 파일이 없어서, 내용 붙여주면 즉시 diff 작성 가능)
