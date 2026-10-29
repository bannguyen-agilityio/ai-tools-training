from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, Response

from app.core.errors import problem

DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
# Never answered with the HTML shell, so /docs stays a 404 outside dev.
NOT_SPA = ("api", "docs", "redoc", "openapi.json")


def mount_spa(app: FastAPI, dist: Path = DIST) -> None:
    """Serve the built frontend at `/`, falling back to index.html for client routes.

    Implemented as the 404 handler rather than a catch-all route, so every real
    route (including ones added after create_app) wins. Anything under /api,
    the docs paths, and missing files with an extension stay a JSON 404.
    Does nothing when the build is absent (backend-only dev and tests).
    """
    index = dist / "index.html"
    if not index.is_file():
        return
    root = dist.resolve()

    async def spa_or_404(request: Request, _: Exception) -> Response:
        path = request.url.path.lstrip("/")
        if request.method not in ("GET", "HEAD") or path.split("/", 1)[0] in NOT_SPA:
            return problem(404)
        try:
            candidate = (root / path).resolve()
            found = bool(path) and candidate.is_relative_to(root) and candidate.is_file()
        except ValueError:  # embedded NUL byte
            return problem(404)
        if found:
            return FileResponse(candidate)
        if "." in path.rsplit("/", 1)[-1]:
            return problem(404)
        return FileResponse(index)

    app.add_exception_handler(404, spa_or_404)
