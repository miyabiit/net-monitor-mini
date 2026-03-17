from __future__ import annotations

import logging

from sqlalchemy.orm import sessionmaker

from net_monitor.config.schema import AppConfig, TargetConfig
from net_monitor.monitoring.ping.service import PingMonitorService
from net_monitor.storage.repositories.ping_results import PingResultRepository


def run_target_monitor_job(
    session_factory: sessionmaker,
    app_config: AppConfig,
    target: TargetConfig,
) -> None:
    logger = logging.getLogger(__name__)
    if not target.enabled:
        return

    monitor_service = PingMonitorService()
    repository = PingResultRepository(session_factory)

    try:
        results = monitor_service.run_cycle(target)
        repository.save_results(results)
    except Exception as exc:  # noqa: BLE001
        logger.exception("monitor job failed for target_id=%s: %s", target.id, exc)
