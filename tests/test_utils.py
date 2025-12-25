"""
Unit Tests for api/utils.py
Tests timezone parsing, datetime conversion, and priority classification
"""

import pytest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from api.utils import (
    parse_iso_any,
    iso_dubai,
    now_dubai,
    days_until,
    classify_priority,
    extract_field_by_id,
    DUBAI_TZ,
)


class TestParseIsoAny:
    """Test timezone parsing (handles Z/UTC format)"""
    
    def test_parse_z_utc_format(self):
        """Test Airtable Z (UTC) format parsing"""
        result = parse_iso_any("2025-12-25T12:00:00.000Z")
        
        assert result is not None
        assert result.tzinfo == DUBAI_TZ
        # UTC 12:00 = Dubai 16:00 (+04:00)
        assert result.hour == 16
    
    def test_parse_explicit_timezone(self):
        """Test explicit timezone format"""
        result = parse_iso_any("2025-12-25T16:00:00+04:00")
        
        assert result is not None
        assert result.tzinfo == DUBAI_TZ
        assert result.hour == 16
    
    def test_parse_naive_as_utc(self):
        """Test naive datetime (assume UTC)"""
        result = parse_iso_any("2025-12-25T12:00:00")
        
        assert result is not None
        assert result.tzinfo == DUBAI_TZ
        # Naive 12:00 treated as UTC = Dubai 16:00
        assert result.hour == 16
    
    def test_parse_none_returns_none(self):
        """Test None input returns None"""
        result = parse_iso_any(None)
        assert result is None
    
    def test_parse_empty_string_returns_none(self):
        """Test empty string returns None"""
        result = parse_iso_any("")
        assert result is None
    
    def test_parse_invalid_format_returns_none(self):
        """Test invalid format returns None"""
        result = parse_iso_any("not-a-date")
        assert result is None


class TestIsoDubai:
    """Test datetime to ISO string conversion"""
    
    def test_convert_datetime_to_iso(self):
        """Test datetime conversion to ISO string"""
        dt = datetime(2025, 12, 25, 16, 30, 0, tzinfo=DUBAI_TZ)
        result = iso_dubai(dt)
        
        assert result == "2025-12-25T16:30:00+04:00"
    
    def test_convert_none_returns_none(self):
        """Test None input returns None"""
        result = iso_dubai(None)
        assert result is None
    
    def test_convert_utc_to_dubai(self):
        """Test UTC datetime converted to Dubai timezone"""
        dt_utc = datetime(2025, 12, 25, 12, 0, 0, tzinfo=timezone.utc)
        result = iso_dubai(dt_utc)
        
        # UTC 12:00 = Dubai 16:00
        assert "16:00:00+04:00" in result


class TestNowDubai:
    """Test current timestamp in Dubai timezone"""
    
    def test_returns_valid_iso_string(self):
        """Test returns valid ISO string"""
        result = now_dubai()
        
        assert isinstance(result, str)
        assert "+04:00" in result
    
    def test_format_is_iso(self):
        """Test format is ISO 8601"""
        result = now_dubai()
        
        # Should be parseable back
        dt = datetime.fromisoformat(result)
        assert dt is not None


class TestDaysUntil:
    """Test days calculation (2 decimal precision)"""
    
    def test_returns_float_with_2_decimals(self):
        """Test daysUntilDue must be float with 2 decimals"""
        now = datetime(2025, 12, 25, 10, 0, 0, tzinfo=DUBAI_TZ)
        due = datetime(2025, 12, 28, 16, 0, 0, tzinfo=DUBAI_TZ)
        
        result = days_until(due, now)
        
        assert isinstance(result, float)
        # 3 days + 6 hours = 3.25 days
        assert 3.20 <= result <= 3.30
    
    def test_negative_days_for_overdue(self):
        """Test negative days for overdue dates"""
        now = datetime(2025, 12, 25, 10, 0, 0, tzinfo=DUBAI_TZ)
        due = datetime(2025, 12, 23, 10, 0, 0, tzinfo=DUBAI_TZ)
        
        result = days_until(due, now)
        
        assert result < 0
        assert result == -2.0
    
    def test_none_due_returns_none(self):
        """Test None due date returns None"""
        now = datetime(2025, 12, 25, 10, 0, 0, tzinfo=DUBAI_TZ)
        
        result = days_until(None, now)
        
        assert result is None
    
    def test_precision_is_2_decimals(self):
        """Test precision is exactly 2 decimal places"""
        now = datetime(2025, 12, 25, 10, 0, 0, tzinfo=DUBAI_TZ)
        due = datetime(2025, 12, 28, 16, 15, 0, tzinfo=DUBAI_TZ)
        
        result = days_until(due, now)
        
        # Check precision
        decimal_str = str(result).split(".")
        if len(decimal_str) > 1:
            assert len(decimal_str[1]) <= 2


class TestClassifyPriority:
    """Test D-5/D-15/Overdue classification"""
    
    @pytest.mark.parametrize("days,expected_priority", [
        (-1.0, "OVERDUE"),
        (-0.5, "OVERDUE"),
        (0.0, "CRITICAL"),
        (1.0, "CRITICAL"),
        (3.0, "CRITICAL"),
        (5.0, "CRITICAL"),
        (5.5, "HIGH"),
        (6.0, "HIGH"),
        (10.0, "HIGH"),
        (15.0, "HIGH"),
        (15.5, "NORMAL"),
        (16.0, "NORMAL"),
        (30.0, "NORMAL"),
    ])
    def test_classification_by_days(self, days, expected_priority):
        """Test priority classification for various day values"""
        result = classify_priority(days)
        assert result == expected_priority
    
    def test_none_returns_unknown(self):
        """Test None days returns UNKNOWN"""
        result = classify_priority(None)
        assert result == "UNKNOWN"


class TestExtractFieldById:
    """Test rename-safe field extraction"""
    
    def test_extracts_by_field_id(self):
        """Test extraction by field ID (primary)"""
        fields = {
            "fldABC123": "value_by_id",
            "fieldName": "value_by_name"
        }
        
        result = extract_field_by_id(fields, "fldABC123", "fieldName")
        
        assert result == "value_by_id"
    
    def test_fallback_to_field_name(self):
        """Test fallback to field name when ID not found"""
        fields = {
            "fieldName": "value_by_name"
        }
        
        result = extract_field_by_id(fields, "fldABC123", "fieldName")
        
        assert result == "value_by_name"
    
    def test_returns_none_when_not_found(self):
        """Test returns None when neither ID nor name found"""
        fields = {
            "otherField": "other_value"
        }
        
        result = extract_field_by_id(fields, "fldABC123", "fieldName")
        
        assert result is None
    
    def test_field_name_optional(self):
        """Test field name is optional"""
        fields = {
            "fldABC123": "value_by_id"
        }
        
        result = extract_field_by_id(fields, "fldABC123")
        
        assert result == "value_by_id"


class TestIntegration:
    """Integration tests for combined utility usage"""
    
    def test_parse_and_convert_roundtrip(self):
        """Test parse and convert roundtrip"""
        original = "2025-12-25T16:00:00+04:00"
        
        dt = parse_iso_any(original)
        result = iso_dubai(dt)
        
        assert result == "2025-12-25T16:00:00+04:00"
    
    def test_days_and_priority_workflow(self):
        """Test days calculation and priority classification workflow"""
        now = datetime(2025, 12, 25, 10, 0, 0, tzinfo=DUBAI_TZ)
        due = datetime(2025, 12, 28, 10, 0, 0, tzinfo=DUBAI_TZ)
        
        days = days_until(due, now)
        priority = classify_priority(days)
        
        assert days == 3.0
        assert priority == "CRITICAL"

