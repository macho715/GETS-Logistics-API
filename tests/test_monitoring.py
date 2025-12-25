"""
Unit tests for api/monitoring.py
Covers structured logging, Slack alerts, and performance tracking.
"""

import json
import logging
import sys
import types
from unittest.mock import Mock

import pytest

import api.monitoring as monitoring


class TestJSONFormatter:
    """Test JSON log formatting."""

    def test_format_includes_standard_fields(self):
        formatter = monitoring.JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="hello",
            args=(),
            exc_info=None,
            func="test_func",
        )

        result = json.loads(formatter.format(record))

        assert result["level"] == "INFO"
        assert result["message"] == "hello"
        assert result["module"] == "test"
        assert result["function"] == "test_func"
        assert result["line"] == 10
        assert "timestamp" in result

    def test_format_includes_exception(self):
        formatter = monitoring.JSONFormatter()

        try:
            raise ValueError("boom")
        except ValueError:
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=5,
            msg="error",
            args=(),
            exc_info=exc_info,
            func="test_func",
        )

        result = json.loads(formatter.format(record))

        assert "exception" in result
        assert "ValueError" in result["exception"]

    def test_format_includes_extra_fields(self):
        formatter = monitoring.JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="hello",
            args=(),
            exc_info=None,
            func="test_func",
        )
        record.extra_fields = {"request_id": "req-123"}

        result = json.loads(formatter.format(record))

        assert result["request_id"] == "req-123"


class TestSetupLogger:
    """Test logger setup."""

    def test_setup_logger_configures_handler(self):
        logger = monitoring.setup_logger(name="test_logger", level="DEBUG")

        assert logger.name == "test_logger"
        assert logger.level == logging.DEBUG
        assert any(
            isinstance(handler.formatter, monitoring.JSONFormatter)
            for handler in logger.handlers
        )


class TestSlackNotifier:
    """Test Slack alert notifier."""

    def test_disabled_when_webhook_missing(self):
        notifier = monitoring.SlackNotifier(webhook_url=None)

        assert notifier.enabled is False
        assert notifier.send_alert("message") is False

    def test_send_alert_success(self, monkeypatch):
        response = Mock()
        response.raise_for_status = Mock()
        mock_post = Mock(return_value=response)
        monkeypatch.setattr(monitoring.requests, "post", mock_post)

        notifier = monitoring.SlackNotifier(webhook_url="https://example.com")
        result = notifier.send_alert("warning", severity="warning", context={"k": "v"})

        assert result is True
        payload = mock_post.call_args.kwargs["json"]
        assert payload["attachments"][0]["color"] == "warning"
        assert payload["attachments"][0]["fields"][0]["title"] == "k"

    def test_send_alert_failure(self, monkeypatch):
        mock_post = Mock(side_effect=Exception("network"))
        monkeypatch.setattr(monitoring.requests, "post", mock_post)

        notifier = monitoring.SlackNotifier(webhook_url="https://example.com")

        assert notifier.send_alert("error", severity="error") is False

    def test_send_error_and_info_helpers(self, monkeypatch):
        response = Mock()
        response.raise_for_status = Mock()
        mock_post = Mock(return_value=response)
        monkeypatch.setattr(monitoring.requests, "post", mock_post)

        notifier = monitoring.SlackNotifier(webhook_url="https://example.com")

        assert notifier.send_error("error") is True
        assert notifier.send_info("info") is True

        payloads = [call.kwargs["json"] for call in mock_post.call_args_list]
        assert payloads[0]["attachments"][0]["color"] == "danger"
        assert payloads[1]["attachments"][0]["color"] == "good"


class TestPerformanceTracker:
    """Test performance metrics collection."""

    def test_track_and_get_metrics(self):
        tracker = monitoring.PerformanceTracker()

        tracker.track_endpoint("/test", 0.2, 200)
        tracker.track_endpoint("/test", 0.6, 500)

        metrics = tracker.get_metrics("/test")

        assert metrics["count"] == 2
        assert metrics["avg_duration_ms"] == pytest.approx(400.0, rel=1e-3)
        assert metrics["max_duration_ms"] == pytest.approx(600.0, rel=1e-3)
        assert metrics["error_rate"] == pytest.approx(50.0, rel=1e-3)

    def test_get_metrics_all_endpoints(self):
        tracker = monitoring.PerformanceTracker()

        tracker.track_endpoint("/a", 0.1, 200)
        tracker.track_endpoint("/b", 0.2, 200)

        metrics = tracker.get_metrics()

        assert set(metrics.keys()) == {"/a", "/b"}
        assert metrics["/a"]["count"] == 1
        assert metrics["/b"]["count"] == 1


class TestMonitorPerformanceDecorator:
    """Test the monitor_performance decorator."""

    def test_monitor_performance_success(self, monkeypatch):
        mock_tracker = Mock()
        mock_slack = Mock()
        monkeypatch.setattr(monitoring, "perf_tracker", mock_tracker)
        monkeypatch.setattr(monitoring, "slack", mock_slack)

        times = iter([1.0, 1.2])
        monkeypatch.setattr(monitoring.time, "time", lambda: next(times))

        @monitoring.monitor_performance("/test")
        def handler():
            return {"ok": True}, 200

        result = handler()

        assert result == ({"ok": True}, 200)
        # Check call was made (allow floating point precision issues)
        assert mock_tracker.track_endpoint.call_count == 1
        call_args = mock_tracker.track_endpoint.call_args[0]
        assert call_args[0] == "/test"
        assert pytest.approx(call_args[1], rel=1e-2) == 0.2
        assert call_args[2] == 200
        mock_slack.send_warning.assert_not_called()

    def test_monitor_performance_slow_response(self, monkeypatch):
        mock_tracker = Mock()
        mock_slack = Mock()
        monkeypatch.setattr(monitoring, "perf_tracker", mock_tracker)
        monkeypatch.setattr(monitoring, "slack", mock_slack)

        times = iter([0.0, 3.5])
        monkeypatch.setattr(monitoring.time, "time", lambda: next(times))

        @monitoring.monitor_performance("/slow")
        def handler():
            return {"ok": True}, 200

        handler()

        mock_slack.send_warning.assert_called_once()

    def test_monitor_performance_error(self, monkeypatch):
        mock_tracker = Mock()
        mock_slack = Mock()
        monkeypatch.setattr(monitoring, "perf_tracker", mock_tracker)
        monkeypatch.setattr(monitoring, "slack", mock_slack)

        times = iter([0.0, 0.5])
        monkeypatch.setattr(monitoring.time, "time", lambda: next(times))

        @monitoring.monitor_performance("/error")
        def handler():
            raise ValueError("boom")

        with pytest.raises(ValueError):
            handler()

        mock_tracker.track_endpoint.assert_called_once_with("/error", 0.5, 500)
        mock_slack.send_error.assert_called_once()


class TestHealthChecks:
    """Test health check helpers."""

    def test_check_airtable_connection_false_when_no_client(self, monkeypatch):
        fake_doc = types.ModuleType("api.document_status")
        fake_doc.airtable_client = None
        monkeypatch.setitem(sys.modules, "api.document_status", fake_doc)

        assert monitoring.check_airtable_connection() is False

    def test_check_airtable_connection_true_when_client_present(self, monkeypatch):
        fake_doc = types.ModuleType("api.document_status")
        fake_doc.airtable_client = object()
        monkeypatch.setitem(sys.modules, "api.document_status", fake_doc)

        assert monitoring.check_airtable_connection() is True

    def test_check_schema_version_matches(self, monkeypatch):
        fake_doc = types.ModuleType("api.document_status")
        fake_doc.SCHEMA_VERSION = "2025-12-25T00:00:00+0400"
        monkeypatch.setitem(sys.modules, "api.document_status", fake_doc)

        class FakeValidator:
            def get_schema_version(self):
                return "2025-12-25T00:00:00+0400"

        fake_schema = types.ModuleType("api.schema_validator")
        fake_schema.SchemaValidator = FakeValidator
        monkeypatch.setitem(sys.modules, "api.schema_validator", fake_schema)

        assert monitoring.check_schema_version() is True

    def test_check_protected_fields_false_on_mismatch(self, monkeypatch):
        import airtable_locked_config

        monkeypatch.setattr(airtable_locked_config, "PROTECTED_FIELDS", {"A": ["a"]})

        assert monitoring.check_protected_fields() is False
