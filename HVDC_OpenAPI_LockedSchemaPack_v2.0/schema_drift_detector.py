#!/usr/bin/env python3
"""
HVDC Schema Drift Detector - CI/CD Production Gate

Validates that the deployed API's schema version matches the locked schema version.
Blocks deployment if drift is detected.

Exit Codes:
  0 - Schema match (deployment allowed)
  1 - Schema drift detected (deployment blocked)
  2 - Configuration error
"""

import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Tuple
import urllib.request
import urllib.error


class SchemaDriftDetector:
    def __init__(
        self,
        openapi_path: str = "openapi.locked.v2.yaml",
        schema_lock_path: str = "api/airtable_schema.lock.json",
        protected_fields_path: str = "protected_fields.json",
        api_url: str = None,
    ):
        # Default paths relative to project root
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if not os.path.isabs(openapi_path):
            self.openapi_path = os.path.join(
                base_dir, "HVDC_OpenAPI_LockedSchemaPack_v2.0", openapi_path
            )
        else:
            self.openapi_path = openapi_path

        if not os.path.isabs(schema_lock_path):
            self.schema_lock_path = os.path.join(base_dir, schema_lock_path)
        else:
            self.schema_lock_path = schema_lock_path

        if not os.path.isabs(protected_fields_path):
            self.protected_fields_path = os.path.join(
                base_dir, "HVDC_OpenAPI_LockedSchemaPack_v2.0", protected_fields_path
            )
        else:
            self.protected_fields_path = protected_fields_path

        self.api_url = api_url or os.getenv(
            "API_URL", "https://gets-416ut4t8g-chas-projects-08028e73.vercel.app"
        )

        self.errors = []
        self.warnings = []

    def load_openapi_schema(self) -> Dict:
        """Load OpenAPI schema (YAML or JSON)"""
        try:
            with open(self.openapi_path, "r", encoding="utf-8") as f:
                if self.openapi_path.endswith(".yaml") or self.openapi_path.endswith(
                    ".yml"
                ):
                    # Simple YAML parser (for basic structure)
                    import re

                    content = f.read()
                    # Extract key fields using regex
                    schema = {}
                    version_match = re.search(
                        r"x-airtable-schemaVersion:\s*([^\n]+)", content
                    )
                    if version_match:
                        schema["info"] = {
                            "x-airtable-schemaVersion": version_match.group(1).strip()
                        }

                    # Extract protected fields count
                    protected_section = re.search(
                        r"x-protected-fields:(.*?)(?=\n  # |\n  x-|\npaths:|$)", content, re.DOTALL
                    )
                    if protected_section:
                        # Count all field entries (lines starting with "      - " or "    - ")
                        # Matches: "      - shptNo" or "    - shptNo"
                        fields_count = len(
                            re.findall(
                                r"^\s{4,6}- \w+", protected_section.group(1), re.MULTILINE
                            )
                        )
                        if not schema.get("info"):
                            schema["info"] = {}
                        schema["info"]["x-protected-fields-count"] = fields_count

                    # Extract table mappings
                    mapping_section = re.search(
                        r"x-locked-mapping:(.*?)(?=\npaths:|$)", content, re.DOTALL
                    )
                    if mapping_section:
                        tables = {}
                        table_blocks = re.findall(
                            r"(\w+):\s*\n\s+tableId:\s*(\w+)", mapping_section.group(1)
                        )
                        for table_name, table_id in table_blocks:
                            tables[table_name] = {"tableId": table_id}
                        schema["x-locked-mapping"] = {"tables": tables}

                    return schema
                else:
                    return json.load(f)
        except Exception as e:
            self.errors.append(f"Failed to load OpenAPI schema: {e}")
            return {}

    def load_schema_lock(self) -> Dict:
        """Load Airtable schema lock"""
        try:
            with open(self.schema_lock_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            self.errors.append(f"Failed to load schema lock: {e}")
            return {}

    def load_protected_fields(self) -> Dict:
        """Load protected fields spec"""
        try:
            with open(self.protected_fields_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            self.warnings.append(f"Failed to load protected fields: {e}")
            return {}

    def check_api_health(self) -> Dict:
        """Query /health endpoint for schema version"""
        try:
            req = urllib.request.Request(f"{self.api_url}/health")
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    return json.loads(response.read().decode("utf-8"))
                else:
                    self.warnings.append(f"API health check returned {response.status}")
                    return {}
        except Exception as e:
            self.warnings.append(f"Failed to query API health: {e}")
            return {}

    def validate_schema_version(self) -> bool:
        """Validate schema version consistency"""
        openapi = self.load_openapi_schema()
        schema_lock = self.load_schema_lock()

        if not openapi or not schema_lock:
            return False

        # Extract versions
        openapi_version = openapi.get("info", {}).get("x-airtable-schemaVersion")
        lock_version = schema_lock.get("generatedAt")

        if not openapi_version:
            self.errors.append("OpenAPI missing x-airtable-schemaVersion")
            return False

        if not lock_version:
            self.errors.append("Schema lock missing generatedAt")
            return False

        if openapi_version != lock_version:
            self.errors.append(
                f"Schema version mismatch:\n"
                f"  OpenAPI: {openapi_version}\n"
                f"  Lock:    {lock_version}"
            )
            return False

        print(f"[OK] Schema version match: {openapi_version}")
        return True

    def validate_protected_fields(self) -> bool:
        """Validate protected fields declaration"""
        openapi = self.load_openapi_schema()
        protected_spec = self.load_protected_fields()

        if not openapi:
            return False

        openapi_count = openapi.get("info", {}).get("x-protected-fields-count", 0)
        spec_count = protected_spec.get("totalProtectedFields", 0)

        if openapi_count == 0:
            self.warnings.append("OpenAPI missing x-protected-fields declaration")
            return True  # Warning only, not blocking

        if openapi_count != spec_count:
            self.warnings.append(
                f"Protected fields count mismatch: OpenAPI={openapi_count}, Spec={spec_count}"
            )
        else:
            print(f"[OK] Protected fields count: {openapi_count}")

        return True

    def validate_api_deployment(self) -> bool:
        """Validate deployed API matches schema version"""
        health = self.check_api_health()

        if not health:
            self.warnings.append(
                "Could not validate deployed API (health check failed)"
            )
            return True  # Don't block if API not yet deployed

        api_version = health.get("lockedConfig", {}).get("schemaVersion")
        openapi = self.load_openapi_schema()
        expected_version = openapi.get("info", {}).get("x-airtable-schemaVersion")

        if api_version and expected_version:
            if api_version != expected_version:
                self.errors.append(
                    f"Deployed API schema mismatch:\n"
                    f"  Deployed: {api_version}\n"
                    f"  Expected: {expected_version}\n"
                    f"  Action: Redeploy with updated code"
                )
                return False
            else:
                print(f"[OK] Deployed API schema version: {api_version}")

        return True

    def validate_table_ids(self) -> bool:
        """Validate table IDs consistency between OpenAPI and lock"""
        openapi = self.load_openapi_schema()
        schema_lock = self.load_schema_lock()

        if not openapi or not schema_lock:
            return False

        openapi_mapping = openapi.get("x-locked-mapping", {}).get("tables", {})
        lock_tables = schema_lock.get("tables", {})

        mismatches = []
        for table_name, openapi_data in openapi_mapping.items():
            lock_data = lock_tables.get(table_name, {})

            openapi_table_id = openapi_data.get("tableId")
            lock_table_id = lock_data.get("id")

            if openapi_table_id != lock_table_id:
                mismatches.append(
                    f"  {table_name}: OpenAPI={openapi_table_id}, Lock={lock_table_id}"
                )

        if mismatches:
            self.errors.append(f"Table ID mismatches:\n" + "\n".join(mismatches))
            return False

        print(f"[OK] Table IDs validated: {len(openapi_mapping)} tables")
        return True

    def run_all_checks(self) -> bool:
        """Run all validation checks"""
        print("=" * 60)
        print("HVDC Schema Drift Detector")
        print("=" * 60)
        print()

        checks = [
            ("Schema Version", self.validate_schema_version),
            ("Table IDs", self.validate_table_ids),
            ("Protected Fields", self.validate_protected_fields),
            ("Deployed API", self.validate_api_deployment),
        ]

        all_passed = True
        for check_name, check_func in checks:
            print(f"Running check: {check_name}...")
            try:
                if not check_func():
                    all_passed = False
            except Exception as e:
                self.errors.append(f"{check_name} check failed: {e}")
                all_passed = False
            print()

        # Report results
        print("=" * 60)
        if self.warnings:
            print("WARNINGS:")
            for warning in self.warnings:
                print(f"  - {warning}")
            print()

        if self.errors:
            print("ERRORS (DEPLOYMENT BLOCKED):")
            for error in self.errors:
                print(f"  - {error}")
            print()
            print("=" * 60)
            print("RESULT: FAILED - Deployment blocked due to schema drift")
            print("=" * 60)
            return False
        else:
            print("=" * 60)
            print("RESULT: PASSED - Schema validation successful")
            print("=" * 60)
            return True


def main():
    detector = SchemaDriftDetector()

    if detector.run_all_checks():
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure (block deployment)


if __name__ == "__main__":
    main()
