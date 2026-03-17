from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone

from sqlalchemy import desc, select
from sqlalchemy.orm import sessionmaker

from net_monitor.config.schema import TargetConfig
from net_monitor.storage.models import MonitorTargetRecord, PingResultRecord
from net_monitor.time_utils import to_jst_isoformat


class TargetRepository:
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def sync_targets_from_config(self, targets: Sequence[TargetConfig]) -> None:
        with self._session_factory() as session:
            existing = {
                item.target_key: item
                for item in session.execute(select(MonitorTargetRecord)).scalars().all()
            }

            for target in targets:
                record = existing.get(target.id)
                if record is None:
                    record = MonitorTargetRecord(
                        target_key=target.id,
                        name=target.name,
                        address=target.address,
                        enabled=target.enabled,
                        monitor_type=target.monitor_type,
                        interval_seconds=target.interval_seconds,
                        probe_count=target.ping_count,
                        timeout_seconds=target.timeout_seconds,
                    )
                    session.add(record)
                    continue

                record.name = target.name
                record.address = target.address
                record.enabled = target.enabled
                record.monitor_type = target.monitor_type
                record.interval_seconds = target.interval_seconds
                record.probe_count = target.ping_count
                record.timeout_seconds = target.timeout_seconds
                record.updated_at = datetime.now(timezone.utc)

            session.commit()

    def list_targets_with_latest_status(self) -> list[dict]:
        with self._session_factory() as session:
            target_records = session.execute(
                select(MonitorTargetRecord).order_by(MonitorTargetRecord.name)
            ).scalars().all()

            results: list[dict] = []
            for record in target_records:
                latest = session.execute(
                    select(PingResultRecord)
                    .where(PingResultRecord.target_id == record.id)
                    .order_by(desc(PingResultRecord.measured_at))
                    .limit(1)
                ).scalar_one_or_none()
                results.append(
                    {
                        "id": record.target_key,
                        "name": record.name,
                        "address": record.address,
                        "enabled": record.enabled,
                        "monitor_type": record.monitor_type,
                        "interval_seconds": record.interval_seconds,
                        "ping_count": record.probe_count,
                        "timeout_seconds": record.timeout_seconds,
                        "latest_result": None
                        if latest is None
                        else {
                            "measured_at": to_jst_isoformat(latest.measured_at),
                            "success": latest.success,
                            "latency_ms": latest.latency_ms,
                            "status_code": latest.status_code,
                            "status_message": latest.status_message,
                        },
                    }
                )
            return results
