from net_monitor.monitoring.ping.parser import parse_ping_output
from net_monitor.monitoring.ping.runner import _decode_output


def test_parse_ping_output_success() -> None:
    success, latency, status_code, _ = parse_ping_output(
        0,
        "Reply from 127.0.0.1: bytes=32 time=5ms TTL=128",
        "",
    )

    assert success is True
    assert latency == 5.0
    assert status_code == "success"


def test_parse_ping_output_timeout() -> None:
    success, latency, status_code, _ = parse_ping_output(
        1,
        "Request timed out.",
        "",
    )

    assert success is False
    assert latency is None
    assert status_code == "timeout"


def test_parse_ping_output_japanese_success() -> None:
    success, latency, status_code, _ = parse_ping_output(
        0,
        "192.168.1.1 からの応答: バイト数 =32 時間 =15ms TTL=255",
        "",
    )

    assert success is True
    assert latency == 15.0
    assert status_code == "success"


def test_decode_output_supports_cp932_ping_text() -> None:
    payload = "192.168.1.1 に ping を送信しています 32 バイトのデータ:".encode("cp932")
    decoded = _decode_output(payload)

    assert "192.168.1.1" in decoded
    assert "32" in decoded
