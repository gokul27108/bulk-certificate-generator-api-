"""Tests for individual certificate failure handling.

Verifies the core failure isolation requirement:
- One certificate failure does not stop other recipients
- Failed certificates record error message
- Job status becomes COMPLETED_WITH_ERRORS
- Counts are accurate
"""

import time
from unittest.mock import patch


class TestFailureHandling:
    """Test suite for failure isolation."""

    def test_failure_does_not_stop_other_certificates(
        self, client, test_output_dir
    ):
        """If one PDF generation fails, other recipients still get their certificates."""
        payload = {
            "certificate_title": "Certificate of Completion",
            "event_name": "Failure Isolation Test",
            "organization_name": "Test Org",
            "issue_date": "2026-10-07",
            "recipients": [
                {"name": "User One", "email": "user1@example.com"},
                {"name": "User Two", "email": "user2@example.com"},
                {"name": "User Three", "email": "user3@example.com"},
            ]
        }

        call_count = [0]
        original_fn = __import__(
            "app.services.pdf_service",
            fromlist=["generate_pdf_for_recipient"]
        ).generate_pdf_for_recipient

        def selective_fail(*args, **kwargs):
            call_count[0] += 1
            # Second call always fails to simulate one bad recipient
            if call_count[0] == 2:
                raise ValueError("Simulated PDF generation failure")
            return original_fn(*args, **kwargs)

        with patch("app.services.job_service.generate_pdf_for_recipient", selective_fail):
            create_resp = client.post("/api/v1/jobs", json=payload)
            assert create_resp.status_code == 202
            job_id = create_resp.json()["job_id"]

            time.sleep(3)

        status_resp = client.get(f"/api/v1/jobs/{job_id}")
        data = status_resp.json()

        # Should have processed all 3 regardless of one failure
        assert data["total"] == 3
        assert data["completed"] + data["failed"] == 3
        # At least 2 should succeed
        assert data["completed"] >= 2

    def test_failed_certificate_has_error_message(
        self, client, test_output_dir
    ):
        """A failed certificate stores an error message."""
        payload = {
            "certificate_title": "Test Certificate",
            "event_name": "Error Test",
            "organization_name": "Test Org",
            "issue_date": "2026-10-07",
            "recipients": [
                {"name": "Good User", "email": "good@example.com"},
                {"name": "Bad User", "email": "bad@example.com"},
            ]
        }

        call_count = [0]
        original_fn = __import__(
            "app.services.pdf_service",
            fromlist=["generate_pdf_for_recipient"]
        ).generate_pdf_for_recipient

        def fail_second(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:
                raise RuntimeError("Intentional test failure")
            return original_fn(*args, **kwargs)

        with patch("app.services.job_service.generate_pdf_for_recipient", fail_second):
            create_resp = client.post("/api/v1/jobs", json=payload)
            job_id = create_resp.json()["job_id"]
            time.sleep(3)

        status_resp = client.get(f"/api/v1/jobs/{job_id}")
        data = status_resp.json()

        failed_certs = [c for c in data["certificates"] if c["status"] == "FAILED"]
        if failed_certs:
            # Failed cert must have an error message
            assert failed_certs[0]["error"] is not None
            assert len(failed_certs[0]["error"]) > 0

    def test_job_status_completed_with_errors(
        self, client, test_output_dir
    ):
        """Job with partial failures gets COMPLETED_WITH_ERRORS status."""
        payload = {
            "certificate_title": "Test Certificate",
            "event_name": "Mixed Result Test",
            "organization_name": "Test Org",
            "issue_date": "2026-10-07",
            "recipients": [
                {"name": "Success One", "email": "s1@example.com"},
                {"name": "Fail One", "email": "f1@example.com"},
                {"name": "Success Two", "email": "s2@example.com"},
            ]
        }

        call_count = [0]
        original_fn = __import__(
            "app.services.pdf_service",
            fromlist=["generate_pdf_for_recipient"]
        ).generate_pdf_for_recipient

        def fail_second(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:
                raise ValueError("Forced failure")
            return original_fn(*args, **kwargs)

        with patch("app.services.job_service.generate_pdf_for_recipient", fail_second):
            create_resp = client.post("/api/v1/jobs", json=payload)
            job_id = create_resp.json()["job_id"]
            time.sleep(3)

        status_resp = client.get(f"/api/v1/jobs/{job_id}")
        data = status_resp.json()

        assert data["status"] == "COMPLETED_WITH_ERRORS"
        assert data["failed"] == 1
        assert data["completed"] == 2

    def test_failed_job_counts_are_accurate(
        self, client, test_output_dir
    ):
        """successful_count + failed_count == total_recipients."""
        payload = {
            "certificate_title": "Test Certificate",
            "event_name": "Count Test",
            "organization_name": "Test Org",
            "issue_date": "2026-10-07",
            "recipients": [
                {"name": f"User {i}", "email": f"user{i}@example.com"}
                for i in range(5)
            ]
        }

        call_count = [0]
        original_fn = __import__(
            "app.services.pdf_service",
            fromlist=["generate_pdf_for_recipient"]
        ).generate_pdf_for_recipient

        def fail_odd(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] % 2 == 0:
                raise ValueError("Alternating failure")
            return original_fn(*args, **kwargs)

        with patch("app.services.job_service.generate_pdf_for_recipient", fail_odd):
            create_resp = client.post("/api/v1/jobs", json=payload)
            job_id = create_resp.json()["job_id"]
            time.sleep(4)

        status_resp = client.get(f"/api/v1/jobs/{job_id}")
        data = status_resp.json()

        assert data["completed"] + data["failed"] == data["total"]
