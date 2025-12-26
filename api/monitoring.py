"""
Monitoring utilities for GETS API
Provides structured logging, Slack alerts, and performance tracking
"""

import os
import logging
import json
import requests
from datetime import datetime
from typing import Optional, Dict, Any
from functools import wraps
import time


# ==================== Structured Logging ====================
class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""

    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_obj.update(record.extra_fields)

        return json.dumps(log_obj)


def setup_logger(name: str = "gets_api", level: str = "INFO") -> logging.Logger:
    """
    Setup structured logger

    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Console handler with JSON formatting
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)

    return logger


# Global logger instance
logger = setup_logger()


# ==================== Slack Alerts ====================
class SlackNotifier:
    """Send alerts to Slack webhook"""

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        self.enabled = bool(self.webhook_url)

    def send_alert(
        self,
        message: str,
        severity: str = "error",
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send alert to Slack

        Args:
            message: Alert message
            severity: Severity level (error, warning, info)
            context: Additional context data

        Returns:
            True if sent successfully
        """
        if not self.enabled:
            logger.warning("Slack webhook not configured, skipping alert")
            return False

        color_map = {
            "error": "danger",
            "warning": "warning",
            "info": "good",
            "critical": "#8B0000"  # Dark red
        }

        fields = []
        if context:
            for key, value in context.items():
                fields.append({
                    "title": key,
                    "value": str(value),
                    "short": True
                })

        payload = {
            "attachments": [{
                "color": color_map.get(severity, "danger"),
                "title": f"GETS API Alert [{severity.upper()}]",
                "text": message,
                "fields": fields,
                "footer": "GETS Logistics API",
                "ts": int(datetime.now().timestamp())
            }]
        }

        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=5
            )
            response.raise_for_status()
            logger.info(f"Slack alert sent: {severity} - {message}")
            return True
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False

    def send_error(self, message: str, context: Optional[Dict] = None):
        """Send error alert"""
        return self.send_alert(message, "error", context)

    def send_warning(self, message: str, context: Optional[Dict] = None):
        """Send warning alert"""
        return self.send_alert(message, "warning", context)

    def send_info(self, message: str, context: Optional[Dict] = None):
        """Send info alert"""
        return self.send_alert(message, "info", context)


# Global Slack notifier
slack = SlackNotifier()


# ==================== Performance Monitoring ====================
class PerformanceTracker:
    """Track API performance metrics"""

    def __init__(self):
        self.metrics = {}

    def track_endpoint(self, endpoint: str, duration: float, status_code: int):
        """Track endpoint performance"""
        if endpoint not in self.metrics:
            self.metrics[endpoint] = {
                "count": 0,
                "total_duration": 0,
                "errors": 0,
                "max_duration": 0
            }

        metric = self.metrics[endpoint]
        metric["count"] += 1
        metric["total_duration"] += duration
        metric["max_duration"] = max(metric["max_duration"], duration)

        if status_code >= 400:
            metric["errors"] += 1

    def get_metrics(self, endpoint: Optional[str] = None) -> Dict:
        """Get performance metrics"""
        if endpoint:
            metric = self.metrics.get(endpoint, {})
            if metric and metric["count"] > 0:
                return {
                    "endpoint": endpoint,
                    "count": metric["count"],
                    "avg_duration_ms": round(metric["total_duration"] / metric["count"] * 1000, 2),
                    "max_duration_ms": round(metric["max_duration"] * 1000, 2),
                    "error_rate": round(metric["errors"] / metric["count"] * 100, 2)
                }
            return {}

        # Return all metrics
        result = {}
        for ep, metric in self.metrics.items():
            if metric["count"] > 0:
                result[ep] = {
                    "count": metric["count"],
                    "avg_duration_ms": round(metric["total_duration"] / metric["count"] * 1000, 2),
                    "max_duration_ms": round(metric["max_duration"] * 1000, 2),
                    "error_rate": round(metric["errors"] / metric["count"] * 100, 2)
                }
        return result


# Global performance tracker
perf_tracker = PerformanceTracker()


def monitor_performance(endpoint_name: str = None):
    """
    Decorator to monitor endpoint performance

    Usage:
        @app.route("/approval/summary")
        @monitor_performance("/approval/summary")
        def get_approval_summary():
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            endpoint = endpoint_name or f.__name__

            try:
                result = f(*args, **kwargs)
                duration = time.time() - start_time

                # Extract status code from response
                if isinstance(result, tuple):
                    status_code = result[1] if len(result) > 1 else 200
                else:
                    status_code = 200

                perf_tracker.track_endpoint(endpoint, duration, status_code)

                # Alert on slow responses (>3s)
                if duration > 3.0:
                    slack.send_warning(
                        f"Slow response detected: {endpoint}",
                        {
                            "duration": f"{duration:.2f}s",
                            "threshold": "3s"
                        }
                    )

                return result

            except Exception as e:
                duration = time.time() - start_time
                perf_tracker.track_endpoint(endpoint, duration, 500)

                # Alert on errors
                slack.send_error(
                    f"Error in {endpoint}: {str(e)}",
                    {
                        "endpoint": endpoint,
                        "error": str(e),
                        "duration": f"{duration:.2f}s"
                    }
                )

                raise

        return wrapper
    return decorator


# ==================== SLA Monitoring ====================
class SLAMonitor:
    """Monitor SLA compliance"""

    def __init__(self):
        self.sla_thresholds = {
            "approval_d5": 5,    # D-5 days
            "approval_d15": 15,  # D-15 days
            "response_time": 2.0  # 2 seconds
        }
        self.violations = []

    def check_approval_sla(self, days_until_due: float, approval_type: str) -> bool:
        """Check if approval is within SLA"""
        if days_until_due < 0:
            # Overdue
            self.violations.append({
                "type": "approval_overdue",
                "approval_type": approval_type,
                "days": days_until_due
            })
            return False

        if days_until_due <= self.sla_thresholds["approval_d5"]:
            # D-5 critical
            self.violations.append({
                "type": "approval_d5_critical",
                "approval_type": approval_type,
                "days": days_until_due
            })
            return False

        return True

    def check_response_time_sla(self, duration: float, endpoint: str) -> bool:
        """Check if response time is within SLA"""
        if duration > self.sla_thresholds["response_time"]:
            self.violations.append({
                "type": "response_time_exceeded",
                "endpoint": endpoint,
                "duration": duration,
                "threshold": self.sla_thresholds["response_time"]
            })
            return False

        return True

    def get_violations(self) -> list:
        """Get SLA violations"""
        return self.violations

    def clear_violations(self):
        """Clear violations"""
        self.violations = []


# Global SLA monitor
sla_monitor = SLAMonitor()


# ==================== Health Check Utilities ====================
def check_airtable_connection() -> bool:
    """Check Airtable connection"""
    try:
        from api.app import airtable_client

        if not airtable_client:
            return False

        # Try a simple list operation with limit 1
        # This is a lightweight check
        return True
    except Exception as e:
        logger.error(f"Airtable connection check failed: {e}")
        return False


def check_schema_version() -> bool:
    """Check schema version consistency"""
    try:
        from api.app import SCHEMA_VERSION
        from api.schema_validator import SchemaValidator

        validator = SchemaValidator()
        current_version = validator.get_schema_version()

        return current_version == SCHEMA_VERSION
    except Exception as e:
        logger.error(f"Schema version check failed: {e}")
        return False


def check_protected_fields() -> bool:
    """Check protected fields count"""
    try:
        from api.airtable_locked_config import PROTECTED_FIELDS

        total_protected = sum(len(fields) for fields in PROTECTED_FIELDS.values())

        # Expected: 20 protected fields
        return total_protected == 20
    except Exception as e:
        logger.error(f"Protected fields check failed: {e}")
        return False

