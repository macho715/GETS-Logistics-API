#!/usr/bin/env python3
import os, sys, json, time
from typing import Any, Dict, List, Optional
import requests
from urllib.parse import urlencode, quote

API_ROOT="https://api.airtable.com/v0"

def headers(token: str) -> Dict[str,str]:
    return {"Authorization": f"Bearer {token}", "Content-Type":"application/json"}

def airtable_get(url: str, token: str, params: Optional[Dict[str,Any]]=None) -> Dict[str,Any]:
    # Rate limit: 5 req/s per base, 50 req/s per PAT. On 429, wait 30s.
    while True:
        r = requests.get(url, headers=headers(token), params=params, timeout=30)
        if r.status_code == 429:
            time.sleep(30)
            continue
        r.raise_for_status()
        return r.json()

def list_all_records(base_id: str, table_id: str, token: str, params: Dict[str,Any]) -> List[Dict[str,Any]]:
    records=[]
    offset=None
    while True:
        p=dict(params)
        p["pageSize"]=min(int(p.get("pageSize",100)),100)
        if offset:
            p["offset"]=offset
        res=airtable_get(f"{API_ROOT}/{base_id}/{table_id}", token, params=p)
        records.extend(res.get("records",[]))
        offset=res.get("offset")
        if not offset:
            break
    return records

def pick_first(records: List[Dict[str,Any]]) -> Optional[Dict[str,Any]]:
    return records[0] if records else None

def main():
    if len(sys.argv)<2:
        print("Usage: python build_document_status_packet.py <shptNo>")
        sys.exit(2)
    shptNo=sys.argv[1]

    token=os.getenv("AIRTABLE_TOKEN")
    base_id=os.getenv("AIRTABLE_BASE_ID")
    if not token or not base_id:
        print("ERROR: set AIRTABLE_TOKEN and AIRTABLE_BASE_ID")
        sys.exit(2)

    lock_path=os.path.join(os.path.dirname(__file__),"out","airtable_schema.lock.json")
    if not os.path.exists(lock_path):
        print("ERROR: run lock_schema_and_generate_mapping.py first")
        sys.exit(2)
    lock=json.load(open(lock_path,"r",encoding="utf-8"))

    def tid(table_name: str) -> str:
        return lock["tables"][table_name]["id"]

    # 1) Shipments (single record)
    shipments = list_all_records(base_id, tid("Shipments"), token, {
        "filterByFormula": f"{{shptNo}}='{shptNo}'",
        "maxRecords": 1
    })
    sh = pick_first(shipments)
    if not sh:
        print(f"NOT FOUND shptNo={shptNo}")
        sys.exit(4)
    shf = sh.get("fields", {})

    # 2) Documents (all for shptNo)
    docs = list_all_records(base_id, tid("Documents"), token, {
        "filterByFormula": f"{{shptNo}}='{shptNo}'",
        "pageSize": 100
    })
    # map docType -> status
    doc_map={}
    for r in docs:
        f=r.get("fields",{})
        dt=f.get("docType")
        st=f.get("status")
        if dt:
            doc_map[str(dt).upper()] = st

    # 3) Actions (open only, sort by priority/dueAt not done here)
    actions = list_all_records(base_id, tid("Actions"), token, {
        "filterByFormula": f"AND({{shptNo}}='{shptNo}', {{status}}!='DONE')",
        "pageSize": 100
    })
    act = pick_first(actions)
    af = act.get("fields", {}) if act else {}

    packet={
        "shptNo": shptNo,
        "doc": {
            "boeStatus": doc_map.get("BOE","UNKNOWN"),
            "doStatus": doc_map.get("DO","UNKNOWN"),
            "cooStatus": doc_map.get("COO","UNKNOWN"),
            "hblStatus": doc_map.get("HBL","UNKNOWN"),
            "ciplStatus": doc_map.get("CIPL","UNKNOWN"),
        },
        "bottleneck":{
            "code": shf.get("currentBottleneckCode"),
            "since": shf.get("bottleneckSince"),
            "riskLevel": shf.get("riskLevel")
        },
        "action":{
            "nextAction": af.get("actionText") or shf.get("nextAction"),
            "owner": af.get("owner") or shf.get("actionOwner"),
            "dueAt": af.get("dueAt") or shf.get("dueAt")
        }
    }

    out_dir=os.path.join(os.path.dirname(__file__),"out")
    os.makedirs(out_dir, exist_ok=True)
    out_path=os.path.join(out_dir,f"status_packet_{shptNo}.json")
    with open(out_path,"w",encoding="utf-8") as fp:
        json.dump(packet, fp, ensure_ascii=False, indent=2)

    print(f"OK: {out_path}")

if __name__=="__main__":
    main()
