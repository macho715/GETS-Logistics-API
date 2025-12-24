# HVDC_Airtable_LockAndMappingGenPack_2025-12-24

목적:
- Airtable **실제 tableId / fieldName(및 fieldId)** 기반으로 스키마를 잠그고(lock),
- Flask의 `/document/status/<shptNo>` 응답(JSON)과 Airtable 레코드 구조가 **1:1로 맞물리도록** mapping을 자동 생성합니다.

## 최소 실행(3 step)
### 0) 준비
- Python 3.10+
- `pip install -r requirements.txt`

### 1) 환경변수 세팅
- Windows(PowerShell):
  - `$env:AIRTABLE_TOKEN="pat_xxx"`
  - `$env:AIRTABLE_BASE_ID="app_xxx"`
- macOS/Linux:
  - `export AIRTABLE_TOKEN="pat_xxx"`
  - `export AIRTABLE_BASE_ID="app_xxx"`

### 2) 스키마 잠금 + 매핑 생성
- `python lock_schema_and_generate_mapping.py`

출력:
- `out/airtable_schema.lock.json`  (tableId/fieldId/name/type 포함)
- `out/document_status_mapping.locked.md` (JSON path ↔ tableId/fieldName/fieldId 매핑표)
- `out/schema_summary.csv` (선택)

### 3) 샘플로 `/document/status/<shptNo>` 조립 테스트(선택)
- `python build_document_status_packet.py SCT-0143`
- 출력: `out/status_packet_SCT-0143.json`

## 전제(권장)
- Child tables(Documents/Approvals/Actions/Events)에 **shptNo 텍스트 필드**가 존재해야, `filterByFormula`로 단순 조회가 됩니다.
- `filterByFormula`는 **field ID를 쓸 수 없고 field name만** 사용 가능하므로, 아래 필드명은 rename 금지 권장:
  - Shipments: shptNo
  - Documents: shptNo, docType, status
  - Actions: shptNo, status, dueAt, priority
  - Evidence: evidenceId
