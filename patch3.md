## Exec (고정안: “실제 tableId + 실제 fieldName”로 Lock → `/document/status/<shptNo>` 완전 정합)

* 현재 대화 환경에서는 **귀하 Airtable Base에 직접 접근할 수 없어서** `tbl…/fld…` 같은 **실제 ID 값을 제가 여기서 채울 수는 없습니다.**
* 대신, Airtable 공식 **Get base schema(Meta) API**로 스키마를 1회 덤프하면, **실제 tableId/fieldId + fieldName** 기준으로 매핑표를 자동 생성해 **SSOT로 고정(lock)** 할 수 있습니다. ([Airtable][1])
* 운영 규칙은 다음 3개를 하드 고정합니다:

  1. REST Path는 **tableId 사용(renaming 안전)** ([Airtable][2])
  2. 조회는 `filterByFormula`로 하되 **fieldName만 사용 가능(=rename 금지 필드 존재)** ([Airtable Support][3])
  3. 호출량은 **5.00 req/s per base / 50.00 req/s per PAT** + 429면 **30.00s 대기** ([Airtable Support][4])

---

## 최소 동작(3-Step)으로 “실제 ID/필드명 기반 매핑표” 생성

### Step 0) Base ID 확보 (app…)

* Airtable에서 base 열기 → Help에서 API 문서로 들어가면 **Base ID(app…)** 확인 가능. ([Airtable Support][5])

### Step 1) 스키마 잠금 + 매핑 자동 생성 (제가 파일로 만들어 둠)

아래 ZIP을 내려받아 실행하면, **실제 tableId/fieldId/name**이 박힌 파일이 자동으로 생성됩니다.

[Download: HVDC_Airtable_LockAndMappingGenPack_2025-12-24.zip](sandbox:/mnt/data/HVDC_Airtable_LockAndMappingGenPack_2025-12-24.zip)

### Step 2) 실행 커맨드

```bash
pip install -r requirements.txt
export AIRTABLE_TOKEN="pat_xxx"
export AIRTABLE_BASE_ID="app_xxx"
python lock_schema_and_generate_mapping.py
```

**생성 결과물(자동)**

* `out/airtable_schema.lock.json` : 테이블/필드 **실제 ID + 이름 + 타입** 고정
* `out/document_status_mapping.locked.md` : `/document/status/<shptNo>` 기준 **JSON path ↔ tableId.fieldName[fieldId]** 1:1 매핑표
* `out/schema_summary.csv` : 전체 스키마(테이블/필드) 덤프

---

## Visual: `/document/status/<shptNo>` Locked Mapping 포맷(생성되는 표의 형태)

| JSON Path         | Airtable Ref(locked)                                              | 조회 방식                                                            |
| ----------------- | ----------------------------------------------------------------- | ---------------------------------------------------------------- |
| `shptNo`          | `Shipments (tblXXXX) . shptNo (fldXXXX)`                          | Shipments에서 `filterByFormula={shptNo}='SCT-0143'`                |
| `doc.boeStatus`   | `Documents (tblYYYY) . status (fldYYYY)` + selector `docType=BOE` | Documents에서 `filterByFormula={shptNo}='SCT-0143'` 후 docType별 map |
| `bottleneck.code` | `Shipments (tblXXXX) . currentBottleneckCode (fldXXXX)`           | Shipment 단일 레코드                                                  |
| `action.dueAt`    | `Shipments (tblXXXX) . dueAt (fldXXXX)` (또는 Actions에서 OPEN 1st)   | Actions를 쓰면 `AND({shptNo}='SCT-0143',{status}!='DONE')`          |

핵심 주의:

* `filterByFormula`는 **fieldId 사용 불가, fieldName만 가능** → `shptNo/docType/status` 등은 rename 금지 필드로 지정하는 게 운영적으로 안전합니다. Airtable도 동일 취지로 안내합니다. ([Airtable Support][3])

---

## 구현 스펙(Flask) — 실제 tableId 기반 조회/조립 규칙

### 1) 스키마/매핑의 “SSOT 잠금” 원칙

* 서버 시작 시(또는 daily job) `airtable_schema.lock.json` 로드
* API 호출 시:

  * URL path: `/v0/{baseId}/{tableId}` (tableId 사용 권장) ([Airtable][2])
  * 조회 formula: `{필드명}` (필드명 기반) ([Airtable Support][3])

### 2) `/document/status/<shptNo>` 조립 시 최소 호출

* Shipments 1 call (maxRecords=1)
* Documents 1 call (shptNo 기준 전체)
* Actions 1 call (open only) — 선택
* Evidence detail까지 붙이면 calls 증가 → v1은 `evidenceIds[]`만 반환하고, 상세는 별도 endpoint 권장

### 3) Pagination 고정

* List Records는 **페이지 단위**로 반환되고, 다음 페이지가 있으면 `offset`이 내려옴 ([Airtable][2])
* `pageSize`는 **최대 100.00** 기준(기본 100.00)으로 루프

---

## Options (3안: “완전 정합” 달성 경로)

1. **A안: fieldName 고정 + tableId 사용(지금 제공팩 방식)**

* Pros: 구현 최소, 즉시 운영
* Cons: `filterByFormula` 때문에 몇 개 필드명 rename 위험 존재 ([Airtable Support][3])
* Time: Fast

2. **B안: shptNo를 Child table에 “중복 저장”하여 조회 단순화(권장)**

* Pros: 링크드레코드 필터 복잡도 제거, 호출/수식 단순
* Cons: denormalization(하지만 운영 API에는 유리)
* Time: Fast

3. **C안: View 기반으로 “API용 고정 View”를 만들어 필드명 변경 리스크 완화**

* Pros: 운영자 UI에서 조건 변경 쉬움(필터/정렬)
* Cons: view 자체도 변경관리 필요(권한 통제 필요)
* Time: Medium

---

## QA / Hard gate (자동 중단 조건)

제가 제공한 `lock_schema_and_generate_mapping.py`는 아래면 **즉시 종료(code=3)** 하도록 만들어 두었습니다.

* 테이블 누락(예: Documents 테이블명 불일치)
* 필수 필드 누락(예: Documents.shptNo/docType/status 없음)

이 방식이 “HallucinationBan(근거 없는 연결 금지)”에 가장 잘 맞습니다.

---

## MISSING (제가 실제 tbl/fld를 채울 수 없는 이유)

* **MISSING: AIRTABLE_BASE_ID(app…)**
* **MISSING: AIRTABLE_TOKEN(pat…)**
* **MISSING: 귀하 베이스의 실제 테이블명/필드명(스키마)**

위 3개는 보안/권한 영역이라 제가 직접 조회할 수 없습니다. 대신 Meta API로 **스키마를 귀하 환경에서 1회 덤프**하면 즉시 해결됩니다. ([Airtable][1])

---

## CmdRec

* `/switch_mode LATTICE /logi-master --deep report`
* `/redo step mapping-lock`
* `/logi-master --KRsummary report`

원하시면, 다음 턴에서 **귀하가 생성한 `out/airtable_schema.lock.json` 일부(테이블/필드명만, 토큰/개인정보 제거)** 를 붙여주시면, 제가 그 내용을 기준으로 `/document/status/<shptNo>` **최종 JSON Contract(필드/디폴트/우선순위/증빙 join 규칙)** 까지 “완전 고정 버전(v1.1)”으로 내려드리겠습니다.

[1]: https://www.airtable.com/developers/web/api/get-base-schema?utm_source=chatgpt.com "Get base schema - Airtable Web API"
[2]: https://www.airtable.com/developers/web/api/list-records?utm_source=chatgpt.com "List records - Airtable Web API"
[3]: https://support.airtable.com/docs/airtable-web-api-using-filterbyformula-or-sort-parameters "Airtable Web API - Using filterByFormula or sort parameters"
[4]: https://support.airtable.com/docs/managing-api-call-limits-in-airtable "Managing API Call Limits in Airtable"
[5]: https://support.airtable.com/docs/finding-airtable-ids "Finding Airtable IDs | Airtable Support "
