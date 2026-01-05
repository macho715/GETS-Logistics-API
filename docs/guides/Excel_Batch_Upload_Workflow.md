# Excel/CSV Batch Upload to Airtable - One-Shot Processing Workflow

## CRITICAL: Execute Immediately, No Repeated Questions

⚠️ **MANDATORY: If user provides Excel data (file OR text table format), execute immediately WITHOUT confirmation UNLESS protected fields are affected.**

**Protected Fields (require confirmation):**
- Shipments: shptNo, currentBottleneckCode, bottleneckSince, riskLevel, nextAction, actionOwner, dueAt
- Documents: shptNo, docType, status
- Actions: shptNo, status, priority, dueAt, actionText, owner
- Events: timestamp, shptNo, entityType, toStatus

**Safe Fields (execute immediately, NO confirmation):**
- site, eta, remarks, itemDescription, vendor (any field NOT in protected fields list above)

**When user provides data (file OR text table):**
1. **Check if protected fields are being modified**
2. **If NO protected fields → Execute immediately (NO confirmation)**
3. **If YES protected fields → Show ONE batch confirmation, then execute**

**Text Table Format Recognition:**
- User provides tabular data in text format (headers + rows)
- Detect columns: shptNo, Site, Delivery Date, Remarks, etc.
- Treat as Excel data (same processing rules)

## Automatic Processing Rules

### Rule 1: Infer Context from User Command
- User says "Action_Tracker 업로드" → Sheet: Action_Tracker, Table: Actions (auto-detect)
- User says "[SheetName] 시트를 [TableName] 테이블에 업로드" → Use exact values provided
- User says "업로드" with file attached → Use first sheet, default to Shipments table
- User says "기존 레코드 업데이트" or "shptNo 기준으로 업데이트" → Update mode (find existing, update)
- User says "신규 생성" or "새로 추가" → Create mode (insert new records)

### Rule 2: Auto-Map Columns (No Questions)
Automatically match Excel columns to Airtable fields:

| Excel Column Pattern | Airtable Field | Notes |
|---------------------|----------------|-------|
| Shipment No, shptNo, Shipment Number, SHPT NO | shptNo | Key field for matching |
| Action, Action Text, Task, 작업내용 | actionText | Actions table |
| Owner, actionOwner, Responsible, 담당자 | owner | Actions table |
| Status, Current Status, 상태 | status | Actions/Documents |
| Due Date, Due At, Deadline, 마감일 | dueAt | Actions (ISO format) |
| Bottleneck, Current Bottleneck, 병목 | currentBottleneckCode | Shipments |
| Risk Level, Risk, 리스크 | riskLevel | Shipments |
| Document Type, Doc Type, 문서유형 | docType | Documents |
| Timestamp, Event Time, 시간 | timestamp | Events |

**Match logic**: Case-insensitive, partial match (e.g., "Shipment No" matches "Shipment Number"), trim spaces.

### Rule 3: Table Auto-Detection from Sheet Names
- "Action_Tracker", "Actions", "Tasks", "작업" → Actions table
- "Shipment_Map", "Shipments", "Cargo", "선적" → Shipments table
- "Thread_Log", "Events", "Log", "이벤트" → Events table
- "Documents", "Document_Status", "문서" → Documents table
- Default: Shipments table if ambiguous

### Rule 4: Batch Processing Execution

**For Update Mode (shptNo 기준 기존 레코드 업데이트)**:

1. Parse Excel file, read target sheet
2. For each row:
   - Extract shptNo column value AS-IS (do not transform format)
   - Normalize for search ONLY: Use UPPER() wrapper, but keep original format
   - Search existing record:
     ```
     airtableGetRecords(
       baseId='appnLz06h07aMm366',
       tableName=[auto_detected_table],
       filterByFormula: "UPPER({shptNo}) = UPPER('{extracted_shptNo_as_is}')"
     )
     ```
   - If not found, automatically try variations (without prefix, without hyphens)
   - If found: Extract recordId AND actual shptNo from response
   - Use actual shptNo from Airtable response for reporting (not Excel column value)
   - If not found after variations: Skip row (log for summary)
3. Process all rows silently
4. Report final summary once

**For Create Mode (신규 생성)**:

1. Parse Excel, map columns
2. For each batch (≤10 records):
   - Prepare fields object with mapped values for each row
   - Execute: `airtableCreateRecord` with batch of up to 10 records
   - Format:
     ```json
     {
       "records": [
         {"fields": {"shptNo": "...", "vendor": "...", ...}},
         {"fields": {"shptNo": "...", "vendor": "...", ...}},
         ...
       ],
       "typecast": true
     }
     ```
3. Process all batches silently
4. Report final summary once (created/skipped/errors)

### Rule 5: Execute Without Repeated Questions

**EXECUTE IMMEDIATELY (NO confirmation) if:**
- ✅ User provided data (file OR text table)
- ✅ No protected fields are being modified (only safe fields like site, eta, remarks)
- ✅ User intent is clear (update shipment status, delivery info, etc.)

**ONLY Ask Confirmation ONCE if:**
- Protected fields are being modified → Show ONE batch confirmation template
- User says "YES" or "CONFIRM" → Execute immediately (no more questions)

**DO NOT Ask:**
- ❌ "Would you like me to proceed?" (if no protected fields)
- ❌ "Please confirm" multiple times (maximum ONE confirmation)
- ❌ "RUN UPDATE NOW" vs "EXPORT PAYLOADS" choices (just execute via Airtable API)
- ❌ "Which table?" (auto-detect from data context)
- ❌ "Which fields?" (auto-map from columns)
- ❌ "Each record confirmation?" (process all silently, report at end)
- ❌ "어떤 시트를 사용할까요?" (if user specified or file has only one sheet)
- ❌ "어떤 테이블에 업로드할까요?" (if inferable from sheet name or user specified)

## Complete Execution Example

**User**: "Action_Tracker 시트를 Actions 테이블에 업로드. shptNo 기준으로 기존 레코드 업데이트"

**You should execute immediately:**

1. Read "Action_Tracker" sheet from uploaded Excel
2. Auto-map columns:
   - "Shipment No" → shptNo
   - "Action" → actionText
   - "Owner" → owner
   - "Status" → status
   - "Due Date" → dueAt
3. Determine: Table = Actions (user specified)
4. For each row:
   - Extract shptNo: "HE-0512"
   - Normalize: "HE-0512" (uppercase)
   - Search: airtableGetRecords(filterByFormula: "UPPER({shptNo}) = UPPER('HE-0512')")
   - Found record: recABC123
   - Update: airtableUpdateRecord(
       baseId='appnLz06h07aMm366',
       tableName='Actions',
       recordId='recABC123',
       { "fields": { "actionText": "...", "owner": "...", "status": "...", "dueAt": "..." } }
     )
5. After all rows processed:
   - Report: "✅ 업로드 완료: 15개 레코드 업데이트, 2개 건너뜀 (shptNo 없음), 0개 오류"

**Total questions asked: 0** (unless protected fields affected, then ONE confirmation)

## Protected Fields Batch Confirmation

If ANY row touches protected fields (shptNo, status, riskLevel, dueAt, etc.):
1. Process all rows to identify which will modify protected fields
2. Show summary ONCE:
   ```
   ⚠️ [Batch Update - Protected Fields Warning]

   Total rows: 15
   Rows affecting protected fields: 8
   Protected fields: status (8 rows), riskLevel (3 rows)

   Proceed with batch update? (YES/NO)
   ```
3. If YES: Execute all updates
4. If NO: Cancel entire batch

**Do NOT ask confirmation for each individual row.**

## Error Handling

- Missing shptNo in row: Skip row, include in "skipped" count
- Invalid field name: Skip that field, update valid fields only
- Record not found: Skip (update mode) or create (create mode if supported)
- Airtable API error (429, 503): Retry once, then skip and log
- Invalid field value: Skip that field, continue with other fields

All errors logged in final summary report.

## Security Validation

**Before batch processing:**

1. **File validation**:
   - Verify Excel file format (xlsx, xls, csv)
   - Check file size limits (max 10MB recommended)
   - Scan for malicious content (if applicable)

2. **Data validation**:
   - Validate shptNo format in each row
   - Check for SQL injection patterns in text fields
   - Verify date formats (ISO 8601)
   - Validate enum values (status, riskLevel against allowed values)

3. **Permission check**:
   - Verify user has permission to modify target table
   - Check if protected fields are being modified
   - Require batch confirmation for protected fields

4. **Rate limiting**:
   - Respect Airtable API rate limits (5 req/s per base)
   - Implement batch delays between API calls (0.2s minimum)
   - Monitor for 429 errors and back off appropriately

**Security Checklist:**
- [ ] File format validated
- [ ] shptNo format verified (no special characters except hyphens)
- [ ] Protected fields identified (show confirmation if any)
- [ ] Date formats validated (ISO 8601)
- [ ] Rate limiting configured (0.2s between batches)
- [ ] Error logging enabled (no sensitive data in logs)

## Summary Report Format

After batch processing, provide ONE comprehensive report:

```
✅ [Batch Upload Complete]

📊 Summary:
- Total rows processed: 15
- Records found and updated: 13
- Records not found (skipped): 2
- Errors: 0

📋 Details:
- Updated: HE-0512, HE-0513, ... (13 shipments)
- Skipped: HE-9999 (not found), [empty shptNo] (1 row)

⏱️ Processing time: 45 seconds
```

**Do NOT ask for confirmation after summary** - Upload is complete.
