import json
import http.client
import os
import secrets
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel

STATIC_DIR = Path(__file__).parent / "static"
STATIC_ROOT = STATIC_DIR.resolve()
SESSION_COOKIE = "pm_session"
VALID_USERNAME = "user"
VALID_PASSWORD = "password"
DEFAULT_DB_PATH = Path(__file__).resolve().parents[1] / "data" / "pm.db"
DB_PATH = Path(os.getenv("PM_DB_PATH", str(DEFAULT_DB_PATH)))
DEFAULT_COLUMNS = [
    {"id": "col-todo", "title": "To Do"},
    {"id": "col-in-progress", "title": "In Progress"},
    {"id": "col-blocked", "title": "Blocked"},
    {"id": "col-in-review", "title": "In Review"},
    {"id": "col-done", "title": "Done"},
]
DEFAULT_COLUMN_IDS = [column["id"] for column in DEFAULT_COLUMNS]
DEFAULT_COLUMN_ID_SET = set(DEFAULT_COLUMN_IDS)
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "openai/gpt-oss-120b"
TWO_PLUS_TWO_PROMPT = "What is 2+2? Reply with only the number."
OPENROUTER_HTTP_REFERER = os.getenv("OPENROUTER_HTTP_REFERER", "http://localhost:8000")
OPENROUTER_APP_TITLE = os.getenv("OPENROUTER_APP_TITLE", "PM MVP Local")

# In-memory sessions intentionally reset on process/container restart for MVP.
SESSIONS: dict[str, str] = {}


class LoginPayload(BaseModel):
    username: str
    password: str


class CreateCardPayload(BaseModel):
    columnId: str
    title: str
    details: str = ""


class EditCardPayload(BaseModel):
    title: str | None = None
    details: str | None = None


class MoveCardPayload(BaseModel):
    toColumnId: str
    toIndex: int | None = None


class AIConnectivityPayload(BaseModel):
    prompt: str = TWO_PLUS_TWO_PROMPT


def _create_default_board() -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "columns": [
            {"id": column["id"], "title": column["title"], "cardIds": []}
            for column in DEFAULT_COLUMNS
        ],
        "cards": {},
    }


def _connect_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def ensure_db_ready() -> None:
    with _connect_db() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS user_boards (
              user_id TEXT PRIMARY KEY,
              board_json TEXT NOT NULL,
              board_version INTEGER NOT NULL DEFAULT 1,
              updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_user_boards_updated_at
            ON user_boards(updated_at)
            """
        )
        connection.commit()


def _validate_board_payload(board: dict[str, object]) -> None:
    if not isinstance(board, dict):
        raise HTTPException(status_code=400, detail="Board payload must be an object")

    schema_version = board.get("schemaVersion")
    if schema_version != 1:
        raise HTTPException(status_code=400, detail="schemaVersion must be 1")

    columns = board.get("columns")
    cards = board.get("cards")
    if not isinstance(columns, list):
        raise HTTPException(status_code=400, detail="columns must be a list")
    if not isinstance(cards, dict):
        raise HTTPException(status_code=400, detail="cards must be an object")

    column_ids: list[str] = []
    seen_card_ids: set[str] = set()
    for column in columns:
        if not isinstance(column, dict):
            raise HTTPException(status_code=400, detail="Each column must be an object")

        column_id = column.get("id")
        title = column.get("title")
        card_ids = column.get("cardIds")

        if not isinstance(column_id, str) or not column_id:
            raise HTTPException(status_code=400, detail="Column id must be a non-empty string")
        if not isinstance(title, str):
            raise HTTPException(status_code=400, detail="Column title must be a string")
        if not isinstance(card_ids, list):
            raise HTTPException(status_code=400, detail="Column cardIds must be a list")

        if column_id in column_ids:
            raise HTTPException(status_code=400, detail="Duplicate column ids are not allowed")
        column_ids.append(column_id)

        for card_id in card_ids:
            if not isinstance(card_id, str):
                raise HTTPException(status_code=400, detail="cardIds entries must be strings")
            if card_id in seen_card_ids:
                raise HTTPException(
                    status_code=400,
                    detail="A card id may only appear in one column",
                )
            seen_card_ids.add(card_id)

    if set(column_ids) != DEFAULT_COLUMN_ID_SET:
        raise HTTPException(status_code=400, detail="Board columns must use fixed MVP column ids")

    for card_key, card in cards.items():
        if not isinstance(card_key, str):
            raise HTTPException(status_code=400, detail="Card keys must be strings")
        if not isinstance(card, dict):
            raise HTTPException(status_code=400, detail="Card values must be objects")

        card_id = card.get("id")
        title = card.get("title")
        details = card.get("details")

        if card_id != card_key:
            raise HTTPException(status_code=400, detail="Card key must match card.id")
        if not isinstance(title, str):
            raise HTTPException(status_code=400, detail="Card title must be a string")
        if not isinstance(details, str):
            raise HTTPException(status_code=400, detail="Card details must be a string")

    if set(cards.keys()) != seen_card_ids:
        raise HTTPException(
            status_code=400,
            detail="Cards object keys must exactly match all cardIds across columns",
        )


def _require_authenticated_user(request: Request) -> str:
    session_id = request.cookies.get(SESSION_COOKIE)
    username = SESSIONS.get(session_id or "")
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return username


def _read_board_for_user(user_id: str) -> dict[str, object]:
    ensure_db_ready()
    with _connect_db() as connection:
        row = connection.execute(
            "SELECT board_json FROM user_boards WHERE user_id = ?",
            (user_id,),
        ).fetchone()

        if row is None:
            board = _create_default_board()
            connection.execute(
                """
                INSERT INTO user_boards (user_id, board_json, board_version, updated_at)
                VALUES (?, ?, 1, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
                """,
                (user_id, json.dumps(board)),
            )
            connection.commit()
            return board

        board = json.loads(row["board_json"])
        return board


def _save_board_for_user(user_id: str, board: dict[str, object]) -> None:
    _validate_board_payload(board)
    ensure_db_ready()
    with _connect_db() as connection:
        connection.execute(
            """
            INSERT INTO user_boards (user_id, board_json, board_version, updated_at)
            VALUES (?, ?, 1, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
            ON CONFLICT(user_id) DO UPDATE SET
              board_json = excluded.board_json,
              board_version = user_boards.board_version + 1,
              updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
            """,
            (user_id, json.dumps(board)),
        )
        connection.commit()


def _find_column(board: dict[str, object], column_id: str) -> dict[str, object] | None:
    columns = board["columns"]
    if not isinstance(columns, list):
        return None
    for column in columns:
        if isinstance(column, dict) and column.get("id") == column_id:
            return column
    return None


def _find_column_for_card(board: dict[str, object], card_id: str) -> dict[str, object] | None:
    columns = board["columns"]
    if not isinstance(columns, list):
        return None

    for column in columns:
        if not isinstance(column, dict):
            continue
        card_ids = column.get("cardIds")
        if isinstance(card_ids, list) and card_id in card_ids:
            return column
    return None


def _create_card_id() -> str:
    return f"card-{secrets.token_hex(6)}"


def _require_openrouter_api_key() -> str:
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY is not configured")
    return api_key


def _extract_openrouter_text(payload: dict[str, object]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("OpenRouter response missing choices")

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        raise RuntimeError("OpenRouter response has invalid choice format")

    message = first_choice.get("message")
    if not isinstance(message, dict):
        raise RuntimeError("OpenRouter response missing message")

    content = message.get("content")
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        text_parts: list[str] = []
        for item in content:
            if not isinstance(item, dict):
                continue
            if item.get("type") == "text" and isinstance(item.get("text"), str):
                text_parts.append(item["text"])
        if text_parts:
            return "\n".join(text_parts).strip()

    raise RuntimeError("OpenRouter response did not include text content")


def _openrouter_chat_completion(prompt: str, api_key: str) -> str:
    body = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "temperature": 0,
    }

    encoded_body = json.dumps(body)
    connection = http.client.HTTPSConnection("openrouter.ai", timeout=30)

    try:
        connection.request(
            "POST",
            "/api/v1/chat/completions",
            body=encoded_body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": OPENROUTER_HTTP_REFERER,
                "X-Title": OPENROUTER_APP_TITLE,
            },
        )
        response = connection.getresponse()
        raw = response.read().decode("utf-8", errors="replace")
    except OSError as exc:
        raise RuntimeError(f"OpenRouter network error: {exc}") from exc
    finally:
        connection.close()

    if response.status >= 400:
        raise RuntimeError(f"OpenRouter HTTP {response.status}: {raw}")

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("OpenRouter returned non-JSON response") from exc

    return _extract_openrouter_text(parsed)


def _answer_indicates_four(answer: str) -> bool:
    compact = "".join(ch for ch in answer if ch.isdigit())
    return "4" in compact or answer.strip() == "4"


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_db_ready()
    yield


app = FastAPI(
    title="Project Management MVP API",
    version="0.1.0",
    lifespan=lifespan,
)


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


@app.get("/api/board")
def get_board(request: Request) -> dict[str, object]:
    user_id = _require_authenticated_user(request)
    return _read_board_for_user(user_id)


@app.put("/api/board")
def update_board(request: Request, board: dict[str, object]) -> dict[str, object]:
    user_id = _require_authenticated_user(request)
    _save_board_for_user(user_id, board)
    return board


@app.post("/api/board/cards")
def create_card(request: Request, payload: CreateCardPayload) -> dict[str, object]:
    user_id = _require_authenticated_user(request)
    board = _read_board_for_user(user_id)

    column = _find_column(board, payload.columnId)
    if column is None:
        raise HTTPException(status_code=404, detail="Column not found")

    cards = board["cards"]
    if not isinstance(cards, dict):
        raise HTTPException(status_code=400, detail="Invalid board cards state")

    card_ids = column.get("cardIds")
    if not isinstance(card_ids, list):
        raise HTTPException(status_code=400, detail="Invalid board column state")

    card_id = _create_card_id()
    cards[card_id] = {
        "id": card_id,
        "title": payload.title,
        "details": payload.details,
    }
    card_ids.append(card_id)

    _save_board_for_user(user_id, board)
    return board


@app.patch("/api/board/cards/{card_id}")
def edit_card(request: Request, card_id: str, payload: EditCardPayload) -> dict[str, object]:
    user_id = _require_authenticated_user(request)
    board = _read_board_for_user(user_id)

    cards = board["cards"]
    if not isinstance(cards, dict) or card_id not in cards:
        raise HTTPException(status_code=404, detail="Card not found")

    if payload.title is None and payload.details is None:
        raise HTTPException(status_code=400, detail="No card updates were provided")

    card = cards[card_id]
    if not isinstance(card, dict):
        raise HTTPException(status_code=400, detail="Invalid card state")

    if payload.title is not None:
        card["title"] = payload.title
    if payload.details is not None:
        card["details"] = payload.details

    _save_board_for_user(user_id, board)
    return board


@app.post("/api/board/cards/{card_id}/move")
def move_card(request: Request, card_id: str, payload: MoveCardPayload) -> dict[str, object]:
    user_id = _require_authenticated_user(request)
    board = _read_board_for_user(user_id)

    source_column = _find_column_for_card(board, card_id)
    if source_column is None:
        raise HTTPException(status_code=404, detail="Card not found")

    target_column = _find_column(board, payload.toColumnId)
    if target_column is None:
        raise HTTPException(status_code=404, detail="Target column not found")

    source_card_ids = source_column.get("cardIds")
    target_card_ids = target_column.get("cardIds")

    if not isinstance(source_card_ids, list) or not isinstance(target_card_ids, list):
        raise HTTPException(status_code=400, detail="Invalid board column state")

    source_card_ids.remove(card_id)
    if payload.toIndex is None:
        insert_index = len(target_card_ids)
    else:
        insert_index = max(0, min(payload.toIndex, len(target_card_ids)))
    target_card_ids.insert(insert_index, card_id)

    _save_board_for_user(user_id, board)
    return board


@app.post("/api/ai/connectivity")
def ai_connectivity(request: Request, payload: AIConnectivityPayload) -> dict[str, object]:
    _require_authenticated_user(request)
    api_key = _require_openrouter_api_key()

    try:
        answer = _openrouter_chat_completion(payload.prompt, api_key)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {
        "ok": True,
        "model": OPENROUTER_MODEL,
        "prompt": payload.prompt,
        "answer": answer,
    }


@app.get("/api/ai/connectivity/2plus2")
def ai_connectivity_two_plus_two(request: Request) -> dict[str, object]:
    _require_authenticated_user(request)
    api_key = _require_openrouter_api_key()

    try:
        answer = _openrouter_chat_completion(TWO_PLUS_TWO_PROMPT, api_key)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {
        "ok": True,
        "model": OPENROUTER_MODEL,
        "prompt": TWO_PLUS_TWO_PROMPT,
        "answer": answer,
        "sanityPassed": _answer_indicates_four(answer),
    }


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
