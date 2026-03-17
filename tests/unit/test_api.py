from pathlib import Path

from fastapi.testclient import TestClient

from net_monitor.app.bootstrap import create_app


def test_health_and_targets_endpoints() -> None:
    app = create_app(Path("config/appsettings.json").resolve())
    client = TestClient(app)

    health_response = client.get("/health")
    targets_response = client.get("/api/targets")

    assert health_response.status_code == 200
    assert health_response.json() == {"status": "ok"}
    assert targets_response.status_code == 200
    assert isinstance(targets_response.json(), list)
