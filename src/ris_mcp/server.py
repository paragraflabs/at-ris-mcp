"""FastMCP server exposing RIS via 6 tools. Thin wrapper: all logic lives in
ris_client (PLAN.md §5 - server.py enthält keine Logik).
"""

from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from ris_client import (
    CaseSearchRequest,
    Config,
    LawSearchRequest,
    RisClient,
    RisError,
    __version__,
    list_collections as _list_collections,
)
from ris_client.errors import NotImplementedYetError

mcp = FastMCP(name="at-ris-mcp")
_config = Config.from_env()


# ---------------------------------------------------------------------------
# Audit log (opt-in via RIS_AUDIT_DIR; PLAN.md §8a) - never logs full text.
# ---------------------------------------------------------------------------
def _audit(tool: str, params: dict[str, Any], total: int | None) -> None:
    if _config.audit_dir is None:
        return
    try:
        _config.audit_dir.mkdir(parents=True, exist_ok=True)
        phash = hashlib.sha256(
            json.dumps(params, sort_keys=True, default=str).encode()
        ).hexdigest()[:16]
        line = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "tool": tool,
            "params_hash": phash,
            "total": total,
        }
        with (_config.audit_dir / "at-ris-mcp.jsonl").open("a") as fh:
            fh.write(json.dumps(line) + "\n")
    except Exception:
        # Auditing must never break a tool call.
        pass


def _err(exc: Exception) -> dict[str, Any]:
    if isinstance(exc, RisError):
        return {"error": exc.as_text(), "code": exc.code}
    return {"error": f"[upstream_error] {exc}", "code": "upstream_error"}


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------
@mcp.tool
async def ris_search_law(
    suchworte: str | None = None,
    titel: str | None = None,
    applikation: str = "BrKons",
    paragraph: str | None = None,
    artikel: str | None = None,
    anlage: str | None = None,
    fassung_vom: str | None = None,
    in_kraft_von: str | None = None,
    in_kraft_bis: str | None = None,
    geaendert_seit: str | None = None,
    gesetzesnummer: str | None = None,
    index: str | None = None,
    typ: str | None = None,
    kundmachungsorgan: str | None = None,
    kundmachungsorgannummer: str | None = None,
    page_size: str = "Twenty",
    page_number: int = 1,
) -> dict[str, Any]:
    """Search Austrian federal law (Bundesrecht).

    applikation: BrKons (consolidated law, default) | BgblAuth | BgblPdf |
    BgblAlt | Begut | RegV | Erv. Use paragraph/artikel/anlage="N" or "N-M"
    for section access (BrKons), fassung_vom=YYYY-MM-DD for a historical
    version snapshot. Each hit carries eli_uri, human_readable_citation,
    source_url and content_urls for ris_get_law_text.
    """
    try:
        req = LawSearchRequest(
            suchworte=suchworte, titel=titel, applikation=applikation,
            paragraph=paragraph, artikel=artikel, anlage=anlage,
            fassung_vom=fassung_vom, in_kraft_von=in_kraft_von,
            in_kraft_bis=in_kraft_bis, geaendert_seit=geaendert_seit,
            gesetzesnummer=gesetzesnummer, index=index, typ=typ,
            kundmachungsorgan=kundmachungsorgan,
            kundmachungsorgannummer=kundmachungsorgannummer,
            page_size=page_size, page_number=page_number,
        )
        async with RisClient(_config) as c:
            res = await c.search_law(req)
        _audit("ris_search_law", req.model_dump(), res.total)
        return res.model_dump()
    except Exception as exc:
        return _err(exc)


@mcp.tool
async def ris_get_law_text(
    content_url: str,
    format: str = "markdown",
    eli_uri: str | None = None,
    human_readable_citation: str | None = None,
) -> dict[str, Any]:
    """Fetch the full text of a statute/section from a hit's content_urls.

    format: markdown (default) | html | xml | raw (unaltered original).
    Pass eli_uri and human_readable_citation from the search hit so the text
    stays citable. content_url must be a .html or .xml URL on ris.bka.gv.at.
    """
    try:
        async with RisClient(_config) as c:
            res = await c.get_text(
                content_url, format,
                citation=human_readable_citation, eli_uri=eli_uri,
            )
        _audit("ris_get_law_text", {"content_url": content_url, "format": format}, None)
        return res.model_dump()
    except Exception as exc:
        return _err(exc)


@mcp.tool
async def ris_search_case(
    suchworte: str | None = None,
    gericht: str = "Justiz",
    norm: str | None = None,
    geschaeftszahl: str | None = None,
    entscheidung_von: str | None = None,
    entscheidung_bis: str | None = None,
    rechtssaetze: bool = True,
    entscheidungstexte: bool = True,
    geaendert_seit: str | None = None,
    page_size: str = "Twenty",
    page_number: int = 1,
) -> dict[str, Any]:
    """Search Austrian case law (Judikatur).

    gericht: Justiz (default, incl. OGH) | Vfgh | Vwgh | Bvwg | Lvwg | Dsk |
    Dok | Pvak | Gbk | Uvs | AsylGH | Ubas | Umse | Bks | Verg | Normenliste.
    norm filters by applied norm (e.g. "ABGB §879"). Keep both rechtssaetze and
    entscheidungstexte true to get full decisions, not just Rechtssätze. Each
    hit carries a native ecli and content_urls for ris_get_case_text.
    """
    try:
        req = CaseSearchRequest(
            suchworte=suchworte, gericht=gericht, norm=norm,
            geschaeftszahl=geschaeftszahl, entscheidung_von=entscheidung_von,
            entscheidung_bis=entscheidung_bis, rechtssaetze=rechtssaetze,
            entscheidungstexte=entscheidungstexte, geaendert_seit=geaendert_seit,
            page_size=page_size, page_number=page_number,
        )
        async with RisClient(_config) as c:
            res = await c.search_case(req)
        _audit("ris_search_case", req.model_dump(), res.total)
        return res.model_dump()
    except Exception as exc:
        return _err(exc)


@mcp.tool
async def ris_get_case_text(
    content_url: str,
    format: str = "markdown",
    ecli: str | None = None,
    human_readable_citation: str | None = None,
) -> dict[str, Any]:
    """Fetch the full text of a decision from a case hit's content_urls.

    format: markdown (default) | html | xml | raw. Pass ecli and
    human_readable_citation from the search hit so the text stays citable.
    content_url must be a .html or .xml URL on ris.bka.gv.at.
    """
    try:
        async with RisClient(_config) as c:
            res = await c.get_text(
                content_url, format,
                citation=human_readable_citation, ecli=ecli,
            )
        _audit("ris_get_case_text", {"content_url": content_url, "format": format}, None)
        return res.model_dump()
    except Exception as exc:
        return _err(exc)


@mcp.tool
async def ris_list_collections() -> dict[str, Any]:
    """Static overview of the RIS endpoints/applications covered by this
    server, plus the scope not yet covered (Landesrecht, History, ...)."""
    return _list_collections()


@mcp.tool
async def ris_list_changes(
    anwendung: str,
    von: str | None = None,
    bis: str | None = None,
    zeitraum: str | None = None,
    include_deleted: bool = False,
) -> dict[str, Any]:
    """Change/early-warning feed (RIS History). NOT YET IMPLEMENTED in v0.1.

    Planned for v0.2: the RIS History query requires the OGD POST endpoint
    (the GET History endpoint currently returns HTTP 500). Tracked in the
    roadmap. For change monitoring today, use ris_search_law /
    ris_search_case with geaendert_seit (ImRisSeit).
    """
    return _err(
        NotImplementedYetError(
            "ris_list_changes is scheduled for v0.2 (History via OGD POST). "
            "Use geaendert_seit on ris_search_law/ris_search_case meanwhile."
        )
    )


if __name__ == "__main__":
    mcp.run()
