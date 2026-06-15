from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import app


client = TestClient(app)


def test_health_endpoint_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_hello_endpoint_returns_message() -> None:
    response = client.get("/api/hello")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello from FastAPI"}


def test_root_serves_static_html_page() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<html" in response.text.lower()


def test_frontend_backend_integration_contract_on_root_page() -> None:
    root_response = client.get("/")

    assert root_response.status_code == 200
    assert (
        "Checking session" in root_response.text
        or "Hello from PM MVP scaffolding" in root_response.text
    )

    api_response = client.get("/api/hello")
    assert api_response.status_code == 200
    assert api_response.json()["message"] == "Hello from FastAPI"
