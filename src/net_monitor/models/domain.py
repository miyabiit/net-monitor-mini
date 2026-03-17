from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class PingProbeResult:
    target_id: str
    cycle_id: str
    measured_at: datetime
    attempt_no: int
    success: bool
    latency_ms: float | None
    status_code: str
    status_message: str
