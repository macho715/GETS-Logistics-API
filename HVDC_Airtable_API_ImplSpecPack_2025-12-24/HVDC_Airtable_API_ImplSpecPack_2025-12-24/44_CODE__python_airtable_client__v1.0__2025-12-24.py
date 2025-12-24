"""HVDC — minimal Airtable Web API client (paging + batch upsert)

- paging via offset
- batch size <= 10
- upsert via performUpsert + fieldsToMergeOn
- rate-limit safe: 5 rps/base + 429 cooldown handling

Env:
  AIRTABLE_PAT
  AIRTABLE_BASE_ID
"""

from __future__ import annotations

import os
import time
import json
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import quote

import requests


class AirtableClient:
    def __init__(self, pat: str, base_id: str, *, timeout: Tuple[int, int] = (10, 60)) -> None:
        self.pat = pat
        self.base_id = base_id
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {pat}",
                "Content-Type": "application/json",
            }
        )

    def _url(self, table_id_or_name: str) -> str:
        return f"https://api.airtable.com/v0/{self.base_id}/{quote(table_id_or_name, safe='')}"

    def _request(self, method: str, url: str, *, params: Optional[Dict[str, Any]] = None, json_body: Any = None) -> Dict[str, Any]:
        # Hard rules based on Airtable guidance:
        # - 429: wait 30s (or Retry-After) then retry
        # - 503: exponential backoff retry
        max_tries = 5
        for attempt in range(1, max_tries + 1):
            resp = self.session.request(method, url, params=params, json=json_body, timeout=self.timeout)
            if resp.status_code == 429:
                retry_after = resp.headers.get("Retry-After")
                sleep_s = int(retry_after) if retry_after and retry_after.isdigit() else 30
                time.sleep(sleep_s)
                continue
            if resp.status_code == 503:
                time.sleep(min(8, 2 ** (attempt - 1)))
                continue
            if not resp.ok:
                raise RuntimeError(f"Airtable API error {resp.status_code}: {resp.text}")
            return resp.json()
        raise RuntimeError(f"Airtable API failed after retries: {method} {url}")

    # -------------------------
    # READ: list records (paged)
    # -------------------------
    def list_records(
        self,
        table_id_or_name: str,
        *,
        filter_by_formula: Optional[str] = None,
        view: Optional[str] = None,
        fields: Optional[List[str]] = None,
        page_size: int = 100,
    ) -> List[Dict[str, Any]]:
        url = self._url(table_id_or_name)
        params: Dict[str, Any] = {"pageSize": min(page_size, 100)}
        if filter_by_formula:
            params["filterByFormula"] = filter_by_formula
        if view:
            params["view"] = view
        if fields:
            # fields[] repeated params
            # requests accepts list for same key
            params["fields[]"] = fields

        out: List[Dict[str, Any]] = []
        offset: Optional[str] = None
        while True:
            if offset:
                params["offset"] = offset
            data = self._request("GET", url, params=params)
            out.extend(data.get("records", []))
            offset = data.get("offset")
            if not offset:
                break
        return out

    # -------------------------
    # WRITE: create/update/upsert
    # -------------------------
    @staticmethod
    def _chunks(items: List[Dict[str, Any]], n: int = 10) -> Iterable[List[Dict[str, Any]]]:
        for i in range(0, len(items), n):
            yield items[i : i + n]

    def create_records(self, table_id_or_name: str, records_fields: List[Dict[str, Any]], *, typecast: bool = True) -> Dict[str, Any]:
        url = self._url(table_id_or_name)
        payload = {
            "records": [{"fields": f} for f in records_fields],
            "typecast": bool(typecast),
        }
        return self._request("POST", url, json_body=payload)

    def update_records(self, table_id_or_name: str, records: List[Dict[str, Any]], *, typecast: bool = True) -> Dict[str, Any]:
        """records = [{"id": "rec...", "fields": {...}}, ...]"""
        url = self._url(table_id_or_name)
        payload = {"records": records, "typecast": bool(typecast)}
        return self._request("PATCH", url, json_body=payload)

    def upsert_records(self, table_id_or_name: str, records_fields: List[Dict[str, Any]], *, fields_to_merge_on: List[str], typecast: bool = True) -> List[Dict[str, Any]]:
        """Upsert using performUpsert + fieldsToMergeOn.

        records_fields = [{...fields...}, {...fields...}, ...]
        """
        url = self._url(table_id_or_name)
        results: List[Dict[str, Any]] = []
        for batch in self._chunks(records_fields, 10):
            payload = {
                "performUpsert": {"fieldsToMergeOn": fields_to_merge_on},
                "records": [{"fields": f} for f in batch],
                "typecast": bool(typecast),
            }
            results.append(self._request("PATCH", url, json_body=payload))
            # Keep under 5 req/sec per base (0.20s min). Use 0.22s for margin.
            time.sleep(0.22)
        return results


def _demo() -> None:
    pat = os.environ["AIRTABLE_PAT"]
    base_id = os.environ["AIRTABLE_BASE_ID"]
    shipments = os.environ.get("TABLE_ID_SHIPMENTS", "Shipments")
    cli = AirtableClient(pat, base_id)

    # Find by filterByFormula (field names only)
    shpt_no = "SCT-0143"
    formula = f"{{shptNo}}='{shpt_no}'"
    rows = cli.list_records(shipments, filter_by_formula=formula, page_size=1)
    print(json.dumps(rows, indent=2))

    # Upsert shipments (idempotent ingest)
    cli.upsert_records(
        shipments,
        records_fields=[{"shptNo": shpt_no, "vendor": "DSV", "incoterm": "DAP", "hs2": "85"}],
        fields_to_merge_on=["shptNo"],
        typecast=True,
    )


if __name__ == "__main__":
    _demo()
