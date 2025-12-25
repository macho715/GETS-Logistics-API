"""
Locked Airtable Configuration
Generated from: airtable_schema.lock.json
Schema Version: 2025-12-25T00:32:52+0400

⚠️ DO NOT MODIFY MANUALLY - Regenerate from lock file using:
   python lock_schema_and_generate_mapping.py

This configuration provides stable table/field references that are
resilient to Airtable table name changes (table IDs are immutable).

Field names used in filterByFormula are marked as PROTECTED and must
not be renamed in Airtable without updating this configuration.
"""

BASE_ID = "appnLz06h07aMm366"
SCHEMA_VERSION = "2025-12-25T00:32:52+0400"

# Table IDs (immutable, safe for table renames)
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

# Field names used in filterByFormula and sort operations
# ⚠️ PROTECTED: These field names must NOT be renamed in Airtable
# because filterByFormula only accepts field names, not field IDs
PROTECTED_FIELDS = {
    "Shipments": [
        "shptNo",
        "currentBottleneckCode",
        "bottleneckSince",
        "riskLevel",
        "nextAction",
        "actionOwner",
        "dueAt",
    ],
    "Documents": [
        "shptNo",
        "docType",
        "status",
    ],
    "Actions": [
        "shptNo",
        "status",
        "priority",
        "dueAt",
        "actionText",
        "owner",
    ],
    "Events": [
        "timestamp",
        "shptNo",
        "entityType",
        "toStatus",
    ],
}

# Field IDs for reference and documentation
# (Not used in API calls, but useful for schema validation)
FIELD_IDS = {
    "Shipments": {
        "shptNo": "fldEQ5GwNfN6dRWnI",
        "vendor": "fldwrC8TWe9rdFNfe",
        "site": "fldFEdNYSbs6Zm2c4",
        "eta": "flddGQaFY1Tn4B0ML",
        "mode": "fldt4XGKLA0krgvIt",
        "forwarder": "fld8nWn3EYk7mYDAj",
        "currentBottleneckCode": "fldIACEWXLqsorJF0",
        "bottleneckSince": "fldTLT6AMTi8udXrB",
        "riskLevel": "fldkbfmbgNi4iFJDk",
        "nextAction": "fldkR6PTLDfvwnJN4",
        "actionOwner": "fldKuqW5THvGbsSzu",
        "dueAt": "fldF1TqRtlxwevnVI",
        "stopFlag": "fldp8hJ6Z2qzld1nu",
        "stopReason": "fldN2KyaGXOtMiY3k",
        "ocrPrecision": "fldhFnzUfwu6Xaj31",
        "mismatchRate": "fldyoo1DZYXXJMFHY",
        "rateOverrun": "fldEdbfWkARPaMY0C",
    },
    "Documents": {
        "docKey": "fldpmMcikUv0u9evG",
        "shptNo": "fldmRTznGzLTEu85V",
        "docType": "fldgN8FmlkC47Yqyf",
        "status": "fld8HQ6WJA5DstrNK",
        "sourceSystem": "fldWctaogKEorEyCo",
        "externalRef": "fldwtDEdNCc1yJx4u",
        "submittedAt": "fld23v40H4l5lHvjI",
        "issuedAt": "fldUAGUFJ33J0YvIo",
        "expiryAt": "fldgED4jeWG0KDmKd",
        "remarks": "fld66rDKVonOfdafL",
    },
    "Approvals": {
        "approvalKey": "fldDElgFkwdKRbUZW",
        "shptNo": "fldM1DSjK9xhkCQgk",
        "approvalType": "fldnBCK8aBkR8BQXg",
        "status": "fldlaNUUV23pfXsVJ",
        "dueAt": "fldLS5JmajZQrbSw2",
        "submittedAt": "fldQvXsEfCfZIQ4eO",
        "approvedAt": "fldoOBQ54EUp7Rqm8",
        "owner": "fldCYsmrPIWQm44zm",
        "remarks": "fldZH57r1l5aR1QU9",
    },
    "Actions": {
        "actionKey": "fldScKtL6EoWbAbXY",
        "shptNo": "fldvQSM4Uf1ckQ107",
        "bottleneckCode": "fldsrgI5AYgNrYh8b",
        "actionText": "fldUgpe4galkjERcY",
        "owner": "fldLI0zldMrrM5fJ4",
        "dueAt": "fldaXsyp6dNTmx56W",
        "status": "fldLmSWCdRprObgST",
        "priority": "fldX80o1udxsK6gmy",
        "closedAt": "fldvcdUEuRP68wwSb",
    },
    "Events": {
        "eventId": "fldVAMh4QxQVdKLE0",
        "timestamp": "fldVIht1pNmtk1jMp",
        "shptNo": "fldmbmNgM2eX97bA7",
        "entityType": "fld85q4BCwZThPm9J",
        "fromStatus": "fld7GbpyCLf0WkPdl",
        "toStatus": "fldDZtWcKQ7WNT8KL",
        "bottleneckCode": "fldcustnLL90tqW9c",
        "actor": "fld1aEgmcsqhnLGQk",
        "sourceSystem": "fldRoX6VWY6EIqe8h",
        "rawPayload": "fld8p9m7ldVCQ2grN",
    },
    "Evidence": {
        "evidenceId": "fldfVD8fGqnS2pqYM",
        "type": "fld144r2em2OBPfIP",
        "externalId": "fld2QEXejDIC4bnVg",
        "sha256": "fldahsNkxpa2NsS5x",
        "url": "fldlx51ieXZ2XzrrM",
        "capturedAt": "fldgA8zIUjQWI4egQ",
        "capturedBy": "fldCoffP1urdoUoXC",
        "notes": "fldHZRfFFwGQ29Nk0",
    },
    "BottleneckCodes": {
        "code": "fldsvpytOY2zuZv8I",
        "category": "fld0KNFCAvybE1gqw",
        "description": "fldwRZHgclhAxeQfW",
        "riskDefault": "fldZ1Mp3L0Sze6Egg",
        "nextActionTemplate": "fldi5I1ZRSlV21lG8",
        "slaHours": "fldCmpVaalPUteU6Q",
        "stopTrigger": "fldCHVRvbRHXTsd1i",
    },
    "Owners": {
        "ownerName": "fldBfTdicJjbZSA2f",
        "team": "fldSXiTbv5uNCK1NS",
        "email": "flda6bh7G3sAdHi7n",
        "chatHandle": "fldo8HpCQiz4wBpnV",
        "roleNotes": "fldQYxOWTGzsoLSwR",
    },
    "Vendors": {
        "vendorName": "fldmMTVSuD5bfTlEJ",
        "vendorType": "fldqxpYvufGlgsM8P",
        "country": "fldDPq1RxgSu9VfhV",
        "contact": "fldcNAXGjq5X01JOG",
    },
    "Sites": {
        "siteCode": "fldWIIqsKVc0N01O1",
        "siteName": "fldk8MBEDkJ5unlIt",
        "country": "fldgMOXHfXFRBlS83",
        "timeZone": "fldlkpK9UiyQihNDj",
    },
}

# Known gaps in current schema (as of 2025-12-25)
SCHEMA_GAPS = {
    "evidence_links": "Documents/Approvals/Actions/Events tables lack Evidence link fields",
    "event_key": "Events table lacks eventKey field for idempotency (using composite key workaround)",
    "incoterm_hs": "Shipments table lacks Incoterm and HS code fields for BOE RED detection",
}

