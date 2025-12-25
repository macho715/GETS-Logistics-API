"""
Load Testing with Locust
Test API performance under concurrent load

Usage:
  # Run with 10 concurrent users for 30 seconds
  locust -f tests/load_test.py --users 10 --spawn-rate 2 --run-time 30s --headless

  # Run with web UI
  locust -f tests/load_test.py --host https://gets-416ut4t8g-chas-projects-08028e73.vercel.app
"""

from locust import HttpUser, task, between, events
import json
from datetime import datetime


class GETSApiUser(HttpUser):
    """
    Simulates a user interacting with GETS API
    
    Weight distribution:
    - Health checks: 30% (most frequent)
    - Approval/Bottleneck summaries: 40% (dashboard queries)
    - Document status: 20% (specific lookups)
    - Events/ingest: 10% (less frequent)
    """
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    host = "https://gets-416ut4t8g-chas-projects-08028e73.vercel.app"
    
    def on_start(self):
        """Called when a user starts"""
        self.test_shpt_no = "SCT-0143"
    
    @task(3)
    def test_health(self):
        """Health check endpoint (high frequency)"""
        self.client.get("/health", name="/health")
    
    @task(2)
    def test_approval_summary(self):
        """Approval summary (dashboard)"""
        with self.client.get(
            "/approval/summary",
            name="/approval/summary",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "summary" in data and "byType" in data:
                    response.success()
                else:
                    response.failure("Missing expected fields")
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(2)
    def test_bottleneck_summary(self):
        """Bottleneck summary (dashboard)"""
        with self.client.get(
            "/bottleneck/summary",
            name="/bottleneck/summary",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "byCode" in data and "aging" in data:
                    response.success()
                else:
                    response.failure("Missing expected fields")
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(2)
    def test_approval_status(self):
        """Approval status for specific shipment"""
        with self.client.get(
            f"/approval/status/{self.test_shpt_no}",
            name="/approval/status/{shptNo}",
            catch_response=True
        ) as response:
            # 200 or 404 are both acceptable
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")
    
    @task(1)
    def test_document_status(self):
        """Document status for specific shipment"""
        with self.client.get(
            f"/document/status/{self.test_shpt_no}",
            name="/document/status/{shptNo}",
            catch_response=True
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")
    
    @task(1)
    def test_document_events(self):
        """Document events for specific shipment"""
        with self.client.get(
            f"/document/events/{self.test_shpt_no}",
            name="/document/events/{shptNo}",
            catch_response=True
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")
    
    @task(1)
    def test_status_summary(self):
        """KPI status summary"""
        with self.client.get(
            "/status/summary",
            name="/status/summary",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")


class GETSApiAdminUser(HttpUser):
    """
    Simulates an admin user performing write operations
    Lower frequency, heavier operations
    """
    
    wait_time = between(5, 10)  # Less frequent
    host = "https://gets-416ut4t8g-chas-projects-08028e73.vercel.app"
    
    @task(1)
    def test_ingest_events(self):
        """Test event ingestion (write operation)"""
        payload = {
            "batchId": f"LOAD_TEST_{datetime.now().isoformat()}",
            "sourceSystem": "LOAD_TEST",
            "events": [
                {
                    "timestamp": datetime.now().isoformat() + "+04:00",
                    "shptNo": "LOAD-TEST-001",
                    "entityType": "DOCUMENT",
                    "toStatus": "SUBMITTED",
                }
            ]
        }
        
        with self.client.post(
            "/ingest/events",
            json=payload,
            headers={"Content-Type": "application/json"},
            name="/ingest/events",
            catch_response=True
        ) as response:
            # 200 or 503 (no connection) are acceptable in load test
            if response.status_code in [200, 503]:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")


# Custom event handlers for reporting
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts"""
    print(f"\n{'='*60}")
    print("GETS API Load Test Starting")
    print(f"Target: {GETSApiUser.host}")
    print(f"{'='*60}\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops"""
    print(f"\n{'='*60}")
    print("GETS API Load Test Completed")
    
    # Print summary statistics
    stats = environment.stats
    print(f"\nTotal Requests: {stats.total.num_requests}")
    print(f"Total Failures: {stats.total.num_failures}")
    print(f"Success Rate: {((stats.total.num_requests - stats.total.num_failures) / stats.total.num_requests * 100):.2f}%")
    print(f"Median Response Time: {stats.total.median_response_time} ms")
    print(f"95th Percentile: {stats.total.get_response_time_percentile(0.95)} ms")
    print(f"Requests/sec: {stats.total.total_rps:.2f}")
    print(f"{'='*60}\n")


# Performance thresholds (optional)
RESPONSE_TIME_THRESHOLD = 2000  # 2 seconds
SUCCESS_RATE_THRESHOLD = 0.95   # 95%


@events.quitting.add_listener
def check_thresholds(environment, **kwargs):
    """Check if performance thresholds are met"""
    stats = environment.stats.total
    
    median_rt = stats.median_response_time
    success_rate = (stats.num_requests - stats.num_failures) / stats.num_requests
    
    if median_rt > RESPONSE_TIME_THRESHOLD:
        print(f"⚠️  WARNING: Median response time ({median_rt} ms) exceeds threshold ({RESPONSE_TIME_THRESHOLD} ms)")
        environment.process_exit_code = 1
    
    if success_rate < SUCCESS_RATE_THRESHOLD:
        print(f"⚠️  WARNING: Success rate ({success_rate*100:.2f}%) below threshold ({SUCCESS_RATE_THRESHOLD*100}%)")
        environment.process_exit_code = 1

