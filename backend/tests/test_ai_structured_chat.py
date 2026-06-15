from pathlib import Path
import json
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
    main.CHAT_HISTORY.clear()
    client.cookies.clear()


def test_ai_chat_schema_validation_pass_path(monkeypatch: pytest.MonkeyPatch) -> None:
    _login()
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    monkeypatch.setattr(
        main,
        "_openrouter_chat_completion_messages",
        lambda messages, api_key: json.dumps(
            {
                "reply": "All good.",
                "boardUpdate": None,
            }
        ),
    )

    response = client.post("/api/ai/chat", json={"message": "Summarize board"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["reply"] == "All good."
    assert payload["boardUpdated"] is False


def test_ai_chat_retry_then_success(monkeypatch: pytest.MonkeyPatch) -> None:
    _login()
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    responses = iter(
        [
            "not-json",
            json.dumps({"reply": "Recovered", "boardUpdate": None}),
        ]
    )

    def _fake_completion(messages: list[dict[str, str]], api_key: str) -> str:
        return next(responses)

    monkeypatch.setattr(main, "_openrouter_chat_completion_messages", _fake_completion)

    response = client.post("/api/ai/chat", json={"message": "Try again"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["reply"] == "Recovered"
    assert payload["boardUpdated"] is False


def test_ai_chat_fallback_after_invalid_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    _login()
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(
        main,
        "_openrouter_chat_completion_messages",
        lambda messages, api_key: "still-invalid",
    )

    response = client.post("/api/ai/chat", json={"message": "Will fail"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["boardUpdated"] is False
    assert "valid structured response" in payload["reply"].lower()


def test_ai_chat_applies_board_update_atomically(monkeypatch: pytest.MonkeyPatch) -> None:
    _login()
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    current_board = client.get("/api/board").json()
    updated_board = json.loads(json.dumps(current_board))
    updated_board["columns"][0]["title"] = "Planned"

    monkeypatch.setattr(
        main,
        "_openrouter_chat_completion_messages",
        lambda messages, api_key: json.dumps(
            {
                "reply": "Renamed the first column.",
                "boardUpdate": updated_board,
            }
        ),
    )

    response = client.post("/api/ai/chat", json={"message": "Rename first column"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["boardUpdated"] is True
    assert payload["board"]["columns"][0]["title"] == "Planned"

    read_back = client.get("/api/board")
    assert read_back.status_code == 200
    assert read_back.json()["columns"][0]["title"] == "Planned"


def test_ai_chat_keeps_board_unchanged_when_update_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    _login()
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    original_board = client.get("/api/board").json()

    invalid_update = {
        "schemaVersion": 1,
        "columns": [],
        "cards": {},
    }

    monkeypatch.setattr(
        main,
        "_openrouter_chat_completion_messages",
        lambda messages, api_key: json.dumps(
            {
                "reply": "Applying broken update",
                "boardUpdate": invalid_update,
            }
        ),
    )

    response = client.post("/api/ai/chat", json={"message": "Break board"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["boardUpdated"] is False

    read_back = client.get("/api/board")
    assert read_back.status_code == 200
    assert read_back.json() == original_board


def test_ai_chat_includes_conversation_history(monkeypatch: pytest.MonkeyPatch) -> None:
    _login()
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    observed_contexts: list[dict[str, object]] = []

    def _fake_completion(messages: list[dict[str, str]], api_key: str) -> str:
        user_prompt = messages[1]["content"]
        prefix = "Generate the structured JSON response for this context: "
        context = json.loads(user_prompt[len(prefix) :])
        observed_contexts.append(context)
        return json.dumps({"reply": "ack", "boardUpdate": None})

    monkeypatch.setattr(main, "_openrouter_chat_completion_messages", _fake_completion)

    first = client.post("/api/ai/chat", json={"message": "First message"})
    assert first.status_code == 200

    second = client.post("/api/ai/chat", json={"message": "Second message"})
    assert second.status_code == 200

    assert len(observed_contexts) >= 2
    first_context = observed_contexts[0]
    second_context = observed_contexts[1]

    assert first_context["history"] == []

    history = second_context["history"]
    assert isinstance(history, list)
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "First message"
    assert history[1]["role"] == "assistant"
    assert history[1]["content"] == "ack"
