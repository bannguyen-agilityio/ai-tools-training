"""Tests for authentication endpoints."""

from fastapi.testclient import TestClient


class TestRegister:
    """Tests for POST /api/v1/auth/register."""

    def test_register_success(self, client: TestClient) -> None:
        """Valid registration returns 201 with the new user profile."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "password": "securepass",
                "full_name": "New User",
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["username"] == "newuser"
        assert body["full_name"] == "New User"
        assert "id" in body

    def test_register_duplicate_username(self, client: TestClient) -> None:
        """Duplicate username returns 409 with USERNAME_ALREADY_EXISTS."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "admin",
                "password": "securepass",
                "full_name": "Another Admin",
            },
        )
        assert response.status_code == 409
        error = response.json()["error"]
        assert error["code"] == "USERNAME_ALREADY_EXISTS"
        assert error["message"] == "Username already exists"

    def test_register_short_username(self, client: TestClient) -> None:
        """Username shorter than 3 characters returns 422."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "ab",
                "password": "securepass",
                "full_name": "Short Name",
            },
        )
        assert response.status_code == 422
        error = response.json()["error"]
        assert error["code"] == "VALIDATION_ERROR"

    def test_register_short_password(self, client: TestClient) -> None:
        """Password shorter than 8 characters returns 422."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "password": "short",
                "full_name": "New User",
            },
        )
        assert response.status_code == 422
        error = response.json()["error"]
        assert error["code"] == "VALIDATION_ERROR"


class TestLogin:
    """Tests for POST /api/v1/auth/login."""

    def test_login_success(self, client: TestClient) -> None:
        """Valid credentials return an access token."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        assert response.status_code == 200
        body = response.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    def test_login_wrong_password(self, client: TestClient) -> None:
        """Invalid password returns 401 with error envelope."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "wrong"},
        )
        assert response.status_code == 401
        error = response.json()["error"]
        assert error["code"] == "INVALID_CREDENTIALS"
        assert error["message"] == "Incorrect username or password"
        assert error["request_id"] is not None

    def test_login_unknown_user(self, client: TestClient) -> None:
        """Unknown username returns 401 with error envelope."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "nobody", "password": "admin123"},
        )
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


class TestCurrentUser:
    """Tests for GET /api/v1/auth/me."""

    def test_get_current_user(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Authenticated user can retrieve their profile."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == 1
        assert body["username"] == "admin"
        assert body["full_name"] == "Admin User"

    def test_get_current_user_no_token(self, client: TestClient) -> None:
        """Request without a token returns 401 with error envelope."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
        error = response.json()["error"]
        assert error["code"] == "UNAUTHENTICATED"

    def test_get_current_user_invalid_token(self, client: TestClient) -> None:
        """Request with an invalid token returns 401 with INVALID_TOKEN."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401
        error = response.json()["error"]
        assert error["code"] == "INVALID_TOKEN"
        assert error["message"] == "Invalid or expired token"
        assert error["request_id"] is not None


class TestRoot:
    """Tests for GET /."""

    def test_root(self, client: TestClient) -> None:
        """Root endpoint returns a welcome message."""
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()
