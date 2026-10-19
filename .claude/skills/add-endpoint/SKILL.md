---
name: add-endpoint
description: Scaffold a new API endpoint following this project's vertical module pattern (router, service, repository, models, schemas, dependencies).
user-invocable: true
---

# Add Endpoint

Quickly scaffold a new endpoint or an entire module following the project's layered architecture. The user will describe what they want (e.g. "add a DELETE endpoint for todos", "create a comments module with CRUD"). Use the patterns below to generate code that matches the existing codebase exactly.

## Determine scope

Ask yourself — does this endpoint belong to an **existing module** or a **new module**?

- **Existing module**: add to the existing router, service, repository (and schemas if needed). Skip to **Add endpoint to existing module**.
- **New module**: scaffold all layers. Go to **Scaffold new module**.

## Scaffold new module

Create `app/modules/<name>/` with these files, following the exact patterns from the `todo` module:

### 1. `models.py`
- ORM model inheriting `app.infrastructure.database.Base`
- Use `Mapped` and `mapped_column` (SQLAlchemy 2.0 style)
- Include `id: Mapped[int]` as primary key
- Add `created_at` with `DateTime(timezone=True)` and `server_default=func.now()`
- Add `ForeignKey("users.id")` with `index=True` if the resource is user-scoped

### 2. `schemas.py`
- Pydantic `BaseModel` classes for Create request, Update request (all fields optional), and Out response
- Use `Field(min_length=..., max_length=...)` for string constraints

### 3. `repository.py`
- Class taking `AsyncSession` in `__init__`
- Use `select()` queries, return ORM model instances
- `flush()` after writes, never `commit()` (the session handler commits)
- For user-scoped resources: always filter by `user_id`
- Include `list_by_user`, `count_by_user`, `get_by_id_and_user`, `create`, `flush` as baseline methods

### 4. `service.py`
- Class taking the repository in `__init__`
- Business logic and validation here
- Raise `AppError` subclasses from `app.core.exceptions` (never return HTTP responses)
- `NotFoundError` for missing resources, `ConflictError` for duplicates

### 5. `dependencies.py`
- `get_<name>_repository(session)` → Repository
- `get_<name>_service(repo)` → Service
- For user-scoped resources: import `get_current_user_id` from `app.modules.todo.dependencies` (or `get_current_user` from auth) as needed

### 6. `router.py`
- `APIRouter()` with endpoint functions
- Use `Annotated[..., Depends()]` for all injected params
- Return Pydantic schema instances directly
- Use `PaginatedResponse[T]` and `PaginationParams` from `app.core.pagination` for list endpoints
- Set `status_code=status.HTTP_201_CREATED` on POST create endpoints

### 7. `__init__.py`
- Include a module-level docstring describing the module's purpose (Google style, enforced by ruff `D` rules)
- Example: `"""Comments module — CRUD operations for user comments."""`

### 8. Wire into the API
- Add `from app.modules.<name>.router import router as <name>_router` in `app/api/v1/router.py`
- Add `router.include_router(<name>_router, prefix="/<plural>", tags=["<Name>"])`

### 9. Tests
- Create `app/tests/modules/<name>/` with `__init__.py` and `test_router.py`
- Use the existing test fixtures: `client`, `auth_headers`, `db_session`
- Test the golden path and key error cases (not found, unauthorized, validation)

### 10. Verify
- Run `uv run pytest` to confirm all tests pass
- Run `uv run ruff check . && uv run ruff format --check . && uv run pyright` to confirm no lint/type issues

## Add endpoint to existing module

When adding to an existing module, touch only the layers that need changes:

1. **schemas.py** — add request/response schemas if the endpoint needs new ones
2. **repository.py** — add data-access methods if the endpoint queries differently
3. **service.py** — add the business logic method
4. **router.py** — add the endpoint function, wire dependencies
5. **tests** — add test cases for the new endpoint
6. **Verify** — run tests, lint, types

## Conventions to follow

- All docstrings: Google style (enforced by ruff `D` rules)
- Module docstring at the top of every file
- Every public class and function needs a docstring
- Async for all I/O: `async def` on service and repository methods
- Type hints everywhere, use `T | None` not `Optional[T]`
- Routes are versioned under `/api/v1` — never hardcode other prefixes
