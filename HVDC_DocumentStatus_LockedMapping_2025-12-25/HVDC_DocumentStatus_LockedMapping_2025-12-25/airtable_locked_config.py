# Auto-generated from airtable_schema.lock.json (2025-12-25T00:32:52+0400)
BASE_ID = "appnLz06h07aMm366"

TABLES = {
  "Shipments": "tbl4NnKYx1ECKmaaC",
  "Documents": "tblbA8htgQSd2lOPO",
  "Actions": "tblkDpCWYORAPqxhw",
  "Approvals": "tblJh4z49DbjX7cyb",
  "Events": "tblGw5wKFQhR9FBRR",
  "Evidence": "tbljDDDNyvZY1sORx",
  "BottleneckCodes": "tblMad2YVdiN8WAYx",
  "Owners": "tblAjPArtKVBsShfE",
  "Vendors": "tblZ6Kc9EQP7Grx3B",
  "Sites": "tblSqSRWCe1IxCIih",
}

# NOTE: filterByFormula requires FIELD NAMES (not fieldIds).
FIELDS = {
  "Shipments": {
    "shptNo": "shptNo",
    "currentBottleneckCode": "currentBottleneckCode",
    "bottleneckSince": "bottleneckSince",
    "riskLevel": "riskLevel",
    "nextAction": "nextAction",
    "actionOwner": "actionOwner",
    "dueAt": "dueAt",
  },
  "Documents": {
    "shptNo": "shptNo",
    "docType": "docType",
    "status": "status",
  },
  "Actions": {
    "shptNo": "shptNo",
    "status": "status",
    "priority": "priority",
    "dueAt": "dueAt",
    "actionText": "actionText",
    "owner": "owner",
  },
}
