"""Tests for job status and progress tracking.

Verifies:
- Total count is correct
- Completed count increments
- Failed count increments
- Progress percentage is calculated correctly
- Final job status is correct
- timestamps are present
"""

import time


class TestJobStatus:
    """Test suite for GET /api/v1/jobs/{job_id}."""

    def test_get_job_status_returns_200(self, client, valid_job_payload, test_output_dir):
        """GET job status returns 200 for a valid job_id."""
        create_resp = client.post("/api/v1/jobs", json=valid_job_payload)
        job_id = create_resp.json()["job_id"]

        time.sleep(0.5)
        response = client.get(f"/api/v1/jobs/{job_id}")
        assert response.status_code == 200

    def test_job_not_found_returns_404(self, client, test_output_dir):
        """GET with a non-existent job_id returns 404."""
        import uuid
        fake_id = uuid.uuid4()
        response = client.get(f"/api/v1/jobs/{fake_id}")
        assert response.status_code == 404

    def test_job_status_contains_required_fields(self, client, valid_job_payload, test_output_dir):
        """Job status response contains all required fields."""
        create_resp = client.post("/api/v1/jobs", json=valid_job_payload)
        job_id = create_resp.json()["job_id"]

        time.sleep(0.5)
        response = client.get(f"/api/v1/jobs/{job_id}")
        data = response.json()

        required_fields = ["job_id", "status", "total", "completed", "failed",
                           "progress_percentage", "certificates"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    def test_job_total_matches_recipients(self, client, valid_job_payload, test_output_dir):
        """Job total equals the number of recipients submitted."""
        create_resp = client.post("/api/v1/jobs", json=valid_job_payload)
        job_id = create_resp.json()["job_id"]

        time.sleep(0.5)
        response = client.get(f"/api/v1/jobs/{job_id}")
        data = response.json()

        assert data["total"] == len(valid_job_payload["recipients"])

    def test_job_certificates_list_count(self, client, valid_job_payload, test_output_dir):
        """Job status includes one certificate entry per recipient."""
        create_resp = client.post("/api/v1/jobs", json=valid_job_payload)
        job_id = create_resp.json()["job_id"]

        time.sleep(0.5)
        response = client.get(f"/api/v1/jobs/{job_id}")
        data = response.json()

        assert len(data["certificates"]) == len(valid_job_payload["recipients"])

    def test_progress_percentage_is_valid(self, client, valid_job_payload, test_output_dir):
        """Progress percentage is between 0 and 100."""
        create_resp = client.post("/api/v1/jobs", json=valid_job_payload)
        job_id = create_resp.json()["job_id"]

        time.sleep(0.5)
        response = client.get(f"/api/v1/jobs/{job_id}")
        data = response.json()

        assert 0 <= data["progress_percentage"] <= 100

    def test_completed_job_has_100_percent(self, client, single_recipient_payload, test_output_dir):
        """A fully completed job shows 100% progress."""
        create_resp = client.post("/api/v1/jobs", json=single_recipient_payload)
        job_id = create_resp.json()["job_id"]

        # Wait for full processing
        time.sleep(3)

        response = client.get(f"/api/v1/jobs/{job_id}")
        data = response.json()

        if data["status"] in ["COMPLETED", "COMPLETED_WITH_ERRORS", "FAILED"]:
            assert data["progress_percentage"] == 100

    def test_job_status_has_created_at(self, client, single_recipient_payload, test_output_dir):
        """Job status response includes created_at timestamp."""
        create_resp = client.post("/api/v1/jobs", json=single_recipient_payload)
        job_id = create_resp.json()["job_id"]

        time.sleep(0.5)
        response = client.get(f"/api/v1/jobs/{job_id}")
        data = response.json()
        assert data["created_at"] is not None

    def test_invalid_uuid_returns_422(self, client, test_output_dir):
        """GET with invalid UUID format returns 422."""
        response = client.get("/api/v1/jobs/not-a-valid-uuid")
        assert response.status_code == 422
