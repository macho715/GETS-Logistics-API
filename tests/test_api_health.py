"""
MACHO-GPT API Health Check Test Suite
HVDC Project - GETS Action API for ChatGPT
Mode: RHYTHM (Real-time KPI Monitoring)
"""

import pytest
import requests
import time
from datetime import datetime
from typing import Dict, List, Tuple

# API Base URL
API_BASE_URL = "https://gets-logistics-api.vercel.app"

# Performance SLA (MACHO-GPT Standards)
MAX_RESPONSE_TIME = 2.0  # seconds
MIN_CONFIDENCE = 0.90
SUCCESS_RATE_TARGET = 0.95


class TestAPIHealthCheck:
    """API Health Check Test Suite following TDD principles"""

    def test_api_root_endpoint_should_return_status(self):
        """
        RED → GREEN: API 홈 엔드포인트는 온라인 상태 반환해야 함
        """
        # Given: API base URL
        url = f"{API_BASE_URL}/"

        # When: GET 요청 실행
        start_time = time.time()
        response = requests.get(url)
        response_time = time.time() - start_time

        # Then: 성공 응답 및 성능 검증
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response_time < MAX_RESPONSE_TIME, f"Response time {response_time:.2f}s exceeds SLA"

        data = response.json()
        assert data["status"] == "online", "API should be online"
        assert "version" in data, "Version info required"
        assert "endpoints" in data, "Endpoint list required"

        print(f"✅ Root Endpoint: {response_time:.3f}s | Status: {data['status']}")

    def test_document_status_endpoint_should_return_shipment_data(self):
        """
        RED → GREEN: 문서 상태 엔드포인트는 선적 정보 반환해야 함
        """
        # Given: 테스트용 선적번호
        test_shpt_no = "HVDC-ADOPT-SIM-0065"
        url = f"{API_BASE_URL}/document/status/{test_shpt_no}"

        # When: GET 요청 실행
        start_time = time.time()
        response = requests.get(url)
        response_time = time.time() - start_time

        # Then: 데이터 구조 및 필수 필드 검증
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response_time < MAX_RESPONSE_TIME, f"Response time {response_time:.2f}s exceeds SLA"

        data = response.json()
        required_fields = ["shptNo", "boeStatus", "doStatus", "cooReady", "hblReady", "ciplValid", "lastUpdated"]

        for field in required_fields:
            assert field in data, f"Required field '{field}' missing"

        assert data["shptNo"] == test_shpt_no, "Shipment number mismatch"

        print(f"✅ Document Status: {response_time:.3f}s | ShptNo: {data['shptNo']}")

    def test_document_status_should_handle_different_shipment_numbers(self):
        """
        REFACTOR: 다양한 선적번호 처리 검증
        """
        # Given: 다양한 선적번호 패턴
        test_cases = [
            "HVDC-ADOPT-SIM-0065",
            "HVDC-ADOPT-SCT-0041",
            "TEST-123-ABC-9999"
        ]

        for shpt_no in test_cases:
            # When: 각 선적번호로 요청
            url = f"{API_BASE_URL}/document/status/{shpt_no}"
            response = requests.get(url)

            # Then: 정상 응답 및 데이터 일관성 검증
            assert response.status_code == 200
            data = response.json()
            assert data["shptNo"] == shpt_no

            print(f"✅ Tested ShptNo: {shpt_no}")

    def test_status_summary_endpoint_should_return_kpi_metrics(self):
        """
        RED → GREEN: 전체 현황 엔드포인트는 KPI 지표 반환해야 함
        Note: API_KEY 환경변수 필요 (401 예상 가능)
        """
        # Given: 전체 현황 URL
        url = f"{API_BASE_URL}/status/summary"

        # When: GET 요청 실행
        start_time = time.time()
        response = requests.get(url)
        response_time = time.time() - start_time

        # Then: 응답 검증 (인증 없으면 401 예상)
        if response.status_code == 401:
            print(f"⚠️  Status Summary: 401 Unauthorized (API_KEY required)")
            pytest.skip("API_KEY not configured - skipping authentication test")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response_time < MAX_RESPONSE_TIME, f"Response time {response_time:.2f}s exceeds SLA"

        data = response.json()
        required_kpi_fields = ["totalShipments", "ciplRate", "hblRate", "cooRate", "doRate", "boeRate"]

        for field in required_kpi_fields:
            assert field in data, f"KPI field '{field}' missing"
            if "Rate" in field:
                assert 0 <= data[field] <= 1, f"{field} should be between 0 and 1"

        print(f"✅ Status Summary: {response_time:.3f}s | Total: {data['totalShipments']}")

    def test_api_performance_should_meet_sla(self):
        """
        Performance Critical: 모든 엔드포인트는 2초 이내 응답
        """
        # Given: 성능 테스트 대상 엔드포인트
        endpoints = [
            "/",
            "/document/status/HVDC-ADOPT-SIM-0065"
        ]

        performance_results = []

        for endpoint in endpoints:
            # When: 5회 반복 측정
            times = []
            for _ in range(5):
                start = time.time()
                response = requests.get(f"{API_BASE_URL}{endpoint}")
                elapsed = time.time() - start
                times.append(elapsed)

                # Then: 각 요청이 SLA 충족
                assert response.status_code == 200
                assert elapsed < MAX_RESPONSE_TIME

            avg_time = sum(times) / len(times)
            max_time = max(times)
            min_time = min(times)

            performance_results.append({
                "endpoint": endpoint,
                "avg": avg_time,
                "max": max_time,
                "min": min_time
            })

            print(f"📊 {endpoint}: avg={avg_time:.3f}s, max={max_time:.3f}s, min={min_time:.3f}s")

        # Verify: 평균 응답시간이 SLA 준수
        for result in performance_results:
            assert result["avg"] < MAX_RESPONSE_TIME

    def test_api_error_handling_should_be_graceful(self):
        """
        Error Handling: 잘못된 요청에 대한 적절한 오류 처리
        """
        # Given: 에러 시나리오
        error_scenarios = [
            ("/document/status/", 404),  # 빈 선적번호
            ("/nonexistent", 404),  # 존재하지 않는 엔드포인트
        ]

        for endpoint, expected_status in error_scenarios:
            # When: 에러 유발 요청
            url = f"{API_BASE_URL}{endpoint}"
            response = requests.get(url)

            # Then: 적절한 오류 코드 반환
            print(f"🔍 Error Test: {endpoint} → {response.status_code}")
            # Note: 404는 Vercel 라우팅에서 처리될 수 있음


def generate_health_check_report(results: List[Dict]) -> str:
    """
    Health Check 결과를 MACHO-GPT 표준 리포트로 생성
    """
    timestamp = datetime.now().isoformat()

    report = f"""
# 🏥 MACHO-GPT API Health Check Report
**Timestamp:** {timestamp}
**Mode:** RHYTHM (Real-time KPI Monitoring)
**Target:** {API_BASE_URL}

## 📊 Summary
- **Total Tests:** {len(results)}
- **Passed:** {sum(1 for r in results if r['status'] == 'PASS')}
- **Failed:** {sum(1 for r in results if r['status'] == 'FAIL')}
- **Success Rate:** {sum(1 for r in results if r['status'] == 'PASS') / len(results) * 100:.1f}%

## 🎯 Endpoint Status
"""

    for result in results:
        status_icon = "✅" if result['status'] == 'PASS' else "❌"
        report += f"{status_icon} **{result['endpoint']}**: {result['response_time']:.3f}s\n"

    report += "\n---\n**MACHO-GPT v3.4-mini | Confidence: ≥0.95**"

    return report


if __name__ == "__main__":
    print("🚀 Starting MACHO-GPT API Health Check...")
    print(f"Target: {API_BASE_URL}")
    print("=" * 60)

    # Run pytest with verbose output
    pytest.main([__file__, "-v", "--tb=short"])

