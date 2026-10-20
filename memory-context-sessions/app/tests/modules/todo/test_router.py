"""Tests for the todo HTTP endpoints."""

from fastapi.testclient import TestClient


def _create_todo(
    client: TestClient,
    auth_headers: dict[str, str],
    title: str = "Test todo",
    description: str | None = "Test description",
) -> dict[str, object]:
    """Create a todo via the API and return its response body."""
    response = client.post(
        "/api/v1/todos",
        json={"title": title, "description": description},
        headers=auth_headers,
    )
    assert response.status_code == 201
    return response.json()


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


class TestGetTodo:
    """Verify GET /api/v1/todos/{todo_id}."""

    def test_get_success(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Fetching a todo by ID returns the full detail."""
        todo = _create_todo(client, auth_headers, "Detail test", "Check detail")
        response = client.get(f"/api/v1/todos/{todo['id']}", headers=auth_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == todo["id"]
        assert body["title"] == "Detail test"
        assert body["description"] == "Check detail"
        assert body["completed"] is False
        assert "created_at" in body

    def test_not_found(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        """Nonexistent todo ID returns 404."""
        response = client.get("/api/v1/todos/9999", headers=auth_headers)
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "TODO_NOT_FOUND"

    def test_unauthenticated(self, client: TestClient) -> None:
        """Request without a token returns 401."""
        response = client.get("/api/v1/todos/1")
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


class TestCopyTodo:
    """Verify POST /api/v1/todos/{todo_id}/copy."""

    def test_copy_success(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Copying a todo returns 201 with duplicated title and description."""
        original = _create_todo(client, auth_headers, "Original", "To be copied")
        response = client.post(
            f"/api/v1/todos/{original['id']}/copy", headers=auth_headers
        )
        assert response.status_code == 201
        body = response.json()
        assert body["id"] != original["id"]
        assert body["title"] == "Original"
        assert body["description"] == "To be copied"
        assert body["completed"] is False

    def test_copy_resets_completed(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Copying a completed todo creates an incomplete copy."""
        original = _create_todo(client, auth_headers, "Original", "To be copied")
        patch_response = client.patch(
            f"/api/v1/todos/{original['id']}",
            json={"completed": True},
            headers=auth_headers,
        )
        assert patch_response.status_code == 200
        response = client.post(
            f"/api/v1/todos/{original['id']}/copy", headers=auth_headers
        )
        assert response.status_code == 201
        assert response.json()["completed"] is False

    def test_copy_not_found(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Copying a nonexistent todo returns 404."""
        response = client.post("/api/v1/todos/9999/copy", headers=auth_headers)
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "TODO_NOT_FOUND"

    def test_copy_unauthenticated(self, client: TestClient) -> None:
        """Request without a token returns 401."""
        response = client.post("/api/v1/todos/1/copy")
        assert response.status_code == 401


class TestDeleteTodo:
    """Verify DELETE /api/v1/todos/{todo_id}."""

    def test_delete_success(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Deleting an existing todo returns 204 and removes it."""
        todo = _create_todo(client, auth_headers, "To delete", "Will be removed")
        response = client.delete(f"/api/v1/todos/{todo['id']}", headers=auth_headers)
        assert response.status_code == 204

        get_response = client.get(f"/api/v1/todos/{todo['id']}", headers=auth_headers)
        assert get_response.status_code == 404

    def test_delete_not_found(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Deleting a nonexistent todo returns 404."""
        response = client.delete("/api/v1/todos/9999", headers=auth_headers)
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "TODO_NOT_FOUND"

    def test_delete_unauthenticated(self, client: TestClient) -> None:
        """Request without a token returns 401."""
        response = client.delete("/api/v1/todos/1")
        assert response.status_code == 401


class TestUpdateTodo:
    """Verify PATCH /api/v1/todos/{todo_id}."""

    def test_update_title(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Updating title returns the modified todo."""
        todo = _create_todo(client, auth_headers, "Original", "Original desc")
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
        todo = _create_todo(client, auth_headers, "Original", "Original desc")
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
        todo = _create_todo(client, auth_headers, "Original", "Original desc")
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
        todo = _create_todo(client, auth_headers, "Original", "Original desc")
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
