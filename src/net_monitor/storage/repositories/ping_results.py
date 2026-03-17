from __future__ import annotations

from sqlalchemy import desc, func, select
from sqlalchemy.orm import sessionmaker

from net_monitor.models.domain import PingProbeResult
from net_monitor.storage.models import MonitorTargetRecord, PingResultRecord
from net_monitor.time_utils import to_jst_isoformat


class PingResultRepository:
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def save_results(self, results: list[PingProbeResult]) -> None:
        if not results:
            return

        target_key = results[0].target_id
        with self._session_factory() as session:
            target_record = session.execute(
                select(MonitorTargetRecord).where(MonitorTargetRecord.target_key == target_key)
            ).scalar_one()
            for result in results:
                session.add(
                    PingResultRecord(
                        target_id=target_record.id,
                        cycle_id=result.cycle_id,
                        measured_at=result.measured_at,
                        attempt_no=result.attempt_no,
                        success=result.success,
                        latency_ms=result.latency_ms,
                        status_code=result.status_code,
                        status_message=result.status_message,
                    )
                )
            session.commit()

    def list_results(self, target_id: str, limit: int = 200) -> list[dict]:
        with self._session_factory() as session:
            rows = session.execute(
                select(PingResultRecord)
                .join(MonitorTargetRecord, PingResultRecord.target_id == MonitorTargetRecord.id)
                .where(MonitorTargetRecord.target_key == target_id)
                .order_by(desc(PingResultRecord.measured_at))
                .limit(limit)
            ).scalars().all()
            return [
                {
                    "cycle_id": row.cycle_id,
                    "measured_at": to_jst_isoformat(row.measured_at),
                    "attempt_no": row.attempt_no,
                    "success": row.success,
                    "latency_ms": row.latency_ms,
                    "status_code": row.status_code,
                    "status_message": row.status_message,
                }
                for row in reversed(rows)
            ]

    def get_summary(self, target_id: str) -> dict:
        with self._session_factory() as session:
            base_query = (
                select(PingResultRecord)
                .join(MonitorTargetRecord, PingResultRecord.target_id == MonitorTargetRecord.id)
                .where(MonitorTargetRecord.target_key == target_id)
            )
            latest = session.execute(
                base_query.order_by(desc(PingResultRecord.measured_at)).limit(1)
            ).scalar_one_or_none()

            total = session.execute(
                select(func.count())
                .select_from(PingResultRecord)
                .join(MonitorTargetRecord, PingResultRecord.target_id == MonitorTargetRecord.id)
                .where(MonitorTargetRecord.target_key == target_id)
            ).scalar_one()

            success_count = session.execute(
                select(func.count())
                .select_from(PingResultRecord)
                .join(MonitorTargetRecord, PingResultRecord.target_id == MonitorTargetRecord.id)
                .where(
                    MonitorTargetRecord.target_key == target_id,
                    PingResultRecord.success.is_(True),
                )
            ).scalar_one()

            avg_latency = session.execute(
                select(func.avg(PingResultRecord.latency_ms))
                .join(MonitorTargetRecord, PingResultRecord.target_id == MonitorTargetRecord.id)
                .where(
                    MonitorTargetRecord.target_key == target_id,
                    PingResultRecord.latency_ms.is_not(None),
                )
            ).scalar_one()

            success_rate = (success_count / total * 100.0) if total else None

            return {
                "target_id": target_id,
                "latest_result": None
                if latest is None
                else {
                    "measured_at": to_jst_isoformat(latest.measured_at),
                    "success": latest.success,
                    "latency_ms": latest.latency_ms,
                    "status_code": latest.status_code,
                    "status_message": latest.status_message,
                },
                "total_count": total,
                "success_count": success_count,
                "success_rate": success_rate,
                "average_latency_ms": float(avg_latency) if avg_latency is not None else None,
            }
