"""
Airtable 업로드 실패 원인 진단 스크립트

사용법:
    python scripts/diagnose_airtable_upload.py \
        --file chatgpt_prepared_data_v14.json \
        --token pat_xxxxx
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from api.airtable_client import AirtableClient
from api.airtable_locked_config import BASE_ID, TABLES, PROTECTED_FIELDS

def check_authentication(token: str) -> Dict[str, Any]:
    """1️⃣ 인증 확인"""
    print("="*60)
    print("1️⃣ 인증 확인 (Authentication)")
    print("="*60)

    if not token:
        return {"status": "❌ FAIL", "error": "토큰이 없습니다"}

    if not token.startswith("pat"):
        return {"status": "⚠️ WARNING", "error": "토큰 형식이 올바르지 않습니다 (pat...로 시작해야 함)"}

    try:
        client = AirtableClient(token.strip(), BASE_ID)
        # 간단한 읽기 테스트
        test_records = client.list_records(
            TABLES["Shipments"],
            page_size=1
        )
        return {
            "status": "✅ PASS",
            "message": f"인증 성공, {len(test_records)}개 레코드 접근 가능"
        }
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "Unauthorized" in error_msg:
            return {"status": "❌ FAIL", "error": "401 Unauthorized - 토큰이 유효하지 않거나 권한이 없습니다"}
        elif "403" in error_msg or "Forbidden" in error_msg:
            return {"status": "❌ FAIL", "error": "403 Forbidden - Base 접근 권한이 없습니다"}
        else:
            return {"status": "❌ FAIL", "error": f"인증 실패: {e}"}

def check_base_and_table() -> Dict[str, Any]:
    """2️⃣ Base ID 및 Table ID 확인"""
    print("\n" + "="*60)
    print("2️⃣ Base ID 및 Table ID 확인")
    print("="*60)

    base_id = BASE_ID
    table_id = TABLES["Shipments"]

    print(f"   Base ID: {base_id}")
    print(f"   Table ID: {table_id}")

    return {
        "status": "✅ PASS",
        "baseId": base_id,
        "tableId": table_id,
        "message": "설정값 확인 완료"
    }

def validate_field_names(records: List[Dict]) -> Dict[str, Any]:
    """3️⃣ 필드명 검증"""
    print("\n" + "="*60)
    print("3️⃣ 필드명 검증 (Field Names)")
    print("="*60)

    # 스키마에서 실제 필드명 로드
    schema_path = Path(__file__).parent.parent / "api" / "airtable_schema.lock.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    valid_fields = set(schema["tables"]["Shipments"]["fields"].keys())

    # JSON에서 사용된 필드명 수집
    used_fields = set()
    invalid_fields = []

    for record in records:
        for field_name in record.keys():
            used_fields.add(field_name)
            if field_name not in valid_fields and field_name not in ["Normalized Shipment ID", "Normalized_No", "sourceFile", "generatedBy", "generatedAt"]:
                if field_name not in invalid_fields:
                    invalid_fields.append(field_name)

    if invalid_fields:
        return {
            "status": "❌ FAIL",
            "error": f"존재하지 않는 필드명: {invalid_fields}",
            "valid_fields": list(valid_fields),
            "invalid_fields": invalid_fields
        }

    return {
        "status": "✅ PASS",
        "message": f"모든 필드명이 유효합니다 ({len(used_fields)}개 필드 사용)",
        "used_fields": list(used_fields)
    }

def validate_field_types(records: List[Dict]) -> Dict[str, Any]:
    """4️⃣ 필드 타입 검증"""
    print("\n" + "="*60)
    print("4️⃣ 필드 타입 검증 (Field Types)")
    print("="*60)

    schema_path = Path(__file__).parent.parent / "api" / "airtable_schema.lock.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    fields_info = schema["tables"]["Shipments"]["fields"]
    errors = []
    warnings = []

    for i, record in enumerate(records[:10], 1):  # 처음 10개만 샘플링
        for field_name, value in record.items():
            if field_name not in fields_info:
                continue

            field_info = fields_info[field_name]
            field_type = field_info["type"]

            # 날짜 필드 검증
            if field_type == "dateTime":
                if value and value not in [None, "NaT", "nan"]:
                    if not isinstance(value, str) or "T" not in str(value):
                        errors.append(f"레코드 {i}: {field_name}는 dateTime이지만 형식이 잘못됨: {value}")

            # singleSelect 검증 (riskLevel)
            if field_name == "riskLevel" and field_type == "singleSelect":
                valid_values = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
                if value and value not in valid_values:
                    warnings.append(f"레코드 {i}: riskLevel='{value}'는 허용되지 않는 값일 수 있음 (허용: {valid_values})")

    if errors:
        return {"status": "❌ FAIL", "errors": errors}

    if warnings:
        return {"status": "⚠️ WARNING", "warnings": warnings}

    return {"status": "✅ PASS", "message": "필드 타입 검증 통과"}

def test_single_upload(token: str, sample_record: Dict) -> Dict[str, Any]:
    """5️⃣ 단일 레코드 업로드 테스트"""
    print("\n" + "="*60)
    print("5️⃣ 단일 레코드 업로드 테스트")
    print("="*60)

    try:
        client = AirtableClient(token.strip(), BASE_ID)
        table_id = TABLES["Shipments"]

        # Protected Fields만 추출
        protected = PROTECTED_FIELDS["Shipments"]
        test_record = {k: v for k, v in sample_record.items() if k in protected or k == "shptNo"}

        # NaT 및 None 처리
        for key, value in test_record.items():
            if value in ["NaT", "nan", None] or (isinstance(value, float) and str(value) == "nan"):
                test_record[key] = None

        print(f"   테스트 레코드: {json.dumps(test_record, indent=2, ensure_ascii=False)}")

        results = client.upsert_records(
            table_id,
            [test_record],
            fields_to_merge_on=["shptNo"],
            typecast=True,
        )

        if results and "records" in results[0]:
            return {
                "status": "✅ PASS",
                "message": "단일 레코드 업로드 성공",
                "record_id": results[0]["records"][0].get("id", "N/A")
            }
        else:
            return {
                "status": "❌ FAIL",
                "error": f"업로드 실패: {results}",
                "response": results
            }

    except Exception as e:
        error_msg = str(e)

        # 에러 메시지 분석
        if "422" in error_msg or "Invalid field" in error_msg:
            return {
                "status": "❌ FAIL",
                "error": "422 Invalid field - 필드명 또는 값이 잘못되었습니다",
                "details": error_msg
            }
        elif "401" in error_msg:
            return {
                "status": "❌ FAIL",
                "error": "401 Unauthorized - 인증 실패",
                "details": error_msg
            }
        elif "429" in error_msg:
            return {
                "status": "⚠️ WARNING",
                "error": "429 Rate Limited - 잠시 후 재시도 필요",
                "details": error_msg
            }
        else:
            return {
                "status": "❌ FAIL",
                "error": f"업로드 실패: {e}",
                "details": error_msg
            }

def main():
    parser = argparse.ArgumentParser(description="Airtable 업로드 실패 원인 진단")
    parser.add_argument("--file", type=str, required=True, help="ChatGPT JSON 파일")
    parser.add_argument("--token", type=str, default=None, help="Airtable PAT (없으면 환경 변수 사용)")

    args = parser.parse_args()

    # JSON 파일 읽기
    json_path = Path(args.file)
    if not json_path.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {json_path}")
        sys.exit(1)

    with open(json_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    print(f"📖 {len(records)}개 레코드 로드 완료\n")

    # API 토큰
    token = args.token or os.getenv("AIRTABLE_API_TOKEN")
    if not token:
        print("❌ AIRTABLE_API_TOKEN이 설정되지 않았습니다.")
        sys.exit(1)

    # 진단 실행
    results = {}

    # 1. 인증 확인
    results["auth"] = check_authentication(token)
    print(f"   결과: {results['auth']['status']}")
    if "error" in results["auth"]:
        print(f"   에러: {results['auth']['error']}")

    # 2. Base/Table 확인
    results["base_table"] = check_base_and_table()
    print(f"   결과: {results['base_table']['status']}")

    # 3. 필드명 검증
    results["fields"] = validate_field_names(records)
    print(f"   결과: {results['fields']['status']}")
    if "error" in results["fields"]:
        print(f"   에러: {results['fields']['error']}")
        print(f"   유효한 필드: {', '.join(results['fields'].get('valid_fields', [])[:10])}...")

    # 4. 필드 타입 검증
    results["types"] = validate_field_types(records)
    print(f"   결과: {results['types']['status']}")
    if "errors" in results["types"]:
        for err in results["types"]["errors"][:5]:
            print(f"   에러: {err}")

    # 5. 단일 레코드 테스트 (첫 번째 레코드)
    if records and results["auth"]["status"] == "✅ PASS":
        results["test_upload"] = test_single_upload(token, records[0])
        print(f"   결과: {results['test_upload']['status']}")
        if "error" in results["test_upload"]:
            print(f"   에러: {results['test_upload']['error']}")

    # 최종 요약
    print("\n" + "="*60)
    print("📊 진단 요약")
    print("="*60)

    for check_name, result in results.items():
        status = result.get("status", "UNKNOWN")
        print(f"   {check_name}: {status}")

    # 실패한 항목이 있으면 종료 코드 1
    if any(r.get("status") == "❌ FAIL" for r in results.values()):
        print("\n❌ 진단 실패 - 위 항목을 수정해주세요")
        sys.exit(1)
    else:
        print("\n✅ 모든 진단 통과 - 업로드 가능합니다")

if __name__ == "__main__":
    main()

