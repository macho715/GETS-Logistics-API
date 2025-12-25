"""
Common utilities for Airtable datetime parsing and timezone normalization
Handles Airtable's Z (UTC) format and ensures all times are Asia/Dubai (+04:00)
"""

from __future__ import annotations
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Optional, Dict, Any

DUBAI_TZ = ZoneInfo("Asia/Dubai")


def parse_iso_any(s: str | None) -> datetime | None:
    """
    Parse ISO datetime from Airtable (handles Z/UTC format)
    
    Airtable may return:
    - 2025-12-25T12:00:00.000Z (UTC)
    - 2025-12-25T12:00:00+04:00 (with timezone)
    - 2025-12-25T12:00:00 (naive, assume UTC)
    
    Always returns Asia/Dubai timezone
    
    Args:
        s: ISO datetime string from Airtable
    
    Returns:
        datetime in Asia/Dubai timezone, or None if input is None/invalid
    """
    if not s:
        return None
    
    s = s.strip()
    
    # Handle Z (UTC) suffix
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    
    # Parse ISO format
    try:
        dt = datetime.fromisoformat(s)
    except ValueError as e:
        print(f"⚠️ Failed to parse datetime: {s} - {e}")
        return None
    
    # If naive (no timezone), assume UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    # Convert to Dubai timezone
    return dt.astimezone(DUBAI_TZ)


def iso_dubai(dt: datetime | None) -> str | None:
    """
    Convert datetime to ISO string in Asia/Dubai timezone
    
    Args:
        dt: datetime object
    
    Returns:
        ISO string like "2025-12-25T16:00:00+04:00", or None if input is None
    """
    if not dt:
        return None
    return dt.astimezone(DUBAI_TZ).isoformat(timespec="seconds")


def now_dubai() -> str:
    """
    Current timestamp in Asia/Dubai timezone
    
    Returns:
        ISO string of current time in Dubai timezone
    """
    return iso_dubai(datetime.now(DUBAI_TZ))


def days_until(due: datetime | None, now: datetime) -> float | None:
    """
    Calculate days until due date (2 decimal precision)
    
    Args:
        due: Due date datetime
        now: Current datetime
    
    Returns:
        - Positive: days remaining
        - Negative: days overdue
        - None: no due date set
    """
    if not due:
        return None
    
    delta_seconds = (due - now).total_seconds()
    return round(delta_seconds / 86400.0, 2)


def classify_priority(days: float | None) -> str:
    """
    Classify approval priority based on days until due
    
    Categories:
    - OVERDUE: < 0 days
    - CRITICAL: 0-5 days (D-5)
    - HIGH: 6-15 days (D-15)
    - NORMAL: > 15 days
    - UNKNOWN: no due date
    
    Args:
        days: Days until due (from days_until())
    
    Returns:
        Priority level string
    """
    if days is None:
        return "UNKNOWN"
    
    if days < 0:
        return "OVERDUE"
    elif days <= 5:
        return "CRITICAL"
    elif days <= 15:
        return "HIGH"
    else:
        return "NORMAL"


def extract_field_by_id(fields: Dict[str, Any], field_id: str, field_name: str = None) -> Any:
    """
    Extract field value from Airtable response
    Supports both field name and field ID keys (rename-safe)
    
    Args:
        fields: Airtable record fields dict
        field_id: Field ID (e.g., "fldABC123")
        field_name: Field name (fallback, e.g., "shptNo")
    
    Returns:
        Field value or None
    """
    # Try field ID first (returnFieldsByFieldId=true)
    if field_id in fields:
        return fields[field_id]
    
    # Fallback to field name
    if field_name and field_name in fields:
        return fields[field_name]
    
    return None

