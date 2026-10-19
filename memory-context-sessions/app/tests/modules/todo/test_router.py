"""Tests for the todo HTTP endpoints."""

from fastapi.testclient import TestClient


class TestListTodos:
    """Verify GET /api/v1/todos."""

    def test_empty_list(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        """Authenticated user with no todos gets an empty paginated response."""
        response = client.get("/api/v1/todos", headers=auth_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["items"] == []
        assert body["meta"]["total_items"] == 0
        assert body["meta"]["total_pages"] == 0
        assert body["meta"]["page"] == 1
        assert body["meta"]["page_size"] == 10

    def test_returns_own_todos(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Listed todos match what the user created."""
        client.post(
            "/api/v1/todos",
            json={"title": "Buy milk"},
            headers=auth_headers,
        )
        client.post(
            "/api/v1/todos",
            json={"title": "Walk dog", "description": "In the park"},
            headers=auth_headers,
        )
        response = client.get("/api/v1/todos", headers=auth_headers)
        assert response.status_code == 200
        body = response.json()
        assert len(body["items"]) == 2
        titles = {t["title"] for t in body["items"]}
        assert titles == {"Buy milk", "Walk dog"}
        assert body["meta"]["total_items"] == 2
        assert body["meta"]["total_pages"] == 1

    def test_pagination_defaults(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Default pagination is page=1, page_size=10."""
        response = client.get("/api/v1/todos", headers=auth_headers)
        meta = response.json()["meta"]
        assert meta["page"] == 1
        assert meta["page_size"] == 10

    def test_pagination_custom_page_size(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Custom page_size limits the returned items."""
        for i in range(3):
            client.post(
                "/api/v1/todos",
                json={"title": f"Todo {i}"},
                headers=auth_headers,
            )
        response = client.get("/api/v1/todos?page=1&page_size=2", headers=auth_headers)
        body = response.json()
        assert len(body["items"]) == 2
        assert body["meta"]["total_items"] == 3
        assert body["meta"]["total_pages"] == 2
        assert body["meta"]["next_page"] == 2
        assert body["meta"]["prev_page"] is None

    def test_pagination_second_page(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Second page returns remaining items."""
        for i in range(3):
            client.post(
                "/api/v1/todos",
                json={"title": f"Todo {i}"},
                headers=auth_headers,
            )
        response = client.get("/api/v1/todos?page=2&page_size=2", headers=auth_headers)
        body = response.json()
        assert len(body["items"]) == 1
        assert body["meta"]["page"] == 2
        assert body["meta"]["prev_page"] == 1
        assert body["meta"]["next_page"] is None

    def test_pagination_beyond_last_page(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Page beyond the last returns an empty items list."""
        client.post(
            "/api/v1/todos",
            json={"title": "Only one"},
            headers=auth_headers,
        )
        response = client.get(
            "/api/v1/todos?page=99&page_size=10", headers=auth_headers
        )
        body = response.json()
        assert body["items"] == []
        assert body["meta"]["total_items"] == 1
        assert body["meta"]["page"] == 99

    def test_pagination_invalid_page(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Page below 1 returns 422."""
        response = client.get("/api/v1/todos?page=0", headers=auth_headers)
        assert response.status_code == 422

    def test_pagination_invalid_page_size(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """page_size > 100 returns 422."""
        response = client.get("/api/v1/todos?page_size=101", headers=auth_headers)
        assert response.status_code == 422

    def test_unauthenticated(self, client: TestClient) -> None:
        """Request without a token returns 401."""
        response = client.get("/api/v1/todos")
        assert response.status_code == 401


class TestCreateTodo:
    """Verify POST /api/v1/todos."""

    def test_create_success(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Creating a todo returns 201 with the new item."""
        response = client.post(
            "/api/v1/todos",
            json={"title": "Read a book", "description": "Chapter 3"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        body = response.json()
        assert body["title"] == "Read a book"
        assert body["description"] == "Chapter 3"
        assert body["completed"] is False
        assert "id" in body
        assert "created_at" in body

    def test_create_without_description(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Description is optional."""
        response = client.post(
            "/api/v1/todos",
            json={"title": "Quick task"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["description"] is None

    def test_create_empty_title(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Empty title returns 422 validation error."""
        response = client.post(
            "/api/v1/todos",
            json={"title": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_unauthenticated(self, client: TestClient) -> None:
        """Request without a token returns 401."""
        response = client.post("/api/v1/todos", json={"title": "Nope"})
        assert response.status_code == 401


class TestUpdateTodo:
    """Verify PATCH /api/v1/todos/{todo_id}."""

    def _create_todo(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> dict[str, object]:
        """Create a todo and return its response body."""
        response = client.post(
            "/api/v1/todos",
            json={"title": "Original", "description": "Original desc"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        return response.json()

    def test_update_title(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Updating title returns the modified todo."""
        todo = self._create_todo(client, auth_headers)
        response = client.patch(
            f"/api/v1/todos/{todo['id']}",
            json={"title": "Updated"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["title"] == "Updated"
        assert body["description"] == "Original desc"
        assert body["completed"] is False

    def test_update_completed(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Marking a todo as completed returns the updated state."""
        todo = self._create_todo(client, auth_headers)
        response = client.patch(
            f"/api/v1/todos/{todo['id']}",
            json={"completed": True},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["completed"] is True

    def test_update_description(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Updating description leaves other fields unchanged."""
        todo = self._create_todo(client, auth_headers)
        response = client.patch(
            f"/api/v1/todos/{todo['id']}",
            json={"description": "New desc"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["description"] == "New desc"
        assert body["title"] == "Original"

    def test_update_not_found(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Updating a nonexistent todo returns 404."""
        response = client.patch(
            "/api/v1/todos/9999",
            json={"title": "Nope"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_update_empty_title(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Empty title returns 422 validation error."""
        todo = self._create_todo(client, auth_headers)
        response = client.patch(
            f"/api/v1/todos/{todo['id']}",
            json={"title": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_unauthenticated(self, client: TestClient) -> None:
        """Request without a token returns 401."""
        response = client.patch("/api/v1/todos/1", json={"title": "Nope"})
        assert response.status_code == 401
