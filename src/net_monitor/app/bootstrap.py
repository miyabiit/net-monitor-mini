from __future__ import annotations

import logging
import webbrowser
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from net_monitor.api.routes.health import router as health_router
from net_monitor.api.routes.targets import router as targets_router
from net_monitor.config.loader import load_app_config
from net_monitor.logging.setup import configure_logging
from net_monitor.scheduler.manager import MonitorScheduler
from net_monitor.storage.database import build_session_factory, create_engine, init_database
from net_monitor.storage.repositories.targets import TargetRepository


def create_app(config_path: Path) -> FastAPI:
    app_config = load_app_config(config_path)
    configure_logging(app_config.logging.file_path, app_config.logging.level)

    engine = create_engine(app_config.storage.database_path)
    session_factory = build_session_factory(engine)
    init_database(engine)

    target_repository = TargetRepository(session_factory)
    target_repository.sync_targets_from_config(app_config.targets)

    scheduler = MonitorScheduler(session_factory, app_config)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logging.getLogger(__name__).info("starting application")
        app.state.scheduler.start()
        if app.state.app_config.app.open_browser_on_start:
            url = f"http://{app.state.app_config.app.host}:{app.state.app_config.app.port}"
            webbrowser.open(url)
        try:
            yield
        finally:
            logging.getLogger(__name__).info("stopping application")
            app.state.scheduler.shutdown()
            app.state.db_engine.dispose()

    app = FastAPI(title="net-monitor-mini", lifespan=lifespan)
    app.state.app_config = app_config
    app.state.db_engine = engine
    app.state.session_factory = session_factory
    app.state.scheduler = scheduler

    app.include_router(health_router)
    app.include_router(targets_router)

    static_dir = Path(__file__).resolve().parent.parent / "visualization" / "static"
    template_dir = Path(__file__).resolve().parent.parent / "visualization" / "templates"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", include_in_schema=False)
    async def index() -> FileResponse:
        return FileResponse(template_dir / "index.html")

    return app
