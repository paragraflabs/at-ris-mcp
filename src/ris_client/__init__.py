"""ris_client - standalone, MCP-independent client for the Austrian RIS.

Public API::

    from ris_client import RisClient, LawSearchRequest, CaseSearchRequest
    async with RisClient() as c:
        res = await c.search_law(LawSearchRequest(suchworte="Datenschutz"))

Convenience module-level coroutines (``search_law`` etc.) create a short-lived
client for one-off calls.
"""

from __future__ import annotations

from .client import RisClient
from .config import Config, __version__
from .errors import (
    InvalidArgError,
    NotFoundError,
    NotImplementedYetError,
    RisError,
    UnsupportedFormatError,
    UpstreamError,
)
from .models import (
    CaseRecord,
    CaseSearchRequest,
    ChangeSetInterval,
    CourtApplikation,
    LawApplikation,
    LawRecord,
    LawSearchRequest,
    PageSize,
    SearchResult,
    SortDirection,
    TextFormat,
    TextResult,
)

__all__ = [
    "RisClient",
    "Config",
    "__version__",
    "LawSearchRequest",
    "CaseSearchRequest",
    "LawRecord",
    "CaseRecord",
    "SearchResult",
    "TextResult",
    "TextFormat",
    "PageSize",
    "ChangeSetInterval",
    "NormabschnittTyp",
    "SortDirection",
    "LawApplikation",
    "CourtApplikation",
    "RisError",
    "InvalidArgError",
    "NotFoundError",
    "UnsupportedFormatError",
    "UpstreamError",
    "NotImplementedYetError",
    "list_collections",
    "search_law",
    "search_case",
    "get_law_text",
    "get_case_text",
]

from .models import NormabschnittTyp  # noqa: E402  (kept in __all__)


def list_collections() -> dict:
    """Static overview of the RIS scope covered by v0.1 (PLAN.md §4)."""
    return {
        "version": __version__,
        "base_url": Config.from_env().base_url,
        "endpoints": {
            "Bundesrecht": {
                "covered": True,
                "applikationen": [a.value for a in LawApplikation],
                "default": LawApplikation.BrKons.value,
                "note": "BrKons = konsolidiertes geltendes Recht (Kern-Mehrwert).",
            },
            "Judikatur": {
                "covered": True,
                "applikationen": [c.value for c in CourtApplikation],
                "default": CourtApplikation.Justiz.value,
            },
        },
        "not_yet_covered": {
            "Landesrecht": "9 Bundesländer - Roadmap v0.3",
            "Sonstige": "Erlässe, Avsv, ... - Roadmap v0.3",
            "Bezirke/Gemeinden": "Roadmap v0.3",
            "History (ris_list_changes)": "Änderungs-/Frühwarn-Feed - Roadmap v0.2",
        },
        "attribution": "Quelle: RIS - Rechtsinformationssystem des Bundes "
        "(data.bka.gv.at), CC BY 4.0",
        "dataset_note": "Landesrecht, Sonstige, Bezirke und Gemeinden sind in "
        "v0.1 noch nicht abgedeckt.",
    }


# -- one-off convenience coroutines ----------------------------------------
async def search_law(req: LawSearchRequest, config: Config | None = None) -> SearchResult:
    async with RisClient(config) as c:
        return await c.search_law(req)


async def search_case(req: CaseSearchRequest, config: Config | None = None) -> SearchResult:
    async with RisClient(config) as c:
        return await c.search_case(req)


async def get_law_text(content_url: str, fmt: TextFormat | str = TextFormat.markdown,
                       config: Config | None = None, **kw) -> TextResult:
    async with RisClient(config) as c:
        return await c.get_text(content_url, fmt, **kw)


async def get_case_text(content_url: str, fmt: TextFormat | str = TextFormat.markdown,
                        config: Config | None = None, **kw) -> TextResult:
    async with RisClient(config) as c:
        return await c.get_text(content_url, fmt, **kw)
