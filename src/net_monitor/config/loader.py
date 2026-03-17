from __future__ import annotations

import json
from pathlib import Path

from net_monitor.config.schema import AppConfig


def load_app_config(config_path: Path) -> AppConfig:
    raw_text = config_path.read_text(encoding="utf-8")
    payload = json.loads(raw_text)
    app_config = AppConfig.model_validate(payload)
    app_config.resolve_paths(config_path.parent.parent.resolve())
    return app_config
