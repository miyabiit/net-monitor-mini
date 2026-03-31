from __future__ import annotations

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from net_monitor.config.schema import AppConfig
from net_monitor.scheduler.jobs import run_target_monitor_job


class MonitorScheduler:
    def __init__(self, session_factory, app_config: AppConfig) -> None:
        self._session_factory = session_factory
        self._app_config = app_config
        self._scheduler = BackgroundScheduler()
        self._logger = logging.getLogger(__name__)

    def start(self) -> None:
        if self._scheduler.running:
            return

        for target in self._app_config.targets:
            if not target.enabled:
                continue
            self._scheduler.add_job(
                run_target_monitor_job,
                trigger="date",
                run_date=datetime.now(timezone.utc),
                id=f"monitor-immediate-{target.id}",
                replace_existing=True,
                kwargs={
                    "session_factory": self._session_factory,
                    "app_config": self._app_config,
                    "target": target,
                },
            )
            self._scheduler.add_job(
                run_target_monitor_job,
                trigger="interval",
                seconds=target.interval_seconds,
                id=f"monitor-{target.id}",
                replace_existing=True,
                kwargs={
                    "session_factory": self._session_factory,
                    "app_config": self._app_config,
                    "target": target,
                },
                max_instances=1,
                coalesce=True,
            )
            self._logger.info(
                "scheduled monitor jobs target_id=%s interval_seconds=%s",
                target.id,
                target.interval_seconds,
            )

        self._scheduler.start()

    def shutdown(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=True)
