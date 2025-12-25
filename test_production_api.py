"""
Production API Test Script
Tests all GETS API endpoints on Vercel
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://gets-416ut4t8g-chas-projects-08028e73.vercel.app"


def test_endpoint(method, path, description):
    """Test a single endpoint"""
    url = f"{BASE_URL}{path}"
    print(f"\n{'='*60}")
    print(f"Testing: {method} {path}")
    print(f"Description: {description}")
    print(f"{'='*60}")

    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json={}, timeout=10)

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            try:
                data = response.json()
                print(f"[OK] Success - Response preview:")
                print(json.dumps(data, indent=2)[:500] + "...")
                return True
            except:
                print(f"[OK] Success - Response length: {len(response.text)} bytes")
                return True
        else:
            print(f"[FAIL] Failed - {response.status_code}")
            print(response.text[:200])
            return False

    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False


def main():
    print(f"\n{'#'*60}")
    print(f"# GETS API Production Test")
    print(f"# Time: {datetime.now().isoformat()}")
    print(f"# Base URL: {BASE_URL}")
    print(f"{'#'*60}\n")

    tests = [
        ("GET", "/", "API Info"),
        ("GET", "/health", "Health Check"),
        ("GET", "/bottleneck/summary", "Bottleneck Summary"),
        ("GET", "/status/summary", "KPI Summary"),
        ("GET", "/document/status/SCT-0143", "Document Status"),
        ("GET", "/approval/status/SCT-0143", "Approval Status"),
        ("GET", "/document/events/SCT-0143", "Event History"),
        ("GET", "/openapi-schema.yaml", "OpenAPI Schema"),
        ("GET", "/api/docs", "Swagger UI"),
    ]

    results = []
    for method, path, desc in tests:
        success = test_endpoint(method, path, desc)
        results.append((path, success))

    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for path, success in results:
        status = "[OK]" if success else "[FAIL]"
        print(f"{status} {path}")

    print(f"\nTotal: {passed}/{total} passed ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n[SUCCESS] All tests passed! API is ready for ChatGPT Actions.")
    elif passed >= total * 0.7:
        print("\n[WARNING] Most tests passed. Review failures before integration.")
    else:
        print("\n[ERROR] Many tests failed. Fix issues before ChatGPT integration.")


if __name__ == "__main__":
    main()
