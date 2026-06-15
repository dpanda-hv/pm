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


def test_ai_connectivity_requires_authentication() -> None:
    response = client.post("/api/ai/connectivity", json={"prompt": "Hello"})

    assert response.status_code == 401


def test_ai_connectivity_rejects_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    _login()
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    response = client.post("/api/ai/connectivity", json={"prompt": "Hello"})

    assert response.status_code == 500
    assert response.json()["detail"] == "OPENROUTER_API_KEY is not configured"


def test_ai_connectivity_configured_key_path(monkeypatch: pytest.MonkeyPatch) -> None:
    _login()
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(main, "_openrouter_chat_completion", lambda prompt, key: "4")

    response = client.post("/api/ai/connectivity", json={"prompt": "What is 2+2?"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["model"] == "openai/gpt-oss-120b"
    assert payload["answer"] == "4"


def test_ai_connectivity_upstream_failure_is_wrapped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _login()
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    def _raise_error(_: str, __: str) -> str:
        raise RuntimeError("OpenRouter network error: timeout")

    monkeypatch.setattr(main, "_openrouter_chat_completion", _raise_error)

    response = client.post("/api/ai/connectivity", json={"prompt": "What is 2+2?"})

    assert response.status_code == 502
    assert "OpenRouter network error" in response.json()["detail"]


def test_two_plus_two_sanity_check_passes(monkeypatch: pytest.MonkeyPatch) -> None:
    _login()
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(main, "_openrouter_chat_completion", lambda prompt, key: "4")

    response = client.get("/api/ai/connectivity/2plus2")

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"] == "4"
    assert payload["sanityPassed"] is True
