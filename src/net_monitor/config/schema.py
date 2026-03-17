from __future__ import annotations

import re
from pathlib import Path

from pydantic import BaseModel, Field, field_validator, model_validator


class AppSection(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8080
    open_browser_on_start: bool = False

    @field_validator("port")
    @classmethod
    def validate_port(cls, value: int) -> int:
        if not 1 <= value <= 65535:
            raise ValueError("port must be between 1 and 65535")
        return value


class LoggingSection(BaseModel):
    level: str = "INFO"
    file_path: str = "./logs/net-monitor.log"
    rotate: bool = False

    @field_validator("level")
    @classmethod
    def validate_level(cls, value: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR"}
        upper = value.upper()
        if upper not in allowed:
            raise ValueError(f"logging.level must be one of {sorted(allowed)}")
        return upper


class StorageSection(BaseModel):
    database_path: str = "./data/net_monitor.db"
    retention_days: int = 30

    @field_validator("retention_days")
    @classmethod
    def validate_retention_days(cls, value: int) -> int:
        if value < 1:
            raise ValueError("storage.retention_days must be 1 or greater")
        return value


class TargetConfig(BaseModel):
    id: str
    name: str
    address: str
    enabled: bool = True
    monitor_type: str = "ping"
    interval_seconds: int = 300
    ping_count: int = 3
    timeout_seconds: float = 2.0
    tags: list[str] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9_-]+", value):
            raise ValueError("target id must contain only letters, digits, hyphen, underscore")
        return value

    @field_validator("name", "address")
    @classmethod
    def validate_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must not be blank")
        return value

    @field_validator("monitor_type")
    @classmethod
    def validate_monitor_type(cls, value: str) -> str:
        if value != "ping":
            raise ValueError("only ping monitor_type is supported in initial release")
        return value

    @field_validator("interval_seconds")
    @classmethod
    def validate_interval_seconds(cls, value: int) -> int:
        if value < 60:
            raise ValueError("interval_seconds must be 60 or greater")
        return value

    @field_validator("ping_count")
    @classmethod
    def validate_ping_count(cls, value: int) -> int:
        if not 1 <= value <= 10:
            raise ValueError("ping_count must be between 1 and 10")
        return value

    @field_validator("timeout_seconds")
    @classmethod
    def validate_timeout_seconds(cls, value: float) -> float:
        if value <= 0.1:
            raise ValueError("timeout_seconds must be greater than 0.1")
        return value


class AppConfig(BaseModel):
    version: int = 1
    app: AppSection = Field(default_factory=AppSection)
    logging: LoggingSection = Field(default_factory=LoggingSection)
    storage: StorageSection = Field(default_factory=StorageSection)
    targets: list[TargetConfig] = Field(default_factory=list)

    @field_validator("version")
    @classmethod
    def validate_version(cls, value: int) -> int:
        if value != 1:
            raise ValueError("only version 1 is supported")
        return value

    @model_validator(mode="after")
    def validate_unique_target_ids(self) -> "AppConfig":
        target_ids = [target.id for target in self.targets]
        if len(target_ids) != len(set(target_ids)):
            raise ValueError("target ids must be unique")
        return self

    def resolve_paths(self, project_root: Path) -> None:
        self.logging.file_path = str(_resolve_path(project_root, self.logging.file_path))
        self.storage.database_path = str(_resolve_path(project_root, self.storage.database_path))


def _resolve_path(project_root: Path, candidate: str) -> Path:
    path = Path(candidate)
    if path.is_absolute():
        return path
    return (project_root / path).resolve()
