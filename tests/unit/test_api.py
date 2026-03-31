from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from net_monitor.app.bootstrap import create_app
from net_monitor.storage.models import MonitorTargetRecord, PingResultRecord


def test_health_and_targets_endpoints() -> None:
    app = create_app(Path("config/appsettings.json").resolve())
    client = TestClient(app)

    health_response = client.get("/health")
    targets_response = client.get("/api/targets")

    assert health_response.status_code == 200
    assert health_response.json() == {"status": "ok"}
    assert targets_response.status_code == 200
    assert isinstance(targets_response.json(), list)


def test_results_endpoint_supports_days_filter(tmp_path: Path) -> None:
    config_path = _create_test_config(tmp_path)
    app = create_app(config_path)
    client = TestClient(app)
    session_factory = app.state.session_factory
    now = datetime.now(timezone.utc)

    with session_factory() as session:
        target_record = session.query(MonitorTargetRecord).filter_by(target_key="test-target").one()
        session.add_all(
            [
                PingResultRecord(
                    target_id=target_record.id,
                    cycle_id="recent-cycle",
                    measured_at=now - timedelta(days=1),
                    attempt_no=1,
                    success=True,
                    latency_ms=10.0,
                    status_code="success",
                    status_message="ok",
                ),
                PingResultRecord(
                    target_id=target_record.id,
                    cycle_id="old-cycle",
                    measured_at=now - timedelta(days=8),
                    attempt_no=1,
                    success=False,
                    latency_ms=None,
                    status_code="timeout",
                    status_message="timeout",
                ),
            ]
        )
        session.commit()

    response = client.get("/api/targets/test-target/results?days=7&limit=100")

    assert response.status_code == 200
    payload = response.json()
    assert payload["target_id"] == "test-target"
    assert len(payload["results"]) == 1
    assert payload["results"][0]["cycle_id"] == "recent-cycle"


def _create_test_config(tmp_path: Path) -> Path:
    root_dir = tmp_path / "project"
    config_dir = root_dir / "config"
    config_dir.mkdir(parents=True)
    config_path = config_dir / "appsettings.json"
    config_path.write_text(
        json.dumps(
            {
                "version": 1,
                "app": {
                    "host": "127.0.0.1",
                    "port": 18080,
                    "open_browser_on_start": False,
                },
                "logging": {
                    "level": "INFO",
                    "file_path": "./logs/test.log",
                    "rotate": False,
                },
                "storage": {
                    "database_path": "./data/test.db",
                    "retention_days": 30,
                },
                "targets": [
                    {
                        "id": "test-target",
                        "name": "Test Target",
                        "address": "127.0.0.1",
                        "enabled": True,
                        "monitor_type": "ping",
                        "interval_seconds": 300,
                        "ping_count": 3,
                        "timeout_seconds": 2,
                        "tags": [],
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return config_path
