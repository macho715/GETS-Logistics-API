"""
Airtable 테스트 실행 스크립트
환경변수 확인 및 실제 테스트 실행
"""

import os
import sys

# Windows 인코딩 문제 해결
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def check_environment():
    """환경변수 확인"""
    print("=" * 70)
    print("환경 설정 확인")
    print("=" * 70)

    token = os.getenv("AIRTABLE_API_TOKEN")
    if token:
        masked_token = token[:8] + "..." + token[-4:] if len(token) > 12 else "***"
        print(f"✅ AIRTABLE_API_TOKEN: {masked_token} (설정됨)")
        return True
    else:
        print("❌ AIRTABLE_API_TOKEN: (설정되지 않음)")
        print("\n💡 환경변수 설정 방법:")
        print("   Windows PowerShell: $env:AIRTABLE_API_TOKEN='pat...'")
        print("   Windows CMD: set AIRTABLE_API_TOKEN=pat...")
        print("   Linux/Mac: export AIRTABLE_API_TOKEN='pat...'")
        return False

def run_unit_tests():
    """유닛 테스트 실행"""
    print("\n" + "=" * 70)
    print("1. Airtable 클라이언트 유닛 테스트 실행")
    print("=" * 70 + "\n")

    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_airtable_client.py", "-v", "--tb=short"],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
    )

    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    return result.returncode == 0

def run_schema_test():
    """스키마 정보 테스트"""
    print("\n" + "=" * 70)
    print("2. 스키마 정보 확인")
    print("=" * 70 + "\n")

    try:
        from api.airtable_locked_config import BASE_ID, TABLES, SCHEMA_VERSION, PROTECTED_FIELDS

        print(f"✅ Base ID: {BASE_ID}")
        print(f"✅ Schema Version: {SCHEMA_VERSION}")
        print(f"\n✅ 테이블 개수: {len(TABLES)}개")
        print(f"✅ Protected Fields: {sum(len(fields) for fields in PROTECTED_FIELDS.values())}개")

        print("\n테이블 목록:")
        for name, table_id in TABLES.items():
            print(f"  - {name}: {table_id}")

        return True
    except Exception as e:
        print(f"❌ 스키마 정보 확인 실패: {str(e)}")
        return False

def run_integration_test():
    """통합 테스트 실행 (환경변수 필요)"""
    print("\n" + "=" * 70)
    print("3. 실제 Airtable API 연결 테스트")
    print("=" * 70 + "\n")

    token = os.getenv("AIRTABLE_API_TOKEN")
    if not token:
        print("⚠️  환경변수가 설정되지 않아 실제 연결 테스트를 건너뜁니다.")
        print("   환경변수를 설정한 후 다시 실행하세요.")
        return None

    try:
        # test_airtable_direct.py 실행
        import subprocess
        result = subprocess.run(
            [sys.executable, "test_airtable_direct.py"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        return result.returncode == 0
    except Exception as e:
        print(f"❌ 통합 테스트 실행 실패: {str(e)}")
        return False

def main():
    """메인 실행"""
    print("\n" + "#" * 70)
    print("#  Airtable 테스트 실행")
    print("#" * 70 + "\n")

    # 환경변수 확인
    has_token = check_environment()

    results = {}

    # 1. 유닛 테스트 (항상 실행)
    results['unit_tests'] = run_unit_tests()

    # 2. 스키마 테스트 (항상 실행)
    results['schema_test'] = run_schema_test()

    # 3. 통합 테스트 (환경변수 있을 때만)
    if has_token:
        results['integration_test'] = run_integration_test()
    else:
        results['integration_test'] = None

    # 최종 요약
    print("\n" + "=" * 70)
    print("테스트 결과 요약")
    print("=" * 70)

    print(f"\n✅ 유닛 테스트: {'통과' if results['unit_tests'] else '실패'}")
    print(f"✅ 스키마 테스트: {'통과' if results['schema_test'] else '실패'}")

    if results['integration_test'] is None:
        print(f"⏭️  통합 테스트: 건너뜀 (환경변수 없음)")
    elif results['integration_test']:
        print(f"✅ 통합 테스트: 통과")
    else:
        print(f"❌ 통합 테스트: 실패")

    # 전체 통과 여부
    passed_tests = [r for r in results.values() if r is True]
    total_runnable = [r for r in results.values() if r is not None]

    if total_runnable:
        pass_rate = len(passed_tests) / len(total_runnable) * 100
        print(f"\n📊 통과율: {len(passed_tests)}/{len(total_runnable)} ({pass_rate:.1f}%)")

        if all(r for r in total_runnable):
            print("\n🎉 모든 테스트 통과!")
        else:
            print("\n⚠️  일부 테스트 실패. 위 결과를 확인하세요.")
    else:
        print("\n⚠️  실행 가능한 테스트가 없습니다.")

    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()

