"""Runtime configuration for the RIS client.

All values are overridable via environment variables so the client can be
retargeted (e.g. a new API version) without code changes, as required by
PLAN.md §6 ("API-Version 2.6 kann sich ändern").
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

__version__ = "0.1.0"

DEFAULT_BASE_URL = "https://data.bka.gv.at/ris/api/v2.6"
# Hosts we are allowed to fetch full text from (PLAN.md §5 host restriction).
ALLOWED_TEXT_HOSTS = ("www.ris.bka.gv.at", "ris.bka.gv.at", "data.bka.gv.at")

# A descriptive, non-browser User-Agent as demanded by RIS netiquette
# (OGD-FAQ: "Das Anfügen eines User-Agent HTTP Headers ... wird empfohlen").
DEFAULT_USER_AGENT = (
    f"at-ris-mcp/{__version__} "
    "(+https://github.com/anomalyco/at-ris-mcp)"
)


def _env_bool(name: str, default: bool = False) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


def _default_cache_path() -> Path:
    base = os.environ.get("RIS_CACHE_DIR")
    if base:
        return Path(base).expanduser() / "ris_cache.sqlite"
    return Path.home() / ".cache" / "at-ris-mcp" / "ris_cache.sqlite"


@dataclass(slots=True)
class Config:
    """Central client configuration; instantiated from the environment."""

    base_url: str = DEFAULT_BASE_URL
    user_agent: str = DEFAULT_USER_AGENT
    # Minimum delay between outgoing HTTP requests (netiquette: 1-2 s/page).
    rate_ms: int = 1200
    timeout_s: float = 30.0
    max_retries: int = 3

    # Cache
    cache_enabled: bool = True
    cache_path: Path = field(default_factory=_default_cache_path)
    cache_ttl_search_s: int = 7 * 24 * 3600  # consolidated law/case law: rarely changes
    cache_ttl_text_s: int = 30 * 24 * 3600

    # Audit log (opt-in, off by default; PLAN.md §8a).
    audit_dir: Path | None = None

    @classmethod
    def from_env(cls) -> "Config":
        audit = os.environ.get("RIS_AUDIT_DIR")
        return cls(
            base_url=os.environ.get("RIS_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
            user_agent=os.environ.get("RIS_USER_AGENT", DEFAULT_USER_AGENT),
            rate_ms=int(os.environ.get("RIS_RATE_MS", "1200")),
            timeout_s=float(os.environ.get("RIS_TIMEOUT_S", "30")),
            max_retries=int(os.environ.get("RIS_MAX_RETRIES", "3")),
            cache_enabled=_env_bool("RIS_CACHE_ENABLED", True),
            cache_path=_default_cache_path(),
            audit_dir=Path(audit).expanduser() if audit else None,
        )
