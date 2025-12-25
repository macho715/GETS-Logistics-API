"""
Unit tests for api/airtable_client.py
Covers request retries, pagination, and batch operations.
"""

from unittest.mock import Mock

import pytest

import api.airtable_client as airtable_client
from api.airtable_client import AirtableClient


class TestAirtableClientInit:
    """Test Airtable client initialization."""

    def test_init_sets_headers_and_timeout(self):
        client = AirtableClient("patTEST", "appTEST")

        assert client.pat == "patTEST"
        assert client.base_id == "appTEST"
        assert client.timeout == (10, 60)
        assert client.session.headers["Authorization"] == "Bearer patTEST"
        assert client.session.headers["Content-Type"] == "application/json"

    def test_url_encodes_table_name(self):
        client = AirtableClient("patTEST", "appTEST")

        url = client._url("Table Name")
        assert url == "https://api.airtable.com/v0/appTEST/Table%20Name"


class TestAirtableClientRequest:
    """Test low-level request handling."""

    def test_request_success(self):
        client = AirtableClient("patTEST", "appTEST")

        response = Mock()
        response.status_code = 200
        response.ok = True
        response.json.return_value = {"records": []}
        client.session.request = Mock(return_value=response)

        result = client._request("GET", "https://api.airtable.com/v0/appTEST/tbl123")

        assert result == {"records": []}
        client.session.request.assert_called_once()

    def test_request_retries_on_429(self, monkeypatch):
        client = AirtableClient("patTEST", "appTEST")

        response_429 = Mock()
        response_429.status_code = 429
        response_429.ok = False
        response_429.headers = {"Retry-After": "2"}

        response_200 = Mock()
        response_200.status_code = 200
        response_200.ok = True
        response_200.json.return_value = {"ok": True}

        client.session.request = Mock(side_effect=[response_429, response_200])

        sleep_calls = []
        monkeypatch.setattr(airtable_client.time, "sleep", lambda s: sleep_calls.append(s))

        result = client._request("GET", "https://api.airtable.com/v0/appTEST/tbl123")

        assert result == {"ok": True}
        assert client.session.request.call_count == 2
        assert sleep_calls == [2]

    def test_request_retries_on_503(self, monkeypatch):
        client = AirtableClient("patTEST", "appTEST")

        response_503 = Mock()
        response_503.status_code = 503
        response_503.ok = False
        response_503.headers = {}

        response_200 = Mock()
        response_200.status_code = 200
        response_200.ok = True
        response_200.json.return_value = {"ok": True}

        client.session.request = Mock(side_effect=[response_503, response_200])

        sleep_calls = []
        monkeypatch.setattr(airtable_client.time, "sleep", lambda s: sleep_calls.append(s))

        result = client._request("GET", "https://api.airtable.com/v0/appTEST/tbl123")

        assert result == {"ok": True}
        assert client.session.request.call_count == 2
        assert sleep_calls == [1]

    def test_request_raises_on_non_retryable_error(self):
        client = AirtableClient("patTEST", "appTEST")

        response = Mock()
        response.status_code = 400
        response.ok = False
        response.text = "bad request"
        response.headers = {}

        client.session.request = Mock(return_value=response)

        with pytest.raises(RuntimeError) as exc:
            client._request("GET", "https://api.airtable.com/v0/appTEST/tbl123")

        assert "Airtable API error 400" in str(exc.value)

    def test_request_exhausts_retries(self, monkeypatch):
        client = AirtableClient("patTEST", "appTEST")

        response_503 = Mock()
        response_503.status_code = 503
        response_503.ok = False
        response_503.headers = {}

        client.session.request = Mock(return_value=response_503)

        sleep_calls = []
        monkeypatch.setattr(airtable_client.time, "sleep", lambda s: sleep_calls.append(s))

        with pytest.raises(RuntimeError) as exc:
            client._request("GET", "https://api.airtable.com/v0/appTEST/tbl123")

        assert "failed after" in str(exc.value)
        assert client.session.request.call_count == 5
        assert len(sleep_calls) == 5


class TestAirtableClientListRecords:
    """Test list_records pagination and params."""

    def test_list_records_paginates_and_builds_params(self, monkeypatch):
        client = AirtableClient("patTEST", "appTEST")

        responses = [
            {"records": [{"id": "rec1"}], "offset": "next"},
            {"records": [{"id": "rec2"}]},
        ]
        mock_request = Mock(side_effect=responses)
        monkeypatch.setattr(client, "_request", mock_request)

        records = client.list_records(
            "tbl123",
            filter_by_formula="{status}='ACTIVE'",
            view="Grid",
            fields=["name", "status"],
            page_size=150,
        )

        assert [r["id"] for r in records] == ["rec1", "rec2"]
        assert mock_request.call_count == 2

        first_params = mock_request.call_args_list[0].kwargs["params"]
        assert first_params["pageSize"] == 100
        assert first_params["filterByFormula"] == "{status}='ACTIVE'"
        assert first_params["view"] == "Grid"
        assert first_params["fields[]"] == ["name", "status"]

        second_params = mock_request.call_args_list[1].kwargs["params"]
        assert second_params["offset"] == "next"


class TestAirtableClientWriteOperations:
    """Test create, update, and upsert operations."""

    def test_create_records_builds_payload(self, monkeypatch):
        client = AirtableClient("patTEST", "appTEST")
        mock_request = Mock(return_value={"records": []})
        monkeypatch.setattr(client, "_request", mock_request)

        client.create_records("tbl123", [{"name": "Item"}], typecast=False)

        args, kwargs = mock_request.call_args
        assert args[0] == "POST"
        payload = kwargs["json_body"]
        assert payload["records"] == [{"fields": {"name": "Item"}}]
        assert payload["typecast"] is False

    def test_update_records_builds_payload(self, monkeypatch):
        client = AirtableClient("patTEST", "appTEST")
        mock_request = Mock(return_value={"records": []})
        monkeypatch.setattr(client, "_request", mock_request)

        records = [{"id": "rec1", "fields": {"name": "Item"}}]
        client.update_records("tbl123", records, typecast=True)

        args, kwargs = mock_request.call_args
        assert args[0] == "PATCH"
        payload = kwargs["json_body"]
        assert payload["records"] == records
        assert payload["typecast"] is True

    def test_upsert_records_batches_and_sleeps(self, monkeypatch):
        client = AirtableClient("patTEST", "appTEST")
        mock_request = Mock(return_value={"records": []})
        monkeypatch.setattr(client, "_request", mock_request)

        sleep_calls = []
        monkeypatch.setattr(airtable_client.time, "sleep", lambda s: sleep_calls.append(s))

        records = [{"name": f"Item {i}"} for i in range(12)]
        results = client.upsert_records(
            "tbl123", records, fields_to_merge_on=["name"], typecast=False
        )

        assert len(results) == 2
        assert mock_request.call_count == 2
        assert sleep_calls == [0.22, 0.22]

        first_payload = mock_request.call_args_list[0].kwargs["json_body"]
        assert first_payload["performUpsert"]["fieldsToMergeOn"] == ["name"]
        assert first_payload["typecast"] is False
