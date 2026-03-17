from __future__ import annotations

from datetime import datetime, timedelta, timezone


JST = timezone(timedelta(hours=9))


def to_jst_isoformat(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(JST).isoformat()
