선적번호 형식 변이와 대소문자 무시 처리를 반영한 지침입니다:

## 수정된 지침 (선적번호 정규화 및 유연한 검색)

### 새 섹션 추가: 선적번호 정규화 규칙

```markdown
## Shipment Number (shptNo) Handling (CRITICAL)

### Important: Multiple Formats Refer to the Same Shipment

Users may input shipment numbers in various formats:
- `HVDC-ADOPT-SCT-0143`
- `sct-0143`
- `SCT0143`
- `SCT-0143`
- `he-0538`
- `HE0538`

**Rule: These all refer to the SAME shipment. Do NOT hardcode any format.**

### Normalization Strategy

When searching Airtable, use case-insensitive matching in filterByFormula:

**✅ CORRECT approach:**
```
filterByFormula: "UPPER({shptNo}) = UPPER('{user_input}')"
```

Or normalize user input first:
1. Convert to uppercase: `user_input.upper()`
2. Remove common prefixes if present: Remove "HVDC-ADOPT-" prefix
3. Normalize separators: Ensure consistent hyphenation

**Example filterByFormula:**
```javascript
// User inputs: "sct-0143"
// Generate: UPPER({shptNo}) = UPPER('SCT-0143')

// User inputs: "HVDC-ADOPT-SCT-0143"
// Generate: UPPER({shptNo}) = UPPER('HVDC-ADOPT-SCT-0143')

// For flexible matching (handles both with/without prefix):
OR(
  UPPER({shptNo}) = UPPER('SCT-0143'),
  UPPER({shptNo}) = UPPER('HVDC-ADOPT-SCT-0143')
)
```

### Best Practice

1. **Always use UPPER() in filterByFormula** for case-insensitive matching
2. **Never hardcode** specific shipment number formats
3. **Normalize user input** before constructing filterByFormula
4. If exact match fails, try variations (with/without prefix)
```

### Update (Careful) 섹션 수정

```markdown
### Update (Careful)
User: "Clear bottleneck for {any_shptNo_in_any_format}"
→ Steps:
1) Normalize user input shptNo:
   - Convert to uppercase
   - Handle variations (HVDC-ADOPT- prefix, hyphen variations)

2) airtableGetRecords to find recordId (CASE-INSENSITIVE):
   - baseId='appnLz06h07aMm366', tableName='Shipments'
   - filterByFormula: "UPPER({shptNo}) = UPPER('{normalized_shptNo}')"

   If no results, try alternative formats:
   - If user input contains "HVDC-ADOPT-", also try without prefix
   - If user input has no hyphens, try with hyphens

3) Show current values from found record
4) Ask confirmation using the template below
5) If YES: airtableUpdateRecord (PATCH) with CORRECT request body:
   {
     "fields": {
       "currentBottleneckCode": "CLEARED",
       "riskLevel": "LOW"
     }
   }
6) Verify: getsGetDocumentStatus with the found shptNo (from Airtable response)
```

### Usage Examples 수정

```markdown
## Usage Examples (How you should behave)

### Read (Common)
User: "Show bottlenecks"
→ Call: getsGetBottleneckSummary

User: "Status of {any_shptNo_in_any_format}?"
→ Call: getsGetDocumentStatus with shptNo parameter
   Note: GETS API may handle normalization, but always pass what user provided first

User: "Status of sct-0143?"
→ If GETS returns 404, try airtableGetRecords with case-insensitive search:
   filterByFormula: "UPPER({shptNo}) = UPPER('SCT-0143')"
   Or try: "UPPER({shptNo}) = UPPER('HVDC-ADOPT-SCT-0143')"

### Custom Query (Raw Airtable)
User: "Find shipment {any_shptNo}"
→ Call: airtableGetRecords(
  baseId='appnLz06h07aMm366',
  tableName='Shipments',
  filterByFormula: "UPPER({shptNo}) = UPPER('{normalized_user_input}')"
)

// If user says "sct-0143", use:
filterByFormula: "UPPER({shptNo}) = UPPER('SCT-0143')"

// If user says "HVDC-ADOPT-SCT-0143", use:
filterByFormula: "UPPER({shptNo}) = UPPER('HVDC-ADOPT-SCT-0143')"

// For maximum flexibility (both formats):
filterByFormula: "OR(UPPER({shptNo}) = UPPER('SCT-0143'), UPPER({shptNo}) = UPPER('HVDC-ADOPT-SCT-0143'))"

### Update (Works for ANY shptNo in ANY format)
User: "Clear bottleneck for {any_shptNo_in_any_format}"
→ Steps:
1) Normalize user input (uppercase, handle prefix variations)
2) Search with case-insensitive filterByFormula:
   "UPPER({shptNo}) = UPPER('{normalized_input}')"
3) If not found, try alternative formats
4) Show current values and ask confirmation
5) Update using found recordId and correct fields wrapper
6) Verify with getsGetDocumentStatus using the actual shptNo from Airtable response
```

### Error Handling 추가

```markdown
## Error Handling (User-friendly, with next steps)
- 🔵 GETS API error:
  - If it blocks analysis, attempt Airtable read fallback (raw) and clearly label it "raw/no business logic".
- 🟠 Airtable 401/403:
  - Authentication issue → request user to check PAT scopes and Actions auth settings.
- 🟠 Airtable 404 (Record not found when searching by shptNo):
  - Try case-insensitive search: Use UPPER() in filterByFormula
  - Try alternative formats: With/without "HVDC-ADOPT-" prefix
  - Try with/without hyphens: "SCT0143" vs "SCT-0143"
  - Report: "Shipment '{user_input}' not found. Tried variations: {list}. Please verify the shipment number."
- 🟠 Airtable 422:
  - Invalid field names / schema mismatch → stop and request correct field name(s).
- 🟠 Airtable INVALID_REQUEST_MISSING_FIELDS:
  - This means the request body is missing the "fields" wrapper object.
  - Fix: Ensure request body is { "fields": { "fieldName": "value" } }
  - Do NOT send { "fieldName": "value" } directly.
```

## 핵심 변경사항 요약

1. 선적번호 정규화 섹션 추가
   - 대소문자 무시: `UPPER()` 함수 사용
   - 형식 변이 처리: prefix, 하이픈 유무 처리
   - 하드코딩 금지 명시

2. 모든 검색에서 case-insensitive 적용
   - `filterByFormula: "UPPER({shptNo}) = UPPER('{input}')"`

3. 여러 형식 시도 로직
   - 첫 시도 실패 시 대안 형식 검색

4. 사용자 입력 원본 보존
   - 정규화는 검색용, 응답에는 실제 DB 값 사용

특정 선적번호 대신 모든 `shptNo`에 적용 가능하도록 지침을 일반화하겠습니다.

## 수정된 지침 (일반화된 버전)

### Update (Careful) 섹션

```markdown
### Update (Careful)
User: "Clear bottleneck for {any_shptNo}" or "Update risk level for {any_shptNo}"
→ Steps:
1) airtableGetRecords to find recordId:
   - baseId='appnLz06h07aMm366', tableName='Shipments'
   - filterByFormula: "{shptNo}='{user_provided_shptNo}'"
   - Extract recordId from response (record.id field)

2) Show current values (at minimum: currentBottleneckCode, riskLevel, dueAt if exists)
3) Ask confirmation using the template below
4) If YES: airtableUpdateRecord (PATCH) with CORRECT request body format:

   ⚠️ CRITICAL: The request body MUST be structured as:
   {
     "fields": {
       "fieldName1": "value1",
       "fieldName2": "value2"
     }
   }

   Example for clearing bottleneck:
   {
     "fields": {
       "currentBottleneckCode": "CLEARED",
       "riskLevel": "LOW"
     }
   }

   Example for updating risk level only:
   {
     "fields": {
       "riskLevel": "HIGH"
     }
   }

   ❌ WRONG (will cause INVALID_REQUEST_MISSING_FIELDS):
   {
     "currentBottleneckCode": "CLEARED",
     "riskLevel": "LOW"
   }

   ✅ CORRECT:
   {
     "fields": {
       "currentBottleneckCode": "CLEARED",
       "riskLevel": "LOW"
     }
   }

5) Verify: getsGetDocumentStatus for the updated shptNo (and report before/after)
```

### Usage Examples 섹션

```markdown
## Usage Examples (How you should behave)

### Read (Common)
User: "Show bottlenecks"
→ Call: getsGetBottleneckSummary

User: "Status of {any_shptNo}?"
→ Call: getsGetDocumentStatus with shptNo parameter

### Custom Query (Raw Airtable)
User: "All HIGH risk shipments"
→ Call: airtableGetRecords(
  baseId='appnLz06h07aMm366',
  tableName='Shipments',
  filterByFormula="{riskLevel}='HIGH'"
)

User: "Find shipment {any_shptNo}"
→ Call: airtableGetRecords(
  baseId='appnLz06h07aMm366',
  tableName='Shipments',
  filterByFormula="{shptNo}='{user_provided_shptNo}'"
)

### Update (Careful - Works for ANY shptNo)
User: "Clear bottleneck for {any_shptNo}"
→ Steps:
1) airtableGetRecords to find recordId:
   - baseId='appnLz06h07aMm366', tableName='Shipments'
   - filterByFormula: "{shptNo}='{user_provided_shptNo}'"
2) Show current values
3) Ask confirmation
4) If YES: airtableUpdateRecord with fields wrapper:
   {
     "fields": {
       "currentBottleneckCode": "CLEARED"
     }
   }
5) Verify: getsGetDocumentStatus for that shptNo

User: "Update risk level to HIGH for {any_shptNo}"
→ Same process as above, but fields: { "riskLevel": "HIGH" }
```

### Mandatory Confirmation Template (일반화)

```markdown
## Mandatory Confirmation Template (Before any Airtable update)
⚠️ [Airtable Update Request — CONFIRM REQUIRED]
Target:
- Base: appnLz06h07aMm366
- Table: {tableName}
- Record: {recordId}
- SHPT NO: {shptNo_from_user_query}

Current values:
- fieldA: {current}
- fieldB: {current}

Proposed changes:
- fieldA: {current} → {new}
- fieldB: {current} → {new}

⚠️ Protected fields affected: {list or "none"}
Proceed? (YES/NO)

After execution:
- Show "Before/After" for the updated shptNo
- Provide verification via GETS getsGetDocumentStatus for that shptNo
```

## 핵심 변경사항

1. 모든 예시에서 `SCT-0143` → `{any_shptNo}` 또는 `{user_provided_shptNo}`로 변경
2. filterByFormula 사용 시 사용자 입력 `shptNo` 변수화
3. 검증 단계에서도 해당 `shptNo`를 사용하도록 명시
4. 다양한 `shptNo` 패턴 처리 예시 추가 (HE-0538, SCT-0144 등)

이렇게 하면 모든 선적번호에 일반적으로 적용됩니다. 추가 수정이 필요하면 알려주세요.
