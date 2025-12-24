# /document/status/<shptNo> — Locked Mapping (tableId + fieldId)

- Airtable BaseId: `appnLz06h07aMm366`
- Schema lock version: `2025-12-25T00:32:52+0400`

## Response Contract (v1)

```json
{
  "shptNo": "SCT-0143",
  "doc": {
    "boeStatus": "SUBMITTED",
    "doStatus": "NOT_STARTED",
    "cooStatus": "UNKNOWN",
    "hblStatus": "UNKNOWN",
    "ciplStatus": "UNKNOWN"
  },
  "bottleneck": {
    "code": "FANR_PENDING",
    "since": "2025-12-24T09:00:00+04:00",
    "riskLevel": "HIGH"
  },
  "action": {
    "nextAction": "FANR 승인 상태 확인 및 가속 요청",
    "owner": "Customs/Compliance",
    "dueAt": "2025-12-25T12:00:00+04:00"
  }
}
```

## 1:1 Field Mapping

| JSON Path | Airtable (tableId.field[fieldId]) | Airtable Type | Rule |
|---|---|---|---|
| `shptNo` | `Shipments`(tbl4NnKYx1ECKmaaC).`shptNo`(fldEQ5GwNfN6dRWnI) | `singleLineText` | direct read |
| `bottleneck.code` | `Shipments`(tbl4NnKYx1ECKmaaC).`currentBottleneckCode`(fldIACEWXLqsorJF0) | `singleLineText` | direct read |
| `bottleneck.since` | `Shipments`(tbl4NnKYx1ECKmaaC).`bottleneckSince`(fldTLT6AMTi8udXrB) | `dateTime` | direct read |
| `bottleneck.riskLevel` | `Shipments`(tbl4NnKYx1ECKmaaC).`riskLevel`(fldkbfmbgNi4iFJDk) | `singleSelect` | direct read |
| `action.nextAction` | `Shipments`(tbl4NnKYx1ECKmaaC).`nextAction`(fldkR6PTLDfvwnJN4) | `singleLineText` | direct read |
| `action.owner` | `Shipments`(tbl4NnKYx1ECKmaaC).`actionOwner`(fldKuqW5THvGbsSzu) | `singleLineText` | direct read |
| `action.dueAt` | `Shipments`(tbl4NnKYx1ECKmaaC).`dueAt`(fldF1TqRtlxwevnVI) | `dateTime` | direct read |
| `doc.boeStatus` | `Documents`(tblbA8htgQSd2lOPO).`status`(fld8HQ6WJA5DstrNK) + selector `Documents`(tblbA8htgQSd2lOPO).`docType`(fldgN8FmlkC47Yqyf)=`BOE` | `singleSelect` | pick status for docType=BOE; if none → `UNKNOWN` |
| `doc.doStatus` | `Documents`(tblbA8htgQSd2lOPO).`status`(fld8HQ6WJA5DstrNK) + selector `Documents`(tblbA8htgQSd2lOPO).`docType`(fldgN8FmlkC47Yqyf)=`DO` | `singleSelect` | pick status for docType=DO; if none → `UNKNOWN` |
| `doc.cooStatus` | `Documents`(tblbA8htgQSd2lOPO).`status`(fld8HQ6WJA5DstrNK) + selector `Documents`(tblbA8htgQSd2lOPO).`docType`(fldgN8FmlkC47Yqyf)=`COO` | `singleSelect` | pick status for docType=COO; if none → `UNKNOWN` |
| `doc.hblStatus` | `Documents`(tblbA8htgQSd2lOPO).`status`(fld8HQ6WJA5DstrNK) + selector `Documents`(tblbA8htgQSd2lOPO).`docType`(fldgN8FmlkC47Yqyf)=`HBL` | `singleSelect` | pick status for docType=HBL; if none → `UNKNOWN` |
| `doc.ciplStatus` | `Documents`(tblbA8htgQSd2lOPO).`status`(fld8HQ6WJA5DstrNK) + selector `Documents`(tblbA8htgQSd2lOPO).`docType`(fldgN8FmlkC47Yqyf)=`CIPL` | `singleSelect` | pick status for docType=CIPL; if none → `UNKNOWN` |

## Query Plan (Airtable Web API)

### Q1) Shipments by shptNo (expect 0..1)

- Table: Shipments `tbl4NnKYx1ECKmaaC`
```http
GET https://api.airtable.com/v0/{baseId}/tbl4NnKYx1ECKmaaC?maxRecords=1&filterByFormula=%7BshptNo%7D%3D%27SCT-0143%27&fields%5B%5D=shptNo&fields%5B%5D=currentBottleneckCode&fields%5B%5D=bottleneckSince&fields%5B%5D=riskLevel&fields%5B%5D=nextAction&fields%5B%5D=actionOwner&fields%5B%5D=dueAt
Authorization: Bearer <PAT>
```

### Q2) Documents by shptNo (0..N)

- Table: Documents `tblbA8htgQSd2lOPO`
```http
GET https://api.airtable.com/v0/{baseId}/tblbA8htgQSd2lOPO?pageSize=100&filterByFormula=%7BshptNo%7D%3D%27SCT-0143%27&fields%5B%5D=shptNo&fields%5B%5D=docType&fields%5B%5D=status
Authorization: Bearer <PAT>
```

### (Optional) Q3) Actions open by shptNo (override action.*)

- Table: Actions `tblkDpCWYORAPqxhw`
```http
GET https://api.airtable.com/v0/{baseId}/tblkDpCWYORAPqxhw?pageSize=100&filterByFormula=AND(%7BshptNo%7D%3D%27SCT-0143%27%2C%7Bstatus%7D!%3D%27DONE%27)&sort%5B0%5D%5Bfield%5D=priority&sort%5B0%5D%5Bdirection%5D=asc&sort%5B1%5D%5Bfield%5D=dueAt&sort%5B1%5D%5Bdirection%5D=asc&fields%5B%5D=actionText&fields%5B%5D=owner&fields%5B%5D=dueAt&fields%5B%5D=status&fields%5B%5D=priority
Authorization: Bearer <PAT>
```

## Hard Gates (ZERO)

- Shipments record not found → HTTP 404 (no status packet)
- Documents has duplicate rows for same (shptNo, docType) → set `bottleneck.code='STOP_DATA_MISMATCH'` or return 409. (**가정:** 운영 게이트 적용)
- Any Airtable 429 → wait 30s and retry (rate limit policy)

## Rename-Protected Fields (because filterByFormula uses field *names*)

- Shipments: `shptNo`
- Documents: `shptNo`, `docType`, `status`
- Actions (if used): `shptNo`, `status`, `priority`, `dueAt`
