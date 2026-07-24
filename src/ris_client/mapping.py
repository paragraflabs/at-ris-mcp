"""Flatten the deeply nested RIS JSON envelope into flat records.

The envelope shape (verified against live responses, see fixtures/):

    OgdSearchResult
      OgdDocumentResults
        Hits { @pageNumber, @pageSize, #text }   # #text = total
        OgdDocumentReference : [ { Data: { Metadaten, Dokumentliste } }, ... ]

``OgdDocumentReference`` may be a single object (one hit) or a list; both are
normalised here.
"""

from __future__ import annotations

from typing import Any

from .models import LawRecord, CaseRecord


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _text(value: Any) -> str | None:
    """Extract a plain string from a RIS field that may be a scalar,
    a {'#text': ...} node, or an {'item': ...} container."""
    if value is None:
        return None
    if isinstance(value, str):
        return value or None
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, dict):
        if "#text" in value:
            return _text(value["#text"])
        if "item" in value:
            items = _as_list(value["item"])
            joined = "; ".join(t for t in (_text(i) for i in items) if t)
            return joined or None
    if isinstance(value, list):
        joined = "; ".join(t for t in (_text(i) for i in value) if t)
        return joined or None
    return None


def parse_hits_total(results: dict[str, Any]) -> tuple[int, int, int]:
    """Return (total, page_number, page_size) from the Hits node."""
    hits = results.get("Hits", {}) if isinstance(results, dict) else {}
    total = int(_text(hits) or hits.get("#text", 0) or 0) if isinstance(hits, dict) else 0
    page_number = int(hits.get("@pageNumber", 1)) if isinstance(hits, dict) else 1
    page_size = int(hits.get("@pageSize", 0)) if isinstance(hits, dict) else 0
    return total, page_number, page_size


def _content_urls(data: dict[str, Any]) -> dict[str, str]:
    urls: dict[str, str] = {}
    dl = data.get("Dokumentliste", {})
    refs = _as_list(dl.get("ContentReference"))
    for ref in refs:
        if not isinstance(ref, dict):
            continue
        # Only the main document is interesting for full-text retrieval.
        if ref.get("ContentType") not in (None, "MainDocument"):
            continue
        for cu in _as_list(ref.get("Urls", {}).get("ContentUrl")):
            if not isinstance(cu, dict):
                continue
            dtype = (cu.get("DataType") or "").lower()
            url = cu.get("Url")
            if dtype and url and dtype not in urls:
                urls[dtype] = url
    return urls


def iter_references(envelope: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    results = (
        envelope.get("OgdSearchResult", {}).get("OgdDocumentResults", {})
        if isinstance(envelope, dict)
        else {}
    )
    refs = _as_list(results.get("OgdDocumentReference"))
    return results, [r for r in refs if isinstance(r, dict)]


def map_law_record(reference: dict[str, Any]) -> LawRecord:
    data = reference.get("Data", {})
    meta = data.get("Metadaten", {})
    tech = meta.get("Technisch", {})
    allg = meta.get("Allgemein", {})
    br = meta.get("Bundesrecht", {})
    # The sub-application block (BrKons/BgblAuth/...) holds the detail fields.
    sub: dict[str, Any] = {}
    for key, val in br.items():
        if isinstance(val, dict) and key not in ("Kurztitel", "Eli"):
            sub = val
            break

    doc_id = _text(tech.get("ID")) or ""
    kundm = _text(sub.get("Kundmachungsorgan"))
    return LawRecord(
        id=doc_id,
        applikation=_text(tech.get("Applikation")),
        kurztitel=_text(br.get("Kurztitel")),
        titel=_text(br.get("Kurztitel")),
        typ=_text(sub.get("Typ")),
        abschnitt=_text(sub.get("ArtikelParagraphAnlage")),
        kundmachungsorgan=kundm,
        bgblnummer=_text(sub.get("StammnormBgblnummer")),
        gesetzesnummer=_text(sub.get("Gesetzesnummer")),
        inkrafttreten=_text(sub.get("Inkrafttretensdatum")),
        ausserkrafttreten=_text(sub.get("Ausserkrafttretensdatum")),
        geaendert=_text(allg.get("Geaendert")),
        eli_uri=_text(br.get("Eli")) or _text(allg.get("DokumentUrl")),
        source_url=_text(allg.get("DokumentUrl")),
        content_urls=_content_urls(data),
    )


def map_case_record(reference: dict[str, Any]) -> CaseRecord:
    data = reference.get("Data", {})
    meta = data.get("Metadaten", {})
    tech = meta.get("Technisch", {})
    allg = meta.get("Allgemein", {})
    jud = meta.get("Judikatur", {})
    # Court-specific detail block (Justiz/Vfgh/...).
    court: dict[str, Any] = {}
    for key, val in jud.items():
        if isinstance(val, dict) and key not in ("Geschaeftszahl",):
            court = val
            break

    doc_id = _text(tech.get("ID")) or ""
    return CaseRecord(
        id=doc_id,
        applikation=_text(tech.get("Applikation")),
        gericht=_text(court.get("Gericht")) or _text(tech.get("Organ")),
        dokumenttyp=_text(jud.get("Dokumenttyp")),
        geschaeftszahl=_text(jud.get("Geschaeftszahl")),
        entscheidungsdatum=_text(jud.get("Entscheidungsdatum")),
        entscheidungsart=_text(court.get("Entscheidungsart")),
        norm=_text(jud.get("Norm")),
        rechtsgebiet=_text(court.get("Rechtsgebiete")),
        ecli=_text(jud.get("EuropeanCaseLawIdentifier")),
        source_url=_text(allg.get("DokumentUrl")),
        content_urls=_content_urls(data),
    )
