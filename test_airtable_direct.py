"""
Airtable Direct API Test Script
GPTs용 Airtable 테스트 - 실제 Airtable API 호출 테스트
"""

import os
import json
import sys
from datetime import datetime
from api.airtable_client import AirtableClient
from api.airtable_locked_config import BASE_ID, TABLES

# Windows 인코딩 문제 해결
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 환경 변수에서 토큰 가져오기
AIRTABLE_API_TOKEN = os.getenv("AIRTABLE_API_TOKEN")

def print_section(title):
    """섹션 구분 출력"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def print_result(success, message, data=None):
    """결과 출력"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {message}")
    if data:
        print(f"   Data: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")

def test_1_connection():
    """테스트 1: 기본 연결 확인"""
    print_section("TEST 1: Airtable 연결 확인")

    if not AIRTABLE_API_TOKEN:
        print_result(False, "AIRTABLE_API_TOKEN 환경변수가 설정되지 않음")
        return False

    try:
        client = AirtableClient(AIRTABLE_API_TOKEN, BASE_ID)
        # Shipments 테이블에서 1개 레코드만 가져와서 연결 확인
        records = client.list_records(
            TABLES["Shipments"],
            max_records=1,
            page_size=1
        )
        print_result(True, f"Airtable 연결 성공 (Base ID: {BASE_ID})")
        print(f"   샘플 레코드 개수: {len(records)}")
        return True
    except Exception as e:
        print_result(False, f"Airtable 연결 실패: {str(e)}")
        return False

def test_2_list_shipments():
    """테스트 2: Shipments 테이블 조회"""
    print_section("TEST 2: Shipments 테이블 조회 (모든 레코드)")

    try:
        client = AirtableClient(AIRTABLE_API_TOKEN, BASE_ID)
        records = client.list_records(TABLES["Shipments"], max_records=5)

        print_result(True, f"Shipments 테이블 조회 성공")
        print(f"   총 조회된 레코드: {len(records)}개 (최대 5개)")

        if records:
            sample = records[0]
            print(f"\n   샘플 레코드 (ID: {sample.get('id', 'N/A')}):")
            fields = sample.get('fields', {})
            print(f"   - shptNo: {fields.get('shptNo', 'N/A')}")
            print(f"   - riskLevel: {fields.get('riskLevel', 'N/A')}")
            print(f"   - currentBottleneckCode: {fields.get('currentBottleneckCode', 'N/A')}")

        return True
    except Exception as e:
        print_result(False, f"Shipments 테이블 조회 실패: {str(e)}")
        return False

def test_3_filter_high_risk():
    """테스트 3: HIGH risk 선적 필터링"""
    print_section("TEST 3: HIGH risk 선적 필터링")

    try:
        client = AirtableClient(AIRTABLE_API_TOKEN, BASE_ID)
        records = client.list_records(
            TABLES["Shipments"],
            filter_by_formula="{riskLevel}='HIGH'",
            max_records=10
        )

        print_result(True, f"HIGH risk 선적 조회 성공")
        print(f"   HIGH risk 선적 개수: {len(records)}개")

        if records:
            print(f"\n   HIGH risk 선적 목록:")
            for i, rec in enumerate(records[:5], 1):  # 최대 5개만 출력
                fields = rec.get('fields', {})
                shpt_no = fields.get('shptNo', 'N/A')
                bottleneck = fields.get('currentBottleneckCode', 'N/A')
                print(f"   {i}. {shpt_no} - Bottleneck: {bottleneck}")

        return True
    except Exception as e:
        print_result(False, f"HIGH risk 필터링 실패: {str(e)}")
        return False

def test_4_specific_shipment():
    """테스트 4: 특정 선적번호 조회"""
    print_section("TEST 4: 특정 선적번호 조회 (SCT-0143)")

    try:
        client = AirtableClient(AIRTABLE_API_TOKEN, BASE_ID)
        records = client.list_records(
            TABLES["Shipments"],
            filter_by_formula="{shptNo}='SCT-0143'",
            max_records=1
        )

        if records:
            rec = records[0]
            fields = rec.get('fields', {})
            print_result(True, f"SCT-0143 선적 찾음")
            print(f"\n   상세 정보:")
            print(f"   - Record ID: {rec.get('id')}")
            print(f"   - shptNo: {fields.get('shptNo', 'N/A')}")
            print(f"   - riskLevel: {fields.get('riskLevel', 'N/A')}")
            print(f"   - currentBottleneckCode: {fields.get('currentBottleneckCode', 'N/A')}")
            print(f"   - bottleneckSince: {fields.get('bottleneckSince', 'N/A')}")
            print(f"   - nextAction: {fields.get('nextAction', 'N/A')}")
            print(f"   - actionOwner: {fields.get('actionOwner', 'N/A')}")
            print(f"   - dueAt: {fields.get('dueAt', 'N/A')}")
            return True
        else:
            print_result(False, "SCT-0143 선적을 찾을 수 없음")
            return False
    except Exception as e:
        print_result(False, f"특정 선적 조회 실패: {str(e)}")
        return False

def test_5_documents_table():
    """테스트 5: Documents 테이블 조회"""
    print_section("TEST 5: Documents 테이블 조회")

    try:
        client = AirtableClient(AIRTABLE_API_TOKEN, BASE_ID)
        records = client.list_records(
            TABLES["Documents"],
            max_records=5
        )

        print_result(True, f"Documents 테이블 조회 성공")
        print(f"   조회된 문서 개수: {len(records)}개")

        if records:
            print(f"\n   문서 목록:")
            for i, rec in enumerate(records, 1):
                fields = rec.get('fields', {})
                shpt_no = fields.get('shptNo', 'N/A')
                doc_type = fields.get('docType', 'N/A')
                status = fields.get('status', 'N/A')
                print(f"   {i}. {shpt_no} - {doc_type}: {status}")

        return True
    except Exception as e:
        print_result(False, f"Documents 테이블 조회 실패: {str(e)}")
        return False

def test_6_approvals_table():
    """테스트 6: Approvals 테이블 조회"""
    print_section("TEST 6: Approvals 테이블 조회")

    try:
        client = AirtableClient(AIRTABLE_API_TOKEN, BASE_ID)
        records = client.list_records(
            TABLES["Approvals"],
            max_records=5
        )

        print_result(True, f"Approvals 테이블 조회 성공")
        print(f"   조회된 승인 개수: {len(records)}개")

        if records:
            print(f"\n   승인 목록:")
            for i, rec in enumerate(records, 1):
                fields = rec.get('fields', {})
                shpt_no = fields.get('shptNo', 'N/A')
                approval_type = fields.get('approvalType', 'N/A')
                status = fields.get('status', 'N/A')
                print(f"   {i}. {shpt_no} - {approval_type}: {status}")

        return True
    except Exception as e:
        print_result(False, f"Approvals 테이블 조회 실패: {str(e)}")
        return False

def test_7_pagination():
    """테스트 7: 페이지네이션 테스트"""
    print_section("TEST 7: 페이지네이션 테스트")

    try:
        client = AirtableClient(AIRTABLE_API_TOKEN, BASE_ID)

        # 첫 페이지
        records_page1 = client.list_records(
            TABLES["Shipments"],
            max_records=2,
            page_size=2
        )

        print_result(True, f"페이지네이션 테스트")
        print(f"   첫 페이지 레코드: {len(records_page1)}개")

        # 더 많은 레코드 가져오기
        records_all = client.list_records(
            TABLES["Shipments"],
            max_records=10,
            page_size=5
        )
        print(f"   전체 조회 레코드: {len(records_all)}개 (max 10개)")

        return True
    except Exception as e:
        print_result(False, f"페이지네이션 테스트 실패: {str(e)}")
        return False

def test_8_complex_filter():
    """테스트 8: 복합 필터 (HIGH/CRITICAL + FANR_PENDING)"""
    print_section("TEST 8: 복합 필터 테스트")

    try:
        client = AirtableClient(AIRTABLE_API_TOKEN, BASE_ID)

        # HIGH 또는 CRITICAL risk이고 FANR_PENDING인 선적
        formula = "AND(OR({riskLevel}='HIGH', {riskLevel}='CRITICAL'), {currentBottleneckCode}='FANR_PENDING')"
        records = client.list_records(
            TABLES["Shipments"],
            filter_by_formula=formula,
            max_records=10
        )

        print_result(True, f"복합 필터 조회 성공")
        print(f"   조건: HIGH/CRITICAL risk AND FANR_PENDING")
        print(f"   조회된 레코드: {len(records)}개")

        if records:
            print(f"\n   필터링된 선적:")
            for i, rec in enumerate(records, 1):
                fields = rec.get('fields', {})
                shpt_no = fields.get('shptNo', 'N/A')
                risk = fields.get('riskLevel', 'N/A')
                print(f"   {i}. {shpt_no} - Risk: {risk}")

        return True
    except Exception as e:
        print_result(False, f"복합 필터 테스트 실패: {str(e)}")
        return False

def print_schema_info():
    """스키마 정보만 출력 (토큰 없이)"""
    print_section("Airtable 스키마 정보")
    print(f"  Base ID: {BASE_ID}")
    print(f"  Schema Version: 2025-12-25T00:32:52+0400")
    print(f"\n  사용 가능한 테이블:")
    for name, table_id in TABLES.items():
        print(f"    - {name}: {table_id}")
    print("\n  Protected Fields:")
    print("    Shipments: shptNo, currentBottleneckCode, bottleneckSince, riskLevel, nextAction, actionOwner, dueAt")
    print("    Documents: shptNo, docType, status")
    print("    Actions: shptNo, status, priority, dueAt, actionText, owner")
    print("    Events: timestamp, shptNo, entityType, toStatus")

def test_9_other_tables():
    """테스트 9: 기타 테이블 조회 (Vendors, Owners, Sites)"""
    print_section("TEST 9: 기타 테이블 조회")

    results = []

    for table_name in ["Vendors", "Owners", "Sites", "BottleneckCodes"]:
        try:
            client = AirtableClient(AIRTABLE_API_TOKEN, BASE_ID)
            records = client.list_records(
                TABLES[table_name],
                max_records=3
            )
            print_result(True, f"{table_name} 테이블 조회 성공 ({len(records)}개)")
            results.append(True)
        except Exception as e:
            print_result(False, f"{table_name} 테이블 조회 실패: {str(e)}")
            results.append(False)

    return all(results)

def main():
    """메인 테스트 실행"""
    global AIRTABLE_API_TOKEN

    print(f"\n{'#'*70}")
    print(f"#  Airtable Direct API Test (GPTs용)")
    print(f"#  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"#  Base ID: {BASE_ID}")
    print(f"{'#'*70}\n")

    if not AIRTABLE_API_TOKEN:
        print("⚠️  WARNING: AIRTABLE_API_TOKEN 환경변수가 설정되지 않았습니다.")
        print("\n환경변수에서 자동으로 확인 중...")

        # .env 파일에서 읽기 시도
        try:
            from dotenv import load_dotenv
            load_dotenv()
            AIRTABLE_API_TOKEN = os.getenv("AIRTABLE_API_TOKEN")
        except ImportError:
            pass

        if not AIRTABLE_API_TOKEN:
            print("\n⚠️  토큰 없이 스키마 정보만 확인합니다...")
            print("\n실제 API 테스트를 하려면 환경변수를 설정하세요:")
            print("  Windows PowerShell: $env:AIRTABLE_API_TOKEN='pat...'")
            print("  Linux/Mac: export AIRTABLE_API_TOKEN='pat...'")
            print_schema_info()
            return

    tests = [
        ("연결 확인", test_1_connection),
        ("Shipments 조회", test_2_list_shipments),
        ("HIGH risk 필터", test_3_filter_high_risk),
        ("특정 선적 조회", test_4_specific_shipment),
        ("Documents 조회", test_5_documents_table),
        ("Approvals 조회", test_6_approvals_table),
        ("페이지네이션", test_7_pagination),
        ("복합 필터", test_8_complex_filter),
        ("기타 테이블", test_9_other_tables),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ 테스트 '{name}' 실행 중 오류: {str(e)}")
            results.append((name, False))

    # 최종 요약
    print_section("테스트 요약")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✅" if success else "❌"
        print(f"  {status} {name}")

    print(f"\n  총 {passed}/{total} 테스트 통과 ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n🎉 모든 테스트 통과! Airtable 연결 정상 작동 중입니다.")
    elif passed >= total * 0.7:
        print("\n⚠️  대부분의 테스트가 통과했습니다. 일부 실패 항목을 확인하세요.")
    else:
        print("\n❌ 많은 테스트가 실패했습니다. Airtable 연결 및 설정을 확인하세요.")

if __name__ == "__main__":
    main()

