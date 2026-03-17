from __future__ import annotations

import locale
import subprocess

from net_monitor.monitoring.ping.parser import parse_ping_output


def run_ping_once(address: str, timeout_seconds: float) -> tuple[bool, float | None, str, str]:
    timeout_ms = max(int(timeout_seconds * 1000), 100)
    command = ["ping", "-n", "1", "-w", str(timeout_ms), address]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=False,
        check=False,
    )
    stdout = _decode_output(completed.stdout)
    stderr = _decode_output(completed.stderr)
    return parse_ping_output(completed.returncode, stdout, stderr)


def _decode_output(payload: bytes) -> str:
    if not payload:
        return ""

    candidates = []
    preferred = locale.getpreferredencoding(False)
    if preferred:
        candidates.append(preferred)
    candidates.extend(["cp932", "utf-8"])

    seen: set[str] = set()
    for encoding in candidates:
        normalized = encoding.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        try:
            return payload.decode(encoding)
        except UnicodeDecodeError:
            continue

    return payload.decode(candidates[0], errors="replace")
