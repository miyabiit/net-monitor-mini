from pathlib import Path

from net_monitor.config.loader import load_app_config


def test_load_config_resolves_relative_paths(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    config_dir = project_root / "config"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "appsettings.json"
    config_file.write_text(
        """
        {
          "version": 1,
          "app": {"host": "127.0.0.1", "port": 8080, "open_browser_on_start": false},
          "logging": {"level": "INFO", "file_path": "./logs/app.log", "rotate": false},
          "storage": {"database_path": "./data/app.db", "retention_days": 30},
          "targets": [
            {
              "id": "target_1",
              "name": "Target 1",
              "address": "127.0.0.1",
              "enabled": true,
              "monitor_type": "ping",
              "interval_seconds": 300,
              "ping_count": 3,
              "timeout_seconds": 2
            }
          ]
        }
        """,
        encoding="utf-8",
    )

    config = load_app_config(config_file)

    assert config.storage.database_path == str((project_root / "data" / "app.db").resolve())
    assert config.logging.file_path == str((project_root / "logs" / "app.log").resolve())


def test_default_config_contains_nine_targets_with_labels() -> None:
    config = load_app_config(Path("config/appsettings.json").resolve())

    assert len(config.targets) == 9
    assert [(target.name, target.address) for target in config.targets] == [
        ("Local Gateway", "192.168.1.1"),
        ("haneda", "192.168.100.1"),
        ("okinawa", "192.168.104.11"),
        ("shibuya", "10.0.16.1"),
        ("tatsumi", "192.168.9.1"),
        ("narita", "192.168.3.1"),
        ("prologi", "192.168.8.1"),
        ("osaka", "192.168.5.1"),
        ("osaka2", "192.168.7.1"),
    ]
