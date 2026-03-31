from __future__ import annotations

import logging
import sys
from pathlib import Path


def configure_logging(log_file_path: str, log_level: str) -> None:
    log_path = Path(log_file_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.__stderr__),
        ],
        force=True,
    )
