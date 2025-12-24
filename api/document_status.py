import os
from flask import Flask, jsonify, request, abort
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo
from enum import Enum

# Import production-ready Airtable client
from api.airtable_client import AirtableClient
from api.schema_validator import SchemaValidator

app = Flask(__name__)

# ==================== Configuration ====================
AIRTABLE_API_TOKEN = os.getenv("AIRTABLE_API_TOKEN")
if AIRTABLE_API_TOKEN:
    AIRTABLE_API_TOKEN = AIRTABLE_API_TOKEN.strip()

AIRTABLE_BASE_ID = "appnLz06h07aMm366"
DUBAI_TZ = ZoneInfo("Asia/Dubai")  # +04:00

# Initialize schema validator (Phase 2.2)
schema_validator = None
try:
    schema_validator = SchemaValidator()
    print(f"✅ Schema validator loaded (version: {schema_validator.get_schema_version()})")
    
    # Use validated table IDs from lock file
    TABLES = {
        "shipments": schema_validator.get_table_id("Shipments"),
        "documents": schema_validator.get_table_id("Documents"),
        "approvals": schema_validator.get_table_id("Approvals"),
        "actions": schema_validator.get_table_id("Actions"),
        "events": schema_validator.get_table_id("Events"),
        "evidence": schema_validator.get_table_id("Evidence"),
        "bottleneckCodes": schema_validator.get_table_id("BottleneckCodes"),
        "owners": schema_validator.get_table_id("Owners"),
    }
    print(f"✅ Table IDs loaded from schema lock")
except FileNotFoundError as e:
    print(f"⚠️ Schema validator not available: {e}")
    print(f"⚠️ Falling back to hardcoded table IDs")
    # Fallback to hardcoded TABLES
    TABLES = {
        "shipments": "tbl4NnKYx1ECKmaaC",
        "documents": "tblbA8htgQSd2lOPO",
        "approvals": "tblJh4z49DbjX7cyb",
        "actions": "tblkDpCWYORAPqxhw",
        "events": "tblGw5wKFQhR9FBRR",
        "evidence": "tbljDDDNyvZY1sORx",
        "bottleneckCodes": "tblMad2YVdiN8WAYx",
        "owners": "tblAjPArtKVBsShfE",
    }

# Initialize production-ready Airtable client
airtable_client = None
if AIRTABLE_API_TOKEN:
    airtable_client = AirtableClient(AIRTABLE_API_TOKEN, AIRTABLE_BASE_ID)


# ==================== Enums (SpecPack v1.0) ====================
class DocStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    PENDING = "PENDING"
    RELEASED = "RELEASED"
    APPROVED = "APPROVED"
    ISSUED = "ISSUED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    MISSING = "MISSING"
    UNKNOWN = "UNKNOWN"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# ==================== Timezone Utilities ====================
def normalize_datetime(dt_string: Optional[str]) -> Optional[str]:
    """Convert datetime to Asia/Dubai timezone (ISO 8601)"""
    if not dt_string:
        return None
    try:
        dt = datetime.fromisoformat(dt_string.replace("Z", "+00:00"))
        dt_dubai = dt.astimezone(DUBAI_TZ)
        return dt_dubai.isoformat()
    except:
        return None


def now_dubai() -> str:
    """Current time in Asia/Dubai"""
    return datetime.now(DUBAI_TZ).isoformat()


# ==================== Airtable API (Production-ready) ====================
def fetch_table_records(
    table_name: str, filter_formula: str = None, max_records: int = 100
) -> List[Dict]:
    """
    Fetch records from Airtable table using production-ready client

    Features:
    - Automatic offset paging
    - Rate limiting (5 rps)
    - Retry logic (429, 503)

    Args:
        table_name: Key in TABLES dict
        filter_formula: Airtable filterByFormula
        max_records: Max records to fetch

    Returns:
        List of records (auto-paged)
    """
    if not airtable_client:
        return []

    table_id = TABLES.get(table_name)
    if not table_id:
        return []

    try:
        return airtable_client.list_records(
            table_id,
            filter_by_formula=filter_formula,
            page_size=min(max_records, 100)
        )
    except Exception as e:
        print(f"❌ Airtable API Error ({table_name}): {e}")
        return []


def get_shipment_by_shpt_no(shpt_no: str) -> Optional[Dict]:
    """Fetch shipment record by shptNo"""
    filter_formula = f"{{shptNo}}='{shpt_no}'"
    records = fetch_table_records("shipments", filter_formula, max_records=1)
    return records[0] if records else None


def get_documents_by_shpt_no(shpt_no: str) -> List[Dict]:
    """Fetch all documents for a shipment"""
    filter_formula = f"{{shptNo}}='{shpt_no}'"
    return fetch_table_records("documents", filter_formula, max_records=20)


def get_approvals_by_shpt_no(shpt_no: str) -> List[Dict]:
    """Fetch all approvals for a shipment"""
    filter_formula = f"{{shptNo}}='{shpt_no}'"
    return fetch_table_records("approvals", filter_formula, max_records=20)


def get_actions_by_shpt_no(shpt_no: str) -> List[Dict]:
    """Fetch all actions for a shipment"""
    filter_formula = f"{{shptNo}}='{shpt_no}'"
    return fetch_table_records("actions", filter_formula, max_records=20)


def get_events_by_shpt_no(shpt_no: str) -> List[Dict]:
    """Fetch all events for a shipment"""
    filter_formula = f"{{shptNo}}='{shpt_no}'"
    return fetch_table_records("events", filter_formula, max_records=100)


def get_bottleneck_code(code: str) -> Optional[Dict]:
    """Fetch bottleneck code definition"""
    filter_formula = f"{{code}}='{code}'"
    records = fetch_table_records("bottleneckCodes", filter_formula, max_records=1)
    return records[0] if records else None


# ==================== Business Logic ====================
def build_document_status(documents: List[Dict]) -> Dict[str, str]:
    """
    Build document status dict from Documents records

    Returns:
        {"boeStatus": "SUBMITTED", "doStatus": "NOT_STARTED", ...}
    """
    doc_types = ["BOE", "DO", "COO", "HBL", "CIPL"]
    doc_status = {}

    for doc_type in doc_types:
        doc = next(
            (d for d in documents if d.get("fields", {}).get("docType") == doc_type),
            None,
        )
        if doc:
            status = doc["fields"].get("status", "UNKNOWN")
        else:
            status = "UNKNOWN"

        doc_status[f"{doc_type.lower()}Status"] = status

    return doc_status


def build_bottleneck_info(
    shipment_fields: Dict, bottleneck_code_record: Optional[Dict]
) -> Dict:
    """
    Build bottleneck info

    Returns:
        {"code": "FANR_PENDING", "since": "...", "riskLevel": "HIGH"}
    """
    code = shipment_fields.get("currentBottleneckCode", "NONE")
    since = normalize_datetime(shipment_fields.get("bottleneckSince"))
    risk = shipment_fields.get("riskLevel", "LOW")

    # Fallback to bottleneck code default risk
    if bottleneck_code_record and not risk:
        risk = bottleneck_code_record["fields"].get("riskDefault", "LOW")

    return {"code": code, "since": since, "riskLevel": risk}


def build_action_info(
    shipment_fields: Dict, actions: List[Dict], bottleneck_code_record: Optional[Dict]
) -> Dict:
    """
    Build action info with priority: Actions > Shipment > BottleneckCode template

    Returns:
        {"nextAction": "...", "owner": "...", "dueAt": "..."}
    """
    # Priority 1: First OPEN action
    open_actions = [
        a
        for a in actions
        if a.get("fields", {}).get("status") in ["OPEN", "IN_PROGRESS"]
    ]

    if open_actions:
        # Sort by priority and dueAt
        open_actions.sort(
            key=lambda a: (
                0 if a["fields"].get("priority") == "HIGH" else 1,
                a["fields"].get("dueAt", "9999"),
            )
        )
        first_action = open_actions[0]["fields"]
        return {
            "nextAction": first_action.get("actionText", ""),
            "owner": first_action.get("owner", "PMT"),
            "dueAt": normalize_datetime(first_action.get("dueAt")),
        }

    # Priority 2: Shipment fields
    if shipment_fields.get("nextAction"):
        return {
            "nextAction": shipment_fields.get("nextAction", ""),
            "owner": shipment_fields.get("actionOwner", "PMT"),
            "dueAt": normalize_datetime(shipment_fields.get("dueAt")),
        }

    # Priority 3: BottleneckCode template
    if bottleneck_code_record:
        bc_fields = bottleneck_code_record["fields"]
        template = bc_fields.get("nextActionTemplate", "Normal progress")
        sla_hours = bc_fields.get("slaHours", 24)
        due_at = datetime.now(DUBAI_TZ) + timedelta(hours=sla_hours)

        return {"nextAction": template, "owner": "PMT", "dueAt": due_at.isoformat()}

    # Default
    return {
        "nextAction": "Monitor progress",
        "owner": "PMT",
        "dueAt": normalize_datetime(shipment_fields.get("dueAt")),
    }


def calculate_data_lag_minutes(events: List[Dict]) -> int:
    """Calculate data lag in minutes from last event"""
    if not events:
        return 0

    timestamps = [
        e["fields"].get("timestamp")
        for e in events
        if e.get("fields", {}).get("timestamp")
    ]

    if not timestamps:
        return 0

    latest_event = max(timestamps)
    try:
        latest_dt = datetime.fromisoformat(latest_event.replace("Z", "+00:00"))
        now = datetime.now(DUBAI_TZ)
        lag = (now - latest_dt).total_seconds() / 60
        return int(lag)
    except:
        return 0


# ==================== API Endpoints ====================
@app.route("/", methods=["GET"])
def index():
    """API root - health check"""
    return jsonify(
        {
            "message": "GETS Action API for ChatGPT - SpecPack v1.0 + Schema Validation",
            "status": "online",
            "version": "1.6.0",
            "dataSource": (
                "Airtable (Real-time)" if airtable_client else "Not Connected"
            ),
            "timezone": "Asia/Dubai (+04:00)",
            "features": {
                "offset_paging": True,
                "rate_limiting": "5 rps per base",
                "retry_logic": "429 (30s), 503 (exponential)",
                "batch_operations": "≤10 records/req",
                "upsert_support": True,
                "schema_validation": schema_validator is not None
            },
            "endpoints": {
                "home": "/",
                "health": "/health",
                "document_status": "/document/status/{shptNo}",
                "approval_status": "/approval/status/{shptNo}",
                "document_events": "/document/events/{shptNo}",
                "status_summary": "/status/summary",
                "bottleneck_summary": "/bottleneck/summary",
                "ingest_events": "POST /ingest/events"
            },
        }
    )


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    configured = airtable_client is not None

    connected = False
    if configured:
        try:
            # Test connection with Shipments table
            test_records = airtable_client.list_records(
                TABLES["shipments"],
                page_size=1
            )
            connected = True
        except:
            connected = False

    return jsonify(
        {
            "status": "healthy" if configured and connected else "degraded",
            "timestamp": now_dubai(),
            "version": "1.6.0",  # Updated for SchemaValidator
            "airtable": {
                "configured": configured,
                "connected": connected,
                "baseId": AIRTABLE_BASE_ID,
                "tables": len(TABLES),
                "features": [
                    "offset_paging",
                    "rate_limiting_5rps",
                    "retry_logic_429_503",
                    "batch_operations",
                    "upsert_support",
                    "schema_validation"
                ]
            },
            "schema_validator": {
                "enabled": schema_validator is not None,
                "version": schema_validator.get_schema_version() if schema_validator else None,
                "base_match": (schema_validator.base_id == AIRTABLE_BASE_ID) if schema_validator else None,
                "tables_validated": len(schema_validator.get_all_tables()) if schema_validator else 0
            }
        }
    )


@app.route("/document/status/<shpt_no>", methods=["GET"])
def get_document_status(shpt_no: str):
    """
    Get document status packet for a shipment (SpecPack v1.0)

    Returns operational status packet with bottleneck/action/evidence
    """
    # Fetch all related data
    shipment = get_shipment_by_shpt_no(shpt_no)
    if not shipment:
        return jsonify({"error": "Shipment not found", "shptNo": shpt_no}), 404

    shipment_fields = shipment.get("fields", {})
    documents = get_documents_by_shpt_no(shpt_no)
    actions = get_actions_by_shpt_no(shpt_no)
    events = get_events_by_shpt_no(shpt_no)

    # Get bottleneck code definition
    bottleneck_code = shipment_fields.get("currentBottleneckCode")
    bottleneck_code_record = None
    if bottleneck_code:
        bottleneck_code_record = get_bottleneck_code(bottleneck_code)

    # Build response packet
    doc_status = build_document_status(documents)
    bottleneck = build_bottleneck_info(shipment_fields, bottleneck_code_record)
    action = build_action_info(shipment_fields, actions, bottleneck_code_record)
    data_lag = calculate_data_lag_minutes(events)

    # Evidence (simplified - IDs only)
    evidence_ids = []
    for doc in documents:
        ev_ids = doc.get("fields", {}).get("evidenceIds", "")
        if ev_ids:
            evidence_ids.extend(ev_ids.split(","))

    return jsonify(
        {
            "shptNo": shpt_no,
            "doc": doc_status,
            "bottleneck": bottleneck,
            "action": action,
            "evidence": [{"id": eid.strip()} for eid in evidence_ids if eid.strip()],
            "meta": {"dataLagMinutes": data_lag, "lastUpdated": now_dubai()},
        }
    )


@app.route("/approval/status/<shpt_no>", methods=["GET"])
def get_approval_status(shpt_no: str):
    """
    Get approval status for a shipment (SpecPack v1.0)
    """
    approvals = get_approvals_by_shpt_no(shpt_no)

    approval_list = []
    for approval in approvals:
        fields = approval.get("fields", {})
        approval_list.append(
            {
                "type": fields.get("approvalType", "UNKNOWN"),
                "status": fields.get("status", "UNKNOWN"),
                "submittedAt": normalize_datetime(fields.get("submittedAt")),
                "dueAt": normalize_datetime(fields.get("dueAt")),
                "owner": fields.get("owner", ""),
                "evidenceIds": (
                    fields.get("evidenceIds", "").split(",")
                    if fields.get("evidenceIds")
                    else []
                ),
            }
        )

    return jsonify(
        {"shptNo": shpt_no, "approvals": approval_list, "lastUpdated": now_dubai()}
    )


@app.route("/document/events/<shpt_no>", methods=["GET"])
def get_document_events(shpt_no: str):
    """
    Get event history for a shipment (SpecPack v1.0)
    """
    events = get_events_by_shpt_no(shpt_no)

    event_list = []
    for event in events:
        fields = event.get("fields", {})
        event_list.append(
            {
                "eventId": fields.get("eventId"),
                "timestamp": normalize_datetime(fields.get("timestamp")),
                "entityType": fields.get("entityType", ""),
                "fromStatus": fields.get("fromStatus"),
                "toStatus": fields.get("toStatus"),
                "bottleneckCode": fields.get("bottleneckCode"),
                "actor": fields.get("actor"),
                "sourceSystem": fields.get("sourceSystem"),
                "evidenceIds": (
                    fields.get("evidenceIds", "").split(",")
                    if fields.get("evidenceIds")
                    else []
                ),
            }
        )

    # Sort by timestamp descending
    event_list.sort(key=lambda e: e.get("timestamp", ""), reverse=True)

    return jsonify(
        {
            "shptNo": shpt_no,
            "events": event_list,
            "totalEvents": len(event_list),
            "lastUpdated": now_dubai(),
        }
    )


@app.route("/status/summary", methods=["GET"])
def get_status_summary():
    """
    Get overall KPI summary
    """
    shipments = fetch_table_records("shipments", max_records=200)
    documents = fetch_table_records("documents", max_records=500)

    if not shipments:
        # Fallback to sample data
        return jsonify(
            {
                "dataSource": "Sample Data (No shipments found)",
                "totalShipments": 0,
                "boeRate": 0.0,
                "doRate": 0.0,
                "cooRate": 0.0,
                "hblRate": 0.0,
                "ciplRate": 0.0,
                "lastUpdated": now_dubai(),
            }
        )

    # Calculate KPIs
    total_shipments = len(shipments)

    # Document completion rates
    doc_types = ["BOE", "DO", "COO", "HBL", "CIPL"]
    completion_rates = {}

    for doc_type in doc_types:
        completed = sum(
            1
            for doc in documents
            if doc.get("fields", {}).get("docType") == doc_type
            and doc.get("fields", {}).get("status")
            in ["ISSUED", "RELEASED", "APPROVED"]
        )
        total = sum(
            1 for doc in documents if doc.get("fields", {}).get("docType") == doc_type
        )
        rate = completed / total if total > 0 else 0.0
        completion_rates[f"{doc_type.lower()}Rate"] = round(rate, 2)

    # Bottleneck analysis
    bottleneck_counts = {}
    risk_summary = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}

    for shipment in shipments:
        fields = shipment.get("fields", {})
        bn_code = fields.get("currentBottleneckCode", "NONE")
        risk = fields.get("riskLevel", "LOW")

        bottleneck_counts[bn_code] = bottleneck_counts.get(bn_code, 0) + 1
        risk_summary[risk] = risk_summary.get(risk, 0) + 1

    # Top bottlenecks
    top_bottlenecks = sorted(
        bottleneck_counts.items(), key=lambda x: x[1], reverse=True
    )[:5]

    return jsonify(
        {
            "dataSource": "Airtable (Real-time)",
            "totalShipments": total_shipments,
            **completion_rates,
            "riskSummary": risk_summary,
            "topBottlenecks": [
                {"code": code, "count": count} for code, count in top_bottlenecks
            ],
            "lastUpdated": now_dubai(),
        }
    )


@app.route("/bottleneck/summary", methods=["GET"])
def get_bottleneck_summary():
    """
    Get bottleneck category summary (SpecPack operational view)
    """
    shipments = fetch_table_records("shipments", max_records=200)

    bottlenecks = {}
    aging_distribution = {
        "under_24h": 0,
        "24h_to_48h": 0,
        "48h_to_72h": 0,
        "over_72h": 0,
    }

    now = datetime.now(DUBAI_TZ)

    for shipment in shipments:
        fields = shipment.get("fields", {})
        bn_code = fields.get("currentBottleneckCode", "NONE")

        if bn_code == "NONE":
            continue

        if bn_code not in bottlenecks:
            bottlenecks[bn_code] = []

        # Calculate aging
        since_str = fields.get("bottleneckSince")
        aging_hours = 0
        if since_str:
            try:
                since_dt = datetime.fromisoformat(since_str.replace("Z", "+00:00"))
                aging_hours = (now - since_dt).total_seconds() / 3600
            except:
                pass

        bottlenecks[bn_code].append(
            {
                "shptNo": fields.get("shptNo"),
                "agingHours": round(aging_hours, 1),
                "riskLevel": fields.get("riskLevel", "LOW"),
            }
        )

        # Aging distribution
        if aging_hours < 24:
            aging_distribution["under_24h"] += 1
        elif aging_hours < 48:
            aging_distribution["24h_to_48h"] += 1
        elif aging_hours < 72:
            aging_distribution["48h_to_72h"] += 1
        else:
            aging_distribution["over_72h"] += 1

    return jsonify(
        {
            "bottlenecks": {code: len(items) for code, items in bottlenecks.items()},
            "details": bottlenecks,
            "agingDistribution": aging_distribution,
            "lastUpdated": now_dubai(),
        }
    )


@app.route("/ingest/events", methods=["POST"])
def ingest_events():
    """
    Ingest events with idempotent upsert (SpecPack v1.0) + Field Validation (Phase 2.2)
    
    Request body example:
    {
      "batchId": "2025-12-24_EDAS_0600",
      "sourceSystem": "RPA",
      "timezone": "Asia/Dubai",
      "events": [
        {
          "timestamp": "2025-12-24T09:00:00+04:00",
          "shptNo": "SCT-0143",
          "entityType": "DOCUMENT",
          "toStatus": "SUBMITTED",
          ...
        }
      ]
    }
    
    Features:
    - Field validation against schema
    - Idempotent (dedupes by unique fields)
    - Batch upsert (≤10 records/req)
    - Rate-limited (5 rps)
    
    Note: eventId is autoNumber in Airtable (cannot be provided)
    """
    if not airtable_client:
        return jsonify({
            "error": "Airtable not configured",
            "status": "unavailable"
        }), 503
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON payload provided"}), 400
        
        events = data.get("events", [])
        
        if not events:
            return jsonify({"error": "No events in payload"}), 400
        
        batch_id = data.get("batchId", "unknown")
        source_system = data.get("sourceSystem", "API")
        
        # Phase 2.2: Validate fields if validator available
        if schema_validator:
            validation_errors = []
            valid_fields = schema_validator.get_valid_fields("Events")
            
            for i, event in enumerate(events):
                result = schema_validator.validate_fields("Events", event)
                if not result["valid"]:
                    validation_errors.append({
                        "index": i,
                        "invalid_fields": result["invalid_fields"],
                        "suggestions": result["suggestions"]
                    })
            
            if validation_errors:
                return jsonify({
                    "error": "Field validation failed",
                    "status": "validation_error",
                    "details": validation_errors,
                    "valid_fields": valid_fields,
                    "hint": "Check field names against Airtable schema. Note: eventId is autoNumber and cannot be provided.",
                    "timestamp": now_dubai()
                }), 400
        
        # Upsert events
        # Note: Events table uses timestamp+shptNo as natural key
        # Airtable will auto-generate eventId (autoNumber)
        results = airtable_client.upsert_records(
            TABLES["events"],
            events,
            fields_to_merge_on=["timestamp", "shptNo"],  # Natural composite key
            typecast=True
        )
        
        return jsonify({
            "status": "success",
            "batchId": batch_id,
            "sourceSystem": source_system,
            "ingested": len(events),
            "batches": len(results),
            "validated": schema_validator is not None,
            "timestamp": now_dubai()
        })
    
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "failed",
            "timestamp": now_dubai()
        }), 500


# ==================== Main ====================
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
