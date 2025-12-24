# Airtable ↔ Flask API 1:1 Mapping Spec (v1.0) — 2025-12-24
Timezone: Asia/Dubai (+04:00)  
Key: shptNo (Shipment No.)

## 1. Endpoints covered
- GET /document/status/<shptNo>
- GET /approval/status/<shptNo>
- GET /document/events/<shptNo>  (append-only ledger)
- POST /ingest/events            (event ingest)
- POST /ingest/daily-report      (snapshot ingest)

## 2. JSON model (Document Status Packet)
### Response shape (example)
```json
{
  "shptNo": "SCT-0143",
  "doc": {
    "boeStatus": "SUBMITTED",
    "doStatus": "NOT_STARTED",
    "cooStatus": "PENDING",
    "hblStatus": "READY",
    "ciplStatus": "VALID"
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
  },
  "evidence": [
    {"type":"email","id":"EV-0002","externalId":"msg_abc","sha256":null,"url":null}
  ],
  "meta": {
    "dataLagMinutes": 0
  }
}
```

### 1:1 Field mapping (document/status)
- shptNo                        ← Shipments.shptNo
- doc.<docType>Status           ← Documents.status where Documents.docType=<docType> AND Documents.shipment=Shipments
- bottleneck.code               ← Shipments.currentBottleneckCode (preferred linked to BottleneckCodes.code)
- bottleneck.since              ← Shipments.bottleneckSince
- bottleneck.riskLevel          ← Shipments.riskLevel (fallback BottleneckCodes.riskDefault)
- action.nextAction             ← First OPEN Actions.actionText (priority asc, dueAt asc) else Shipments.nextAction else BottleneckCodes.nextActionTemplate
- action.owner                  ← Actions.owner else Shipments.actionOwner
- action.dueAt                  ← Actions.dueAt else Shipments.dueAt else NOW + BottleneckCodes.slaHours
- evidence[]                    ← UNION of linked Evidence from Documents/Approvals/Actions/Events (dedupe by evidenceId)
- meta.dataLagMinutes           ← DATETIME_DIFF(NOW, MAX(Events.timestamp), minutes) (or Shipments.dataLagMinutes formula)

## 3. JSON model (Approval Status)
```json
{
  "shptNo": "SCT-0143",
  "approvals": [
    {
      "type": "FANR",
      "status": "PENDING",
      "submittedAt": "2025-12-24T09:00:00+04:00",
      "dueAt": "2025-12-25T12:00:00+04:00",
      "owner": "Customs/Compliance",
      "evidenceIds": ["EV-0002"]
    }
  ]
}
```

### 1:1 Field mapping (approval/status)
- approvals[].type             ← Approvals.approvalType
- approvals[].status           ← Approvals.status
- approvals[].submittedAt      ← Approvals.submittedAt
- approvals[].dueAt            ← Approvals.dueAt
- approvals[].owner            ← Approvals.owner (linked to Owners.ownerName)
- approvals[].evidenceIds      ← Approvals.evidence (linked Evidence.evidenceId)

## 4. Events ledger model (document/events)
```json
{
  "shptNo": "SCT-0143",
  "events": [
    {
      "eventId": 1,
      "timestamp": "2025-12-24T09:00:00+04:00",
      "entityType": "APPROVAL",
      "fromStatus": "SUBMITTED",
      "toStatus": "PENDING",
      "bottleneckCode": "FANR_PENDING",
      "actor": "Customs/Compliance",
      "sourceSystem": "RPA",
      "evidenceIds": ["EV-0002"],
      "rawPayload": {"fanr":"pending"}
    }
  ]
}
```

### 1:1 Field mapping (events)
- eventId                      ← Events.eventId
- timestamp                    ← Events.timestamp
- entityType                   ← Events.entityType
- fromStatus / toStatus        ← Events.fromStatus / Events.toStatus
- bottleneckCode               ← Events.bottleneckCode (linked to BottleneckCodes.code or stored text)
- actor                        ← Events.actor
- sourceSystem                 ← Events.sourceSystem
- evidenceIds                  ← Events.evidence (linked Evidence.evidenceId)
- rawPayload                   ← Events.rawPayload (JSON text stored)

## 5. Enums (v1)
DocStatus: NOT_STARTED, IN_PROGRESS, SUBMITTED, PENDING, RELEASED, APPROVED, ISSUED, REJECTED, EXPIRED, MISSING, UNKNOWN  
ApprovalStatus: NOT_STARTED, SUBMITTED, PENDING, APPROVED, REJECTED, ON_HOLD, UNKNOWN  
RiskLevel: LOW, MEDIUM, HIGH, CRITICAL  
EntityType: SHIPMENT, DOCUMENT, APPROVAL, ACTION, DATA_QUALITY  

## 6. Notes
- Airtable “Linked record” fields are best stored as record IDs internally (Airtable API), but for operations we keep a stable business key (evidenceId, vendorName, ownerName) in the Primary field to avoid leaking record IDs.
- All datetime fields are ISO 8601 strings in payloads.
