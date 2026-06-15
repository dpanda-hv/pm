from pathlib import Path
import sys

from fastapi.testclient import TestClient
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app import main


client = TestClient(main.app)


def _login() -> None:
    response = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "password"},
    )
    assert response.status_code == 200


@pytest.fixture(autouse=True)
def isolated_state(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "pm.db")
    main.SESSIONS.clear()
    client.cookies.clear()


def test_db_auto_create_on_first_board_read() -> None:
    assert not main.DB_PATH.exists()

    _login()
    response = client.get("/api/board")

    assert response.status_code == 200
    assert main.DB_PATH.exists()
    payload = response.json()
    assert payload["schemaVersion"] == 1
    assert [column["id"] for column in payload["columns"]] == [
        "col-todo",
        "col-in-progress",
        "col-blocked",
        "col-in-review",
        "col-done",
    ]


def test_unauthorized_board_access_rejected() -> None:
    get_response = client.get("/api/board")
    assert get_response.status_code == 401

    put_response = client.put("/api/board", json={})
    assert put_response.status_code == 401


def test_invalid_board_payload_is_rejected() -> None:
    _login()
    response = client.put(
        "/api/board",
        json={
            "schemaVersion": 1,
            "columns": [],
            # cards key intentionally missing
        },
    )

    assert response.status_code == 400
    assert "cards" in response.json()["detail"]


def test_board_round_trip_update_persists() -> None:
    _login()

    initial_response = client.get("/api/board")
    assert initial_response.status_code == 200
    board = initial_response.json()

    board["columns"][0]["title"] = "Planned"

    update_response = client.put("/api/board", json=board)
    assert update_response.status_code == 200

    read_response = client.get("/api/board")
    assert read_response.status_code == 200
    assert read_response.json()["columns"][0]["title"] == "Planned"
