import secrets
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel

app = FastAPI(title="Project Management MVP API", version="0.1.0")

STATIC_DIR = Path(__file__).parent / "static"
STATIC_ROOT = STATIC_DIR.resolve()
SESSION_COOKIE = "pm_session"
VALID_USERNAME = "user"
VALID_PASSWORD = "password"

# In-memory sessions intentionally reset on process/container restart for MVP.
SESSIONS: dict[str, str] = {}


class LoginPayload(BaseModel):
    username: str
    password: str


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


@app.get("/api/auth/session")
def auth_session(request: Request) -> dict[str, str | bool | None]:
    session_id = request.cookies.get(SESSION_COOKIE)
    username = SESSIONS.get(session_id or "")
    if username:
        return {"authenticated": True, "username": username}
    return {"authenticated": False, "username": None}


@app.post("/api/auth/login")
def auth_login(payload: LoginPayload) -> Response:
    if payload.username != VALID_USERNAME or payload.password != VALID_PASSWORD:
        return JSONResponse(status_code=401, content={"detail": "Invalid credentials"})

    session_id = secrets.token_urlsafe(24)
    SESSIONS[session_id] = payload.username

    response = JSONResponse(
        status_code=200,
        content={"authenticated": True, "username": payload.username},
    )
    response.set_cookie(
        key=SESSION_COOKIE,
        value=session_id,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
    )
    return response


@app.post("/api/auth/logout")
def auth_logout(request: Request) -> Response:
    session_id = request.cookies.get(SESSION_COOKIE)
    if session_id:
        SESSIONS.pop(session_id, None)

    response = JSONResponse(status_code=200, content={"authenticated": False})
    response.delete_cookie(key=SESSION_COOKIE, path="/")
    return response


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
