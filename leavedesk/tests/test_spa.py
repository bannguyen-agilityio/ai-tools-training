from pathlib import Path

import httpx
from fastapi import FastAPI

from app.spa import mount_spa


def _client(app: FastAPI) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


def _dist(tmp_path: Path) -> Path:
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<html>shell</html>")
    (tmp_path / "assets" / "app.js").write_text("console.log(1)")
    return tmp_path


# R31 SPA serving
async def test_serves_assets_and_falls_back_to_index(tmp_path: Path) -> None:
    app = FastAPI()
    mount_spa(app, _dist(tmp_path))
    async with _client(app) as c:
        assert (await c.get("/assets/app.js")).text == "console.log(1)"
        assert "shell" in (await c.get("/requests/new")).text
        assert "shell" in (await c.get("/")).text


async def test_api_paths_are_not_swallowed(tmp_path: Path) -> None:
    app = FastAPI()
    mount_spa(app, _dist(tmp_path))
    async with _client(app) as c:
        assert (await c.get("/api/v1/nope")).status_code == 404
        assert (await c.get("/api")).status_code == 404


async def test_path_traversal_returns_shell_not_files(tmp_path: Path) -> None:
    app = FastAPI()
    (tmp_path / "secret.txt").write_text("secret")
    (tmp_path / "dist").mkdir()
    mount_spa(app, _dist(tmp_path / "dist"))
    async with _client(app) as c:
        r = await c.get("/..%2fsecret.txt")
        assert "secret" not in r.text


def test_noop_without_build(tmp_path: Path) -> None:
    app = FastAPI()
    mount_spa(app, tmp_path / "missing")
    assert not [r for r in app.routes if getattr(r, "path", "") == "/{path:path}"]


async def test_missing_asset_is_404_and_nul_byte_is_not_a_500(tmp_path: Path) -> None:
    app = FastAPI()
    mount_spa(app, _dist(tmp_path))
    async with _client(app) as c:
        assert (await c.get("/assets/old-hash.js")).status_code == 404
        assert (await c.get("/favicon.ico")).status_code == 404
        assert (await c.get("/%00")).status_code == 404
