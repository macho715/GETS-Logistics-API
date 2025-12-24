#!/usr/bin/env python3
import os, sys, json, time, csv
from typing import Any, Dict, List, Optional, Tuple
import requests

API_ROOT = "https://api.airtable.com/v0"

REQUIRED_TABLES = {
    "Shipments": ["shptNo","vendor","site","eta","mode","forwarder","currentBottleneckCode","bottleneckSince","riskLevel","nextAction","actionOwner","dueAt","stopFlag","stopReason","ocrPrecision","mismatchRate","rateOverrun"],
    "Documents": ["docKey","shptNo","docType","status","sourceSystem","externalRef","submittedAt","issuedAt","expiryAt","remarks"],
    "Approvals": ["approvalKey","shptNo","approvalType","status","dueAt","submittedAt","approvedAt","owner","remarks"],
    "Actions": ["actionKey","shptNo","bottleneckCode","actionText","owner","dueAt","status","priority","closedAt"],
    "Events": ["eventId","timestamp","shptNo","entityType","fromStatus","toStatus","bottleneckCode","actor","sourceSystem","rawPayload"],
    "Evidence": ["evidenceId","type","externalId","sha256","url","capturedAt","capturedBy","notes"],
    "BottleneckCodes": ["code","category","description","riskDefault","nextActionTemplate","slaHours","stopTrigger"],
    "Owners": ["ownerName","team","email","chatHandle","roleNotes"],
    "Vendors": ["vendorName","vendorType","country","contact"],
    "Sites": ["siteCode","siteName","country","timeZone"],
}

# JSON paths for /document/status/<shptNo>
DOC_STATUS_JSON_MAP = [
    ("shptNo", "Shipments", "shptNo"),
    ("doc.boeStatus", "Documents", "status", {"docType":"BOE"}),
    ("doc.doStatus", "Documents", "status", {"docType":"DO"}),
    ("doc.cooStatus", "Documents", "status", {"docType":"COO"}),
    ("doc.hblStatus", "Documents", "status", {"docType":"HBL"}),
    ("doc.ciplStatus", "Documents", "status", {"docType":"CIPL"}),
    ("bottleneck.code", "Shipments", "currentBottleneckCode"),
    ("bottleneck.since", "Shipments", "bottleneckSince"),
    ("bottleneck.riskLevel", "Shipments", "riskLevel"),
    ("action.nextAction", "Shipments", "nextAction"),
    ("action.owner", "Shipments", "actionOwner"),
    ("action.dueAt", "Shipments", "dueAt"),
]

def req_headers(token: str) -> Dict[str,str]:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

def get_base_schema(base_id: str, token: str) -> Dict[str,Any]:
    url = f"{API_ROOT}/meta/bases/{base_id}/tables"
    r = requests.get(url, headers=req_headers(token), timeout=30)
    r.raise_for_status()
    return r.json()

def build_lock(schema: Dict[str,Any]) -> Dict[str,Any]:
    tables = schema.get("tables", [])
    by_name = {t["name"]: t for t in tables}

    lock: Dict[str,Any] = {
        "base": {"id": None},
        "tables": {},
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }

    for tname, required_fields in REQUIRED_TABLES.items():
        if tname not in by_name:
            lock["tables"][tname] = {"missing": True}
            continue
        t = by_name[tname]
        fields_by_name = {f["name"]: f for f in t.get("fields", [])}

        lock_table = {
            "id": t.get("id"),
            "name": t.get("name"),
            "primaryFieldId": t.get("primaryFieldId"),
            "fields": {},
            "missingFields": [],
        }
        for fname in required_fields:
            f = fields_by_name.get(fname)
            if not f:
                lock_table["missingFields"].append(fname)
                continue
            lock_table["fields"][fname] = {
                "id": f.get("id"),
                "name": f.get("name"),
                "type": f.get("type"),
                "description": f.get("description"),
            }
        lock["tables"][tname] = lock_table

    return lock

def write_schema_summary_csv(schema: Dict[str,Any], out_csv: str) -> None:
    rows: List[List[str]] = [["tableName","tableId","fieldName","fieldId","fieldType"]]
    for t in schema.get("tables", []):
        for f in t.get("fields", []):
            rows.append([t.get("name",""), t.get("id",""), f.get("name",""), f.get("id",""), f.get("type","")])
    with open(out_csv, "w", newline="", encoding="utf-8") as fp:
        writer = csv.writer(fp)
        writer.writerows(rows)

def write_locked_mapping_md(lock: Dict[str,Any], out_md: str) -> None:
    def field_ref(tname: str, fname: str) -> str:
        t = lock["tables"].get(tname, {})
        tid = t.get("id", "MISSING_TABLE_ID")
        f = (t.get("fields") or {}).get(fname, {})
        fid = f.get("id","MISSING_FIELD_ID")
        return f"`{tname}` ({tid}) . `{fname}` ({fid})"

    lines = []
    lines.append("# /document/status/<shptNo> — Airtable ↔ JSON 1:1 Locked Mapping")
    lines.append("")
    lines.append("| JSON Path | Airtable Field (tableId.fieldName[fieldId]) | Notes |")
    lines.append("|---|---|---|")
    for item in DOC_STATUS_JSON_MAP:
        json_path, tname, fname, *rest = item
        cond = rest[0] if rest else None
        notes = ""
        if cond:
            notes = f"selector: {cond}"
        lines.append(f"| `{json_path}` | {field_ref(tname, fname)} | {notes} |")

    lines.append("")
    lines.append("## Notes")
    lines.append("- `filterByFormula` 조회를 쓰는 경우, **field ID가 아니라 field name만** 사용 가능합니다. (rename 금지 권장)")
    lines.append("- tableId는 rename에도 안전하므로, REST path는 tableId 사용 권장.")
    with open(out_md, "w", encoding="utf-8") as fp:
        fp.write("\n".join(lines))

def main():
    token = os.getenv("AIRTABLE_TOKEN")
    base_id = os.getenv("AIRTABLE_BASE_ID")
    if not token or not base_id:
        print("ERROR: Set AIRTABLE_TOKEN and AIRTABLE_BASE_ID", file=sys.stderr)
        sys.exit(2)

    out_dir = os.path.join(os.path.dirname(__file__), "out")
    os.makedirs(out_dir, exist_ok=True)

    schema = get_base_schema(base_id, token)
    lock = build_lock(schema)
    lock["base"]["id"] = base_id

    lock_path = os.path.join(out_dir, "airtable_schema.lock.json")
    with open(lock_path, "w", encoding="utf-8") as fp:
        json.dump(lock, fp, ensure_ascii=False, indent=2)

    md_path = os.path.join(out_dir, "document_status_mapping.locked.md")
    write_locked_mapping_md(lock, md_path)

    csv_path = os.path.join(out_dir, "schema_summary.csv")
    write_schema_summary_csv(schema, csv_path)

    print("OK")
    print(f"- {lock_path}")
    print(f"- {md_path}")
    print(f"- {csv_path}")

    # Hard-gate: missing tables/fields
    missing = []
    for tname, tinfo in lock["tables"].items():
        if tinfo.get("missing"):
            missing.append(f"Missing table: {tname}")
        else:
            for mf in tinfo.get("missingFields", []):
                missing.append(f"Missing field: {tname}.{mf}")
    if missing:
        print("\nHARD-GATE FAIL (schema mismatch):")
        for m in missing:
            print(f"- {m}")
        sys.exit(3)

if __name__ == "__main__":
    main()
