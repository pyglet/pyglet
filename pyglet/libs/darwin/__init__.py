from __future__ import annotations

from typing import Any

from .cocoapy import *  # noqa: F403


def get_display_link_dt(display_link: Any, last_timestamp: float | None) -> tuple[float, float]:
    """Return the callback timestamp and the elapsed time since the prior frame."""
    timestamp = display_link.timestamp()
    if last_timestamp is None:
        dt = display_link.targetTimestamp() - timestamp
    else:
        dt = timestamp - last_timestamp

    if dt <= 0:
        dt = display_link.duration()
    return timestamp, dt
