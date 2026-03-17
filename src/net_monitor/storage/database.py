from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine as sqlalchemy_create_engine
from sqlalchemy.orm import sessionmaker

from net_monitor.storage.models import Base


def create_engine(database_path: str):
    db_path = Path(database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlalchemy_create_engine(f"sqlite:///{db_path}", future=True)


def build_session_factory(engine) -> sessionmaker:
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


def init_database(engine) -> None:
    Base.metadata.create_all(engine)
