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


def test_create_edit_move_cards_preserves_order() -> None:
    _login()

    first_create = client.post(
        "/api/board/cards",
        json={"columnId": "col-todo", "title": "Card A", "details": "first"},
    )
    assert first_create.status_code == 200
    first_board = first_create.json()
    first_card_id = first_board["columns"][0]["cardIds"][0]

    second_create = client.post(
        "/api/board/cards",
        json={"columnId": "col-todo", "title": "Card B", "details": "second"},
    )
    assert second_create.status_code == 200
    second_board = second_create.json()
    todo_ids = second_board["columns"][0]["cardIds"]
    assert len(todo_ids) == 2
    second_card_id = todo_ids[1]

    edit_response = client.patch(
        f"/api/board/cards/{second_card_id}",
        json={"title": "Card B Updated", "details": "edited"},
    )
    assert edit_response.status_code == 200
    assert edit_response.json()["cards"][second_card_id]["title"] == "Card B Updated"

    move_second = client.post(
        f"/api/board/cards/{second_card_id}/move",
        json={"toColumnId": "col-in-progress", "toIndex": 0},
    )
    assert move_second.status_code == 200

    move_first = client.post(
        f"/api/board/cards/{first_card_id}/move",
        json={"toColumnId": "col-in-progress", "toIndex": 0},
    )
    assert move_first.status_code == 200

    board = move_first.json()
    progress_column = [
        column for column in board["columns"] if column["id"] == "col-in-progress"
    ][0]
    assert progress_column["cardIds"] == [first_card_id, second_card_id]


def test_card_endpoints_validate_missing_entities() -> None:
    _login()

    bad_column = client.post(
        "/api/board/cards",
        json={"columnId": "col-missing", "title": "Nope", "details": "x"},
    )
    assert bad_column.status_code == 404

    bad_card = client.patch(
        "/api/board/cards/card-missing",
        json={"title": "Nope"},
    )
    assert bad_card.status_code == 404

    bad_target = client.post(
        "/api/board/cards/card-missing/move",
        json={"toColumnId": "col-todo", "toIndex": 0},
    )
    assert bad_target.status_code == 404


def test_unauthorized_card_mutations_rejected() -> None:
    response = client.post(
        "/api/board/cards",
        json={"columnId": "col-todo", "title": "Card", "details": "x"},
    )
    assert response.status_code == 401
