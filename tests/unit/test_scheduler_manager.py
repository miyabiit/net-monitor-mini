from pathlib import Path
import time

from net_monitor.config.loader import load_app_config
from net_monitor.scheduler.manager import MonitorScheduler
from net_monitor.storage.database import build_session_factory, create_engine, init_database
from net_monitor.storage.repositories.ping_results import PingResultRepository
from net_monitor.storage.repositories.targets import TargetRepository


def test_scheduler_jobs_are_not_paused(tmp_path: Path) -> None:
    db_path = tmp_path / "app.db"
    engine = create_engine(str(db_path))
    init_database(engine)
    session_factory = build_session_factory(engine)
    config = load_app_config(Path("config/appsettings.json").resolve())
    TargetRepository(session_factory).sync_targets_from_config(config.targets)

    scheduler = MonitorScheduler(session_factory, config)
    scheduler.start()

    try:
        jobs = scheduler._scheduler.get_jobs()  # noqa: SLF001
        assert jobs
        job_ids = {job.id for job in jobs}
        assert "monitor-local-gateway" in job_ids
        for job in jobs:
            assert job.next_run_time is not None

        time.sleep(1.0)
        results = PingResultRepository(session_factory).list_results("local-gateway", limit=10)
        assert results
    finally:
        scheduler.shutdown()
        engine.dispose()
