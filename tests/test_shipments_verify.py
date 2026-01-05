"""
Tests for /shipments/verify endpoint.
"""

import api.app
from api.airtable_locked_config import SCHEMA_VERSION, TABLES


def test_shipments_verify_missing_shptno(client, mock_airtable_client):
    """Missing shptNo returns 400."""
    response = client.get("/shipments/verify")
    assert response.status_code == 400
    data = response.get_json()
    assert data["status"] == "bad_request"
    assert data["error"] == "shptNo is empty"
    assert data["schemaVersion"] == SCHEMA_VERSION


def test_shipments_verify_too_many(client, mock_airtable_client):
    """More than 50 shptNo values returns 400."""
    shptnos = ",".join([f"HE-{i:04d}" for i in range(51)])
    response = client.get(f"/shipments/verify?shptNo={shptnos}")
    assert response.status_code == 400
    data = response.get_json()
    assert data["status"] == "bad_request"
    assert "Too many shptNo" in data["error"]


def test_shipments_verify_returns_items(client, mock_airtable_client):
    """Single shptNo returns items and meta."""
    mock_airtable_client.records[TABLES["Shipments"]] = [
        {
            "id": "rec1",
            "fields": {
                "shptNo": "HE-0512",
                "site": "MIR",
                "eta": "2025-12-18T00:00:00Z",
                "nextAction": "Test action",
                "riskLevel": "HIGH",
                "currentBottleneckCode": "INSPECT_RED",
            },
        }
    ]

    response = client.get("/shipments/verify?shptNo=HE-0512")
    assert response.status_code == 200
    data = response.get_json()
    assert data["meta"]["count"] == 1
    assert data["meta"]["duplicates"] == []
    assert data["meta"]["schemaVersion"] == SCHEMA_VERSION
    assert data["items"][0]["shptNo"] == "HE-0512"
    assert data["items"][0]["site"] == "MIR"
    assert data["items"][0]["riskLevel"] == "HIGH"


def test_shipments_verify_duplicates(client, mock_airtable_client):
    """Duplicate shptNo values are reported in meta."""
    mock_airtable_client.records[TABLES["Shipments"]] = [
        {
            "id": "rec1",
            "fields": {
                "shptNo": "SCT-0151",
                "site": "MIR",
                "eta": "2025-12-19T00:00:00Z",
                "nextAction": "Action 1",
                "riskLevel": "MEDIUM",
                "currentBottleneckCode": "NONE",
            },
        },
        {
            "id": "rec2",
            "fields": {
                "shptNo": "SCT-0151",
                "site": "MIR",
                "eta": "2025-12-20T00:00:00Z",
                "nextAction": "Action 2",
                "riskLevel": "LOW",
                "currentBottleneckCode": "NONE",
            },
        },
    ]

    response = client.get("/shipments/verify?shptNo=SCT-0151")
    assert response.status_code == 200
    data = response.get_json()
    assert "SCT-0151" in data["meta"]["duplicates"]
    assert data["meta"]["count"] == 2


def test_shipments_verify_no_airtable(client, monkeypatch):
    """Airtable not connected returns 503."""
    monkeypatch.setattr(api.app, "airtable_client", None)

    response = client.get("/shipments/verify?shptNo=HE-0512")
    assert response.status_code == 503
    data = response.get_json()
    assert data["status"] == "service_unavailable"
    assert data["schemaVersion"] == SCHEMA_VERSION


def test_shipments_verify_airtable_error(client, monkeypatch):
    """Airtable errors return 502."""
    class BrokenClient:
        def list_records(self, *args, **kwargs):
            raise Exception("Airtable API error")

    monkeypatch.setattr(api.app, "airtable_client", BrokenClient())

    response = client.get("/shipments/verify?shptNo=HE-0512")
    assert response.status_code == 502
    data = response.get_json()
    assert data["status"] == "upstream_error"
    assert data["schemaVersion"] == SCHEMA_VERSION


def test_shipments_verify_api_key_auth(client, mock_airtable_client, monkeypatch):
    """API key enforcement returns 401 for missing/invalid keys."""
    monkeypatch.setattr(api.app, "API_KEY", "test-key-123")

    response = client.get("/shipments/verify?shptNo=HE-0512")
    assert response.status_code == 401

    response = client.get(
        "/shipments/verify?shptNo=HE-0512",
        headers={"X-API-Key": "wrong-key"},
    )
    assert response.status_code == 401

    response = client.get(
        "/shipments/verify?shptNo=HE-0512",
        headers={"X-API-Key": "test-key-123"},
    )
    assert response.status_code == 200

    response = client.get(
        "/shipments/verify?shptNo=HE-0512",
        headers={"Authorization": "Bearer test-key-123"},
    )
    assert response.status_code == 200
