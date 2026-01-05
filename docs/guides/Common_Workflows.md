# Common Workflow Patterns

## New Shipment Creation Workflow

**User**: "새로운 선적 {shptNo}를 추가해줘" (예: "SCT-0144", "HE-0512", "HVDC-ADOPT-HE-0512")

1. Check existence:
   - Use user input as-is: `airtableGetRecords(filterByFormula: "UPPER({shptNo}) = UPPER('{user_input_exact}')")`
   - If not found, try variations automatically (without prefix, without hyphens)
   - If found: "Shipment {actual_shptNo_from_airtable} already exists. Use update workflow instead?"
   - If NOT found: Proceed to step 2

2. Collect required information:
   - Required: shptNo (from user input, use as-is)
   - Optional: vendor, site, eta, riskLevel, currentBottleneckCode, etc.
   - If user didn't provide: Ask for minimum required fields (shptNo + vendor or site)

3. Show creation preview:
   ```
   ⚠️ [New Shipment Creation - CONFIRM]
   - Base: appnLz06h07aMm366
   - Table: Shipments
   - SHPT NO: {user_input_shptNo} (NEW)
   Fields to create:
   - shptNo: {user_input_shptNo}
   - vendor: {user_provided_or_default}
   - site: {user_provided_or_default}
   - riskLevel: MEDIUM (default)

   Protected fields: shptNo
   Proceed? (YES/NO)
   ```

4. If YES: Create record:
   - `airtableCreateRecord` with `{"records": [{"fields": {...}}], "typecast": true}`
   - Extract record ID from response

5. Verify creation:
   - Wait 1-2 seconds
   - Call: `getsGetDocumentStatus(shptNo='{user_input_shptNo}')` (use user input as-is)
   - Show: "✅ Shipment {actual_shptNo_from_airtable_response} created successfully. Record ID: rec..."

6. Subsequent updates:
   - Use normal update workflow (airtableUpdateRecord)
   - Use created record ID from step 4

## Single Record Update Workflow

**User**: "{shptNo}의 riskLevel을 HIGH로 변경" (예: "HE-0538", "he-0538", "HVDC-ADOPT-HE-0538")

1. Search: Use user input as-is: `airtableGetRecords(filterByFormula: "UPPER({shptNo}) = UPPER('{user_input_exact}')")`
2. If not found, try variations automatically
3. If found:
   - Extract actual shptNo from Airtable response
   - Show current: `riskLevel=LOW` (using actual shptNo from response)
   - Ask: "Change riskLevel from LOW to HIGH for {actual_shptNo}. Proceed? (YES/NO)"
   - If YES: `airtableUpdateRecord({ "fields": { "riskLevel": "HIGH" } })`
   - Verify: `getsGetDocumentStatus(shptNo='{actual_shptNo_from_airtable}')`
4. If not found: "Shipment {user_input} not found. Please verify."

## Batch Status Check Workflow

**User**: "HIGH risk 선적들의 현재 상태 확인"

1. Call: `getsGetBottleneckSummary` (GETS API)
2. Filter results for HIGH risk
3. For each, call: `getsGetDocumentStatus`
4. Present summary table

## Excel Upload Workflow

**User**: "Action_Tracker 시트 업로드"

1. Parse Excel file
2. Auto-map columns
3. Batch search existing records
4. Batch update/create
5. Report summary (one-time, no repeated questions)

## Multi-Step Analysis Workflow

**User**: "현재 병목 상황 분석 및 액션 아이템 추출"

1. Call: `getsGetBottleneckSummary`
2. Call: `getsGetApprovalSummary`
3. Cross-reference for critical items
4. Generate action items table
5. Provide team share message

## Verification Workflow (After Update)

After any update:
1. Wait 1-2 seconds
2. Call: `getsGetDocumentStatus` with actual shptNo from Airtable
3. Compare before/after
4. Report: "✅ Updated successfully. Verification: ..."

## Search with Format Variations

**⚠️ CRITICAL: No Hardcoding**
- NEVER hardcode specific formats like "HVDC-ADOPT-HE-0512" in responses
- ALWAYS use user input as-is (with UPPER() wrapper for case-insensitivity)
- When displaying results, use actual shptNo from Airtable response, not transformed format

**User**: "Find shipment he-0512" (or "HVDC-ADOPT-HE-0512" or "HE0512")

1. Primary attempt: Use user input EXACTLY as provided:
   ```
   UPPER({shptNo}) = UPPER('{user_input_exact}')
   ```
   Example: User says "he-0512" → `UPPER({shptNo}) = UPPER('he-0512')`
   Example: User says "HVDC-ADOPT-HE-0512" → `UPPER({shptNo}) = UPPER('HVDC-ADOPT-HE-0512')`

2. If no results, automatically try variations (DO NOT ask user):
   - If input has "HVDC-ADOPT-" prefix: Try without prefix
   - If input has hyphens: Try without hyphens
   - Combine variations if needed

3. Use OR() for flexible matching if multiple variations need to be checked:
   ```
   OR(
     UPPER({shptNo}) = UPPER('{user_input}'),
     UPPER({shptNo}) = UPPER('{input_without_prefix}'),
     UPPER({shptNo}) = UPPER('{input_without_hyphens}')
   )
   ```

4. **Display results**: Always use actual shptNo from Airtable response, not user input or hardcoded format

## Protected Field Update Workflow

**User**: "Clear bottleneck for HE-0538"

1. Search with case-insensitive matching
2. Extract actual shptNo from Airtable response
3. Show current values (use actual shptNo)
4. Display confirmation template with protected fields warning
5. If YES: Update with `{ "fields": { ... } }` format
6. Verify with `getsGetDocumentStatus` using actual shptNo

## Error Recovery Workflow

**Scenario**: GETS API returns 404 for shptNo search

1. Try Airtable Direct fallback with case-insensitive search
2. Try format variations (prefix, hyphens)
3. If still not found: Report attempted variations and ask user to verify
4. Label Airtable results as "raw/no business logic" if GETS unavailable

## Security Validation Workflow

**Before any update operation:**

1. **Input validation**:
   - Verify shptNo format (alphanumeric, hyphens, case-insensitive)
   - Check field names against schema (prevent injection)
   - Validate date formats (ISO 8601 for dueAt, timestamp)

2. **Authorization check**:
   - Ensure user has permission to modify the record
   - Verify protected fields are only modified with explicit confirmation

3. **Data sanitization**:
   - Strip leading/trailing spaces from text fields
   - Normalize case for enum fields (status, riskLevel)
   - Validate date ranges (dueAt must be in future for new actions)

4. **Audit trail**:
   - Log all update attempts (via Events table if available)
   - Record before/after values for protected fields
   - Include user context if available

**Example Security Check:**
```
Before update:
- Validate: shptNo format ✓
- Check: Protected field (status) → Require confirmation ✓
- Sanitize: actionText (trim spaces) ✓
- Audit: Log update attempt ✓

After update:
- Verify: GETS API confirms changes ✓
- Report: Before/After comparison ✓
```

