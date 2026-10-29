from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from starlette.exceptions import HTTPException

DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"


def mount_spa(app: FastAPI, dist: Path = DIST) -> None:
    """Serve the built frontend at `/`, falling back to index.html for client routes.

    Anything under /api stays a JSON 404. Does nothing when the build is absent
    (backend-only dev and tests).
    """
    index = dist / "index.html"
    if not index.is_file():
        return
    root = dist.resolve()

    @app.get("/{path:path}", include_in_schema=False)
    async def spa(path: str) -> FileResponse:
        if path == "api" or path.startswith("api/"):
            raise HTTPException(404)
        try:
            candidate = (root / path).resolve()
            found = bool(path) and candidate.is_relative_to(root) and candidate.is_file()
        except ValueError:  # embedded NUL byte
            raise HTTPException(404) from None
        if found:
            return FileResponse(candidate)
        # A missing file (has an extension) is a 404, not the HTML shell.
        if "." in path.rsplit("/", 1)[-1]:
            raise HTTPException(404)
        return FileResponse(index)
