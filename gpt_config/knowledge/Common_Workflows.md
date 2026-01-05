# Common Workflow Patterns

## Single Record Update Workflow

**User**: "HE-0538의 riskLevel을 HIGH로 변경"

1. Search: `airtableGetRecords(filterByFormula: "UPPER({shptNo}) = UPPER('HE-0538')")`
2. If found:
   - Show current: `riskLevel=LOW`
   - Ask: "Change riskLevel from LOW to HIGH. Proceed? (YES/NO)"
   - If YES: `airtableUpdateRecord({ "fields": { "riskLevel": "HIGH" } })`
   - Verify: `getsGetDocumentStatus`
3. If not found: "Shipment HE-0538 not found. Please verify."

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

**User**: "Find shipment sct-0143"

1. Primary attempt: `UPPER({shptNo}) = UPPER('SCT-0143')`
2. If no results, try variations:
   - `UPPER({shptNo}) = UPPER('SCT0143')` (no hyphen)
   - `UPPER({shptNo}) = UPPER('HVDC-ADOPT-SCT-0143')` (with prefix)
3. Use OR() for flexible matching if needed:
   ```
   OR(
     UPPER({shptNo}) = UPPER('SCT-0143'),
     UPPER({shptNo}) = UPPER('SCT0143'),
     UPPER({shptNo}) = UPPER('HVDC-ADOPT-SCT-0143')
   )
   ```

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

