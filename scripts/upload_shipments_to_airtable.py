"""
ChatGPT가 준비한 JSON 데이터를 Airtable Shipments 테이블에 업로드

사용법:
    python scripts/upload_shipments_to_airtable.py \
        --file chatgpt_prepared_data_v14.json \
        --token pat_xxxxxxxxxxxxx
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.airtable_client import AirtableClient
from api.airtable_locked_config import BASE_ID, TABLES, PROTECTED_FIELDS
from api.utils import parse_iso_any, iso_dubai, DUBAI_TZ

def normalize_datetime_field(value: Any) -> Optional[str]:
    """날짜/시간 필드를 Airtable 형식으로 정규화"""
    if value is None:
        return None

    # pandas NaT 처리
    if isinstance(value, str) and value in ["NaT", "nan", "NaN"]:
        return None

    # float NaN 처리
    if isinstance(value, float) and str(value) == "nan":
        return None

    if isinstance(value, str):
        # ISO 형식이면 파싱
        if "T" in value or "-" in value:
            dt = parse_iso_any(value)
            if dt:
                return iso_dubai(dt)
            # 파싱 실패 시 그대로 반환 (Airtable typecast가 처리)
            return value

    # datetime 객체면 변환
    if isinstance(value, datetime):
        return iso_dubai(value.astimezone(DUBAI_TZ))

    return str(value) if value else None

def prepare_airtable_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """ChatGPT JSON 레코드를 Airtable 필드 형식으로 변환"""
    # Protected Fields만 추출 (필수 필드)
    protected = PROTECTED_FIELDS["Shipments"]

    airtable_record = {}

    # shptNo는 필수 (upsert 기준)
    if "shptNo" not in record:
        raise ValueError(f"레코드에 shptNo가 없습니다: {list(record.keys())}")

    shpt_no = record["shptNo"]
    if not shpt_no or str(shpt_no).strip() == "":
        raise ValueError(f"shptNo가 비어있습니다: {record}")

    airtable_record["shptNo"] = str(shpt_no).strip()

    # Protected Fields 처리
    for field in protected:
        if field in record:
            value = record[field]

            # 날짜 필드 정규화
            if field in ["bottleneckSince", "dueAt"]:
                normalized = normalize_datetime_field(value)
                if normalized:
                    airtable_record[field] = normalized
            else:
                # 문자열 필드는 None/NaN 처리
                if value is None or (isinstance(value, float) and str(value) == "nan"):
                    continue
                if isinstance(value, str) and value in ["NaT", "nan", "NaN"]:
                    continue
                airtable_record[field] = str(value).strip() if isinstance(value, str) else value

    # 메타데이터 필드는 제외 (Airtable에 저장하지 않음)
    excluded_fields = ["sourceFile", "generatedBy", "generatedAt",
                      "Normalized Shipment ID", "Normalized_No"]

    # 선택적 필드 추가 (remarks 등)
    for key, value in record.items():
        if key not in excluded_fields and key not in airtable_record:
            if value is not None and not (isinstance(value, float) and str(value) == "nan"):
                if isinstance(value, str) and value not in ["NaT", "nan", "NaN"]:
                    airtable_record[key] = value.strip() if isinstance(value, str) else value

    return airtable_record

def upload_shipments(
    records: List[Dict[str, Any]],
    api_token: str,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Shipments 레코드를 Airtable에 Upsert

    Args:
        records: ChatGPT가 준비한 JSON 레코드 리스트
        api_token: Airtable Personal Access Token
        dry_run: True면 실제 업로드 없이 검증만

    Returns:
        업로드 결과 통계
    """
    if not api_token:
        raise ValueError("AIRTABLE_API_TOKEN이 필요합니다")

    # Airtable 클라이언트 초기화
    client = AirtableClient(api_token.strip(), BASE_ID)
    table_id = TABLES["Shipments"]

    # 레코드 준비
    print(f"📦 {len(records)}개 레코드 준비 중...")
    prepared_records = []
    errors = []

    for i, record in enumerate(records, 1):
        try:
            prepared = prepare_airtable_record(record)
            prepared_records.append(prepared)
        except Exception as e:
            error_msg = f"레코드 {i} 변환 실패: {e}"
            errors.append(error_msg)
            print(f"⚠️ {error_msg}")
            continue

    print(f"✅ {len(prepared_records)}개 레코드 준비 완료")
    if errors:
        print(f"⚠️ {len(errors)}개 레코드 변환 실패")

    if dry_run:
        print("\n🔍 DRY RUN 모드 - 실제 업로드하지 않습니다")
        print(f"   준비된 레코드 샘플 (첫 3개):")
        for i, rec in enumerate(prepared_records[:3], 1):
            print(f"   {i}. {json.dumps(rec, indent=2, ensure_ascii=False)}")
        return {
            "status": "dry_run",
            "total_records": len(records),
            "prepared_records": len(prepared_records),
            "errors": len(errors),
            "batches": (len(prepared_records) + 9) // 10,
        }

    if not prepared_records:
        raise ValueError("업로드할 레코드가 없습니다")

    # Upsert 실행
    print(f"\n🚀 Airtable에 업로드 중...")
    print(f"   테이블: Shipments ({table_id})")
    print(f"   기준 필드: shptNo (Protected Field)")
    print(f"   배치 크기: 10 레코드/요청")
    print()

    results = client.upsert_records(
        table_id,
        prepared_records,
        fields_to_merge_on=["shptNo"],  # Protected Field
        typecast=True,
    )

    # 결과 집계
    total_uploaded = 0
    upload_errors = []

    for batch_idx, batch_result in enumerate(results, 1):
        if "records" in batch_result:
            total_uploaded += len(batch_result["records"])
        elif "error" in batch_result:
            error_info = batch_result.get("error", {})
            error_msg = error_info.get("message", str(batch_result))
            upload_errors.append(f"배치 {batch_idx}: {error_msg}")

    return {
        "status": "success" if not upload_errors else "partial",
        "total_records": len(records),
        "prepared_records": len(prepared_records),
        "batches": len(results),
        "uploaded": total_uploaded,
        "errors": errors + upload_errors,
        "schemaVersion": "2025-12-25T00:32:52+0400",
    }

def main():
    parser = argparse.ArgumentParser(
        description="ChatGPT JSON 데이터를 Airtable에 업로드"
    )
    parser.add_argument(
        "--file",
        type=str,
        default="chatgpt_prepared_data_v14.json",
        help="ChatGPT가 생성한 JSON 파일 경로",
    )
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="Airtable Personal Access Token (없으면 환경 변수 사용)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="실제 업로드 없이 검증만 수행",
    )

    args = parser.parse_args()

    # JSON 파일 읽기
    json_path = Path(args.file)
    if not json_path.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {json_path}")
        print(f"   현재 디렉토리: {Path.cwd()}")
        sys.exit(1)

    print(f"📖 JSON 파일 읽기: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    print(f"✅ {len(records)}개 레코드 로드 완료\n")

    # API 토큰 확인
    api_token = args.token or os.getenv("AIRTABLE_API_TOKEN")
    if not api_token:
        print("❌ AIRTABLE_API_TOKEN이 설정되지 않았습니다.")
        print("   다음 중 하나를 수행하세요:")
        print("   1. --token 파라미터로 전달")
        print("   2. 환경 변수 설정: export AIRTABLE_API_TOKEN=pat...")
        sys.exit(1)

    # 업로드 실행
    try:
        result = upload_shipments(records, api_token, dry_run=args.dry_run)

        print("\n" + "="*60)
        print("✅ 업로드 완료!")
        print("="*60)
        print(json.dumps(result, indent=2, ensure_ascii=False))

        if result.get("status") == "success":
            print(f"\n📊 요약:")
            print(f"   총 레코드: {result['total_records']}개")
            print(f"   준비된 레코드: {result['prepared_records']}개")
            print(f"   배치 수: {result['batches']}개")
            print(f"   업로드된 레코드: {result['uploaded']}개")

            if result.get("errors"):
                print(f"\n⚠️ 경고:")
                for err in result["errors"][:5]:
                    print(f"   - {err}")

            # 검증용 API 호출 안내
            print(f"\n🔍 업로드 검증:")
            print(f"   curl https://gets-logistics-api.vercel.app/status/summary")
            print(f"   curl https://gets-logistics-api.vercel.app/document/status/{{shptNo}}")

    except Exception as e:
        print(f"\n❌ 업로드 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

