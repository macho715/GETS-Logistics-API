"""
HVDC - Production-ready Airtable Web API client

Features:
- Offset paging (automatic pagination)
- Batch operations (≤10 records/req)
- Upsert support (performUpsert + fieldsToMergeOn)
- Rate limiting (5 rps per base)
- Retry logic (429, 503 with exponential backoff)

Based on: HVDC_Airtable_API_ImplSpecPack_2025-12-24
"""

import time
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import quote

import requests


class AirtableClient:
    """Production-ready Airtable Web API client"""

    def __init__(
        self, pat: str, base_id: str, *, timeout: Tuple[int, int] = (10, 60)
    ) -> None:
        """
        Initialize Airtable client

        Args:
            pat: Personal Access Token
            base_id: Airtable Base ID (app...)
            timeout: (connect_timeout, read_timeout) in seconds
        """
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
        """Build Airtable API URL"""
        return f"https://api.airtable.com/v0/{self.base_id}/{quote(table_id_or_name, safe='')}"

    def _request(
        self,
        method: str,
        url: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Any = None,
    ) -> Dict[str, Any]:
        """
        Execute request with retry logic

        Handles:
        - 429 (Rate limit): Wait 30s or Retry-After header
        - 503 (Service unavailable): Exponential backoff
        """
        max_tries = 5

        for attempt in range(1, max_tries + 1):
            resp = self.session.request(
                method, url, params=params, json=json_body, timeout=self.timeout
            )

            # Rate limit: wait and retry
            if resp.status_code == 429:
                retry_after = resp.headers.get("Retry-After")
                sleep_s = (
                    int(retry_after) if retry_after and retry_after.isdigit() else 30
                )
                print(f"⚠️ Rate limited (429), waiting {sleep_s}s...")
                time.sleep(sleep_s)
                continue

            # Service unavailable: exponential backoff
            if resp.status_code == 503:
                wait_s = min(8, 2 ** (attempt - 1))
                print(
                    f"⚠️ Service unavailable (503), retry {attempt}/{max_tries}, waiting {wait_s}s..."
                )
                time.sleep(wait_s)
                continue

            # Other errors: raise immediately
            if not resp.ok:
                raise RuntimeError(
                    f"Airtable API error {resp.status_code}: {resp.text}"
                )

            return resp.json()

        raise RuntimeError(
            f"Airtable API failed after {max_tries} retries: {method} {url}"
        )

    # ==================== READ: List records (paged) ====================
    def list_records(
        self,
        table_id_or_name: str,
        *,
        filter_by_formula: Optional[str] = None,
        view: Optional[str] = None,
        fields: Optional[List[str]] = None,
        page_size: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        List records with automatic offset paging

        Args:
            table_id_or_name: Table ID (tbl...) or name
            filter_by_formula: Airtable filterByFormula expression
            view: View name or ID
            fields: List of field names to return
            page_size: Records per page (max 100)

        Returns:
            List of all records (auto-paged)
        """
        url = self._url(table_id_or_name)
        params: Dict[str, Any] = {"pageSize": min(page_size, 100)}

        if filter_by_formula:
            params["filterByFormula"] = filter_by_formula
        if view:
            params["view"] = view
        if fields:
            # fields[] repeated params
            params["fields[]"] = fields

        records: List[Dict[str, Any]] = []
        offset: Optional[str] = None

        while True:
            if offset:
                params["offset"] = offset

            data = self._request("GET", url, params=params)
            records.extend(data.get("records", []))

            offset = data.get("offset")
            if not offset:
                break

        return records

    # ==================== WRITE: Create/Update/Upsert ====================
    @staticmethod
    def _chunks(
        items: List[Dict[str, Any]], n: int = 10
    ) -> Iterable[List[Dict[str, Any]]]:
        """Split list into chunks of size n"""
        for i in range(0, len(items), n):
            yield items[i : i + n]

    def create_records(
        self,
        table_id_or_name: str,
        records_fields: List[Dict[str, Any]],
        *,
        typecast: bool = True,
    ) -> Dict[str, Any]:
        """
        Create records (batch ≤10)

        Args:
            table_id_or_name: Table ID or name
            records_fields: List of field dicts
            typecast: Auto-convert types (recommended)

        Returns:
            Airtable API response
        """
        url = self._url(table_id_or_name)
        payload = {
            "records": [{"fields": f} for f in records_fields],
            "typecast": bool(typecast),
        }
        return self._request("POST", url, json_body=payload)

    def update_records(
        self,
        table_id_or_name: str,
        records: List[Dict[str, Any]],
        *,
        typecast: bool = True,
    ) -> Dict[str, Any]:
        """
        Update records (batch ≤10)

        Args:
            table_id_or_name: Table ID or name
            records: [{"id": "rec...", "fields": {...}}, ...]
            typecast: Auto-convert types

        Returns:
            Airtable API response
        """
        url = self._url(table_id_or_name)
        payload = {"records": records, "typecast": bool(typecast)}
        return self._request("PATCH", url, json_body=payload)

    def upsert_records(
        self,
        table_id_or_name: str,
        records_fields: List[Dict[str, Any]],
        *,
        fields_to_merge_on: List[str],
        typecast: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Upsert records (idempotent ingest)

        Uses performUpsert + fieldsToMergeOn:
        - 0 matches: Creates new record
        - 1 match: Updates that record
        - >1 matches: Request fails (merge fields must be unique)

        Args:
            table_id_or_name: Table ID or name
            records_fields: List of field dicts
            fields_to_merge_on: Field names for matching (must be unique)
            typecast: Auto-convert types

        Returns:
            List of Airtable API responses (one per batch)
        """
        url = self._url(table_id_or_name)
        results: List[Dict[str, Any]] = []

        # Batch: ≤10 records/req
        for batch in self._chunks(records_fields, 10):
            payload = {
                "performUpsert": {"fieldsToMergeOn": fields_to_merge_on},
                "records": [{"fields": f} for f in batch],
                "typecast": bool(typecast),
            }
            results.append(self._request("PATCH", url, json_body=payload))

            # Rate limiting: 5 req/s = 0.2s/req, use 0.22s for margin
            time.sleep(0.22)

        return results
