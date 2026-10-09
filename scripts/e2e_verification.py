"""End-to-End verification script.

Executes the complete manual verification flow:
1. Create a job with 5 recipients
2. Verify job ID is returned
3. Check job status
4. Wait for processing
5. Verify all successful certificates
6. Download one certificate
7. Verify PDF opens and has valid magic bytes
8. Create a job containing one failing recipient (via selective mock)
9. Verify the other recipients still generate successfully
10. Verify COMPLETED_WITH_ERRORS and correct counts
11. Test invalid request (422)
12. Test invalid job ID (404)
13. Test invalid certificate ID (404)
"""

import time
import uuid
import sys
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.core.database import Base, engine
from app.models import generation_job, certificate  # noqa

# Ensure tables exist
Base.metadata.create_all(bind=engine)

client = TestClient(app)

def run_verification():
    print("=" * 70)
    print("STARTING COMPLETE END-TO-END VERIFICATION FLOW")
    print("=" * 70)

    # -------------------------------------------------------------
    # Step 1 & 2: Create a job with 5 recipients and verify job ID
    # -------------------------------------------------------------
    print("\n[Step 1 & 2] Submitting job with 5 recipients...")
    payload_5 = {
        "certificate_title": "Certificate of Excellence",
        "event_name": "Full Stack Backend Mastery",
        "organization_name": "Aero Engineering Academy",
        "issue_date": "2026-10-07",
        "recipients": [
            {"name": "Gokul M", "email": "gokul@example.com"},
            {"name": "Rahul Kumar", "email": "rahul@example.com"},
            {"name": "Priya Sharma", "email": "priya@example.com"},
            {"name": "Ananya Roy", "email": "ananya@example.com"},
            {"name": "Vikram Patel", "email": "vikram@example.com"},
        ]
    }
    resp = client.post("/api/v1/jobs", json=payload_5)
    assert resp.status_code == 202, f"Expected 202, got {resp.status_code}"
    job_data = resp.json()
    job_id = job_data["job_id"]
    print(f" -> Job created successfully! HTTP 202 Accepted. Job ID: {job_id}")
    assert job_data["total"] == 5
    assert job_data["status"] == "PENDING"

    # -------------------------------------------------------------
    # Step 3, 4, 5: Check status, wait for completion, verify
    # -------------------------------------------------------------
    print("\n[Step 3, 4, 5] Waiting for background processing to complete...")
    max_wait = 15
    start_time = time.time()
    final_status = None
    while time.time() - start_time < max_wait:
        status_resp = client.get(f"/api/v1/jobs/{job_id}")
        assert status_resp.status_code == 200
        final_status = status_resp.json()
        if final_status["status"] in ["COMPLETED", "COMPLETED_WITH_ERRORS", "FAILED"]:
            break
        time.sleep(1)

    print(f" -> Final Status: {final_status['status']}")
    print(f" -> Total: {final_status['total']} | Completed: {final_status['completed']} | Failed: {final_status['failed']}")
    print(f" -> Progress: {final_status['progress_percentage']}%")
    assert final_status["status"] == "COMPLETED"
    assert final_status["completed"] == 5
    assert final_status["failed"] == 0
    assert final_status["progress_percentage"] == 100
    assert len(final_status["certificates"]) == 5

    # -------------------------------------------------------------
    # Step 6 & 7: Download one certificate and verify PDF format
    # -------------------------------------------------------------
    print("\n[Step 6 & 7] Downloading certificate for recipient #1...")
    cert_id = final_status["certificates"][0]["certificate_id"]
    download_url = final_status["certificates"][0]["download_url"]
    dl_resp = client.get(download_url)
    assert dl_resp.status_code == 200
    assert dl_resp.headers["content-type"] == "application/pdf"
    content = dl_resp.content
    assert content[:5] == b"%PDF-", "File header does not match %PDF- magic bytes!"
    print(f" -> Successfully downloaded certificate {cert_id}")
    print(f" -> Content-Type: {dl_resp.headers['content-type']}")
    print(f" -> Size: {len(content)} bytes. Magic bytes: {content[:5].decode('latin1')}")

    # -------------------------------------------------------------
    # Step 8, 9, 10: Intentionally failing recipient (Failure Isolation)
    # -------------------------------------------------------------
    print("\n[Step 8, 9, 10] Testing Failure Isolation with mixed batch (3 recipients, 1 failing)...")
    payload_failure = {
        "certificate_title": "Certificate of Completion",
        "event_name": "Failure Resilience Lab",
        "organization_name": "Aero",
        "issue_date": "2026-10-07",
        "recipients": [
            {"name": "Valid Recipient One", "email": "valid1@example.com"},
            {"name": "Intentional Failure Recipient", "email": "fail@example.com"},
            {"name": "Valid Recipient Two", "email": "valid2@example.com"},
        ]
    }

    import app.services.job_service as js
    real_pdf_generator = js.generate_pdf_for_recipient

    def fail_specific_recipient(*args, **kwargs):
        if kwargs.get("recipient_name") == "Intentional Failure Recipient":
            raise ValueError("Intentional simulated rendering fault for validation")
        return real_pdf_generator(*args, **kwargs)

    with patch.object(js, "generate_pdf_for_recipient", side_effect=fail_specific_recipient):
        f_resp = client.post("/api/v1/jobs", json=payload_failure)
        assert f_resp.status_code == 202
        f_job_id = f_resp.json()["job_id"]
        time.sleep(4)

        f_status_resp = client.get(f"/api/v1/jobs/{f_job_id}")
        f_status = f_status_resp.json()

    print(f" -> Failure Job Status: {f_status['status']}")
    print(f" -> Total: {f_status['total']} | Completed: {f_status['completed']} | Failed: {f_status['failed']}")
    assert f_status["status"] == "COMPLETED_WITH_ERRORS"
    assert f_status["total"] == 3
    assert f_status["completed"] == 2
    assert f_status["failed"] == 1

    # Verify failed cert has error message
    failed_items = [c for c in f_status["certificates"] if c["status"] == "FAILED"]
    assert len(failed_items) == 1
    print(f" -> Failed Recipient: {failed_items[0]['recipient_name']}")
    print(f" -> Error captured: {failed_items[0]['error']}")
    assert "Intentional simulated rendering fault" in failed_items[0]["error"]

    # Verify valid certs in the same batch succeeded and have download URLs
    success_items = [c for c in f_status["certificates"] if c["status"] == "COMPLETED"]
    assert len(success_items) == 2
    for s in success_items:
        print(f" -> Successful sibling in same batch: {s['recipient_name']} (URL: {s['download_url']})")
        assert s["download_url"] is not None

    # -------------------------------------------------------------
    # Step 11: Test invalid request
    # -------------------------------------------------------------
    print("\n[Step 11] Testing invalid request body...")
    bad_resp = client.post("/api/v1/jobs", json={"certificate_title": ""})
    assert bad_resp.status_code == 422
    print(f" -> Empty payload correctly rejected: HTTP {bad_resp.status_code} Unprocessable Entity")

    # -------------------------------------------------------------
    # Step 12: Test invalid job ID
    # -------------------------------------------------------------
    print("\n[Step 12] Testing non-existent job ID...")
    fake_job_uuid = uuid.uuid4()
    not_found_job = client.get(f"/api/v1/jobs/{fake_job_uuid}")
    assert not_found_job.status_code == 404
    print(f" -> Unknown job correctly returns HTTP 404 Not Found: {not_found_job.json()}")

    # -------------------------------------------------------------
    # Step 13: Test invalid certificate ID
    # -------------------------------------------------------------
    print("\n[Step 13] Testing non-existent certificate ID...")
    fake_cert_uuid = uuid.uuid4()
    not_found_cert = client.get(f"/api/v1/certificates/{fake_cert_uuid}")
    assert not_found_cert.status_code == 404
    print(f" -> Unknown certificate correctly returns HTTP 404 Not Found: {not_found_cert.json()}")

    # Download failed certificate verification
    print("\n[Step 13b] Testing downloading of FAILED certificate record...")
    failed_cert_id = failed_items[0]["certificate_id"]
    dl_fail_resp = client.get(f"/api/v1/certificates/{failed_cert_id}")
    assert dl_fail_resp.status_code == 422
    print(f" -> Downloading failed certificate correctly returns HTTP 422: {dl_fail_resp.json()}")

    print("\n" + "=" * 70)
    print("ALL 13 END-TO-END VERIFICATION STEPS PASSED WITH 100% SUCCESS!")
    print("=" * 70)

if __name__ == "__main__":
    run_verification()
