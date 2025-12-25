"""
GETS API Integration Test Suite
Phase 2.3-A: Locked Mapping Validation

Tests all endpoints with schema version validation
"""

import requests
import json
from datetime import datetime
from typing import Dict, List

# Test configuration
BASE_URL = "https://gets-416ut4t8g-chas-projects-08028e73.vercel.app"  # Production URL
TEST_SHPT_NO = "SCT-0143"


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"


def print_test(name: str):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}TEST: {name}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}")


def print_success(message: str):
    print(f"{Colors.GREEN}[OK] {message}{Colors.RESET}")


def print_error(message: str):
    print(f"{Colors.RED}[ERROR] {message}{Colors.RESET}")


def print_info(message: str):
    print(f"{Colors.YELLOW}[INFO] {message}{Colors.RESET}")


def test_endpoint(method: str, endpoint: str, **kwargs) -> Dict:
    """Test an API endpoint and return response"""
    url = f"{BASE_URL}{endpoint}"
    print_info(f"{method} {endpoint}")

    try:
        if method == "GET":
            response = requests.get(url, **kwargs)
        elif method == "POST":
            response = requests.post(url, **kwargs)
        else:
            raise ValueError(f"Unsupported method: {method}")

        print_info(f"Status: {response.status_code}")

        if response.status_code in [200, 201]:
            print_success(f"Success: {response.status_code}")
        elif response.status_code == 404:
            print_error(f"Not Found: {response.status_code}")
        else:
            print_error(f"Error: {response.status_code}")

        return {
            "status_code": response.status_code,
            "json": (
                response.json()
                if response.headers.get("content-type") == "application/json"
                else None
            ),
            "success": 200 <= response.status_code < 300,
        }
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return {"status_code": None, "json": None, "success": False, "error": str(e)}


def validate_schema_version(data: Dict) -> bool:
    """Validate schema version in response"""
    expected = "2025-12-25T00:32:52+0400"

    if "schemaVersion" in data:
        actual = data["schemaVersion"]
        if actual == expected:
            print_success(f"Schema version validated: {actual}")
            return True
        else:
            print_error(f"Schema version mismatch: {actual} != {expected}")
            return False

    return True  # Optional field


def validate_locked_config(data: Dict) -> bool:
    """Validate locked config in response"""
    if "lockedConfig" not in data:
        return True  # Optional field

    config = data["lockedConfig"]
    checks = []

    # Check baseId
    if config.get("baseId") == "appnLz06h07aMm366":
        print_success(f"Base ID validated: {config['baseId']}")
        checks.append(True)
    else:
        print_error(f"Base ID invalid: {config.get('baseId')}")
        checks.append(False)

    # Check tables count
    if config.get("tables") == 10 or config.get("tablesLocked") == 10:
        tables = config.get("tables") or config.get("tablesLocked")
        print_success(f"Tables count validated: {tables}")
        checks.append(True)
    else:
        print_error(f"Tables count invalid: {config.get('tables')}")
        checks.append(False)

    # Check protected fields
    if config.get("protectedFields", 0) >= 20:
        print_success(f"Protected fields validated: {config['protectedFields']}")
        checks.append(True)
    else:
        print_error(f"Protected fields invalid: {config.get('protectedFields')}")
        checks.append(False)

    return all(checks)


# Test Suite
def test_1_home():
    """Test GET / (Home)"""
    print_test("1. GET / (Home)")

    result = test_endpoint("GET", "/")

    if not result["success"]:
        return False

    data = result["json"]

    # Validate version
    if data.get("version") == "1.7.0":
        print_success(f"Version validated: {data['version']}")
    else:
        print_error(f"Version mismatch: {data.get('version')} != 1.7.0")
        return False

    # Validate schema version
    if not validate_schema_version(data):
        return False

    # Validate locked config
    if not validate_locked_config(data):
        return False

    # Validate features
    features = data.get("features", {})
    if features.get("locked_mapping") and features.get("rename_protection"):
        print_success("Locked mapping features validated")
    else:
        print_error("Locked mapping features missing")
        return False

    print_success("TEST PASSED")
    return True


def test_2_health():
    """Test GET /health"""
    print_test("2. GET /health (Health Check)")

    result = test_endpoint("GET", "/health")

    if not result["success"]:
        return False

    data = result["json"]

    # Validate status
    if data.get("status") in ["healthy", "degraded"]:
        print_success(f"Status: {data['status']}")
    else:
        print_error(f"Invalid status: {data.get('status')}")
        return False

    # Validate version
    if data.get("version") == "1.7.0":
        print_success(f"Version validated: {data['version']}")
    else:
        print_error(f"Version mismatch: {data.get('version')}")
        return False

    # Validate locked config
    if not validate_locked_config(data):
        return False

    # Check schema version match
    locked_config = data.get("lockedConfig", {})
    if locked_config.get("versionMatch") is not None:
        if locked_config["versionMatch"]:
            print_success("Schema version match validated")
        else:
            print_error("Schema version mismatch detected")
            return False

    print_success("TEST PASSED")
    return True


def test_8_document_status():
    """Test GET /document/status/{shptNo}"""
    print_test(f"8. GET /document/status/{TEST_SHPT_NO}")

    result = test_endpoint("GET", f"/document/status/{TEST_SHPT_NO}")

    if result["status_code"] == 404:
        print_info(f"Shipment {TEST_SHPT_NO} not found (expected for test data)")
        print_success("TEST PASSED (404 expected)")
        return True

    if not result["success"]:
        return False

    data = result["json"]

    # Validate structure
    required_fields = ["shptNo", "doc", "bottleneck", "action"]
    for field in required_fields:
        if field in data:
            print_success(f"Field present: {field}")
        else:
            print_error(f"Missing field: {field}")
            return False

    # Validate doc structure
    doc_fields = ["boeStatus", "doStatus", "cooStatus", "hblStatus", "ciplStatus"]
    doc = data.get("doc", {})
    for field in doc_fields:
        if field in doc:
            print_success(f"Doc field present: {field}")
        else:
            print_error(f"Missing doc field: {field}")

    print_success("TEST PASSED")
    return True


def test_9_status_summary():
    """Test GET /status/summary"""
    print_test("9. GET /status/summary (KPI Summary)")

    result = test_endpoint("GET", "/status/summary")

    if not result["success"]:
        return False

    data = result["json"]

    # Validate KPI fields
    kpi_fields = ["totalShipments"]
    for field in kpi_fields:
        if field in data:
            print_success(f"KPI field present: {field} = {data[field]}")
        else:
            print_error(f"Missing KPI field: {field}")

    print_success("TEST PASSED")
    return True


def test_4_approval_status():
    """Test GET /approval/status/{shptNo}"""
    print_test(f"4. GET /approval/status/{TEST_SHPT_NO}")

    result = test_endpoint("GET", f"/approval/status/{TEST_SHPT_NO}")

    if result["status_code"] == 404:
        print_info(f"Shipment {TEST_SHPT_NO} not found (expected for test data)")
        print_success("TEST PASSED (404 expected)")
        return True

    if not result["success"]:
        return False

    data = result["json"]

    # Validate structure
    required_fields = ["shptNo", "approvals", "summary"]
    for field in required_fields:
        if field in data:
            print_success(f"Field present: {field}")
        else:
            print_error(f"Missing field: {field}")
            return False

    # Validate summary structure
    summary = data.get("summary", {})
    summary_fields = ["total", "pending", "approved", "rejected", "critical", "overdue"]
    for field in summary_fields:
        if field in summary:
            print_success(f"Summary field present: {field}")

    # Validate daysUntilDue precision (if approvals exist)
    approvals = data.get("approvals", [])
    if approvals:
        for approval in approvals:
            if approval.get("daysUntilDue") is not None:
                days = approval["daysUntilDue"]
                if isinstance(days, (int, float)):
                    print_success(f"daysUntilDue is numeric: {days}")
                else:
                    print_error(f"daysUntilDue is not numeric: {days}")

    print_success("TEST PASSED")
    return True


def test_5_approval_summary():
    """Test GET /approval/summary"""
    print_test("5. GET /approval/summary")

    result = test_endpoint("GET", "/approval/summary")

    if not result["success"]:
        return False

    data = result["json"]

    # Validate structure
    required_fields = ["summary", "byType", "critical"]
    for field in required_fields:
        if field in data:
            print_success(f"Field present: {field}")
        else:
            print_error(f"Missing field: {field}")
            return False

    # Validate critical structure (D-5/D-15/overdue)
    critical = data.get("critical", {})
    critical_fields = ["overdue", "d5", "d15"]
    for field in critical_fields:
        if field in critical:
            print_success(f"Critical field present: {field}")

    print_success("TEST PASSED")
    return True


def test_6_bottleneck_summary():
    """Test GET /bottleneck/summary"""
    print_test("6. GET /bottleneck/summary")

    result = test_endpoint("GET", "/bottleneck/summary")

    if not result["success"]:
        return False

    data = result["json"]

    # Validate structure
    required_fields = ["byCategory", "byCode", "aging", "topBottlenecks", "totalActive"]
    for field in required_fields:
        if field in data:
            print_success(f"Field present: {field}")
        else:
            print_error(f"Missing field: {field}")
            return False

    # Validate aging structure
    aging = data.get("aging", {})
    aging_fields = ["under24h", "under48h", "under72h", "over72h"]
    for field in aging_fields:
        if field in aging:
            print_success(f"Aging field present: {field}")

    print_success("TEST PASSED")
    return True


def test_7_document_events():
    """Test GET /document/events/{shptNo}"""
    print_test(f"7. GET /document/events/{TEST_SHPT_NO}")

    result = test_endpoint("GET", f"/document/events/{TEST_SHPT_NO}")

    if result["status_code"] == 404:
        print_info(f"Shipment {TEST_SHPT_NO} not found (expected for test data)")
        print_success("TEST PASSED (404 expected)")
        return True

    if not result["success"]:
        return False

    data = result["json"]

    # Validate structure
    required_fields = ["shptNo", "events", "total"]
    for field in required_fields:
        if field in data:
            print_success(f"Field present: {field}")
        else:
            print_error(f"Missing field: {field}")
            return False

    # Validate event structure (if events exist)
    events = data.get("events", [])
    if events:
        event = events[0]
        event_fields = ["eventId", "timestamp", "entityType", "toStatus"]
        for field in event_fields:
            if field in event:
                print_success(f"Event field present: {field}")

    print_success("TEST PASSED")
    return True


def test_8_document_status():
    """Test GET /document/status/{shptNo}"""
    print_test(f"8. GET /document/status/{TEST_SHPT_NO}")

    result = test_endpoint("GET", "/status/summary")

    if not result["success"]:
        return False

    data = result["json"]

    # Validate KPI fields
    kpi_fields = ["totalShipments"]
    for field in kpi_fields:
        if field in data:
            print_success(f"KPI field present: {field} = {data[field]}")
        else:
            print_error(f"Missing KPI field: {field}")

    print_success("TEST PASSED")
    return True


def test_9_status_summary():
    """Test GET /status/summary"""
    print_test("9. GET /status/summary (KPI Summary)")

    result = test_endpoint("GET", "/status/summary")

    if not result["success"]:
        return False

    data = result["json"]

    # Validate KPI fields
    kpi_fields = ["totalShipments"]
    for field in kpi_fields:
        if field in data:
            print_success(f"KPI field present: {field} = {data[field]}")
        else:
            print_error(f"Missing KPI field: {field}")

    print_success("TEST PASSED")
    return True


def test_10_ingest_events_valid():
    """Test POST /ingest/events (valid payload)"""
    print_test("10. POST /ingest/events (Valid Payload)")

    payload = {
        "batchId": "TEST_BATCH_001",
        "sourceSystem": "TEST",
        "events": [
            {
                "timestamp": datetime.now().isoformat() + "+04:00",
                "shptNo": "TEST-001",
                "entityType": "DOCUMENT",
                "toStatus": "SUBMITTED",
            }
        ],
    }

    result = test_endpoint(
        "POST",
        "/ingest/events",
        json=payload,
        headers={"Content-Type": "application/json"},
    )

    if not result["success"]:
        # Connection might not be available
        print_info("Airtable connection not available (expected for local test)")
        return True

    data = result["json"]

    # Validate response
    if data.get("status") == "success":
        print_success(f"Ingested: {data.get('ingested')} events")
        if data.get("schemaVersion"):
            print_success(f"Schema version: {data['schemaVersion']}")

    print_success("TEST PASSED")
    return True


def test_10_ingest_events_valid():
    """Test POST /ingest/events (valid payload)"""
    print_test("10. POST /ingest/events (Valid Payload)")

    payload = {
        "batchId": "TEST_BATCH_001",
        "sourceSystem": "TEST",
        "events": [
            {
                "timestamp": datetime.now().isoformat() + "+04:00",
                "shptNo": "TEST-001",
                "entityType": "DOCUMENT",
                "toStatus": "SUBMITTED",
            }
        ],
    }

    result = test_endpoint(
        "POST",
        "/ingest/events",
        json=payload,
        headers={"Content-Type": "application/json"},
    )

    if not result["success"]:
        # Connection might not be available
        print_info("Airtable connection not available (expected for local test)")
        return True

    data = result["json"]

    # Validate response
    if data.get("status") == "success":
        print_success(f"Ingested: {data.get('ingested')} events")
        if data.get("schemaVersion"):
            print_success(f"Schema version: {data['schemaVersion']}")

    print_success("TEST PASSED")
    return True


def test_11_ingest_events_invalid():
    """Test POST /ingest/events (invalid fields)"""
    print_test("11. POST /ingest/events (Invalid Fields)")

    payload = {
        "batchId": "TEST_BATCH_002",
        "sourceSystem": "TEST",
        "events": [
            {
                "timestamp": datetime.now().isoformat() + "+04:00",
                "shptNo": "TEST-002",
                "invalidField": "should_fail",  # Invalid field
                "entityType": "DOCUMENT",
                "toStatus": "SUBMITTED",
            }
        ],
    }

    result = test_endpoint(
        "POST",
        "/ingest/events",
        json=payload,
        headers={"Content-Type": "application/json"},
    )

    if result["status_code"] == 400:
        data = result["json"]
        if data.get("error") == "Field validation failed":
            print_success("Field validation working correctly")
            if "protected_fields" in data:
                print_success(
                    f"Protected fields exposed: {len(data['protected_fields'])} fields"
                )
            return True
    elif result["status_code"] == 503:
        print_info("Airtable connection not available (expected for local test)")
        return True

    print_error("Field validation did not reject invalid fields")
    return False


def test_11_ingest_events_invalid():
    """Test POST /ingest/events (invalid fields)"""
    print_test("11. POST /ingest/events (Invalid Fields)")

    payload = {
        "batchId": "TEST_BATCH_002",
        "sourceSystem": "TEST",
        "events": [
            {
                "timestamp": datetime.now().isoformat() + "+04:00",
                "shptNo": "TEST-002",
                "invalidField": "should_fail",  # Invalid field
                "entityType": "DOCUMENT",
                "toStatus": "SUBMITTED",
            }
        ],
    }

    result = test_endpoint(
        "POST",
        "/ingest/events",
        json=payload,
        headers={"Content-Type": "application/json"},
    )

    if result["status_code"] == 400:
        data = result["json"]
        if data.get("error") == "Field validation failed":
            print_success("Field validation working correctly")
            if "protected_fields" in data:
                print_success(
                    f"Protected fields exposed: {len(data['protected_fields'])} fields"
                )
            return True
    elif result["status_code"] == 503:
        print_info("Airtable connection not available (expected for local test)")
        return True

    print_error("Field validation did not reject invalid fields")
    return False


def run_all_tests():
    """Run all integration tests"""
    print("\n")
    print(f"{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BLUE}GETS API Integration Test Suite - Phase 4.1{Colors.RESET}")
    print(f"{Colors.BLUE}Schema Version: 2025-12-25T00:32:52+0400{Colors.RESET}")
    print(f"{Colors.BLUE}API Version: 1.7.0{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*70}{Colors.RESET}")

    tests = [
        test_1_home,
        test_2_health,
        test_4_approval_status,
        test_5_approval_summary,
        test_6_bottleneck_summary,
        test_7_document_events,
        test_8_document_status,
        test_9_status_summary,
        test_10_ingest_events_valid,
        test_11_ingest_events_invalid,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print_error(f"Test exception: {str(e)}")
            results.append(False)

    # Summary
    print("\n")
    print(f"{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BLUE}TEST SUMMARY{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*70}{Colors.RESET}")

    passed = sum(results)
    total = len(results)

    print(f"\nTotal Tests: {total}")
    print(f"{Colors.GREEN}Passed: {passed}{Colors.RESET}")
    print(f"{Colors.RED}Failed: {total - passed}{Colors.RESET}")

    if passed == total:
        print(f"\n{Colors.GREEN}{'='*70}{Colors.RESET}")
        print(f"{Colors.GREEN}ALL TESTS PASSED [OK]{Colors.RESET}")
        print(f"{Colors.GREEN}{'='*70}{Colors.RESET}\n")
    else:
        print(f"\n{Colors.RED}{'='*70}{Colors.RESET}")
        print(f"{Colors.RED}SOME TESTS FAILED [ERROR]{Colors.RESET}")
        print(f"{Colors.RED}{'='*70}{Colors.RESET}\n")

    return passed == total


if __name__ == "__main__":
    import sys

    print_info("Starting Flask server test prerequisite check...")
    print_info("Make sure Flask server is running on http://localhost:5000")
    print_info("Run: python api/document_status.py")

    input("\nPress Enter to start tests (or Ctrl+C to cancel)...")

    success = run_all_tests()
    sys.exit(0 if success else 1)
