"""Tests for the centralized error handling infrastructure."""

from fastapi.testclient import TestClient

from app.core.config import settings


class TestErrorEnvelope:
    """Verify that all error responses follow the standard envelope."""

    def test_envelope_structure_on_domain_error(self, client: TestClient) -> None:
        """Domain error response contains all envelope fields."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": settings.seed_username, "password": "wrong!!!"},
        )
        assert response.status_code == 401
        body = response.json()
        assert "error" in body
        error = body["error"]
        assert "code" in error
        assert "message" in error
        assert "details" in error
        assert "request_id" in error
        assert error["request_id"].startswith("req_")

    def test_401_includes_www_authenticate_header(self, client: TestClient) -> None:
        """Authentication errors include the WWW-Authenticate header."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": settings.seed_username, "password": "wrong!!!"},
        )
        assert response.headers.get("www-authenticate") == "Bearer"


class TestValidationErrors:
    """Verify that validation errors use the standard envelope."""

    def test_missing_required_field(self, client: TestClient) -> None:
        """Missing JSON fields returns 422 with VALIDATION_ERROR envelope."""
        response = client.post("/api/v1/auth/login", json={})
        assert response.status_code == 422
        error = response.json()["error"]
        assert error["code"] == "VALIDATION_ERROR"
        assert error["message"] == "Request validation failed."
        assert isinstance(error["details"], list)
        assert len(error["details"]) > 0
        detail = error["details"][0]
        assert "field" in detail
        assert "message" in detail
        assert "type" in detail


class TestHttpExceptionWrapping:
    """Verify that HTTP exceptions are wrapped in the standard envelope."""

    def test_404_returns_envelope(self, client: TestClient) -> None:
        """Unknown route returns 404 with error envelope."""
        response = client.get("/nonexistent")
        assert response.status_code == 404
        error = response.json()["error"]
        assert error["code"] == "RESOURCE_NOT_FOUND"
        assert error["request_id"] is not None

    def test_405_returns_envelope(self, client: TestClient) -> None:
        """Wrong HTTP method returns 405 with error envelope."""
        response = client.delete("/")
        assert response.status_code == 405
        error = response.json()["error"]
        assert error["code"] == "METHOD_NOT_ALLOWED"


class TestRequestId:
    """Verify that request IDs are present in all error responses."""

    def test_request_id_is_unique(self, client: TestClient) -> None:
        """Each request gets a different request_id."""
        r1 = client.get("/nonexistent")
        r2 = client.get("/nonexistent")
        id1 = r1.json()["error"]["request_id"]
        id2 = r2.json()["error"]["request_id"]
        assert id1 != id2
