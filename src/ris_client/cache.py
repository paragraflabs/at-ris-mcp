"""SQLite-backed response cache with TTL (PLAN.md §8a).

Reduces load on the RIS API (netiquette) and speeds up repeated recherche.
A single file, atomic, with an expiry column. Deliberately simple; FTS5
full-text search is a v2 upgrade path.
"""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from threading import Lock


class Cache:
    def __init__(self, path: Path, enabled: bool = True) -> None:
        self.enabled = enabled
        self.path = path
        self._lock = Lock()
        self._conn: sqlite3.Connection | None = None
        if enabled:
            path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(str(path), check_same_thread=False)
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS cache ("
                "  key TEXT PRIMARY KEY,"
                "  value TEXT NOT NULL,"
                "  expires_at REAL NOT NULL"
                ")"
            )
            self._conn.commit()

    def get(self, key: str) -> str | None:
        if not self.enabled or self._conn is None:
            return None
        with self._lock:
            row = self._conn.execute(
                "SELECT value, expires_at FROM cache WHERE key = ?", (key,)
            ).fetchone()
            if row is None:
                return None
            value, expires_at = row
            if expires_at < time.time():
                self._conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                self._conn.commit()
                return None
            return value

    def set(self, key: str, value: str, ttl_s: int) -> None:
        if not self.enabled or self._conn is None or ttl_s <= 0:
            return
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, ?)",
                (key, value, time.time() + ttl_s),
            )
            self._conn.commit()

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None
