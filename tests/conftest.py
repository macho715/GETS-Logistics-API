"""
Pytest configuration and fixtures
Provides test fixtures for Flask app and Airtable mocking
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime
from zoneinfo import ZoneInfo

DUBAI_TZ = ZoneInfo("Asia/Dubai")


@pytest.fixture
def app():
    """Flask app fixture"""
    from api.app import app as flask_app
    
    flask_app.config['TESTING'] = True
    flask_app.config['DEBUG'] = False
    
    return flask_app


@pytest.fixture
def client(app):
    """Flask test client"""
    return app.test_client()


@pytest.fixture
def mock_airtable_client(monkeypatch):
    """Mock AirtableClient for isolated testing"""
    
    class MockAirtableClient:
        def __init__(self):
            self.records = {}
        
        def list_records(self, table_id, **kwargs):
            """Return mock records"""
            return self.records.get(table_id, [])
        
        def upsert_records(self, table_id, records_fields, **kwargs):
            """Mock upsert"""
            return [{
                "id": f"rec{i}",
                "fields": record
            } for i, record in enumerate(records_fields)]
        
        def mock_shipments_exists(self, shpt_no):
            """Mock shipment exists"""
            self.records["tbl4NnKYx1ECKmaaC"] = [{
                "id": "recSHIPMENT",
                "fields": {"shptNo": shpt_no}
            }]
        
        def mock_shipments_empty(self):
            """Mock no shipments"""
            self.records["tbl4NnKYx1ECKmaaC"] = []
        
        def mock_approvals_empty(self):
            """Mock no approvals"""
            self.records["tblJh4z49DbjX7cyb"] = []
        
        def mock_approval_with_due_date(self, shpt_no, due_at):
            """Mock approval with due date"""
            self.records["tblJh4z49DbjX7cyb"] = [{
                "id": "recAPPROVAL",
                "fields": {
                    "approvalKey": f"FANR-{shpt_no}-001",
                    "shptNo": shpt_no,
                    "approvalType": "FANR",
                    "status": "PENDING",
                    "dueAt": due_at
                }
            }]
        
        def mock_approvals_paginated(self, total, page_size):
            """Mock paginated approvals"""
            approvals = []
            for i in range(total):
                approvals.append({
                    "id": f"recAPP{i}",
                    "fields": {
                        "approvalType": f"TYPE_{i % 3}",
                        "status": "PENDING" if i % 2 == 0 else "APPROVED",
                        "dueAt": datetime.now(DUBAI_TZ).isoformat()
                    }
                })
            self.records["tblJh4z49DbjX7cyb"] = approvals
    
    mock_client = MockAirtableClient()
    
    # Patch airtable_client in the module
    import api.app
    monkeypatch.setattr(api.app, "airtable_client", mock_client)
    
    return mock_client


@pytest.fixture
def sample_shipment_data():
    """Sample shipment data"""
    return {
        "id": "recSHIPMENT123",
        "fields": {
            "shptNo": "SCT-0143",
            "vendor": "Samsung",
            "site": "AGI",
            "eta": "2025-12-30T12:00:00+04:00",
            "currentBottleneckCode": "FANR_PENDING",
            "bottleneckSince": "2025-12-24T09:00:00+04:00",
            "riskLevel": "HIGH"
        }
    }


@pytest.fixture
def sample_approval_data():
    """Sample approval data"""
    return {
        "id": "recAPPROVAL123",
        "fields": {
            "approvalKey": "FANR-SCT0143-001",
            "shptNo": "SCT-0143",
            "approvalType": "FANR",
            "status": "PENDING",
            "dueAt": "2025-12-30T12:00:00+04:00",
            "submittedAt": "2025-12-24T09:00:00+04:00",
            "owner": "Customs Team",
            "remarks": "Nuclear materials certification"
        }
    }


@pytest.fixture
def sample_event_data():
    """Sample event data"""
    return {
        "id": "recEVENT123",
        "fields": {
            "eventId": 1001,
            "timestamp": "2025-12-25T10:30:00+04:00",
            "shptNo": "SCT-0143",
            "entityType": "DOCUMENT",
            "fromStatus": "PENDING",
            "toStatus": "SUBMITTED",
            "actor": "John Doe"
        }
    }


@pytest.fixture
def sample_bottleneck_code():
    """Sample bottleneck code"""
    return {
        "id": "recBOTTLENECK123",
        "fields": {
            "code": "FANR_PENDING",
            "category": "APPROVAL",
            "description": "FANR approval pending",
            "riskDefault": "HIGH",
            "slaHours": 72
        }
    }

