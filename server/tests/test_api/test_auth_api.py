"""Auth API response shape tests."""

from fastapi.testclient import TestClient


def test_demo_status_returns_wrapped_response(client: TestClient) -> None:
    """Ensure /api/auth/demo-status adopts the unified BaseResponse envelope."""

    response = client.get("/api/auth/demo-status")
    assert response.status_code == 200
    payload = response.json()

    assert payload["success"] is True
    assert payload["message"] == "ok"
    assert isinstance(payload["data"], dict)
    assert payload["data"]["demo_enabled"] is False

