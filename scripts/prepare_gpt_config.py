#!/usr/bin/env python3
"""
GPTs 설정 준비 스크립트

GPTs 설정에 필요한 모든 파일을 검증하고, 복사/붙여넣기용 텍스트를 생성합니다.

사용법:
    python scripts/prepare_gpt_config.py
    python scripts/prepare_gpt_config.py --output-dir ./gpt_config
    python scripts/prepare_gpt_config.py --validate-only
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple
from zoneinfo import ZoneInfo

import yaml

# Windows 콘솔 UTF-8 인코딩 설정
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    os.environ["PYTHONIOENCODING"] = "utf-8"

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

# 파일 경로
BASE_DIR = Path(__file__).parent.parent
GUIDES_DIR = BASE_DIR / "docs" / "guides"
OPENAPI_DIR = BASE_DIR / "docs" / "openapi"

INSTRUCTIONS_FILE = GUIDES_DIR / "GPT_INSTRUCTIONS.md"
CONVERSATION_STARTERS_FILE = GUIDES_DIR / "GPT_CONVERSATION_STARTERS.md"
KNOWLEDGE_FILES = [
    GUIDES_DIR / "Excel_Batch_Upload_Workflow.md",
    GUIDES_DIR / "Common_Workflows.md",
    GUIDES_DIR / "API_Reference_Guide.md",
]
# NOTE: This script uses Airtable Direct API schema (v1.0.4).
# For GETS API with /shipments/verify endpoint, use: OPENAPI_DIR / "openapi-gets-api.yaml"
# The Airtable Direct API provides raw Airtable access, while GETS API includes business logic.
OPENAPI_SCHEMA_FILE = OPENAPI_DIR / "openapi-airtable-api-v1.0.4.yaml"

GPT_NAME = "GETS Logistics Assistant"
GPT_DESCRIPTION = "HVDC Project Logistics Assistant with real-time Airtable integration"

# GPT Builder UI 관측 기반 제한값 (운영 시 변동 가능)
INSTRUCTIONS_MAX_LEN = 8000
MAX_KNOWLEDGE_FILES = 20
MAX_FILE_BYTES = 512 * 1024 * 1024  # 512MB
DUBAI_TZ = ZoneInfo("Asia/Dubai")


@dataclass(frozen=True)
class LimitCheck:
    ok: bool
    message: str


def load_file_content(file_path: Path) -> str:
    """파일 내용 읽기"""
    if not file_path.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

    return file_path.read_text(encoding="utf-8").strip()


def parse_conversation_starters(file_path: Path) -> List[str]:
    """
    Conversation starters 파일에서 4개 추출

    - 우선: "추천 세트" / "Option A" 섹션 아래 ordered list(1. ~) 추출
    - 폴백: 문서 전체에서 ordered list 1~4를 순서대로 추출
    - 최종 폴백: 기본값 4개
    """
    content = load_file_content(file_path)
    lines = content.splitlines()

    starters: List[str] = []
    in_section = False

    ordered_re = re.compile(r"^\s*(\d+)\.\s+(.*\S)\s*$")

    for line in lines:
        if "추천 세트" in line or "Option A" in line:
            in_section = True
            continue

        m = ordered_re.match(line)
        if in_section and m:
            num = int(m.group(1))
            if 1 <= num <= 10:
                starters.append(m.group(2).strip())

        if len(starters) >= 4:
            break

    if len(starters) < 4:
        starters = []
        for line in lines:
            m = ordered_re.match(line)
            if m:
                starters.append(m.group(2).strip())
            if len(starters) >= 4:
                break

    if len(starters) < 4:
        starters = [
            "📊 현재 병목(bottleneck) 상황을 요약해줘",
            "🚢 SCT-0143 선적 상태를 자세히 보여줘",
            "⏰ D-5 또는 초과된 승인 건이 있어?",
            "📈 오늘의 KPI 대시보드를 보여줘",
        ]

    return starters[:4]


def validate_instructions(instructions: str) -> LimitCheck:
    """Instructions 길이 검증"""
    if len(instructions) > INSTRUCTIONS_MAX_LEN:
        return LimitCheck(
            False, f"⚠️ 초과: {len(instructions)}자 (최대 {INSTRUCTIONS_MAX_LEN}자)"
        )
    return LimitCheck(
        True, f"✅ {len(instructions)}자 ({INSTRUCTIONS_MAX_LEN}자 제한 내)"
    )


def validate_openapi_schema(file_path: Path) -> Tuple[bool, Dict[str, Any]]:
    """OpenAPI 스키마 검증 (최소 검증)"""
    try:
        schema = yaml.safe_load(file_path.read_text(encoding="utf-8"))

        if not isinstance(schema, dict):
            return False, {"error": "스키마 파싱 결과가 dict가 아닙니다."}

        required_keys = ["openapi", "info", "paths"]
        missing = [key for key in required_keys if key not in schema]
        if missing:
            return False, {"error": f"필수 키 누락: {missing}"}

        openapi_ver = str(schema.get("openapi", ""))
        if not openapi_ver.startswith("3."):
            return False, {"error": f"OpenAPI 버전이 3.x가 아닙니다: {openapi_ver}"}

        return True, schema
    except Exception as e:
        return False, {"error": str(e)}


def check_knowledge_files() -> Dict[str, Any]:
    """Knowledge 파일 확인 + 제한값 경고"""
    result: Dict[str, Any] = {
        "total": len(KNOWLEDGE_FILES),
        "found": [],
        "missing": [],
        "over_limit": {
            "count_exceeded": False,
            "files_over_512mb": [],
        },
    }

    for file_path in KNOWLEDGE_FILES:
        if file_path.exists():
            size = file_path.stat().st_size
            entry = {"name": file_path.name, "path": str(file_path), "size": size}
            result["found"].append(entry)

            if size > MAX_FILE_BYTES:
                result["over_limit"]["files_over_512mb"].append(entry)
        else:
            result["missing"].append({"name": file_path.name, "path": str(file_path)})

    if result["total"] > MAX_KNOWLEDGE_FILES:
        result["over_limit"]["count_exceeded"] = True

    return result


def generate_setup_guide(
    instructions: str,
    conversation_starters: List[str],
    openapi_schema: Dict[str, Any],
    knowledge_files: Dict[str, Any],
) -> str:
    """GPTs 설정 가이드 생성"""

    schema_info = (
        openapi_schema.get("info", {}) if isinstance(openapi_schema, dict) else {}
    )
    schema_title = schema_info.get("title", "N/A")
    schema_version = schema_info.get("version", "N/A")

    found_cnt = len(knowledge_files.get("found", []))
    total_cnt = knowledge_files.get("total", 0)
    generated_at = datetime.now(DUBAI_TZ).isoformat(timespec="seconds")

    guide = f"""# GETS Logistics GPT 설정 가이드

이 가이드는 ChatGPT GPT Builder에서 GPTs를 설정하는 단계별 안내입니다.

## 📋 사전 준비

✅ Instructions 파일: {len(instructions)}자
✅ Conversation Starters: {len(conversation_starters)}개 (Desktop 최초 4개 노출 권장)
✅ OpenAPI Schema: {schema_title} v{schema_version}
✅ Knowledge Files: {total_cnt}개 (발견: {found_cnt}개)

참고: Knowledge는 GPT당 최대 {MAX_KNOWLEDGE_FILES}개 파일, 파일당 최대 512MB 제한이 있습니다.

---

## 🚀 설정 단계

### Step 1: GPT 생성

1. ChatGPT → Explore GPTs → Create
2. Configure 탭
3. Name: **{GPT_NAME}**
4. Description: **{GPT_DESCRIPTION}**

---

### Step 2: Instructions 설정

Instructions 섹션에 아래 텍스트를 전체 복사하여 붙여넣기:

---

## 📝 Instructions (아래 내용 복사)

```
{instructions}
```

---

### Step 3: Conversation Starters 설정

1. "Conversation starters" 섹션으로 스크롤
2. 아래 4개를 각각 입력:

1. {conversation_starters[0]}
2. {conversation_starters[1]}
3. {conversation_starters[2]}
4. {conversation_starters[3]}

---

### Step 4: Actions 설정 (OpenAPI Schema)

1. "Actions" 섹션으로 스크롤
2. "Create new action" 클릭
3. "Manual schema" 선택 (또는 "Import from URL" 사용 가능)

**옵션 A: Import from URL (권장)**
```
https://gets-logistics-api.vercel.app/openapi-schema.yaml
```

**옵션 B: Manual Schema**
OpenAPI 스키마 파일 위치: `{OPENAPI_SCHEMA_FILE}`
파일 내용을 전체 복사하여 붙여넣기

4. **Authentication 설정**:
   - Type: **Bearer**
   - Token: Airtable Personal Access Token 입력
     - 토큰 발급: https://airtable.com/create/tokens
     - Scopes: `data.records:read`, `data.records:write`
     - Base: `appnLz06h07aMm366`

---

### Step 5: Knowledge Files 업로드

1. "Knowledge" 섹션으로 스크롤
2. "Upload files" 클릭
3. 다음 파일들을 업로드:

"""

    for file_info in knowledge_files.get("found", []):
        guide += f"- `{file_info['name']}` ({file_info['size']:,} bytes)\n"

    if knowledge_files.get("missing"):
        guide += "\n⚠️ 다음 파일을 찾을 수 없습니다:\n"
        for file_info in knowledge_files["missing"]:
            guide += f"- `{file_info['name']}`\n"

    guide += f"""
4. 파일 업로드 완료 대기

---

### Step 6: 저장 및 테스트

1. "Save" 버튼 클릭 (오른쪽 상단)
2. Visibility 선택:
   - **Only me** - 개인용
   - **Anyone with a link** - 링크 공유
   - **Public** - GPT Store 공개

3. 테스트 쿼리:
   - "현재 병목 상황을 요약해줘"
   - "SCT-0143 선적 상태를 보여줘"
   - "D-5 초과 승인 건이 있어?"

---

## ✅ 확인 사항

- [ ] Instructions가 8,000자 이내인지 확인
- [ ] Conversation Starters 4개 입력 확인
- [ ] Actions에서 OpenAPI Schema 로드 확인
- [ ] Authentication (Bearer Token) 설정 확인
- [ ] Knowledge Files 업로드 완료 확인
- [ ] 테스트 쿼리 성공 확인

---

## 🔗 참고 링크

- **API Base URL**: https://gets-logistics-api.vercel.app
- **OpenAPI Schema URL**: https://gets-logistics-api.vercel.app/openapi-schema.yaml
- **Airtable Base ID**: appnLz06h07aMm366
- **Schema Version**: 2025-12-25T00:32:52+0400

---

**생성 일시**: {generated_at}
"""

    return guide


def save_config_files(
    output_dir: Path,
    instructions: str,
    conversation_starters: List[str],
    openapi_schema: Dict[str, Any],
    knowledge_files: Dict[str, Any],
) -> None:
    """설정 파일들을 출력 디렉토리에 저장"""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Instructions
    instructions_file = output_dir / "instructions.txt"
    instructions_file.write_text(instructions, encoding="utf-8")
    print(f"✅ Instructions 저장: {instructions_file}")

    # Conversation Starters
    starters_file = output_dir / "conversation_starters.json"
    starters_data = {
        "starters": conversation_starters,
        "count": len(conversation_starters),
    }
    starters_file.write_text(
        json.dumps(starters_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"✅ Conversation Starters 저장: {starters_file}")

    # OpenAPI Schema
    schema_file = output_dir / "openapi-schema.yaml"
    with open(schema_file, "w", encoding="utf-8") as f:
        yaml.dump(openapi_schema, f, allow_unicode=True, sort_keys=False)
    print(f"✅ OpenAPI Schema 저장: {schema_file}")

    # Knowledge Files 복사
    knowledge_dir = output_dir / "knowledge"
    knowledge_dir.mkdir(exist_ok=True)

    for file_info in knowledge_files.get("found", []):
        src = Path(file_info["path"])
        dst = knowledge_dir / file_info["name"]
        shutil.copy2(src, dst)
        print(f"✅ Knowledge 파일 복사: {dst}")

    # 설정 가이드
    guide = generate_setup_guide(
        instructions, conversation_starters, openapi_schema, knowledge_files
    )
    guide_file = output_dir / "SETUP_GUIDE.md"
    guide_file.write_text(guide, encoding="utf-8")
    print(f"✅ 설정 가이드 저장: {guide_file}")

    # 요약 JSON
    summary = {
        "gpt_name": GPT_NAME,
        "gpt_description": GPT_DESCRIPTION,
        "instructions_length": len(instructions),
        "instructions_valid": len(instructions) <= INSTRUCTIONS_MAX_LEN,
        "conversation_starters_count": len(conversation_starters),
        "openapi_schema": {
            "title": (
                openapi_schema.get("info", {}).get("title", "N/A")
                if isinstance(openapi_schema, dict)
                else "N/A"
            ),
            "version": (
                openapi_schema.get("info", {}).get("version", "N/A")
                if isinstance(openapi_schema, dict)
                else "N/A"
            ),
        },
        "knowledge_files": {
            "total": knowledge_files.get("total", 0),
            "found": len(knowledge_files.get("found", [])),
            "missing": len(knowledge_files.get("missing", [])),
            "over_limit": knowledge_files.get("over_limit", {}),
        },
        "generated_at": datetime.now(DUBAI_TZ).isoformat(timespec="seconds"),
    }
    summary_file = output_dir / "summary.json"
    summary_file.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"✅ 요약 저장: {summary_file}")


def main() -> None:
    parser = argparse.ArgumentParser(description="GPTs 설정 파일 준비 및 검증")
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="출력 디렉토리 (지정하지 않으면 콘솔 출력만)",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="검증만 수행 (파일 저장 안 함)",
    )

    args = parser.parse_args()

    print("🔍 GPTs 설정 파일 검증 중...\n")

    # 파일 로드 및 검증
    errors = []
    warnings = []

    try:
        # Instructions
        print("📝 Instructions 검증 중...")
        instructions = load_file_content(INSTRUCTIONS_FILE)
        check = validate_instructions(instructions)
        print(f"   {check.message}")
        if not check.ok:
            warnings.append(f"Instructions: {check.message}")

        # Conversation Starters
        print("\n💬 Conversation Starters 검증 중...")
        conversation_starters = parse_conversation_starters(CONVERSATION_STARTERS_FILE)
        print(f"   ✅ {len(conversation_starters)}개 추출 완료")
        for i, starter in enumerate(conversation_starters, 1):
            print(f"      {i}. {starter[:50]}...")

        # OpenAPI Schema
        print("\n📋 OpenAPI Schema 검증 중...")
        valid, schema_result = validate_openapi_schema(OPENAPI_SCHEMA_FILE)
        if valid:
            schema_info = schema_result.get("info", {})
            print("   ✅ 유효한 OpenAPI 스키마")
            print(f"      Title: {schema_info.get('title', 'N/A')}")
            print(f"      Version: {schema_info.get('version', 'N/A')}")
            openapi_schema = schema_result
        else:
            print(f"   ❌ 검증 실패: {schema_result.get('error', 'Unknown error')}")
            errors.append(
                f"OpenAPI Schema: {schema_result.get('error', 'Unknown error')}"
            )
            openapi_schema = {}

        # Knowledge Files
        print("\n📚 Knowledge Files 확인 중...")
        knowledge_files = check_knowledge_files()
        print(f"   발견: {len(knowledge_files['found'])}/{knowledge_files['total']}개")
        for file_info in knowledge_files["found"]:
            print(f"      ✅ {file_info['name']} ({file_info['size']:,} bytes)")
        for file_info in knowledge_files["missing"]:
            print(f"      ❌ {file_info['name']} (파일 없음)")
            warnings.append(f"Knowledge 파일 누락: {file_info['name']}")

        # 크기 제한 경고
        if knowledge_files["over_limit"]["files_over_512mb"]:
            for file_info in knowledge_files["over_limit"]["files_over_512mb"]:
                size_mb = file_info["size"] / (1024 * 1024)
                warnings.append(
                    f"Knowledge 파일 초과: {file_info['name']} ({size_mb:.1f}MB > 512MB)"
                )

    except Exception as e:
        print(f"\n❌ 파일 로드 실패: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    # 검증 결과 요약
    print("\n" + "=" * 60)
    print("📊 검증 결과 요약")
    print("=" * 60)

    if errors:
        print(f"\n❌ 오류: {len(errors)}개")
        for error in errors:
            print(f"   - {error}")

    if warnings:
        print(f"\n⚠️ 경고: {len(warnings)}개")
        for warning in warnings:
            print(f"   - {warning}")

    if not errors and not warnings:
        print("\n✅ 모든 검증 통과!")

    # 파일 저장 (--validate-only가 아닐 때)
    if not args.validate_only:
        if args.output_dir:
            output_dir = Path(args.output_dir)
            print(f"\n💾 설정 파일 저장 중: {output_dir}")
            save_config_files(
                output_dir,
                instructions,
                conversation_starters,
                openapi_schema,
                knowledge_files,
            )
            print(f"\n✅ 모든 파일 저장 완료: {output_dir}")
        else:
            # 콘솔에 설정 가이드 출력
            print("\n" + "=" * 60)
            print("📋 GPTs 설정 가이드")
            print("=" * 60)
            guide = generate_setup_guide(
                instructions, conversation_starters, openapi_schema, knowledge_files
            )
            print(guide)

            print("\n💡 파일로 저장하려면: --output-dir ./gpt_config")


if __name__ == "__main__":
    main()
