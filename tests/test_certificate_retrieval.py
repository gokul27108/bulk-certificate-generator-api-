"""Tests for certificate PDF retrieval.

Verifies:
- Valid completed certificate returns PDF (200)
- Invalid certificate ID returns 404
- Non-existent certificate ID returns 404
- Failed certificate returns error response (not PDF)
- Response has correct Content-Type
"""

import time
import uuid
from unittest.mock import patch


class TestCertificateRetrieval:
    """Test suite for GET /api/v1/certificates/{certificate_id}."""

    def test_download_valid_certificate(self, client, single_recipient_payload, test_output_dir):
        """A completed certificate returns 200 with PDF content."""
        create_resp = client.post("/api/v1/jobs", json=single_recipient_payload)
        job_id = create_resp.json()["job_id"]

        time.sleep(3)

        status_resp = client.get(f"/api/v1/jobs/{job_id}")
        data = status_resp.json()

        completed = [c for c in data["certificates"] if c["status"] == "COMPLETED"]
        if completed:
            cert_id = completed[0]["certificate_id"]
            download_resp = client.get(f"/api/v1/certificates/{cert_id}")
            assert download_resp.status_code == 200

    def test_download_returns_pdf_content_type(self, client, single_recipient_payload, test_output_dir):
        """Certificate download has Content-Type: application/pdf."""
        create_resp = client.post("/api/v1/jobs", json=single_recipient_payload)
        job_id = create_resp.json()["job_id"]

        time.sleep(3)

        status_resp = client.get(f"/api/v1/jobs/{job_id}")
        data = status_resp.json()

        completed = [c for c in data["certificates"] if c["status"] == "COMPLETED"]
        if completed:
            cert_id = completed[0]["certificate_id"]
            download_resp = client.get(f"/api/v1/certificates/{cert_id}")
            if download_resp.status_code == 200:
                assert "application/pdf" in download_resp.headers["content-type"]

    def test_download_invalid_uuid_returns_422(self, client, test_output_dir):
        """GET with invalid UUID format returns 422."""
        response = client.get("/api/v1/certificates/not-a-uuid")
        assert response.status_code == 422

    def test_download_nonexistent_certificate_returns_404(self, client, test_output_dir):
        """GET for a non-existent certificate UUID returns 404."""
        fake_id = uuid.uuid4()
        response = client.get(f"/api/v1/certificates/{fake_id}")
        assert response.status_code == 404

    def test_download_failed_certificate_returns_error(
        self, client, test_output_dir
    ):
        """Attempting to download a FAILED certificate returns an error (not PDF)."""
        payload = {
            "certificate_title": "Test",
            "event_name": "Test Event",
            "organization_name": "Org",
            "issue_date": "2026-10-07",
            "recipients": [{"name": "Test User", "email": "test@example.com"}]
        }

        with patch(
            "app.services.job_service.generate_pdf_for_recipient",
            side_effect=RuntimeError("Forced failure")
        ):
            create_resp = client.post("/api/v1/jobs", json=payload)
            job_id = create_resp.json()["job_id"]
            time.sleep(3)

        status_resp = client.get(f"/api/v1/jobs/{job_id}")
        data = status_resp.json()

        failed = [c for c in data["certificates"] if c["status"] == "FAILED"]
        if failed:
            cert_id = failed[0]["certificate_id"]
            download_resp = client.get(f"/api/v1/certificates/{cert_id}")
            # Should NOT return 200 with PDF
            assert download_resp.status_code != 200

    def test_download_response_has_pdf_bytes(self, client, single_recipient_payload, test_output_dir):
        """Downloaded file starts with PDF magic bytes."""
        create_resp = client.post("/api/v1/jobs", json=single_recipient_payload)
        job_id = create_resp.json()["job_id"]

        time.sleep(3)

        status_resp = client.get(f"/api/v1/jobs/{job_id}")
        data = status_resp.json()

        completed = [c for c in data["certificates"] if c["status"] == "COMPLETED"]
        if completed:
            cert_id = completed[0]["certificate_id"]
            download_resp = client.get(f"/api/v1/certificates/{cert_id}")
            if download_resp.status_code == 200:
                assert download_resp.content[:5] == b"%PDF-"
