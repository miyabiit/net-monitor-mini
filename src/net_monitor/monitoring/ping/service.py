from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from net_monitor.config.schema import TargetConfig
from net_monitor.models.domain import PingProbeResult
from net_monitor.monitoring.base import MonitorService
from net_monitor.monitoring.ping.runner import run_ping_once


class PingMonitorService(MonitorService):
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def run_cycle(self, target: TargetConfig) -> list[PingProbeResult]:
        cycle_id = str(uuid.uuid4())
        results: list[PingProbeResult] = []

        for attempt_no in range(1, target.ping_count + 1):
            success, latency_ms, status_code, status_message = run_ping_once(
                target.address,
                target.timeout_seconds,
            )
            result = PingProbeResult(
                target_id=target.id,
                cycle_id=cycle_id,
                measured_at=datetime.now(timezone.utc),
                attempt_no=attempt_no,
                success=success,
                latency_ms=latency_ms,
                status_code=status_code,
                status_message=status_message,
            )
            results.append(result)
            self.logger.info(
                "ping result target_id=%s attempt=%s success=%s latency_ms=%s status=%s",
                target.id,
                attempt_no,
                success,
                latency_ms,
                status_code,
            )

        return results
