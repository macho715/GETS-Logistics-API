import os
import requests
from flask import Flask, jsonify, request, abort
from datetime import datetime
from typing import Dict, List, Optional
from functools import lru_cache

app = Flask(__name__)

# ==================== Airtable 설정 ====================
AIRTABLE_API_TOKEN = os.getenv("AIRTABLE_API_TOKEN")
AIRTABLE_BASE_ID = "appnLz06h07aMm366"
AIRTABLE_TABLE_ID = "tblQufXEl5lIUNg6s"
AIRTABLE_API_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_ID}"


# ==================== Airtable API 헤더 ====================
def get_airtable_headers() -> Dict[str, str]:
    """Airtable API 요청 헤더 생성"""
    if not AIRTABLE_API_TOKEN:
        return None

    return {
        "Authorization": f"Bearer {AIRTABLE_API_TOKEN}",
        "Content-Type": "application/json",
    }


# ==================== Airtable 데이터 조회 ====================
def fetch_airtable_records(max_records: int = 100) -> List[Dict]:
    """
    Airtable에서 레코드 조회

    Args:
        max_records: 최대 조회 레코드 수

    Returns:
        레코드 리스트
    """
    headers = get_airtable_headers()

    # 토큰이 없으면 빈 리스트 반환 (샘플 데이터 모드)
    if not headers:
        return []

    try:
        params = {"maxRecords": max_records}

        response = requests.get(
            AIRTABLE_API_URL, headers=headers, params=params, timeout=10
        )
        response.raise_for_status()

        data = response.json()
        return data.get("records", [])

    except requests.exceptions.RequestException as e:
        print(f"❌ Airtable API Error: {e}")
        return []


def search_shipment_by_shpt_no(shpt_no: str) -> Optional[Dict]:
    """
    특정 선적번호로 레코드 검색

    Args:
        shpt_no: 선적번호

    Returns:
        매칭되는 레코드 또는 None
    """
    records = fetch_airtable_records()

    for record in records:
        fields = record.get("fields", {})
        # 여러 필드명 패턴 지원
        record_shpt_no = fields.get(
            "SHPT NO", fields.get("Shipment Number", fields.get("Ship Number", ""))
        )

        if record_shpt_no == shpt_no:
            return record

    return None


def calculate_completion_rate(records: List[Dict], field_name: str) -> float:
    """
    특정 필드의 완료율 계산

    Args:
        records: Airtable 레코드 리스트
        field_name: 체크할 필드명

    Returns:
        완료율 (0.0 ~ 1.0)
    """
    if not records:
        return 0.0

    # 완료 상태로 간주되는 값들
    completed_statuses = [
        "Released",
        "Issued",
        "Ready",
        "Valid",
        "Complete",
        "Done",
        "Completed",
    ]

    completed_count = sum(
        1
        for record in records
        if record.get("fields", {}).get(field_name) in completed_statuses
    )

    return round(completed_count / len(records), 2)


# ==================== API 엔드포인트 ====================


@app.route("/", methods=["GET"])
def index():
    """API 홈 - 상태 확인"""
    airtable_status = "connected" if AIRTABLE_API_TOKEN else "sample_data_mode"

    return jsonify(
        {
            "status": "online",
            "message": "GETS Action API for ChatGPT",
            "version": "1.3.0",
            "dataSource": "Airtable" if AIRTABLE_API_TOKEN else "Sample Data",
            "airtableStatus": airtable_status,
            "endpoints": {
                "home": "/",
                "document_status": "/document/status/{shptNo}",
                "status_summary": "/status/summary",
                "health": "/health",
            },
        }
    )


@app.route("/document/status/<shptNo>", methods=["GET"])
def get_document_status(shptNo):
    """
    특정 선적번호(SHPT NO)의 문서 상태 조회
    Airtable 실시간 데이터 또는 샘플 데이터
    """
    try:
        # Airtable에서 검색
        record = search_shipment_by_shpt_no(shptNo)

        if record:
            # Airtable 실제 데이터 반환
            fields = record.get("fields", {})

            return jsonify(
                {
                    "shptNo": fields.get(
                        "SHPT NO", fields.get("Shipment Number", shptNo)
                    ),
                    "boeStatus": fields.get(
                        "BOE Status", fields.get("BOE_STATUS", "Unknown")
                    ),
                    "doStatus": fields.get(
                        "DO Status", fields.get("DO_STATUS", "Unknown")
                    ),
                    "cooReady": fields.get(
                        "COO Ready", fields.get("COO_READY", "Unknown")
                    ),
                    "hblReady": fields.get(
                        "HBL Ready", fields.get("HBL_READY", "Unknown")
                    ),
                    "ciplValid": fields.get(
                        "CIPL Valid", fields.get("CIPL_VALID", "Unknown")
                    ),
                    "lastUpdated": datetime.now().isoformat() + "Z",
                    "dataSource": "Airtable",
                    "airtableRecordId": record.get("id"),
                }
            )

        # 샘플 데이터 반환 (Airtable에 없을 경우)
        return jsonify(
            {
                "shptNo": shptNo,
                "boeStatus": "Released",
                "doStatus": "Issued",
                "cooReady": "Ready",
                "hblReady": "Ready",
                "ciplValid": "Valid",
                "lastUpdated": datetime.now().isoformat() + "Z",
                "dataSource": "Sample Data",
            }
        )

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"error": "Internal server error", "message": str(e)}), 500


@app.route("/status/summary", methods=["GET"])
def get_status_summary():
    """
    전체 선적 현황 KPI 요약
    Airtable 실시간 데이터 또는 샘플 데이터
    """
    try:
        # Airtable에서 모든 레코드 조회
        records = fetch_airtable_records()

        if records:
            # Airtable 실제 데이터로 KPI 계산
            total_shipments = len(records)

            # 여러 필드명 패턴 지원
            cipl_rate = calculate_completion_rate(
                records, "CIPL Valid"
            ) or calculate_completion_rate(records, "CIPL_VALID")
            hbl_rate = calculate_completion_rate(
                records, "HBL Ready"
            ) or calculate_completion_rate(records, "HBL_READY")
            coo_rate = calculate_completion_rate(
                records, "COO Ready"
            ) or calculate_completion_rate(records, "COO_READY")
            do_rate = calculate_completion_rate(
                records, "DO Status"
            ) or calculate_completion_rate(records, "DO_STATUS")
            boe_rate = calculate_completion_rate(
                records, "BOE Status"
            ) or calculate_completion_rate(records, "BOE_STATUS")

            # Pending BOE 추출
            pending_boe = []
            for record in records:
                fields = record.get("fields", {})
                boe_status = fields.get("BOE Status", fields.get("BOE_STATUS", ""))
                shpt_no = fields.get("SHPT NO", fields.get("Shipment Number", ""))

                if boe_status not in ["Released", "Issued"] and shpt_no:
                    pending_boe.append(shpt_no)
                    if len(pending_boe) >= 10:
                        break

            # At Risk 추출
            upcoming_risk = []
            for record in records:
                fields = record.get("fields", {})
                do_status = fields.get("DO Status", fields.get("DO_STATUS", ""))
                shpt_no = fields.get("SHPT NO", fields.get("Shipment Number", ""))

                if not do_status and shpt_no:
                    upcoming_risk.append(shpt_no)
                    if len(upcoming_risk) >= 10:
                        break

            return jsonify(
                {
                    "totalShipments": total_shipments,
                    "ciplRate": cipl_rate,
                    "hblRate": hbl_rate,
                    "cooRate": coo_rate,
                    "doRate": do_rate,
                    "boeRate": boe_rate,
                    "pendingBOE": pending_boe,
                    "upcomingRisk": upcoming_risk,
                    "lastUpdated": datetime.now().isoformat() + "Z",
                    "dataSource": "Airtable (Real-time)",
                }
            )

        # 샘플 데이터 반환 (Airtable 미설정 또는 연결 실패)
        return jsonify(
            {
                "totalShipments": 73,
                "ciplRate": 0.88,
                "hblRate": 0.75,
                "cooRate": 0.70,
                "doRate": 0.52,
                "boeRate": 0.41,
                "pendingBOE": ["HVDC-ADOPT-SIM-0065", "HVDC-ADOPT-SCT-0041"],
                "upcomingRisk": ["HVDC-ADOPT-SCT-0058"],
                "lastUpdated": datetime.now().isoformat() + "Z",
                "dataSource": "Sample Data",
            }
        )

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"error": "Internal server error", "message": str(e)}), 500


@app.route("/health", methods=["GET"])
def health_check():
    """Health check 엔드포인트 (Airtable 연결 포함)"""
    try:
        headers = get_airtable_headers()
        airtable_healthy = False

        if headers:
            # Airtable 연결 테스트
            test_response = requests.get(
                AIRTABLE_API_URL, headers=headers, params={"maxRecords": 1}, timeout=5
            )
            test_response.raise_for_status()
            airtable_healthy = True

        return jsonify(
            {
                "status": "healthy",
                "timestamp": datetime.now().isoformat() + "Z",
                "version": "1.3.0",
                "airtable": {
                    "configured": bool(AIRTABLE_API_TOKEN),
                    "connected": airtable_healthy,
                    "baseId": AIRTABLE_BASE_ID,
                    "tableId": AIRTABLE_TABLE_ID,
                },
            }
        ), (200 if (not AIRTABLE_API_TOKEN or airtable_healthy) else 503)

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat() + "Z",
                }
            ),
            503,
        )


# ✅ Vercel Serverless Functions 호환
# Flask app 객체를 자동으로 WSGI handler로 변환
