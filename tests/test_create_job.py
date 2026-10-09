"""Tests for creating generation jobs.

Verifies:
- Valid request creates a job and returns job_id
- Correct initial state (PENDING, 0 completed, 0 failed)
- HTTP 202 Accepted is returned
- Job can be retrieved after creation
"""

import time


class TestCreateJob:
    """Test suite for POST /api/v1/jobs."""

    def test_create_job_returns_202(self, client, valid_job_payload, test_output_dir):
        """Creating a valid job returns HTTP 202 Accepted."""
        response = client.post("/api/v1/jobs", json=valid_job_payload)
        assert response.status_code == 202

    def test_create_job_returns_job_id(self, client, valid_job_payload, test_output_dir):
        """Response includes a valid UUID job_id."""
        response = client.post("/api/v1/jobs", json=valid_job_payload)
        data = response.json()
        assert "job_id" in data
        # Verify it's a valid UUID format
        import uuid
        uuid.UUID(str(data["job_id"]))

    def test_create_job_initial_status_is_pending(self, client, valid_job_payload, test_output_dir):
        """Newly created job has PENDING status."""
        response = client.post("/api/v1/jobs", json=valid_job_payload)
        data = response.json()
        assert data["status"] == "PENDING"

    def test_create_job_correct_recipient_count(self, client, valid_job_payload, test_output_dir):
        """Total count matches the number of recipients submitted."""
        response = client.post("/api/v1/jobs", json=valid_job_payload)
        data = response.json()
        assert data["total"] == len(valid_job_payload["recipients"])

    def test_create_job_initial_completed_is_zero(self, client, valid_job_payload, test_output_dir):
        """Initially, completed count is 0."""
        response = client.post("/api/v1/jobs", json=valid_job_payload)
        data = response.json()
        assert data["completed"] == 0

    def test_create_job_initial_failed_is_zero(self, client, valid_job_payload, test_output_dir):
        """Initially, failed count is 0."""
        response = client.post("/api/v1/jobs", json=valid_job_payload)
        data = response.json()
        assert data["failed"] == 0

    def test_create_job_includes_message(self, client, valid_job_payload, test_output_dir):
        """Response includes a human-readable message."""
        response = client.post("/api/v1/jobs", json=valid_job_payload)
        data = response.json()
        assert "message" in data
        assert len(data["message"]) > 0

    def test_create_job_with_single_recipient(self, client, single_recipient_payload, test_output_dir):
        """Job with one recipient is created successfully."""
        response = client.post("/api/v1/jobs", json=single_recipient_payload)
        assert response.status_code == 202
        assert response.json()["total"] == 1

    def test_created_job_retrievable_by_id(self, client, valid_job_payload, test_output_dir):
        """After creating a job, it can be retrieved via GET /jobs/{job_id}."""
        create_resp = client.post("/api/v1/jobs", json=valid_job_payload)
        job_id = create_resp.json()["job_id"]

        # Wait briefly for background tasks in TestClient
        time.sleep(0.5)

        get_resp = client.get(f"/api/v1/jobs/{job_id}")
        assert get_resp.status_code == 200
        assert str(get_resp.json()["job_id"]) == str(job_id)
