from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import SESSIONS, app


client = TestClient(app)


def setup_function() -> None:
    SESSIONS.clear()
    client.cookies.clear()


def test_session_is_unauthenticated_by_default() -> None:
    response = client.get("/api/auth/session")

    assert response.status_code == 200
    assert response.json() == {"authenticated": False, "username": None}


def test_login_with_valid_credentials_creates_session_cookie() -> None:
    login_response = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "password"},
    )

    assert login_response.status_code == 200
    assert login_response.json() == {"authenticated": True, "username": "user"}
    assert "pm_session" in login_response.cookies

    session_response = client.get("/api/auth/session")
    assert session_response.status_code == 200
    assert session_response.json() == {"authenticated": True, "username": "user"}


def test_login_with_invalid_credentials_is_rejected() -> None:
    response = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "wrong"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


def test_logout_clears_session() -> None:
    client.post(
        "/api/auth/login",
        json={"username": "user", "password": "password"},
    )

    logout_response = client.post("/api/auth/logout")
    assert logout_response.status_code == 200
    assert logout_response.json() == {"authenticated": False}

    session_response = client.get("/api/auth/session")
    assert session_response.status_code == 200
    assert session_response.json() == {"authenticated": False, "username": None}
