from __future__ import annotations

from abc import ABC, abstractmethod

from net_monitor.config.schema import TargetConfig
from net_monitor.models.domain import PingProbeResult


class MonitorService(ABC):
    @abstractmethod
    def run_cycle(self, target: TargetConfig) -> list[PingProbeResult]:
        raise NotImplementedError
