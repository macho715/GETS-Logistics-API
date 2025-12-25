"""
Unit tests for api/schema_validator.py
Covers schema loading, validation, and field suggestions.
"""

import json

import pytest

import api.schema_validator as schema_validator
from api.schema_validator import SchemaValidator


@pytest.fixture
def sample_schema_lock(tmp_path):
    """Create a schema lock file matching the expected structure."""
    schema = {
        "base": {"id": "appTEST123"},
        "generatedAt": "2025-12-25T00:00:00+0400",
        "tables": {
            "Shipments": {
                "id": "tblABC123",
                "name": "Shipments",
                "fields": {
                    "shptNo": {
                        "id": "fld001",
                        "name": "shptNo",
                        "type": "singleLineText",
                        "description": None,
                    },
                    "vendor": {
                        "id": "fld002",
                        "name": "vendor",
                        "type": "singleLineText",
                        "description": None,
                    },
                    "status": {
                        "id": "fld003",
                        "name": "status",
                        "type": "singleSelect",
                        "description": None,
                    },
                },
                "missingFields": ["missingField"],
            },
            "Documents": {
                "id": "tblDEF456",
                "name": "Documents",
                "fields": {
                    "docType": {
                        "id": "fld101",
                        "name": "docType",
                        "type": "singleLineText",
                        "description": None,
                    },
                    "status": {
                        "id": "fld102",
                        "name": "status",
                        "type": "singleSelect",
                        "description": None,
                    },
                },
            },
            "MissingTable": {"id": "tblMISSING", "missing": True},
        },
    }

    path = tmp_path / "airtable_schema.lock.json"
    path.write_text(json.dumps(schema))
    return str(path)


class TestSchemaValidatorInit:
    """Test schema validator initialization and metadata."""

    def test_init_loads_lock_file(self, sample_schema_lock):
        validator = SchemaValidator(lock_path=sample_schema_lock)

        assert validator.base_id == "appTEST123"
        assert validator.get_schema_version() == "2025-12-25T00:00:00+0400"
        assert set(validator.get_all_tables()) == {"Shipments", "Documents"}

    def test_init_missing_lock_raises(self, monkeypatch):
        monkeypatch.setattr(schema_validator.os.path, "exists", lambda _: False)

        with pytest.raises(FileNotFoundError):
            SchemaValidator()


class TestSchemaValidatorLookup:
    """Test table and field lookup helpers."""

    def test_get_table_id(self, sample_schema_lock):
        validator = SchemaValidator(lock_path=sample_schema_lock)

        assert validator.get_table_id("Shipments") == "tblABC123"
        assert validator.get_table_id("MissingTable") is None
        assert validator.get_table_id("Unknown") is None

    def test_get_valid_fields(self, sample_schema_lock):
        validator = SchemaValidator(lock_path=sample_schema_lock)

        assert validator.get_valid_fields("Shipments") == ["shptNo", "status", "vendor"]
        assert validator.get_valid_fields("Unknown") == []

    def test_get_missing_fields(self, sample_schema_lock):
        validator = SchemaValidator(lock_path=sample_schema_lock)

        assert validator.get_missing_fields("Shipments") == ["missingField"]
        assert validator.get_missing_fields("Unknown") == []

    def test_get_field_info(self, sample_schema_lock):
        validator = SchemaValidator(lock_path=sample_schema_lock)

        info = validator.get_field_info("Shipments", "shptNo")
        assert info["id"] == "fld001"
        assert info["type"] == "singleLineText"
        assert validator.get_field_info("MissingTable", "shptNo") is None
        assert validator.get_field_info("Shipments", "unknown") is None


class TestSchemaValidatorValidation:
    """Test field validation and suggestions."""

    def test_validate_fields_all_valid(self, sample_schema_lock):
        validator = SchemaValidator(lock_path=sample_schema_lock)

        record = {"shptNo": "SCT-0143", "vendor": "Samsung"}
        result = validator.validate_fields("Shipments", record)

        assert result["valid"] is True
        assert result["invalid_fields"] == []
        assert set(result["valid_fields"]) == {"shptNo", "vendor"}
        assert result["suggestions"] is None

    def test_validate_fields_with_invalid(self, sample_schema_lock):
        validator = SchemaValidator(lock_path=sample_schema_lock)

        record = {"SHPTNO": "SCT-0143", "vend": "Samsung"}
        result = validator.validate_fields("Shipments", record)

        assert result["valid"] is False
        assert set(result["invalid_fields"]) == {"SHPTNO", "vend"}
        assert "SHPTNO" in result["suggestions"]
        assert "vend" in result["suggestions"]
        assert "shptNo" in result["suggestions"]["SHPTNO"]
        assert "vendor" in result["suggestions"]["vend"]

    def test_validate_fields_unknown_table(self, sample_schema_lock):
        validator = SchemaValidator(lock_path=sample_schema_lock)

        record = {"field": "value"}
        result = validator.validate_fields("Unknown", record)

        assert result["valid"] is False
        assert result["invalid_fields"] == ["field"]
        assert result["table_id"] is None
        assert result["suggestions"] == {}
