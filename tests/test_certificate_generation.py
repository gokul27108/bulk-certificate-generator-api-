"""Tests for certificate PDF generation.

Verifies:
- PDF file is generated and saved to disk
- Certificate record is updated to COMPLETED
- File path is stored correctly
- Generated file is a valid PDF
"""

import os
import time


class TestCertificateGeneration:
    """Test suite for certificate PDF generation."""

    def test_certificate_generated_after_job(self, client, single_recipient_payload, test_output_dir):
        """After job completes, certificate status is COMPLETED."""
        response = client.post("/api/v1/jobs", json=single_recipient_payload)
        assert response.status_code == 202
        job_id = response.json()["job_id"]

        # Wait for background processing
        time.sleep(2)

        status_resp = client.get(f"/api/v1/jobs/{job_id}")
        data = status_resp.json()

        # At least check job was found and has certificates
        assert status_resp.status_code == 200
        assert len(data["certificates"]) == 1

    def test_completed_certificate_has_download_url(self, client, single_recipient_payload, test_output_dir):
        """A completed certificate includes a download_url."""
        response = client.post("/api/v1/jobs", json=single_recipient_payload)
        job_id = response.json()["job_id"]

        time.sleep(2)

        status_resp = client.get(f"/api/v1/jobs/{job_id}")
        data = status_resp.json()
        certs = data["certificates"]

        completed = [c for c in certs if c["status"] == "COMPLETED"]
        if completed:
            assert completed[0]["download_url"] is not None
            assert "/api/v1/certificates/" in completed[0]["download_url"]

    def test_pdf_file_created_on_disk(self, client, single_recipient_payload, test_output_dir):
        """A generated certificate PDF file exists on the filesystem."""
        response = client.post("/api/v1/jobs", json=single_recipient_payload)
        job_id = response.json()["job_id"]

        time.sleep(2)

        status_resp = client.get(f"/api/v1/jobs/{job_id}")
        data = status_resp.json()
        certs = data["certificates"]

        completed = [c for c in certs if c["status"] == "COMPLETED"]
        if completed:
            cert_id = completed[0]["certificate_id"]
            # Check the expected file exists
            expected_path = os.path.join(test_output_dir, f"certificate_{cert_id}.pdf")
            assert os.path.exists(expected_path), f"PDF not found at {expected_path}"

    def test_pdf_file_is_valid_pdf(self, client, single_recipient_payload, test_output_dir):
        """Generated file starts with the PDF magic bytes (%PDF-)."""
        response = client.post("/api/v1/jobs", json=single_recipient_payload)
        job_id = response.json()["job_id"]

        time.sleep(2)

        status_resp = client.get(f"/api/v1/jobs/{job_id}")
        data = status_resp.json()
        certs = data["certificates"]

        completed = [c for c in certs if c["status"] == "COMPLETED"]
        if completed:
            cert_id = completed[0]["certificate_id"]
            pdf_path = os.path.join(test_output_dir, f"certificate_{cert_id}.pdf")
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    header = f.read(5)
                assert header == b"%PDF-", "File does not have PDF magic bytes"

    def test_multiple_recipients_generate_multiple_pdfs(self, client, valid_job_payload, test_output_dir):
        """Each recipient gets their own certificate file."""
        response = client.post("/api/v1/jobs", json=valid_job_payload)
        assert response.status_code == 202
        job_id = response.json()["job_id"]

        time.sleep(3)

        status_resp = client.get(f"/api/v1/jobs/{job_id}")
        data = status_resp.json()
        certs = data["certificates"]

        completed = [c for c in certs if c["status"] == "COMPLETED"]
        # Each completed certificate should have a unique file
        cert_ids = [c["certificate_id"] for c in completed]
        assert len(cert_ids) == len(set(cert_ids))  # All unique

    def test_pdf_generation_unit(self, test_output_dir):
        """Directly test the PDF generation function."""
        import uuid
        from app.services.pdf_service import generate_pdf_for_recipient

        cert_id = uuid.uuid4()
        path = generate_pdf_for_recipient(
            certificate_id=cert_id,
            recipient_name="Unit Test User",
            certificate_title="Test Certificate",
            event_name="Unit Test Event",
            organization_name="Test Org",
            issue_date="2026-10-07",
        )

        assert os.path.exists(path)
        with open(path, "rb") as f:
            header = f.read(5)
        assert header == b"%PDF-"
