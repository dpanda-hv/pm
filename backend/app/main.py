from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, Response

app = FastAPI(title="Project Management MVP API", version="0.1.0")

STATIC_DIR = Path(__file__).parent / "static"
STATIC_ROOT = STATIC_DIR.resolve()


def _safe_static_path(path: str) -> Path | None:
    candidate = (STATIC_DIR / path).resolve()
    if STATIC_ROOT in candidate.parents or candidate == STATIC_ROOT:
        return candidate
    return None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/hello")
def hello() -> dict[str, str]:
    return {"message": "Hello from FastAPI"}


@app.get("/")
def root() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/{full_path:path}")
def static_files(full_path: str) -> Response:
    safe_path = _safe_static_path(full_path)
    if safe_path is None:
        return Response(status_code=404)

    if safe_path.is_file():
        return FileResponse(safe_path)

    nested_index = safe_path / "index.html"
    if nested_index.is_file():
        return FileResponse(nested_index)

    return Response(status_code=404)
