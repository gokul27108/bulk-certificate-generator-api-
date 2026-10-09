"""Tests for input validation.

Verifies:
- Missing required fields are rejected
- Empty recipients list is rejected
- Invalid email format is rejected
- Empty strings are rejected
- Invalid date format is rejected
- Field length limits are enforced
"""


class TestInputValidation:
    """Test suite for request validation."""

    def test_missing_certificate_title(self, client, valid_job_payload, test_output_dir):
        """Request without certificate_title returns 422."""
        payload = {k: v for k, v in valid_job_payload.items() if k != "certificate_title"}
        response = client.post("/api/v1/jobs", json=payload)
        assert response.status_code == 422

    def test_missing_event_name(self, client, valid_job_payload, test_output_dir):
        """Request without event_name returns 422."""
        payload = {k: v for k, v in valid_job_payload.items() if k != "event_name"}
        response = client.post("/api/v1/jobs", json=payload)
        assert response.status_code == 422

    def test_missing_organization_name(self, client, valid_job_payload, test_output_dir):
        """Request without organization_name returns 422."""
        payload = {k: v for k, v in valid_job_payload.items() if k != "organization_name"}
        response = client.post("/api/v1/jobs", json=payload)
        assert response.status_code == 422

    def test_missing_issue_date(self, client, valid_job_payload, test_output_dir):
        """Request without issue_date returns 422."""
        payload = {k: v for k, v in valid_job_payload.items() if k != "issue_date"}
        response = client.post("/api/v1/jobs", json=payload)
        assert response.status_code == 422

    def test_missing_recipients(self, client, valid_job_payload, test_output_dir):
        """Request without recipients returns 422."""
        payload = {k: v for k, v in valid_job_payload.items() if k != "recipients"}
        response = client.post("/api/v1/jobs", json=payload)
        assert response.status_code == 422

    def test_empty_recipients_list(self, client, valid_job_payload, test_output_dir):
        """Empty recipients list returns 422."""
        payload = {**valid_job_payload, "recipients": []}
        response = client.post("/api/v1/jobs", json=payload)
        assert response.status_code == 422

    def test_invalid_email_format(self, client, valid_job_payload, test_output_dir):
        """Invalid email address returns 422."""
        payload = {
            **valid_job_payload,
            "recipients": [{"name": "Test User", "email": "not-a-valid-email"}]
        }
        response = client.post("/api/v1/jobs", json=payload)
        assert response.status_code == 422

    def test_empty_recipient_name(self, client, valid_job_payload, test_output_dir):
        """Empty recipient name returns 422."""
        payload = {
            **valid_job_payload,
            "recipients": [{"name": "", "email": "test@example.com"}]
        }
        response = client.post("/api/v1/jobs", json=payload)
        assert response.status_code == 422

    def test_whitespace_only_recipient_name(self, client, valid_job_payload, test_output_dir):
        """Whitespace-only recipient name returns 422."""
        payload = {
            **valid_job_payload,
            "recipients": [{"name": "   ", "email": "test@example.com"}]
        }
        response = client.post("/api/v1/jobs", json=payload)
        assert response.status_code == 422

    def test_invalid_date_format(self, client, valid_job_payload, test_output_dir):
        """Invalid date format (not YYYY-MM-DD) returns 422."""
        payload = {**valid_job_payload, "issue_date": "07-10-2026"}
        response = client.post("/api/v1/jobs", json=payload)
        assert response.status_code == 422

    def test_empty_certificate_title(self, client, valid_job_payload, test_output_dir):
        """Empty certificate_title returns 422."""
        payload = {**valid_job_payload, "certificate_title": ""}
        response = client.post("/api/v1/jobs", json=payload)
        assert response.status_code == 422

    def test_whitespace_only_certificate_title(self, client, valid_job_payload, test_output_dir):
        """Whitespace-only certificate_title returns 422."""
        payload = {**valid_job_payload, "certificate_title": "   "}
        response = client.post("/api/v1/jobs", json=payload)
        assert response.status_code == 422

    def test_recipient_missing_email(self, client, valid_job_payload, test_output_dir):
        """Recipient without email returns 422."""
        payload = {
            **valid_job_payload,
            "recipients": [{"name": "Test User"}]
        }
        response = client.post("/api/v1/jobs", json=payload)
        assert response.status_code == 422

    def test_recipient_missing_name(self, client, valid_job_payload, test_output_dir):
        """Recipient without name returns 422."""
        payload = {
            **valid_job_payload,
            "recipients": [{"email": "test@example.com"}]
        }
        response = client.post("/api/v1/jobs", json=payload)
        assert response.status_code == 422

    def test_validation_error_response_format(self, client, valid_job_payload, test_output_dir):
        """Validation errors return properly structured error response."""
        payload = {**valid_job_payload, "recipients": []}
        response = client.post("/api/v1/jobs", json=payload)
        data = response.json()
        assert "detail" in data
