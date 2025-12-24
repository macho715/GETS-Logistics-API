## Exec (고정안 v1.0)

* 아래는 **Airtable(Base: Status Ledger) 필드 ↔ Flask API 응답(JSON) 1:1 매핑표**와 **Ingest payload 스펙(Event schema)** 를 **바로 운영 가능한 형태로 고정**한 v1.0입니다.
* 시간은 **Asia/Dubai(+04:00)** 기준으로 응답(Flask에서 normalize)하고, Airtable 저장/입출력은 **ISO 8601**을 강제합니다. ([Airtable][1])
* Airtable Web API 운용은 **5 req/sec/base**, 배치 입력은 **최대 10 records/request**를 전제로 설계합니다. ([Airtable][2])
* 산출물 파일(다운로드): 아래 SpecPack에 **Markdown 매핑표 + JSON Schema 2종** 포함.

[Download Spec Pack (ZIP)](sandbox:/mnt/data/HVDC_Airtable_Flask_SpecPack_2025-12-24.zip)

---

## Visual

### A) `GET /document/status/<shptNo>` — Status Packet 1:1 매핑표

| JSON Path              | Airtable Source (Table.Field)                                                                            |     Type | Rule/Transform (v1)                | Notes                                                                       |
| ---------------------- | -------------------------------------------------------------------------------------------------------- | -------: | ---------------------------------- | --------------------------------------------------------------------------- |
| `shptNo`               | `Shipments.shptNo`                                                                                       |     text | 그대로                                | Join Key(SSOT)                                                              |
| `doc.boeStatus`        | `Documents.status` (where `docType=BOE`, `shptNo=<shptNo>`)                                              |     enum | 없으면 `UNKNOWN`                      | Airtable API는 빈 값 필드가 응답에서 누락될 수 있음 → default 처리 필요 ([Airtable Support][3]) |
| `doc.doStatus`         | Documents (docType=DO)                                                                                   |     enum | 동일                                 |                                                                             |
| `doc.cooStatus`        | Documents (docType=COO)                                                                                  |     enum | 동일                                 |                                                                             |
| `doc.hblStatus`        | Documents (docType=HBL)                                                                                  |     enum | 동일                                 |                                                                             |
| `doc.ciplStatus`       | Documents (docType=CIPL)                                                                                 |     enum | 동일                                 |                                                                             |
| `bottleneck.code`      | `Shipments.currentBottleneckCode` → `BottleneckCodes.code`                                               |     text | link면 code로 resolve                | 병목 Taxonomy SSOT                                                            |
| `bottleneck.since`     | `Shipments.bottleneckSince`                                                                              | datetime | ISO 8601                           | DateTime은 ISO 8601로 read/write ([Airtable][1])                              |
| `bottleneck.riskLevel` | `Shipments.riskLevel` (fallback `BottleneckCodes.riskDefault`)                                           |     enum | fallback 적용                        |                                                                             |
| `action.nextAction`    | `Actions.actionText`(OPEN 1st) else `Shipments.nextAction` else `BottleneckCodes.nextActionTemplate`     |     text | 우선순위: Action > Shipment > Template | “운영 가능한 상태패킷” 핵심                                                            |
| `action.owner`         | `Actions.owner` else `Shipments.actionOwner`                                                             |     text | ownerName 반환                       |                                                                             |
| `action.dueAt`         | `Actions.dueAt` else `Shipments.dueAt` else NOW+`BottleneckCodes.slaHours`                               | datetime | ISO 8601(+04:00 normalize)         | SLA countdown                                                               |
| `evidence[]`           | UNION( `Documents.evidence`, `Approvals.evidence`, `Actions.evidence`, `Events.evidence`) → `Evidence.*` |    array | `evidenceId` 기준 dedupe             | 감사추적/근거 링크                                                                  |
| `meta.dataLagMinutes`  | `MAX(Events.timestamp)` 기반 계산 (또는 Shipments formula)                                                     |   number | NOW - lastEventAt                  | 대시보드 관측성                                                                    |

**샘플 응답(형상 고정 예시)**

```json
{
  "shptNo": "SCT-0143",
  "doc": {
    "boeStatus": "SUBMITTED",
    "doStatus": "NOT_STARTED",
    "cooStatus": "PENDING",
    "hblStatus": "READY",
    "ciplStatus": "VALID"
  },
  "bottleneck": {
    "code": "FANR_PENDING",
    "since": "2025-12-24T09:00:00+04:00",
    "riskLevel": "HIGH"
  },
  "action": {
    "nextAction": "FANR 승인 상태 확인 및 가속 요청",
    "owner": "Customs/Compliance",
    "dueAt": "2025-12-25T12:00:00+04:00"
  },
  "evidence": [
    { "type": "email", "id": "EV-0002", "externalId": "msg_abc", "sha256": null, "url": null }
  ],
  "meta": { "dataLagMinutes": 0 }
}
```

---

### B) `GET /approval/status/<shptNo>` — Approval Packet 1:1 매핑표

| JSON Path                   | Airtable Source                              |     Type | Rule/Transform             |
| --------------------------- | -------------------------------------------- | -------: | -------------------------- |
| `shptNo`                    | `Shipments.shptNo`                           |     text | 그대로                        |
| `approvals[].type`          | `Approvals.approvalType`                     |     enum | 그대로                        |
| `approvals[].status`        | `Approvals.status`                           |     enum | 그대로                        |
| `approvals[].submittedAt`   | `Approvals.submittedAt`                      | datetime | ISO 8601 ([Airtable][1])   |
| `approvals[].dueAt`         | `Approvals.dueAt`                            | datetime | ISO 8601(+04:00 normalize) |
| `approvals[].owner`         | `Approvals.owner` → `Owners.ownerName`       |     text | ownerName 반환               |
| `approvals[].evidenceIds[]` | `Approvals.evidence` → `Evidence.evidenceId` |    array | evidenceId 배열              |

---

### C) `GET /document/events/<shptNo>` — Events Ledger 1:1 매핑표

| JSON Path                 | Airtable Source                                |          Type | Rule                                           |
| ------------------------- | ---------------------------------------------- | ------------: | ---------------------------------------------- |
| `events[].eventId`        | `Events.eventId`                               |           int | 그대로                                            |
| `events[].timestamp`      | `Events.timestamp`                             |      datetime | ISO 8601 ([Airtable][1])                       |
| `events[].entityType`     | `Events.entityType`                            |          enum | SHIPMENT/DOCUMENT/APPROVAL/ACTION/DATA_QUALITY |
| `events[].fromStatus`     | `Events.fromStatus`                            |          text | optional                                       |
| `events[].toStatus`       | `Events.toStatus`                              |          text | required                                       |
| `events[].bottleneckCode` | `Events.bottleneckCode`→`BottleneckCodes.code` |          text | optional                                       |
| `events[].actor`          | `Events.actor`                                 |          text | optional                                       |
| `events[].sourceSystem`   | `Events.sourceSystem`                          |          enum | eDAS/SAP/EMAIL/RPA/API/MANUAL                  |
| `events[].evidenceIds[]`  | `Events.evidence`→`Evidence.evidenceId`        |         array | optional                                       |
| `events[].rawPayload`     | `Events.rawPayload`                            | object/string | JSON text 저장(원문)                               |

---

## Ingest payload 스펙 (Event schema 고정 v1.0)

### 1) 권장 엔드포인트 (운영형)

* `POST /ingest/events` : **append-only 이벤트 적재(감사추적/병목 분석 최적)**
* `POST /ingest/daily-report` : 일일 엑셀/리포트 스냅샷 업서트(원하면 diff→events 자동 생성)

### 2) `/ingest/events` — Request Contract (요약)

* Header: `Content-Type: application/json` 권장 ([Airtable Support][4])
* DateTime: **ISO 8601** 강제 ([Airtable][1])
* Airtable 자동화 Webhook로 바로 붙일 경우:

  * payload top-level은 **object여야 함**(array 불가) ([Airtable Support][4])
  * payload size limit **100kb**, trigger rate limit **5 req/sec**, **signature verification 미지원** ([Airtable Support][4])

**Request (example)**

```json
{
  "batchId": "2025-12-24_EDAS_0600",
  "sourceSystem": "RPA",
  "timezone": "Asia/Dubai",
  "receivedAt": "2025-12-24T06:00:05+04:00",
  "events": [
    {
      "eventKey": "sha256:...deterministic...",
      "timestamp": "2025-12-24T09:00:00+04:00",
      "shptNo": "SCT-0143",
      "entityType": "APPROVAL",
      "entityRef": { "approvalType": "FANR" },
      "fromStatus": "SUBMITTED",
      "toStatus": "PENDING",
      "bottleneckCode": "FANR_PENDING",
      "riskLevel": "HIGH",
      "actor": "Customs/Compliance",
      "owner": "Customs/Compliance",
      "dueAt": "2025-12-25T12:00:00+04:00",
      "evidenceIds": ["EV-0002"],
      "rawPayload": { "fanr": "pending", "portalRef": "..." }
    }
  ]
}
```

### 3) Idempotency(중복 방지) — v1 고정 규칙

* `eventKey`는 필수(권장: deterministic hash)

  * 예: `SHA256(shptNo|timestamp|entityType|docType/approvalType|toStatus|sourceSystem)`
* 서버(Flask)에서 `eventKey`를 Events에 unique로 관리 → 재전송/중복 수신 시 **NOOP** 처리

---

## Options (3안: 어떤 방식으로 Airtable에 쓰는지)

1. **Flask가 Airtable Web API 직접 Write (Upsert/Batch)**

   * Pros: 통제/감사/규칙엔진 일원화, 운영형 확장 용이
   * Cons: Airtable API rate limit 고려 필수(5 rps/base), 배치 최대 10 rec/request ([Airtable][2])
   * Fit: B안(원장+Ingest) 정석

2. **Airtable Automations(When webhook received)로 직접 적재**

   * Pros: 서버 없이도 트리거 연결 쉬움 ([Airtable Support][4])
   * Cons: 100kb/5rps/서명검증 미지원(보안·대량적재 한계) ([Airtable Support][4])
   * Fit: 소량 이벤트/파일럿

3. **스냅샷(daily-report)만 업서트 + 서버에서 diff 생성**

   * Pros: 엑셀 리포트 기반 “빠른 스타트”
   * Cons: 이벤트 타임라인 정밀도가 떨어질 수 있음(원천 이벤트 부족)
   * Fit: A안→B안 전환 구간

---

## Steps (P→Pi→B→O→S + KPI)

* **P(Definition)**: Enum/병목코드/Owner 표준 확정, `eventKey` 규칙 확정

  * KPI: status 정확도 ≥ 98.00%(가정), data lag ≤ 240.00min(가정)
* **Pi(Pilot)**: `/document/status`, `/approval/status`, `/actions/today` 먼저 고정

  * KPI: daily meeting prep -25.00%(가정)
* **B(Build)**: `/ingest/events` 운영 투입 + Events append-only 정착
* **O(Operate)**: KPI Summary(Top bottleneck/Aging/SLA breach) 자동화
* **S(Scale)**: CostGuard/WH Forecast/Heat-Stow 연동(추가 테이블 확장)

---

## QA / MISSING (바로 확정하면 v1.1로 잠금 가능)

* ApprovalType 전체 리스트(FANR 외 MOEI/MOIAT/MOI 범위)
* DocType 운영 범위(BOE/DO/COO/HBL/CIPL 외 추가)
* SLA 기준(slaHours, D-15/D-5 계산 규칙)
* STOP 게이트 수치(ocrPrecision/mismatchRate/rateOverrun 임계)와 산출 책임(어느 소스가 authoritative인지)

---

## CmdRec

* `/switch_mode LATTICE /logi-master --deep report`
* `/switch_mode ORACLE /logi-master predict`
* `/switch_mode COST-GUARD /logi-master kpi-dash`

---

## 전달 파일

* [HVDC_Airtable_Flask_SpecPack_2025-12-24.zip](sandbox:/mnt/data/HVDC_Airtable_Flask_SpecPack_2025-12-24.zip)

  * `40_SPEC__Airtable_to_Flask_Mapping__v1.0__2025-12-24.md`
  * `41_SPEC__Ingest_EventSchema__v1.0__2025-12-24.json`
  * `42_SPEC__Ingest_DailyReportSchema__v1.0__2025-12-24.json`

원하시면 다음으로, **Airtable API 호출 설계(필터/페이지/배치/업서트)까지** “구현 스펙”으로 내려서 드리겠습니다. (예: `filterByFormula`로 shptNo 조회, paging(최대 100/페이지), 배치(10/req) 운영 규칙) ([Airtable Support][5])

[1]: https://www.airtable.com/developers/scripting/api/cell_values?utm_source=chatgpt.com "Cell values & field options"
[2]: https://www.airtable.com/developers/web/api/rate-limits?utm_source=chatgpt.com "Rate limits - Airtable Web API"
[3]: https://support.airtable.com/docs/getting-started-with-airtables-web-api "Getting started with Airtable's Web API | Airtable Support"
[4]: https://support.airtable.com/docs/when-webhook-received-trigger "Airtable automation trigger: When webhook received"
[5]: https://support.airtable.com/docs/airtable-web-api-using-filterbyformula-or-sort-parameters "Airtable Web API - Using filterByFormula or sort parameters"
