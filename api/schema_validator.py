"""
Schema Validator for Airtable Integration

Validates API requests against locked Airtable schema to prevent:
- UNKNOWN_FIELD_NAME errors (422)
- Field name typos
- Missing required fields

Based on: HVDC_Airtable_LockAndMappingGenPack_2025-12-24
"""

import json
import os
from typing import Dict, List, Optional, Set
from pathlib import Path


class SchemaValidator:
    """
    Validate API requests against Airtable schema lock

    Features:
    - Field name validation
    - Table ID lookup
    - Fuzzy field name suggestions
    - Missing field detection
    """

    def __init__(self, lock_path: Optional[str] = None):
        """
        Initialize validator with schema lock file

        Args:
            lock_path: Path to airtable_schema.lock.json
                      If None, searches common locations

        Raises:
            FileNotFoundError: If lock file not found
        """
        if lock_path is None:
            # Try common locations
            candidates = [
                os.getenv("AIRTABLE_SCHEMA_LOCK_PATH"),
                os.path.join(os.path.dirname(__file__), "airtable_schema.lock.json"),
                "api/airtable_schema.lock.json",
                "airtable_schema.lock.json",
                "../airtable_schema.lock.json",
                "out/airtable_schema.lock.json",
                os.path.join(
                    os.path.dirname(__file__), "..", "airtable_schema.lock.json"
                ),
            ]

            for path in candidates:
                if path and os.path.exists(path):
                    lock_path = path
                    break

        if not lock_path or not os.path.exists(lock_path):
            raise FileNotFoundError(
                "Schema lock file not found. Run lock_schema_and_generate_mapping.py first. "
                "Searched locations: " + ", ".join([str(c) for c in candidates if c])
            )

        with open(lock_path, encoding="utf-8") as f:
            self.lock = json.load(f)

        self.base_id = self.lock["base"]["id"]
        self._build_lookup_tables()

    def _build_lookup_tables(self):
        """Build fast lookup tables for validation"""
        self._table_fields: Dict[str, Set[str]] = {}
        self._table_ids: Dict[str, str] = {}

        for table_name, table_info in self.lock["tables"].items():
            if table_info.get("missing"):
                continue

            # Store table ID
            self._table_ids[table_name] = table_info.get("id")

            # Store field names
            fields = table_info.get("fields", {})
            self._table_fields[table_name] = set(fields.keys())

    def get_table_id(self, table_name: str) -> Optional[str]:
        """
        Get table ID from lock file

        Args:
            table_name: Name of the table (case-sensitive)

        Returns:
            Table ID (tbl...) or None if not found
        """
        return self._table_ids.get(table_name)

    def get_valid_fields(self, table_name: str) -> List[str]:
        """
        Get list of valid field names for a table

        Args:
            table_name: Name of the table

        Returns:
            List of valid field names (sorted)
        """
        return sorted(self._table_fields.get(table_name, []))

    def validate_fields(self, table_name: str, record: Dict) -> Dict:
        """
        Validate record fields against schema

        Args:
            table_name: Name of the table
            record: Dict of field names to values

        Returns:
            {
                "valid": bool,
                "invalid_fields": List[str],
                "valid_fields": List[str],
                "table_id": str or None,
                "suggestions": Dict[str, str] or None
            }
        """
        valid_fields = self._table_fields.get(table_name, set())
        record_fields = set(record.keys())

        invalid = list(record_fields - valid_fields)

        return {
            "valid": len(invalid) == 0,
            "invalid_fields": invalid,
            "valid_fields": list(record_fields & valid_fields),
            "table_id": self.get_table_id(table_name),
            "suggestions": (
                self._suggest_fields(table_name, invalid) if invalid else None
            ),
        }

    def _suggest_fields(
        self, table_name: str, invalid_fields: List[str]
    ) -> Dict[str, List[str]]:
        """
        Suggest correct field names for invalid fields (fuzzy match)

        Args:
            table_name: Name of the table
            invalid_fields: List of invalid field names

        Returns:
            Dict mapping invalid field name to list of suggestions
        """
        valid = self._table_fields.get(table_name, set())
        suggestions = {}

        for invalid in invalid_fields:
            # Simple fuzzy match (case-insensitive, partial match)
            invalid_lower = invalid.lower()
            matches = []

            for field in valid:
                field_lower = field.lower()

                # Exact match (case-insensitive)
                if invalid_lower == field_lower:
                    matches.insert(0, field)  # Priority
                # Substring match
                elif invalid_lower in field_lower or field_lower in invalid_lower:
                    matches.append(field)
                # Starts with match
                elif field_lower.startswith(invalid_lower) or invalid_lower.startswith(
                    field_lower
                ):
                    matches.append(field)

            if matches:
                suggestions[invalid] = matches[:3]  # Top 3 matches

        return suggestions

    def get_schema_version(self) -> str:
        """Get schema lock timestamp"""
        return self.lock.get("generatedAt", "unknown")

    def get_missing_fields(self, table_name: str) -> List[str]:
        """
        Get list of fields that were expected but missing in Airtable

        Args:
            table_name: Name of the table

        Returns:
            List of missing field names
        """
        table = self.lock["tables"].get(table_name, {})
        return table.get("missingFields", [])

    def get_all_tables(self) -> List[str]:
        """Get list of all table names"""
        return list(self._table_ids.keys())

    def get_field_info(self, table_name: str, field_name: str) -> Optional[Dict]:
        """
        Get detailed field information

        Args:
            table_name: Name of the table
            field_name: Name of the field

        Returns:
            Field info dict with id, name, type, description
            or None if not found
        """
        table = self.lock["tables"].get(table_name, {})
        if table.get("missing"):
            return None

        fields = table.get("fields", {})
        return fields.get(field_name)
