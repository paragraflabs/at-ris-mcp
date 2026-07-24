"""Rate limiting to honour RIS netiquette (1-2 s pause per page).

A single async lock serialises requests and enforces a minimum inter-request
delay. Office-hours guidance from the OGD-FAQ (mass downloads only 18:00-06:00
or on weekends) is surfaced as an advisory, not enforced, because interactive
recherche is not a mass download.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 at-ris-mcp contributors

from __future__ import annotations

import asyncio
import time


class RateLimiter:
    """Enforces a minimum delay between successive requests."""

    def __init__(self, min_interval_ms: int) -> None:
        self._min_interval = max(0.0, min_interval_ms / 1000.0)
        self._lock = asyncio.Lock()
        self._last: float = 0.0

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            wait = self._min_interval - (now - self._last)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last = time.monotonic()


def office_hours_hint(now: time.struct_time | None = None) -> str | None:
    """Return an advisory string if a heavy run would fall in office hours.

    Per OGD-FAQ, massive access should happen outside 06:00-18:00 or on
    weekends. Returns None during the recommended window.
    """
    t = now or time.localtime()
    is_weekend = t.tm_wday >= 5
    in_office_hours = 6 <= t.tm_hour < 18
    if in_office_hours and not is_weekend:
        return (
            "RIS netiquette: large/bulk access should occur outside office "
            "hours (18:00-06:00) or on weekends. Announce mass downloads to "
            "ris.it@bka.gv.at."
        )
    return None
