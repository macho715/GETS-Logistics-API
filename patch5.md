좋습니다. 업로드하신 `airtable_schema.lock.json` 기준으로 **“실제 tableId + 실제 fieldName/fieldId”** 를 박아 **`/document/status/<shptNo>` 응답(JSON) ↔ Airtable 레코드 구조**가 1:1로 맞물리도록 **Locked Mapping**을 확정했습니다.

아래 ZIP에는 **(1) Locked Mapping MD**, **(2) base/table/field ID 딕셔너리(JSON)**, **(3) Flask용 config(py)** 가 들어 있습니다.

[Download: HVDC_DocumentStatus_LockedMapping_2025-12-25.zip](sandbox:/mnt/data/HVDC_DocumentStatus_LockedMapping_2025-12-25.zip)

---

## 1) Exec (3–5L + Incoterm/HS)

* 이제부터 `/document/status/<shptNo>`는 **BaseId(app…) + TableId(tbl…)** 기준으로 고정되어, Airtable에서 **테이블명 변경(renaming)** 이 발생해도 API가 깨질 확률이 크게 줄어듭니다. (Airtable도 table ID 사용을 권장) ([Airtable][1])
* 단, `filterByFormula`는 **fieldId가 아니라 fieldName만 사용 가능**하므로(`shptNo/docType/status` 등) 해당 필드명은 **rename 금지(LOCK)** 로 운용해야 합니다. ([Airtable Support][2])
* 문서 상태는 `Documents`에서 `(shptNo + docType)`로 집계해 `doc.*Status`로 리턴하고, 병목/액션은 `Shipments`의 필드(또는 Actions override)로 운영 패킷을 완성합니다.
* Phase 2.3에서 `Shipments`에 **Incoterm/HS(HS2/HS6)** 를 추가하면, BOE RED/검사리스크/DEM·DET(berth free time) 알림을 “규칙 엔진”으로 확장하기 좋습니다. (**가정:** 현행 스키마에는 incoterm/hs 필드 없음)

---

## 2) Visual — Locked Mapping (실제 tableId/fieldId 확정)

### 2.1 Base / Table IDs (SSOT)

* BaseId: `appnLz06h07aMm366`
* Shipments: `tbl4NnKYx1ECKmaaC`
* Documents: `tblbA8htgQSd2lOPO`
* Actions(옵션): `tblkDpCWYORAPqxhw`

### 2.2 `/document/status/<shptNo>` JSON ↔ Airtable 1:1 매핑표

| JSON Path              | Airtable Ref (tableId.fieldName[fieldId])                                                                    | Type           | Rule                         |
| ---------------------- | ------------------------------------------------------------------------------------------------------------ | -------------- | ---------------------------- |
| `shptNo`               | Shipments `tbl4NnKYx1ECKmaaC`. `shptNo`[`fldEQ5GwNfN6dRWnI`]                                                 | singleLineText | direct                       |
| `doc.boeStatus`        | Documents `tblbA8htgQSd2lOPO`. `status`[`fld8HQ6WJA5DstrNK`] + selector `docType`[`fldgN8FmlkC47Yqyf`]=`BOE` | singleSelect   | if none → `UNKNOWN`          |
| `doc.doStatus`         | (동일) selector docType=`DO`                                                                                   | singleSelect   | if none → `UNKNOWN`          |
| `doc.cooStatus`        | (동일) selector docType=`COO`                                                                                  | singleSelect   | if none → `UNKNOWN`          |
| `doc.hblStatus`        | (동일) selector docType=`HBL`                                                                                  | singleSelect   | if none → `UNKNOWN`          |
| `doc.ciplStatus`       | (동일) selector docType=`CIPL`                                                                                 | singleSelect   | if none → `UNKNOWN`          |
| `bottleneck.code`      | Shipments. `currentBottleneckCode`[`fldIACEWXLqsorJF0`]                                                      | singleLineText | direct                       |
| `bottleneck.since`     | Shipments. `bottleneckSince`[`fldTLT6AMTi8udXrB`]                                                            | dateTime       | direct                       |
| `bottleneck.riskLevel` | Shipments. `riskLevel`[`fldkbfmbgNi4iFJDk`]                                                                  | singleSelect   | direct                       |
| `action.nextAction`    | Shipments. `nextAction`[`fldkR6PTLDfvwnJN4`]                                                                 | singleLineText | direct (or Actions override) |
| `action.owner`         | Shipments. `actionOwner`[`fldKuqW5THvGbsSzu`]                                                                | singleLineText | direct (or Actions override) |
| `action.dueAt`         | Shipments. `dueAt`[`fldF1TqRtlxwevnVI`]                                                                      | dateTime       | direct (or Actions override) |

근거: 위 tableId/fieldId는 업로드하신 Lock 파일에서 추출한 “실제값”입니다.

---

## 3) Airtable API 조회 구현 스펙 (완전 고정)

### 3.1 공통 규칙 (필수)

* **REST Path는 tableId 사용**: table name 변경에 안전 ([Airtable][1])
* **List pagination**: `pageSize` 최대 **100.00**, 다음 페이지는 `offset` 반복 ([Airtable][3])
* **filterByFormula는 fieldName만**: fieldId 사용 불가 → rename 금지 목록 지정 ([Airtable Support][2])
* **Rate limit**: base당 **5.00 req/s**, PAT 트래픽 **50.00 req/s**, 초과 시 429 및 재시도 전략 필요 ([Airtable][4])

### 3.2 실제 호출 템플릿 (Locked)

#### Q1) Shipments 1건 조회 (0..1)

```http
GET https://api.airtable.com/v0/appnLz06h07aMm366/tbl4NnKYx1ECKmaaC
  ?maxRecords=1
  &filterByFormula={shptNo}='SCT-0143'
  &fields[]=shptNo
  &fields[]=currentBottleneckCode
  &fields[]=bottleneckSince
  &fields[]=riskLevel
  &fields[]=nextAction
  &fields[]=actionOwner
  &fields[]=dueAt
Authorization: Bearer <PAT>
```

* List Records 동작/offset/pageSize 규칙은 Airtable 공식 문서 기준입니다. ([Airtable][3])

#### Q2) Documents 전체 조회 (0..N) → docType별 status 매핑

```http
GET https://api.airtable.com/v0/appnLz06h07aMm366/tblbA8htgQSd2lOPO
  ?pageSize=100
  &filterByFormula={shptNo}='SCT-0143'
  &fields[]=shptNo
  &fields[]=docType
  &fields[]=status
Authorization: Bearer <PAT>
```

#### (옵션) Q3) Actions OPEN 1건으로 action.* override

```http
GET https://api.airtable.com/v0/appnLz06h07aMm366/tblkDpCWYORAPqxhw
  ?pageSize=100
  &filterByFormula=AND({shptNo}='SCT-0143',{status}!='DONE')
  &sort[0][field]=priority&sort[0][direction]=asc
  &sort[1][field]=dueAt&sort[1][direction]=asc
  &fields[]=actionText&fields[]=owner&fields[]=dueAt&fields[]=status&fields[]=priority
Authorization: Bearer <PAT>
```

---

## 4) Hard Gate (ZERO) — “완전 정합”을 위한 중단 조건

* **Shipments 0건**: `/document/status/<shptNo>`는 **404** (원장 키 없으면 패킷 생성 불가)
* **Documents에 동일 docType 중복**(같은 shptNo에서 BOE 2건 등):

  * 권장: `409 Conflict` 또는 `bottleneck.code='STOP_DATA_MISMATCH'`로 표기 (**가정:** 운영 게이트 적용 시)
* **429 Too Many Requests**: **30.00s backoff 후 재시도** (Airtable rate limit 정책) ([Airtable Support][5])

---

## 5) Gap / Recheck (중요)

업로드된 lock 기준으로 확인된 “현행 스키마 제약”입니다.

* **Evidence 링크 필드가 없음**: Documents/Approvals/Actions/Events에 evidence 연결 필드가 없어서 `/document/status`에서 evidence를 “정합하게” 붙일 수 없습니다.

  * 해결(선택): 각 테이블에 `evidenceIds`(multilineText) 또는 Evidence 링크드레코드 필드 추가(Phase 2.3)
* **Events에 eventKey 없음**: idempotency(중복방지)를 Events 단에서 하려면 `eventKey` 필드 추가가 필요합니다. (현재는 validator에서 eventKey를 invalid로 처리한 상태)

---

## 6) 제공 파일 구성

ZIP 내부:

* `document_status_mapping.locked.md` : 위 매핑을 문서로 고정
* `airtable_ids.locked.json` : base/table/field id 딕셔너리(코드 로딩용)
* `airtable_locked_config.py` : Flask에서 바로 import 가능한 상수 템플릿

[Download: HVDC_DocumentStatus_LockedMapping_2025-12-25.zip](sandbox:/mnt/data/HVDC_DocumentStatus_LockedMapping_2025-12-25.zip)

---

## CmdRec

* `/switch_mode LATTICE /logi-master --deep report` (정합/스키마 잠금 기준으로 리포트 고정)
* `/switch_mode ORACLE /logi-master predict` (D-15/D-5, SLA breach, BOE RED risk 확장)
* `/redo step mapping-lock` (lock 버전 갱신 시 재생성)

원하시면 다음으로, **현재 Vercel 배포본(v1.6.0)** 기준으로 `/document/status/<shptNo>`의 **OpenAPI 스키마**까지 “이 Lock 버전(2025-12-25T00:32:52+0400)”으로 고정해드리겠습니다. (schema drift 시 CI에서 즉시 FAIL하도록)

[1]: https://www.airtable.com/developers/web/api/update-record?utm_source=chatgpt.com "Update record - Airtable Web API"
[2]: https://support.airtable.com/docs/airtable-web-api-using-filterbyformula-or-sort-parameters?utm_source=chatgpt.com "Airtable Web API - Using filterByFormula or sort parameters"
[3]: https://www.airtable.com/developers/web/api/list-records?utm_source=chatgpt.com "List records - Airtable Web API"
[4]: https://www.airtable.com/developers/web/api/rate-limits?utm_source=chatgpt.com "Rate limits - Airtable Web API"
[5]: https://support.airtable.com/docs/managing-api-call-limits-in-airtable?utm_source=chatgpt.com "Managing API Call Limits in Airtable"
