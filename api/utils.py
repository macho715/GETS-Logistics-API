"""
Common utility functions for GETS API
Provides robust datetime parsing, timezone conversion, and field extraction
"""

from __future__ import annotations
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Optional, Dict, Any

DUBAI_TZ = ZoneInfo("Asia/Dubai")


def parse_iso_any(s: str | None) -> datetime | None:
    """
    Parse ISO datetime string, handling Z/UTC and naive formats

    Args:
        s: ISO datetime string (e.g., "2025-12-25T12:00:00.000Z" or "2025-12-25T16:00:00+04:00")

    Returns:
        datetime object in Asia/Dubai timezone, or None if parsing fails

    Examples:
        >>> parse_iso_any("2025-12-25T12:00:00.000Z")  # UTC with Z
        datetime.datetime(2025, 12, 25, 16, 0, tzinfo=ZoneInfo('Asia/Dubai'))

        >>> parse_iso_any("2025-12-25T16:00:00+04:00")  # Explicit timezone
        datetime.datetime(2025, 12, 25, 16, 0, tzinfo=ZoneInfo('Asia/Dubai'))

        >>> parse_iso_any("2025-12-25T12:00:00")  # Naive (assumed UTC)
        datetime.datetime(2025, 12, 25, 16, 0, tzinfo=ZoneInfo('Asia/Dubai'))
    """
    if not s:
        return None

    try:
        s = s.strip()

        # Airtable may return Z (UTC)
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"

        dt = datetime.fromisoformat(s)

        # If naive (no timezone), assume UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        # Convert to Dubai timezone
        return dt.astimezone(DUBAI_TZ)

    except (ValueError, AttributeError):
        return None


def iso_dubai(dt: datetime | None) -> str | None:
    """
    Convert datetime to ISO string in Asia/Dubai timezone

    Args:
        dt: datetime object (any timezone)

    Returns:
        ISO string in Asia/Dubai timezone, or None if dt is None

    Examples:
        >>> from datetime import datetime, timezone
        >>> dt = datetime(2025, 12, 25, 12, 0, 0, tzinfo=timezone.utc)
        >>> iso_dubai(dt)
        '2025-12-25T16:00:00+04:00'
    """
    if not dt:
        return None

    return dt.astimezone(DUBAI_TZ).isoformat(timespec="seconds")


def now_dubai() -> str:
    """
    Get current timestamp in Asia/Dubai timezone

    Returns:
        ISO string of current time in Asia/Dubai

    Examples:
        >>> now_dubai()
        '2025-12-25T16:30:45+04:00'
    """
    return datetime.now(DUBAI_TZ).isoformat(timespec="seconds")


def days_until(due: datetime | None, now: datetime) -> float | None:
    """
    Calculate days until due date (2 decimal precision)

    Args:
        due: Due date (datetime)
        now: Current time (datetime)

    Returns:
        Days until due (float, 2 decimals), negative if overdue, or None if due is None

    Examples:
        >>> from datetime import datetime
        >>> now = datetime(2025, 12, 25, 10, 0, 0, tzinfo=DUBAI_TZ)
        >>> due = datetime(2025, 12, 28, 16, 0, 0, tzinfo=DUBAI_TZ)
        >>> days_until(due, now)
        3.25
    """
    if not due:
        return None

    delta = due - now
    days = delta.total_seconds() / 86400.0
    return round(days, 2)


def classify_priority(days: float | None) -> str:
    """
    Classify approval priority based on days until due

    Args:
        days: Days until due (from days_until function)

    Returns:
        Priority level: OVERDUE, CRITICAL (D-5), HIGH (D-15), NORMAL, or UNKNOWN

    Classification:
        - OVERDUE: days < 0
        - CRITICAL: 0 <= days <= 5 (D-5)
        - HIGH: 5 < days <= 15 (D-15)
        - NORMAL: days > 15
        - UNKNOWN: days is None

    Examples:
        >>> classify_priority(-1.0)
        'OVERDUE'
        >>> classify_priority(3.0)
        'CRITICAL'
        >>> classify_priority(10.0)
        'HIGH'
        >>> classify_priority(20.0)
        'NORMAL'
    """
    if days is None:
        return "UNKNOWN"

    if days < 0:
        return "OVERDUE"

    if days <= 5:
        return "CRITICAL"

    if days <= 15:
        return "HIGH"

    return "NORMAL"


def extract_field_by_id(
    fields: Dict[str, Any],
    field_id: str,
    field_name: str = None
) -> Any:
    """
    Extract field value by ID (rename-safe), with fallback to field name

    This function provides rename-safety by prioritizing field IDs over field names.
    When Airtable API is called with returnFieldsByFieldId=true, response keys are
    field IDs (e.g., "fldABC123"). This function handles both formats gracefully.

    Args:
        fields: Airtable record fields dict
        field_id: Field ID (e.g., "fldABC123" from airtable_locked_config.FIELD_IDS)
        field_name: Optional field name for fallback (e.g., "shptNo")

    Returns:
        Field value, or None if not found

    Examples:
        >>> fields = {"fldABC123": "SCT-0143", "shptNo": "SCT-0143"}
        >>> extract_field_by_id(fields, "fldABC123", "shptNo")
        'SCT-0143'

        >>> fields = {"shptNo": "SCT-0143"}
        >>> extract_field_by_id(fields, "fldABC123", "shptNo")
        'SCT-0143'
    """
    # Priority 1: Field ID (rename-safe)
    if field_id and field_id in fields:
        return fields[field_id]

    # Priority 2: Field name (fallback)
    if field_name and field_name in fields:
        return fields[field_name]

    # Not found
    return None
