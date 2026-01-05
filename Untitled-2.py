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
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

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
OPENAPI_SCHEMA_FILE = OPENAPI_DIR / "openapi-airtable-api-v1.0.4.yaml"

GPT_NAME = "GETS Logistics Assistant"
GPT_DESCRIPTION = "HVDC Project Logistics Assistant with real-time Airtable integration"

# GPT Builder UI 관측 기반 제한값 (운영 시 변동 가능)
INSTRUCTIONS_MAX_LEN = 8000
MAX_KNOWLEDGE_FILES = 20
MAX_FILE_BYTES = 512 * 1024 * 1024  # 512MB


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
        return LimitCheck(False, f"⚠️ 초과: {len(instructions)}자 (최대 {INSTRUCTIONS_MAX_LEN}자)")
    return LimitCheck(True, f"✅ {len(instructions)}자 ({INSTRUCTIONS_MAX_LEN}자 제한 내)")


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
    no_timestamp: bool = False,
) -> str:
    """GPTs 설정 가이드 생성"""

    schema_info = openapi_schema.get("info", {}) if isinstance(openapi_schema, dict) else {}
    schema_title = schema_info.get("title", "N/A")
    schema_version = schema_info.get("version", "N/A")

    found_cnt = len(knowledge_files.get("found", []))
    total_cnt = knowledge_files.get("total", 0)

    stamp = "" if no_timestamp else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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

