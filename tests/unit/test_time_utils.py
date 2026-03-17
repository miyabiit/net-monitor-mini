from __future__ import annotations

from datetime import datetime, timezone

from net_monitor.time_utils import to_jst_isoformat


def test_to_jst_isoformat_converts_utc_to_jst() -> None:
    value = datetime(2026, 3, 17, 0, 20, 49, tzinfo=timezone.utc)

    assert to_jst_isoformat(value) == "2026-03-17T09:20:49+09:00"


def test_to_jst_isoformat_treats_naive_datetime_as_utc() -> None:
    value = datetime(2026, 3, 17, 0, 20, 49)

    assert to_jst_isoformat(value) == "2026-03-17T09:20:49+09:00"
