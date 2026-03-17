from __future__ import annotations

import re


def parse_ping_output(return_code: int, stdout: str, stderr: str) -> tuple[bool, float | None, str, str]:
    text = "\n".join(part for part in [stdout, stderr] if part).strip()
    normalized = text.lower()

    latency = _extract_latency_ms(text)
    if return_code == 0 and latency is not None:
        return True, latency, "success", "ping succeeded"

    if "could not find host" in normalized or "ping request could not find host" in normalized:
        return False, None, "dns_error", "host name could not be resolved"
    if "一般エラー" in text:
        return False, None, "unknown_error", "general error"
    if "request timed out" in normalized or "要求がタイムアウトしました" in text:
        return False, None, "timeout", "request timed out"
    if "destination host unreachable" in normalized or "宛先ホストに到達できません" in text:
        return False, None, "unreachable", "destination host unreachable"
    if latency is not None:
        return return_code == 0, latency, "success" if return_code == 0 else "partial", "ping completed"
    return False, None, "unknown_error", text or "unknown ping error"


def _extract_latency_ms(text: str) -> float | None:
    patterns = [
        r"time\s*[=<]\s*(\d+(?:\.\d+)?)\s*ms",
        r"時間\s*[=<]\s*(\d+(?:\.\d+)?)\s*ms",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return float(match.group(1))
    normalized = text.lower()
    if (
        "time<1ms" in normalized
        or "time <1ms" in normalized
        or "time< 1ms" in normalized
        or "time < 1ms" in normalized
        or "時間<1ms" in text
        or "時間 <1ms" in text
        or "時間< 1ms" in text
        or "時間 < 1ms" in text
    ):
        return 1.0
    return None
