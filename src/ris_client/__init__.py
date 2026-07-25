"""ris_client - standalone, MCP-independent client for the Austrian RIS.

Public API::

    from ris_client import RisClient, LawSearchRequest, CaseSearchRequest
    async with RisClient() as c:
        res = await c.search_law(LawSearchRequest(suchworte="Datenschutz"))

Convenience module-level coroutines (``search_law`` etc.) create a short-lived
client for one-off calls.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 at-ris-mcp contributors

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
    Bundesland,
    CaseRecord,
    CaseSearchRequest,
    ChangeRecord,
    ChangeSetInterval,
    ChangesResult,
    CourtApplikation,
    DistrictApplikation,
    DistrictSearchRequest,
    HistoryApplikation,
    HistoryRequest,
    LawApplikation,
    LawRecord,
    LawSearchRequest,
    MiscApplikation,
    MiscSearchRequest,
    MunicipalityApplikation,
    MunicipalitySearchRequest,
    PageSize,
    SearchResult,
    SortDirection,
    StateLawApplikation,
    StateLawSearchRequest,
    TextFormat,
    TextResult,
)

__all__ = [
    "RisClient",
    "Config",
    "__version__",
    "LawSearchRequest",
    "CaseSearchRequest",
    "HistoryRequest",
    "StateLawSearchRequest",
    "MiscSearchRequest",
    "DistrictSearchRequest",
    "MunicipalitySearchRequest",
    "LawRecord",
    "CaseRecord",
    "ChangeRecord",
    "SearchResult",
    "ChangesResult",
    "TextResult",
    "TextFormat",
    "PageSize",
    "ChangeSetInterval",
    "NormabschnittTyp",
    "SortDirection",
    "Bundesland",
    "LawApplikation",
    "CourtApplikation",
    "HistoryApplikation",
    "StateLawApplikation",
    "MiscApplikation",
    "DistrictApplikation",
    "MunicipalityApplikation",
    "list_collections",
    "search_law",
    "search_case",
    "search_changes",
    "search_state_law",
    "search_misc",
    "search_district",
    "search_municipality",
    "get_law_text",
    "get_case_text",
]

from .models import NormabschnittTyp  # noqa: E402  (kept in __all__)


def list_collections() -> dict:
    """Static overview of the RIS scope covered by this server."""
    return {
        "version": __version__,
        "base_url": Config.from_env().base_url,
        "endpoints": {
            "Bundesrecht": {
                "covered": True,
                "applikationen": [a.value for a in LawApplikation],
                "default": LawApplikation.BrKons.value,
                "note": "BrKons = konsolidiertes geltendes Recht (Kern-Mehrwert). "
                "Begut/RegV: einbringende_stelle, in_begutachtung_am, "
                "beschluss_von/bis werden unterstützt.",
            },
            "Judikatur": {
                "covered": True,
                "applikationen": [c.value for c in CourtApplikation],
                "default": CourtApplikation.Justiz.value,
            },
            "History": {
                "covered": True,
                "applikationen": [h.value for h in HistoryApplikation],
                "note": "Änderungs-/Frühwarn-Feed via OGD-SOAP. Konsolidiertes "
                "Bundesrecht = 'Bundesnormen' (nicht 'BrKons'). "
                "include_deleted verfügbar.",
            },
            "Landesrecht": {
                "covered": True,
                "applikationen": [a.value for a in StateLawApplikation],
                "default": StateLawApplikation.LrKons.value,
                "note": "9 Bundesländer. LrKons wählt Länder über "
                "bundeslaender=[...] (Bundesland.SucheIn<Land>-Flags).",
            },
            "Sonstige": {
                "covered": True,
                "applikationen": [a.value for a in MiscApplikation],
                "default": MiscApplikation.Erlaesse.value,
                "note": "Erlässe, Avsv, Avn, Spg, KmGer, Upts, Mrp, PruefGewO - "
                "inkl. app-spezifischer Feinfilter (Avsvnummer, Spgnummer, "
                "Sitzungsnummer, Gericht, Partei, ...).",
            },
            "Bezirke": {
                "covered": True,
                "applikationen": [a.value for a in DistrictApplikation],
                "default": DistrictApplikation.Bvb.value,
            },
            "Gemeinden": {
                "covered": True,
                "applikationen": [a.value for a in MunicipalityApplikation],
                "default": MunicipalityApplikation.Gr.value,
            },
        },
        "not_yet_covered": {},
        "attribution": "Quelle: RIS - Rechtsinformationssystem des Bundes "
        "(data.bka.gv.at), CC BY 4.0",
        "dataset_note": "Bundesrecht (inkl. Erv), Landesrecht, Judikatur, "
        "Sonstige, Bezirke, Gemeinden und der History-Änderungsfeed sind "
        "abgedeckt.",
    }


# -- one-off convenience coroutines ----------------------------------------
async def search_law(req: LawSearchRequest, config: Config | None = None) -> SearchResult:
    async with RisClient(config) as c:
        return await c.search_law(req)


async def search_case(req: CaseSearchRequest, config: Config | None = None) -> SearchResult:
    async with RisClient(config) as c:
        return await c.search_case(req)


async def search_changes(req: HistoryRequest, config: Config | None = None) -> "ChangesResult":
    async with RisClient(config) as c:
        return await c.search_changes(req)


async def search_state_law(req: StateLawSearchRequest, config: Config | None = None) -> SearchResult:
    async with RisClient(config) as c:
        return await c.search_state_law(req)


async def search_misc(req: MiscSearchRequest, config: Config | None = None) -> SearchResult:
    async with RisClient(config) as c:
        return await c.search_misc(req)


async def search_district(req: DistrictSearchRequest, config: Config | None = None) -> SearchResult:
    async with RisClient(config) as c:
        return await c.search_district(req)


async def search_municipality(req: MunicipalitySearchRequest, config: Config | None = None) -> SearchResult:
    async with RisClient(config) as c:
        return await c.search_municipality(req)


async def get_law_text(content_url: str, format: TextFormat | str = TextFormat.markdown,
                       config: Config | None = None, *,
                       citation: str | None = None, eli_uri: str | None = None,
                       ecli: str | None = None) -> TextResult:
    async with RisClient(config) as c:
        return await c.get_text(content_url, format, citation=citation,
                                eli_uri=eli_uri, ecli=ecli)


async def get_case_text(content_url: str, format: TextFormat | str = TextFormat.markdown,
                        config: Config | None = None, *,
                        citation: str | None = None, eli_uri: str | None = None,
                        ecli: str | None = None) -> TextResult:
    async with RisClient(config) as c:
        return await c.get_text(content_url, format, citation=citation,
                                eli_uri=eli_uri, ecli=ecli)
