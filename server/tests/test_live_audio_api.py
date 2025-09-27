import pytest
from fastapi.testclient import TestClient


def get_app():
    # Import the FastAPI app
    from server.app.main import app  # type: ignore
    return app


@pytest.fixture(scope="module")
def client():
    return TestClient(get_app())


def test_live_audio_status_shape(client: TestClient):
    resp = client.get("/api/live_audio/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "is_running" in data
    assert "stats" in data
    assert set(data["stats"]).issuperset({
        "total_audio_chunks",
        "successful_transcriptions",
        "failed_transcriptions",
        "average_confidence",
    })


def test_douyin_web_status_shape(client: TestClient):
    resp = client.get("/api/douyin/web/status")
    assert resp.status_code == 200
    data = resp.json()
    assert set(data).issuperset({"is_running", "live_id", "room_id", "last_error"})


def test_live_report_status_shape(client: TestClient):
    resp = client.get("/api/report/live/status")
    assert resp.status_code == 200
    data = resp.json()
    assert set(data).issuperset({"active", "status"})

