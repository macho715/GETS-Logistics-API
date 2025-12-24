import os
from flask import Flask, jsonify, request, abort

app = Flask(__name__)

# 보안을 위한 API 키 확인 (선택사항)
API_KEY = os.getenv("API_KEY")


@app.before_request
def authenticate():
    """Bearer Token 인증 체크 (API_KEY 환경변수가 설정된 경우만)"""
    if API_KEY:  # API_KEY가 설정된 경우만 인증 체크
        token = request.headers.get("Authorization")
        if token != f"Bearer {API_KEY}":
            abort(401)


@app.route("/document/status/<shptNo>", methods=["GET"])
def get_document_status(shptNo):
    """
    특정 선적번호(SHPT NO)의 문서 상태 조회
    예: /document/status/HVDC-ADOPT-SIM-0065
    """
    # 실제 데이터베이스나 Airtable 연동 시 여기를 수정하세요
    # 현재는 샘플 데이터를 반환합니다

    sample_data = {
        "shptNo": shptNo,
        "boeStatus": "Released",
        "doStatus": "Issued",
        "cooReady": "Ready",
        "hblReady": "Ready",
        "ciplValid": "Valid",
        "lastUpdated": "2025-12-24T19:30:00Z",
    }

    return jsonify(sample_data)


@app.route("/status/summary", methods=["GET"])
def get_status_summary():
    """
    전체 선적 현황 KPI 요약
    예: /status/summary
    """
    # 실제 데이터베이스나 Airtable 연동 시 여기를 수정하세요
    # 현재는 샘플 데이터를 반환합니다

    summary = {
        "totalShipments": 73,
        "ciplRate": 0.88,
        "hblRate": 0.75,
        "cooRate": 0.70,
        "doRate": 0.52,
        "boeRate": 0.41,
        "pendingBOE": ["HVDC-ADOPT-SIM-0065", "HVDC-ADOPT-SCT-0041"],
        "upcomingRisk": ["HVDC-ADOPT-SCT-0058"],
        "lastUpdated": "2025-12-24T19:30:00Z",
    }

    return jsonify(summary)


@app.route("/", methods=["GET"])
def index():
    """API 홈 - 상태 확인"""
    return jsonify(
        {
            "status": "online",
            "message": "GETS Action API for ChatGPT",
            "version": "1.2.0",
            "endpoints": {
                "document_status": "/document/status/{shptNo}",
                "status_summary": "/status/summary",
            },
        }
    )
