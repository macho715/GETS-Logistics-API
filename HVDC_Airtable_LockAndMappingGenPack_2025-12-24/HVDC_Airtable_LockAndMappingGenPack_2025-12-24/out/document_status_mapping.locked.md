# /document/status/<shptNo> — Airtable ↔ JSON 1:1 Locked Mapping

| JSON Path | Airtable Field (tableId.fieldName[fieldId]) | Notes |
|---|---|---|
| `shptNo` | `Shipments` (tbl4NnKYx1ECKmaaC) . `shptNo` (fldEQ5GwNfN6dRWnI) |  |
| `doc.boeStatus` | `Documents` (tblbA8htgQSd2lOPO) . `status` (fld8HQ6WJA5DstrNK) | selector: {'docType': 'BOE'} |
| `doc.doStatus` | `Documents` (tblbA8htgQSd2lOPO) . `status` (fld8HQ6WJA5DstrNK) | selector: {'docType': 'DO'} |
| `doc.cooStatus` | `Documents` (tblbA8htgQSd2lOPO) . `status` (fld8HQ6WJA5DstrNK) | selector: {'docType': 'COO'} |
| `doc.hblStatus` | `Documents` (tblbA8htgQSd2lOPO) . `status` (fld8HQ6WJA5DstrNK) | selector: {'docType': 'HBL'} |
| `doc.ciplStatus` | `Documents` (tblbA8htgQSd2lOPO) . `status` (fld8HQ6WJA5DstrNK) | selector: {'docType': 'CIPL'} |
| `bottleneck.code` | `Shipments` (tbl4NnKYx1ECKmaaC) . `currentBottleneckCode` (fldIACEWXLqsorJF0) |  |
| `bottleneck.since` | `Shipments` (tbl4NnKYx1ECKmaaC) . `bottleneckSince` (fldTLT6AMTi8udXrB) |  |
| `bottleneck.riskLevel` | `Shipments` (tbl4NnKYx1ECKmaaC) . `riskLevel` (fldkbfmbgNi4iFJDk) |  |
| `action.nextAction` | `Shipments` (tbl4NnKYx1ECKmaaC) . `nextAction` (fldkR6PTLDfvwnJN4) |  |
| `action.owner` | `Shipments` (tbl4NnKYx1ECKmaaC) . `actionOwner` (fldKuqW5THvGbsSzu) |  |
| `action.dueAt` | `Shipments` (tbl4NnKYx1ECKmaaC) . `dueAt` (fldF1TqRtlxwevnVI) |  |

## Notes
- `filterByFormula` 조회를 쓰는 경우, **field ID가 아니라 field name만** 사용 가능합니다. (rename 금지 권장)
- tableId는 rename에도 안전하므로, REST path는 tableId 사용 권장.