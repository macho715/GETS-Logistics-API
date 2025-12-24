아래는 **Airtable Web API 호출(필터/페이지/배치/업서트)** 을 Flask(또는 Ingest Worker)에서 “운영형”으로 쓰기 위한 **구현 스펙(고정값/규칙/예시)** 입니다.
(Incoterm/HS는 `Shipments`에 고정 필드로 두고, `filterByFormula`/Upsert 키로는 **SHPT NO 기반**을 유지하는 구성이 가장 안정적입니다.)

[Download: HVDC_Airtable_API_ImplSpecPack_2025-12-24.zip](sandbox:/mnt/data/HVDC_Airtable_API_ImplSpecPack_2025-12-24.zip)

---

## 1) Exec (3–5L + Incoterm/HS)

* Airtable는 **Status Ledger(원장)** 로 두고, Flask는 **Status/KPI Engine(규칙 계산)** 로 분리하면 운영 확장(봇/대시보드/감사)이 쉽습니다.
* API 호출은 **(1) List+offset paging**, **(2) filterByFormula**, **(3) batch(≤10.00 rec/req)**, **(4) performUpsert(fieldsToMergeOn)** 를 표준으로 고정합니다. ([Airtable Support][1])
* 레이트리밋은 **5.00 req/s per base**, PAT 트래픽은 **50.00 req/s**, 초과 시 **HTTP 429 + 30.00s 대기**가 하드룰입니다. ([Airtable Support][2])
* `Shipments`에 **Incoterm / HS(예: hs2, hs6)** 를 넣고, 문서·승인 병목은 `Documents/Approvals`로 분리 Upsert하면 **DEM/DET·berth·gate 의사결정**에 바로 연결됩니다.

---

## 2) Visual (API Call Recipes 표)

| Use-case               | Method | Path                           | Key params/body                                                           | Hard limits / Notes                                                                               |
| ---------------------- | -----: | ------------------------------ | ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| List records (paged)   |    GET | `/v0/{baseId}/{tableIdOrName}` | `pageSize=100`, `offset=<cursor>`                                         | `pageSize` **최대 100.00**, 응답에 `offset` 있으면 다음 페이지 반복 ([Airtable Support][1])                      |
| Find by SHPT NO        |    GET | same                           | `filterByFormula={shptNo}='SCT-0143'`                                     | `filterByFormula`는 **필드명만** 사용(필드ID 불가), 값은 URL-encode 권장 ([Airtable Support][3])                 |
| Sort                   |    GET | same                           | `sort[0][field]=ETA&sort[0][direction]=desc`                              | `view`와 함께 쓰면 sort가 view 정렬을 override ([Airtable Support][3])                                     |
| Batch create           |   POST | same                           | `{ records:[{fields:{...}},...], typecast:true }`                         | **≤10.00 records/req** ([Airtable Support][2])                                                    |
| Batch update           |  PATCH | same                           | `{ records:[{id:"rec..", fields:{...}}], typecast:true }`                 | PATCH는 **부분 업데이트**, PUT는 **파괴적 업데이트**(미포함 필드 clear) ([Airtable][4])                               |
| Batch upsert (권장)      |  PATCH | same                           | `{ performUpsert:{fieldsToMergeOn:[...]} , records:[{fields:{...}}...] }` | `fieldsToMergeOn`로 매칭하여 **0=Create / 1=Update / 다중매칭=Fail** (merge field는 유니크 전제) ([Airtable][4]) |
| cellFormat string 사용 시 |    GET | List/Get                       | `cellFormat=string&timeZone=...&userLocale=...`                           | string cellFormat이면 timeZone/userLocale **필수**, 문자열 포맷에 의존하지 말 것 ([Airtable][5])                  |

추가 운영 주의:

* List 응답은 **빈 값 필드가 아예 누락**될 수 있으니, Consumer에서 null/empty default 처리 필요 ([Airtable Support][1])
* Airtable 날짜는 **GMT 저장** + 표시 타임존 설정 개념이므로, ops는 ISO-8601(+04:00)로 쓰되 필요 시 UTC도 병행 권장 ([Airtable Support][6])

---

## 3) 3-Options (pro / con / $ / risk / time)

| Option                           | What                                    | Pros                            | Cons                  | $/Risk/Time                                            |
| -------------------------------- | --------------------------------------- | ------------------------------- | --------------------- | ------------------------------------------------------ |
| A. “List+filterByFormula” 중심(단순) | Upsert 없이 `search→create/update`        | 구현이 직관적                         | 호출 수 증가(429 리스크↑)     | $: Low / Risk: Med / Time: Fast                        |
| B. **performUpsert 표준화(권장)**     | PATCH + `performUpsert.fieldsToMergeOn` | **Idempotent ingest**, 호출 수 최소화 | merge field 유니크 관리 필요 | $: Low / Risk: Low / Time: Fast                        |
| C. CSV 대량이면 Sync API 고려          | CSV Sync로 10,000.00 rows/req            | 대량 Ingest 최적                    | 운영/권한/흐름 설계 필요        | $: Med / Risk: Med / Time: Med ([Airtable Support][2]) |

---

## 4) Steps (P→Pi→B→O→S + KPI)

### P (Prepare)

* 테이블별 **Upsert 키 필드(유니크)** 고정

  * `Shipments`: `shptNo`
  * `Documents`: `docKey = shptNo|docType`
  * `Approvals`: `approvalKey = shptNo|approvalType`
  * `Events`: `eventKey`(리플레이 dedupe용)
* URL Path는 **tableId 사용**(rename 영향 최소) ([Airtable][5])

### Pi (Pilot)

* Read: `pageSize=100` + `offset` 루프 템플릿 고정 ([Airtable Support][1])
* Filter: `filterByFormula`는 **필드명만** + URL encode ([Airtable Support][3])
* KPI: 429 발생 0.00건(목표), ingest 1회당 API call 수(Down)

### B (Build)

* Write는 무조건 **batch(≤10.00)** + **typecast=true**(셀렉트 옵션 에러 방지) ([Airtable Support][2])
* Upsert는 표준으로 **performUpsert(fieldsToMergeOn)** 적용 ([Airtable][4])

### O (Operate)

* Rate-limit gate: **5.00 req/s per base** 유지, 429면 **30.00s 대기 후 재시도** ([Airtable Support][2])
* 관측: `429_count`, `retry_count`, `batch_size_avg`, `ingest_latency` 로그

### S (Scale)

* `view` 기반 필터링 + `sort`로 운영회의용 “Open/AtRisk” 뷰를 API에서 그대로 재사용 ([Airtable Support][3])

---

## 5) Data / Sim / BI-Viz (운영 KPI로 바로 쓰는 필드)

* `Documents`: `status`, `updatedAt`, `bottleneckCode`, `agingHours`(계산), `evidenceId`
* `Approvals`: `status`, `dueAt`, `D_minus`(계산), `owner`
* `Shipments`: `ETA`, `site`, `vendor`, **`incoterm`**, **`hs2/hs6`**, `demDetRiskFlag`(계산)

이렇게 두면 **berth/gate/DEM-DET** “오늘 액션”이 `filterByFormula`+`sort`로 바로 뽑힙니다.

---

## 6) Auto (RPA + LLM + Sheets)

* RPA(eDAS/Customs portal) → `Events` append (eventKey로 dedupe) → Status Engine이 `Documents/Approvals`를 Upsert
* LLM은 **요약/분류/액션 문장**만(사실 기입 금지) + EvidenceId 없으면 write 금지(게이트)

---

## 7) QA / Gap / Recheck (하드 체크)

* `fieldsToMergeOn`로 쓰는 필드는 **유니크 보장**(중복 있으면 Upsert 요청 실패 가능) ([Airtable][4])
* `filterByFormula`는 **필드명만**(필드ID 불가) → 필드 rename 시 영향(운영 변경관리 필요) ([Airtable Support][3])
* List 응답에서 **빈 필드 누락**은 정상 → Consumer default 처리 ([Airtable Support][1])

---

## 8) Acc (data-only) + 가정

* **가정:** 현재 인증은 PAT(Bearer) 기반이며, Flask(또는 Worker)가 Airtable를 직접 호출합니다.
* 본 답변의 수치/제한(5.00 req/s, 50.00 req/s, 10.00 rec/req, 30.00s cooldown, pageSize 100.00)은 Airtable Support 문서 기준입니다. ([Airtable Support][2])

---

## 9) CmdRec (Slash 1–3)

* `/logi-master --deep report` : “Airtable API CallDesign + UpsertKey + RateLimitGate” 스펙 출력
* `/switch_mode LATTICE|COST-GUARD` : Evidence/정합/비용감사 필드까지 포함한 스키마로 확장
* `/redo step upsert` : `performUpsert(fieldsToMergeOn)` 적용 범위 재산정(테이블별)

---

### 첨부팩 구성

다운로드 ZIP에 포함:

* `43_IMPL__Airtable_API_CallDesign__v1.0__2025-12-24.md` (콜 설계 문서)
* `44_CODE__python_airtable_client__v1.0__2025-12-24.py` (paging+batch upsert 샘플)
* `45_POSTMAN__HVDC_Airtable_API_Recipes__v1.0.postman_collection.json` (즉시 테스트)

[Download: HVDC_Airtable_API_ImplSpecPack_2025-12-24.zip](sandbox:/mnt/data/HVDC_Airtable_API_ImplSpecPack_2025-12-24.zip)

원하시면 다음 턴에서 **(Airtable 필드 ↔ Flask JSON 1:1 매핑표)** 를 “실제 테이블ID/필드명 기준”으로 고정해서, `/document/status/<shptNo>` 응답과 Airtable 레코드 구조가 완전히 맞물리게 정리하겠습니다.

[1]: https://support.airtable.com/docs/getting-started-with-airtables-web-api "Getting started with Airtable's Web API | Airtable Support"
[2]: https://support.airtable.com/docs/managing-api-call-limits-in-airtable "Managing API Call Limits in Airtable"
[3]: https://support.airtable.com/docs/airtable-web-api-using-filterbyformula-or-sort-parameters "Airtable Web API - Using filterByFormula or sort parameters"
[4]: https://www.airtable.com/developers/web/api/update-multiple-records?utm_source=chatgpt.com "Update multiple records - Web API ..."
[5]: https://www.airtable.com/developers/web/api/list-records?utm_source=chatgpt.com "List records - Airtable Web API"
[6]: https://support.airtable.com/docs/timezones-and-locales "Timezones and Locales In Airtable | Airtable Support"
