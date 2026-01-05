#!/usr/bin/env python3
"""
Airtable 스키마 확인 및 검증 스크립트
기존 lock_schema_and_generate_mapping.py의 get_base_schema 함수 사용

사용법:
  $env:AIRTABLE_API_TOKEN='pat...' python scripts/check_airtable_schema.py
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Set
import requests

# UTF-8 인코딩 설정 (Windows)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    os.environ["PYTHONIOENCODING"] = "utf-8"

API_ROOT = "https://api.airtable.com/v0"
BASE_ID = "appnLz06h07aMm366"
LOCKED_SCHEMA_PATH = Path("api/airtable_schema.lock.json")

def req_headers(token: str) -> Dict[str, str]:
    """기존 lock_schema_and_generate_mapping.py와 동일한 헤더"""
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

def get_base_schema(base_id: str, token: str) -> Dict[str, Any]:
    """
    기존 lock_schema_and_generate_mapping.py의 get_base_schema 함수 (그대로 사용)
    Airtable Meta API로 현재 스키마 가져오기
    """
    url = f"{API_ROOT}/meta/bases/{base_id}/tables"
    r = requests.get(url, headers=req_headers(token), timeout=30)
    r.raise_for_status()
    return r.json()

def compare_schemas(current_schema: Dict[str, Any], locked_schema: Dict[str, Any]) -> Dict[str, Any]:
    """두 스키마 비교 (필드 이름 중심)"""
    current_tables = {t["name"]: t for t in current_schema.get("tables", [])}
    locked_tables = locked_schema.get("tables", {})

    differences = {
        "new_tables": [],
        "missing_tables": [],
        "field_differences": {},
    }

    # 테이블 비교
    current_table_names = set(current_tables.keys())
    locked_table_names = set(locked_tables.keys())

    differences["new_tables"] = list(current_table_names - locked_table_names)
    differences["missing_tables"] = list(locked_table_names - current_table_names)

    # 공통 테이블의 필드 비교
    common_tables = current_table_names & locked_table_names
    for table_name in common_tables:
        current_fields = {f["name"] for f in current_tables[table_name].get("fields", [])}
        locked_fields = set(locked_tables[table_name].get("fields", {}).keys())

        new_fields = current_fields - locked_fields
        missing_fields = locked_fields - current_fields

        if new_fields or missing_fields:
            differences["field_differences"][table_name] = {
                "new_fields": list(new_fields),
                "missing_fields": list(missing_fields),
                "matching_fields": list(current_fields & locked_fields),
            }

    return differences

def print_comparison(differences: Dict[str, Any]):
    """비교 결과 출력"""
    print("\n" + "="*70)
    print("📊 Airtable 스키마 비교 결과")
    print("="*70)

    if differences["new_tables"]:
        print(f"\n🆕 새로운 테이블 ({len(differences['new_tables'])}):")
        for table in differences["new_tables"]:
            print(f"  - {table}")
    else:
        print("\n✅ 새로운 테이블 없음")

    if differences["missing_tables"]:
        print(f"\n❌ 누락된 테이블 ({len(differences['missing_tables'])}):")
        for table in differences["missing_tables"]:
            print(f"  - {table}")
    else:
        print("\n✅ 누락된 테이블 없음")

    if differences["field_differences"]:
        print(f"\n⚠️ 필드 차이 ({len(differences['field_differences'])} 테이블):")
        for table_name, diff in differences["field_differences"].items():
            print(f"\n  📋 {table_name}:")
            if diff["missing_fields"]:
                print(f"    ❌ Locked에 있으나 현재 스키마에 없는 필드:")
                for field in diff["missing_fields"]:
                    print(f"       - {field}")
            if diff["new_fields"]:
                print(f"    🆕 현재 스키마에만 있는 필드 ({len(diff['new_fields'])}개):")
                for field in diff["new_fields"][:10]:  # 최대 10개만 표시
                    print(f"       - {field}")
                if len(diff["new_fields"]) > 10:
                    print(f"       ... 외 {len(diff['new_fields']) - 10}개")
            if diff["matching_fields"]:
                print(f"    ✅ 일치하는 필드: {len(diff['matching_fields'])}개")
    else:
        print("\n✅ 모든 테이블의 필드 이름이 일치합니다!")

def check_openapi_fields(current_schema: Dict[str, Any], locked_schema: Dict[str, Any]):
    """OpenAPI 스키마에서 사용하는 필드 이름 확인"""
    print("\n" + "="*70)
    print("🔍 OpenAPI 스키마 필드 검증")
    print("="*70)

    # OpenAPI에서 자주 사용하는 필드들 (updateRecord 예시에서 사용)
    openapi_fields_to_check = {
        "Shipments": ["shptNo", "riskLevel", "currentBottleneckCode", "dueAt"],
        "Actions": ["shptNo", "actionText", "status", "owner", "dueAt"],
        "Documents": ["shptNo", "docType", "status"],
    }

    current_tables = {t["name"]: t for t in current_schema.get("tables", [])}
    locked_tables = locked_schema.get("tables", {})

    all_valid = True
    for table_name, fields_to_check in openapi_fields_to_check.items():
        if table_name not in current_tables:
            print(f"\n❌ {table_name}: 테이블이 현재 스키마에 없음")
            all_valid = False
            continue

        current_fields = {f["name"]: f for f in current_tables[table_name].get("fields", [])}
        missing = []

        for field_name in fields_to_check:
            if field_name not in current_fields:
                missing.append(field_name)
                all_valid = False

        if missing:
            print(f"\n❌ {table_name}: 다음 필드가 현재 스키마에 없음:")
            for field in missing:
                print(f"   - {field}")
        else:
            print(f"\n✅ {table_name}: 모든 OpenAPI 필드 존재")
            for field_name in fields_to_check:
                field_info = current_fields[field_name]
                print(f"   - {field_name} ({field_info.get('type', 'unknown')})")

    return all_valid

def main():
    """메인 실행"""
    # PAT 토큰 가져오기
    token = os.getenv("AIRTABLE_TOKEN") or os.getenv("AIRTABLE_API_TOKEN")
    if not token:
        print("❌ ERROR: AIRTABLE_TOKEN 또는 AIRTABLE_API_TOKEN 환경 변수가 설정되지 않았습니다.")
        print("\n사용법:")
        print("  $env:AIRTABLE_API_TOKEN='pat...' python scripts/check_airtable_schema.py")
        sys.exit(1)

    try:
        # 1. 현재 스키마 가져오기 (기존 검증된 함수 사용)
        print(f"📡 Airtable Base에서 현재 스키마 가져오는 중...")
        print(f"   Base ID: {BASE_ID}")
        current_schema = get_base_schema(BASE_ID, token)
        current_tables = current_schema.get("tables", [])
        print(f"✅ 스키마 가져오기 성공 ({len(current_tables)} 테이블)")

        # 2. Locked 스키마 로드
        if not LOCKED_SCHEMA_PATH.exists():
            print(f"\n⚠️ Locked 스키마 파일을 찾을 수 없습니다: {LOCKED_SCHEMA_PATH}")
            print("\n현재 스키마 테이블 목록:")
            for table in current_tables:
                field_count = len(table.get("fields", []))
                print(f"  - {table['name']} ({field_count} 필드)")
            sys.exit(0)

        with open(LOCKED_SCHEMA_PATH, "r", encoding="utf-8") as f:
            locked_schema = json.load(f)
        locked_tables = locked_schema.get("tables", {})
        print(f"✅ Locked 스키마 로드 완료 ({len(locked_tables)} 테이블)")

        # 3. 스키마 비교
        differences = compare_schemas(current_schema, locked_schema)
        print_comparison(differences)

        # 4. OpenAPI 필드 검증
        openapi_valid = check_openapi_fields(current_schema, locked_schema)

        # 5. 결과 요약
        print("\n" + "="*70)
        print("📋 검증 결과 요약")
        print("="*70)

        has_differences = (
            differences["new_tables"] or
            differences["missing_tables"] or
            differences["field_differences"]
        )

        if not has_differences and openapi_valid:
            print("\n✅ 모든 검증 통과!")
            print("   - 테이블 구조 일치")
            print("   - 필드 이름 일치")
            print("   - OpenAPI 필드 검증 통과")
            sys.exit(0)
        else:
            print("\n⚠️ 차이점이 발견되었습니다.")
            if not openapi_valid:
                print("   - OpenAPI에서 사용하는 필드 중 일부가 현재 스키마에 없을 수 있습니다.")
            sys.exit(1)

    except requests.exceptions.HTTPError as e:
        print(f"\n❌ HTTP ERROR: {e}")
        if e.response.status_code == 401:
            print("   → PAT 토큰이 잘못되었거나 권한이 없습니다.")
        elif e.response.status_code == 403:
            print("   → Base 접근 권한이 없습니다.")
        elif e.response.status_code == 404:
            print("   → Base ID가 잘못되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

