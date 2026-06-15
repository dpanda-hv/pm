from pathlib import Path
import sys

from fastapi.testclient import TestClient
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app import main


client = TestClient(main.app)


@pytest.fixture
def fake_static_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    static_dir = tmp_path / "static"
    static_dir.mkdir(parents=True, exist_ok=True)
    (static_dir / "index.html").write_text("<h1>Home</h1>", encoding="utf-8")
    (static_dir / "about.html").write_text("about", encoding="utf-8")
    (static_dir / "docs").mkdir(parents=True, exist_ok=True)
    (static_dir / "docs" / "index.html").write_text("docs", encoding="utf-8")

    monkeypatch.setattr(main, "STATIC_DIR", static_dir)
    monkeypatch.setattr(main, "STATIC_ROOT", static_dir.resolve())
    return static_dir


def test_root_serves_index_html(fake_static_dir: Path) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Home" in response.text


def test_static_file_and_nested_index_routes(fake_static_dir: Path) -> None:
    about = client.get("/about.html")
    assert about.status_code == 200
    assert "about" in about.text

    docs = client.get("/docs")
    assert docs.status_code == 200
    assert "docs" in docs.text


def test_static_route_rejects_traversal_and_missing(fake_static_dir: Path) -> None:
    traversal = client.get("/../secret.txt")
    assert traversal.status_code == 404

    missing = client.get("/does-not-exist")
    assert missing.status_code == 404
