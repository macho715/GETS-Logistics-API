"""
Upload Actions records to Airtable from a TSV/CSV file.

Usage:
    python scripts/upload_actions_to_airtable.py \
        --file data/today_tomorrow_deliveries.tsv \
        --token pat_xxxxxxxxxxxxx
"""

import argparse
import csv
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from api.airtable_client import AirtableClient
from api.airtable_locked_config import BASE_ID, TABLES
from api.utils import DUBAI_TZ, iso_dubai, parse_iso_any


def normalize_cell(value: Any) -> Optional[str]:
    """Normalize a raw cell value to a cleaned string or None."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    lowered = text.lower()
    if lowered in {"na", "n/a", "none", "null", "nan", "-"}:
        return None
    return text


def split_shpt_no(raw_shpt_no: str) -> tuple[str, Optional[str]]:
    """Split shptNo when it contains a reference suffix."""
    if " // " in raw_shpt_no:
        base, ref = raw_shpt_no.split(" // ", 1)
        return base.strip(), ref.strip()
    return raw_shpt_no.strip(), None


def normalize_datetime_field(value: Any) -> Optional[str]:
    """Normalize date/datetime to ISO string in Asia/Dubai timezone."""
    if value is None:
        return None

    if isinstance(value, str):
        text = value.strip()
        if not text or text in {"NaT", "nan", "NaN"}:
            return None
        dt = parse_iso_any(text)
        if dt:
            return iso_dubai(dt)
        return text

    if isinstance(value, datetime):
        return iso_dubai(value.astimezone(DUBAI_TZ))

    return str(value)


def generate_action_key(
    shpt_no: str,
    action_text: Optional[str],
    owner: Optional[str],
    due_at: Optional[str],
    status: Optional[str],
) -> str:
    """Create a deterministic actionKey for idempotent upserts."""
    normalized_shpt = shpt_no.strip().upper()
    date_part = "NA"
    if due_at and "T" in due_at:
        date_part = due_at.split("T", 1)[0].replace("-", "")
    key_input = "|".join(
        [normalized_shpt, action_text or "", owner or "", due_at or "", status or ""]
    )
    digest = hashlib.sha1(key_input.encode("utf-8")).hexdigest()[:10]
    return f"ACT-{normalized_shpt}-{date_part}-{digest}"


def pick_value(row: Dict[str, Any], keys: List[str]) -> Optional[str]:
    """Return the first non-empty value from row for any of the keys."""
    for key in keys:
        if key in row:
            value = normalize_cell(row.get(key))
            if value is not None:
                return value
    return None


def prepare_action_record(row: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a TSV row into an Airtable Actions record."""
    raw_shpt_no = pick_value(
        row, ["shipment_no", "shptNo", "Today / Tomorrow Delivery", "Shipment No"]
    )
    if not raw_shpt_no:
        raise ValueError(f"Missing shptNo in row: {row}")

    shpt_no, ref = split_shpt_no(raw_shpt_no)
    action_text = pick_value(row, ["item_description", "actionText", "Item Description"])
    owner = pick_value(row, ["site", "owner", "Site"])
    due_at = normalize_datetime_field(
        pick_value(row, ["delivery_date", "dueAt", "Delivery Date"])
    )
    status = pick_value(row, ["remarks", "status", "Remarks"])

    if ref:
        if action_text:
            action_text = f"{action_text} (Ref: {ref})"
        else:
            action_text = f"Ref: {ref}"

    action_key = pick_value(row, ["actionKey", "action_key"])
    if not action_key:
        action_key = generate_action_key(shpt_no, action_text, owner, due_at, status)

    record: Dict[str, Any] = {"shptNo": shpt_no, "actionKey": action_key}
    if action_text:
        record["actionText"] = action_text
    if owner:
        record["owner"] = owner
    if due_at:
        record["dueAt"] = due_at
    if status:
        record["status"] = status

    return record


def load_rows(file_path: Path, delimiter: str) -> List[Dict[str, Any]]:
    """Load rows from a delimited file with headers."""
    with open(file_path, "r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        if not reader.fieldnames:
            raise ValueError("Missing header row in input file")
        return [row for row in reader]


def upload_actions(
    rows: List[Dict[str, Any]],
    api_token: Optional[str],
    dry_run: bool,
    merge_fields: List[str],
) -> Dict[str, Any]:
    """Prepare and upsert Actions records to Airtable."""
    print(f"Preparing {len(rows)} rows...")
    prepared_records: List[Dict[str, Any]] = []
    errors: List[str] = []

    for index, row in enumerate(rows, 1):
        try:
            prepared_records.append(prepare_action_record(row))
        except Exception as exc:
            errors.append(f"Row {index}: {exc}")

    print(f"Prepared {len(prepared_records)} records")
    if errors:
        print(f"Skipped {len(errors)} rows due to errors")

    if dry_run:
        print("Dry run: no records uploaded")
        print("Sample records:")
        for sample in prepared_records[:3]:
            print(json.dumps(sample, indent=2))
        return {
            "status": "dry_run",
            "total_rows": len(rows),
            "prepared_records": len(prepared_records),
            "errors": errors,
            "batches": (len(prepared_records) + 9) // 10,
        }

    if not api_token:
        raise ValueError("AIRTABLE_API_TOKEN is required for upload")
    if not prepared_records:
        raise ValueError("No prepared records to upload")

    if any(field not in prepared_records[0] for field in merge_fields):
        missing = [field for field in merge_fields if field not in prepared_records[0]]
        raise ValueError(f"Missing merge fields in records: {missing}")

    client = AirtableClient(api_token.strip(), BASE_ID)
    table_id = TABLES["Actions"]

    results = client.upsert_records(
        table_id,
        prepared_records,
        fields_to_merge_on=merge_fields,
        typecast=True,
    )

    uploaded = 0
    upload_errors: List[str] = []
    for batch_index, batch_result in enumerate(results, 1):
        if "records" in batch_result:
            uploaded += len(batch_result["records"])
        elif "error" in batch_result:
            upload_errors.append(f"Batch {batch_index}: {batch_result['error']}")

    return {
        "status": "success" if not upload_errors else "partial",
        "total_rows": len(rows),
        "prepared_records": len(prepared_records),
        "uploaded": uploaded,
        "batches": len(results),
        "errors": errors + upload_errors,
        "schemaVersion": "2025-12-25T00:32:52+0400",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload Actions from TSV/CSV")
    parser.add_argument(
        "--file",
        type=str,
        default="data/today_tomorrow_deliveries.tsv",
        help="Input TSV/CSV file path",
    )
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="Airtable PAT (defaults to AIRTABLE_API_TOKEN env var)",
    )
    parser.add_argument(
        "--delimiter",
        type=str,
        default="\\t",
        help="Field delimiter (default: tab)",
    )
    parser.add_argument(
        "--merge-on",
        action="append",
        default=["actionKey"],
        help="Field to merge on for upsert (repeatable, default: actionKey)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print sample output without uploading",
    )

    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"File not found: {file_path}")
        sys.exit(1)

    rows = load_rows(file_path, args.delimiter)
    api_token = args.token or os.getenv("AIRTABLE_API_TOKEN")

    try:
        result = upload_actions(rows, api_token, args.dry_run, args.merge_on)
        print(json.dumps(result, indent=2))
    except Exception as exc:
        print(f"Upload failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
