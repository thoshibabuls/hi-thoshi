import base64

import pytest
from fastapi.testclient import TestClient

from src import db, main
from src.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    with TestClient(app) as c:
        yield c


# --- page + health ---------------------------------------------------------

def test_index_serves_the_dashboard(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


# --- greeting --------------------------------------------------------------

@pytest.mark.parametrize(
    "hour, part",
    [
        (5, "morning"), (11, "morning"),
        (12, "afternoon"), (16, "afternoon"),
        (17, "evening"), (21, "evening"),
        (22, "night"), (0, "night"), (4, "night"),
    ],
)
def test_greeting_follows_time_of_day(client, hour, part):
    res = client.get("/api/greeting", params={"name": "Thoshi", "hour": hour})
    assert res.status_code == 200
    assert res.json()["part_of_day"] == part


def test_greeting_message_uses_name(client):
    res = client.get("/api/greeting", params={"name": "Thoshi", "hour": 19})
    assert res.json()["message"] == "Good evening, Thoshi 🌆"


def test_greeting_blank_name_falls_back_to_default(client):
    res = client.get("/api/greeting", params={"name": "   ", "hour": 9})
    assert res.json()["message"] == "Good morning, Thoshi ☀️"


def test_greeting_without_hour_uses_server_clock(client):
    res = client.get("/api/greeting")
    assert res.status_code == 200
    assert res.json()["part_of_day"] in {"morning", "afternoon", "evening", "night"}


def test_greeting_rejects_invalid_hour(client):
    assert client.get("/api/greeting", params={"hour": 24}).status_code == 422


# --- tasks -----------------------------------------------------------------

def test_tasks_start_empty(client):
    assert client.get("/api/tasks").json() == []


def test_create_task_trims_title(client):
    res = client.post("/api/tasks", json={"title": "  Buy milk  "})
    assert res.status_code == 201
    task = res.json()
    assert task["title"] == "Buy milk"
    assert task["done"] is False
    assert isinstance(task["id"], int)
    assert task["created_at"]


@pytest.mark.parametrize("title", ["", "   ", "x" * 201])
def test_create_task_rejects_bad_titles(client, title):
    assert client.post("/api/tasks", json={"title": title}).status_code == 422


def test_list_returns_tasks_in_creation_order(client):
    client.post("/api/tasks", json={"title": "First"})
    client.post("/api/tasks", json={"title": "Second"})
    titles = [t["title"] for t in client.get("/api/tasks").json()]
    assert titles == ["First", "Second"]


def test_tick_and_untick_task(client):
    task_id = client.post("/api/tasks", json={"title": "Call mom"}).json()["id"]

    res = client.patch(f"/api/tasks/{task_id}", json={"done": True})
    assert res.status_code == 200
    assert res.json()["done"] is True

    res = client.patch(f"/api/tasks/{task_id}", json={"done": False})
    assert res.json()["done"] is False


def test_rename_task(client):
    task_id = client.post("/api/tasks", json={"title": "Old"}).json()["id"]
    res = client.patch(f"/api/tasks/{task_id}", json={"title": " New "})
    assert res.json()["title"] == "New"
    assert res.json()["done"] is False


def test_patch_missing_task_is_404(client):
    assert client.patch("/api/tasks/999", json={"done": True}).status_code == 404


def test_delete_task(client):
    task_id = client.post("/api/tasks", json={"title": "Temp"}).json()["id"]

    assert client.delete(f"/api/tasks/{task_id}").status_code == 204
    assert client.get("/api/tasks").json() == []
    assert client.delete(f"/api/tasks/{task_id}").status_code == 404


def test_tasks_survive_restart(client):
    client.post("/api/tasks", json={"title": "Keep me"})

    with TestClient(app) as restarted:
        titles = [t["title"] for t in restarted.get("/api/tasks").json()]
    assert titles == ["Keep me"]


# --- password (only when APP_PASSWORD is set) -------------------------------

def _basic(password, user="thoshi"):
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


@pytest.fixture
def locked(client, monkeypatch):
    monkeypatch.setattr(main, "APP_PASSWORD", "open-sesame")
    return client


def test_no_password_configured_means_open(client):
    assert client.get("/api/tasks").status_code == 200


def test_password_required_when_configured(locked):
    res = locked.get("/")
    assert res.status_code == 401
    assert res.headers["WWW-Authenticate"].startswith("Basic")


def test_wrong_password_rejected(locked):
    assert locked.get("/api/tasks", headers=_basic("nope")).status_code == 401


def test_malformed_auth_header_rejected(locked):
    assert locked.get("/api/tasks", headers={"Authorization": "Basic !!!notbase64"}).status_code == 401


def test_right_password_allowed_with_any_username(locked):
    assert locked.get("/api/tasks", headers=_basic("open-sesame", user="anyone")).status_code == 200


def test_health_stays_open_for_monitoring(locked):
    assert locked.get("/health").status_code == 200
