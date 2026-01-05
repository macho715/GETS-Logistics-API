# GETS Logistics API - Complete Reference Guide

## API Operations Quick Reference

### GETS API Endpoints
- **getsGetApiInfo**: API information
- **getsGetHealth**: System health check
- **getsGetStatusSummary**: Global KPI metrics
- **getsGetBottleneckSummary**: All bottlenecks with aging analysis
- **getsGetDocumentStatus**: Shipment status with bottleneck + next action
- **getsGetApprovalStatus**: Approval details with D-5/D-15 SLA
- **getsGetApprovalSummary**: Global approval statistics
- **getsGetDocumentEvents**: Event history / audit trail
- **getsIngestEvents**: Add events (ETL/RPA ledger insert)

### Airtable Direct Operations
- **airtableGetRecords**: Query tables with filtering, sorting, pagination
- **airtableUpdateRecord**: Modify single record (PATCH)

## FilterByFormula Examples

### Shipment Number Search (Case-Insensitive)

**⚠️ Use user input as-is, never hardcode formats**

Basic case-insensitive search:
```
UPPER({shptNo}) = UPPER('{user_input}')
```

Flexible matching with variations (if single search fails):
```
OR(
  UPPER({shptNo}) = UPPER('{user_input}'),
  UPPER({shptNo}) = UPPER('{input_without_prefix}'),
  UPPER({shptNo}) = UPPER('{input_without_hyphens}')
)
```

**Examples** (all refer to same shipment):
- User input: "he-0512" → `UPPER({shptNo}) = UPPER('he-0512')`
- User input: "HVDC-ADOPT-HE-0512" → `UPPER({shptNo}) = UPPER('HVDC-ADOPT-HE-0512')`
- User input: "HE0512" → `UPPER({shptNo}) = UPPER('HE0512')`

**Display**: Always show actual shptNo from Airtable response, not user input format

### Risk Level Filtering
```
{riskLevel}='HIGH'
AND({riskLevel}='HIGH', {currentBottleneckCode}='FANR_PENDING')
```

### Status Filtering
```
{status}='PENDING'
OR({status}='PENDING', {status}='SUBMITTED')
NOT({status}='COMPLETED')
```

### Date Comparisons
```
IS_BEFORE({dueAt}, '2025-12-30')
IS_AFTER({dueAt}, TODAY())
```

## Update Request Body Format

### Correct Format (Required)
```json
{
  "fields": {
    "currentBottleneckCode": "CLEARED",
    "riskLevel": "LOW"
  }
}
```

### Wrong Format (Will Cause Error)
```json
{
  "currentBottleneckCode": "CLEARED",
  "riskLevel": "LOW"
}
```

## Response Time Expectations
- GETS API: ~1-2 seconds
- Airtable Direct (read): ~1 second
- Airtable Direct (write): ~2-3 seconds

## Error Codes Reference
- **200**: Success
- **401**: Unauthorized (check PAT)
- **403**: Forbidden (check scopes)
- **404**: Not found (base/table/record)
- **422**: Invalid field names/values
- **429**: Rate limit exceeded (retry after delay)
- **503**: Service unavailable (retry)

## Protected Fields List
- **Shipments**: shptNo, currentBottleneckCode, bottleneckSince, riskLevel, nextAction, actionOwner, dueAt
- **Documents**: shptNo, docType, status
- **Actions**: shptNo, status, priority, dueAt, actionText, owner
- **Events**: timestamp, shptNo, entityType, toStatus

## Key Constants
- **Base ID**: `appnLz06h07aMm366` (always use this)
- **Timezone**: Asia/Dubai (UTC+04:00)
- **Schema Version**: 2025-12-25T00:32:52+0400
- **Available Tables**: Shipments, Documents, Approvals, Actions, Events, Evidence, BottleneckCodes, Owners, Vendors, Sites

