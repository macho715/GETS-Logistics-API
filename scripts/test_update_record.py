#!/usr/bin/env python3
"""
Airtable updateRecord 간단한 테스트 스크립트
실제 API를 호출하여 request body 구조 검증

사용법:
  $env:AIRTABLE_API_TOKEN='pat...' python scripts/test_update_record.py
"""

import json
import os
import sys
from typing import Dict, Any, Optional
import requests

# UTF-8 인코딩 설정 (Windows)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    os.environ["PYTHONIOENCODING"] = "utf-8"

API_ROOT = "https://api.airtable.com/v0"
BASE_ID = "appnLz06h07aMm366"
TEST_TABLE = "Shipments"  # 테스트용 테이블

def req_headers(token: str) -> Dict[str, str]:
    """Airtable API 헤더"""
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

def get_test_record_id(pat: str, base_id: str, table_name: str, shpt_no: str) -> Optional[str]:
    """테스트용 record ID 가져오기"""
    url = f"{API_ROOT}/{base_id}/{table_name}"
    headers = req_headers(pat)

    # UPPER({shptNo}) 사용하여 대소문자 무시
    params = {
        "filterByFormula": f"UPPER({{shptNo}})='{shpt_no.upper()}'",
        "maxRecords": 1,
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        records = data.get("records", [])
        if records:
            return records[0]["id"]
    except Exception as e:
        print(f"   ⚠️ 레코드 검색 실패: {e}")

    return None

def test_update_record(
    pat: str,
    base_id: str,
    table_name: str,
    record_id: str,
    fields: Dict[str, Any],
) -> Dict[str, Any]:
    """updateRecord API 테스트 (올바른 구조)"""
    url = f"{API_ROOT}/{base_id}/{table_name}/{record_id}"
    headers = req_headers(pat)

    # 올바른 형식: {"fields": {...}}
    payload = {"fields": fields}

    print(f"\n📡 updateRecord 테스트:")
    print(f"   URL: {url}")
    print(f"   Request Body: {json.dumps(payload, indent=2, ensure_ascii=False)}")

    try:
        response = requests.patch(url, headers=headers, json=payload, timeout=30)

        result = {
            "status_code": response.status_code,
            "success": response.ok,
            "headers": dict(response.headers),
        }

        try:
            result["response_body"] = response.json()
        except:
            result["response_text"] = response.text

        return result
    except Exception as e:
        return {
            "status_code": 0,
            "success": False,
            "error": str(e),
        }

def main():
    """메인 실행"""
    pat = os.getenv("AIRTABLE_TOKEN") or os.getenv("AIRTABLE_API_TOKEN")
    if not pat:
        print("❌ ERROR: AIRTABLE_TOKEN 또는 AIRTABLE_API_TOKEN 환경 변수가 설정되지 않았습니다.")
        print("\n사용법:")
        print("  $env:AIRTABLE_API_TOKEN='pat...' python scripts/test_update_record.py")
        sys.exit(1)

    # 테스트할 shipment number (실제 존재하는 것으로 변경 가능)
    test_shpt_no = "HE-0538"  # 검증 스크립트에서 확인한 실제 레코드

    print("="*70)
    print("🧪 Airtable updateRecord 간단한 테스트")
    print("="*70)

    try:
        # 1. 테스트 레코드 ID 가져오기
        print(f"\n1️⃣ 테스트 레코드 검색: {test_shpt_no}")
        record_id = get_test_record_id(pat, BASE_ID, TEST_TABLE, test_shpt_no)

        if not record_id:
            print(f"❌ 레코드를 찾을 수 없습니다: {test_shpt_no}")
            print("\n💡 다른 shipment number를 사용하거나 Airtable에서 직접 record ID를 확인하세요.")
            sys.exit(1)

        print(f"✅ Record ID: {record_id}")

        # 2. updateRecord 테스트 (작은 변경사항 - 실제로 업데이트하지 않음)
        print(f"\n2️⃣ updateRecord 호출 테스트")
        print("⚠️ 주의: 실제 레코드가 업데이트됩니다!")
        print("\n💡 실제 업데이트를 원하지 않으면 스크립트의 test_fields를 비워두세요.")

        # 테스트 필드 (실제로 업데이트해도 안전한 필드 사용)
        # 테스트용으로 현재 시간을 포함하여 원래 값과 구분 가능하게 함
        from datetime import datetime
        test_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        test_fields = {
            "nextAction": f"Test update from script - {test_timestamp}",
        }

        # 실제 업데이트 테스트
        result = test_update_record(pat, BASE_ID, TEST_TABLE, record_id, test_fields)

        # 3. 결과 출력
        print(f"\n3️⃣ 결과:")
        print(f"   Status Code: {result['status_code']}")
        print(f"   Success: {result['success']}")

        if result.get("response_body"):
            print(f"\n   Response Body:")
            print(json.dumps(result["response_body"], indent=2, ensure_ascii=False))
        elif result.get("response_text"):
            print(f"\n   Response Text:")
            print(result["response_text"])
        elif result.get("error"):
            print(f"\n   Error:")
            print(result["error"])

        if result["success"]:
            print("\n✅ updateRecord 성공! request body 구조가 올바릅니다.")
            print("   → ChatGPT Actions도 이와 동일한 구조로 요청해야 합니다.")
        else:
            print("\n❌ updateRecord 실패!")
            if result["status_code"] == 422:
                print("   → 422 오류는 필드 이름 또는 값이 잘못되었을 수 있습니다.")
                print("   → 필드 이름과 타입을 확인하세요.")
            elif result["status_code"] == 404:
                print("   → 404 오류는 record ID가 잘못되었을 수 있습니다.")
            elif result["status_code"] == 401:
                print("   → 401 오류는 PAT 토큰이 잘못되었거나 권한이 없습니다.")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

