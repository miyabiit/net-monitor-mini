from __future__ import annotations

import argparse
from pathlib import Path

import uvicorn

from net_monitor.app.bootstrap import create_app


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Network monitor server")
    parser.add_argument(
        "--config",
        default="config/appsettings.json",
        help="Path to configuration file",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config_path = Path(args.config).resolve()
    app = create_app(config_path)
    app_config = app.state.app_config.app
    uvicorn.run(
        app,
        host=app_config.host,
        port=app_config.port,
        log_config=None,
    )


if __name__ == "__main__":
    main()
