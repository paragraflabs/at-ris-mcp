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

from .models import LawRecord, CaseRecord, ChangeRecord


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


_LAW_CATEGORIES = ("Bundesrecht", "Landesrecht", "Sonstige", "Bezirke", "Gemeinden")


def map_law_record(reference: dict[str, Any]) -> LawRecord:
    """Flatten a law-like reference into a LawRecord.

    Works across all law endpoints; the metadata category differs per endpoint
    (Bundesrecht, Landesrecht, Sonstige, Bezirke, Gemeinden) but the inner
    structure (Kurztitel + one nested application sub-block) is analogous.
    """
    data = reference.get("Data", {})
    meta = data.get("Metadaten", {})
    tech = meta.get("Technisch", {})
    allg = meta.get("Allgemein", {})

    # Locate the category block (e.g. Metadaten.Landesrecht).
    cat: dict[str, Any] = {}
    for name in _LAW_CATEGORIES:
        if isinstance(meta.get(name), dict):
            cat = meta[name]
            break

    # The nested application sub-block (BrKons/LrKons/Erlaesse/Bvb/Gr/...) holds
    # the detail fields. Skip scalar/known-container keys.
    _skip = ("Kurztitel", "Titel", "Eli", "Bundesland", "Gemeinde",
             "Geschaeftszahl", "Typ")
    sub: dict[str, Any] = {}
    for key, val in cat.items():
        if isinstance(val, dict) and key not in _skip:
            sub = val
            break

    doc_id = _text(tech.get("ID")) or ""
    kundm = _text(sub.get("Kundmachungsorgan")) or _text(cat.get("Kundmachungsorgan"))
    return LawRecord(
        id=doc_id,
        applikation=_text(tech.get("Applikation")),
        kurztitel=_text(cat.get("Kurztitel")),
        titel=_text(cat.get("Titel")) or _text(cat.get("Kurztitel")),
        typ=_text(sub.get("Typ")) or _text(cat.get("Typ")),
        abschnitt=_text(sub.get("ArtikelParagraphAnlage")),
        bundesland=_text(cat.get("Bundesland")),
        gemeinde=_text(cat.get("Gemeinde")),
        geschaeftszahl=_text(cat.get("Geschaeftszahl")),
        kundmachungsorgan=kundm,
        bgblnummer=_text(sub.get("StammnormBgblnummer")),
        gesetzesnummer=_text(sub.get("Gesetzesnummer")),
        inkrafttreten=_text(sub.get("Inkrafttretensdatum")),
        ausserkrafttreten=_text(sub.get("Ausserkrafttretensdatum")),
        geaendert=_text(allg.get("Geaendert")),
        eli_uri=_text(cat.get("Eli")) or _text(allg.get("DokumentUrl")),
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


# ---------------------------------------------------------------------------
# History (Änderungen) - SOAP response parsing + flat records
# ---------------------------------------------------------------------------
def soap_body_to_envelope(xml_text: str) -> dict[str, Any]:
    """Parse the SOAP XML response of a History query into the same dict shape
    as the JSON search envelope (so the shared helpers can be reused).

    Uses lxml (already a dependency) via BeautifulSoup's ``xml`` parser to avoid
    adding xmltodict. Namespaces are stripped; repeated siblings become lists.
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(xml_text, "xml")
    result = soup.find("OgdDocumentResults")
    if result is None:
        # Surface SOAP faults as an empty, well-formed envelope.
        return {"OgdSearchResult": {"OgdDocumentResults": {}}}

    def node_to_dict(node) -> Any:
        children = [c for c in node.find_all(recursive=False)]
        if not children:
            text = node.get_text(strip=True)
            out: dict[str, Any] = {}
            for k, v in node.attrs.items():
                out[f"@{k}"] = v
            if out:
                if text:
                    out["#text"] = text
                return out
            return text
        d: dict[str, Any] = {}
        for k, v in node.attrs.items():
            d[f"@{k}"] = v
        for child in children:
            key = child.name
            val = node_to_dict(child)
            if key in d:
                if not isinstance(d[key], list):
                    d[key] = [d[key]]
                d[key].append(val)
            else:
                d[key] = val
        return d

    return {"OgdSearchResult": {"OgdDocumentResults": node_to_dict(result)}}


def map_change_record(reference: dict[str, Any]) -> ChangeRecord:
    data = reference.get("Data", {})
    meta = data.get("Metadaten", {})
    tech = meta.get("Technisch", {})
    allg = meta.get("Allgemein", {})
    jud = meta.get("Judikatur", {})
    # Any law-like category (Bundesrecht/Landesrecht/Sonstige/...).
    cat: dict[str, Any] = {}
    for name in _LAW_CATEGORIES:
        if isinstance(meta.get(name), dict):
            cat = meta[name]
            break

    titel = (
        _text(cat.get("Kurztitel"))
        or _text(cat.get("Titel"))
        or _text(jud.get("Geschaeftszahl"))
    )
    urls = _content_urls(data)
    return ChangeRecord(
        id=_text(tech.get("ID")) or "",
        applikation=_text(tech.get("Applikation")),
        titel=titel,
        geaendert=_text(allg.get("Geaendert")),
        veroeffentlicht=_text(allg.get("Veroeffentlicht")),
        # Heuristic: the History XSD only offers IncludeDeletedDocuments as a
        # request flag and exposes no explicit deletion marker; a reference
        # without any retrievable document is treated as deleted.
        deleted=not urls,
        eli_uri=_text(cat.get("Eli")) or _text(allg.get("DokumentUrl")),
        source_url=_text(allg.get("DokumentUrl")),
        content_urls=urls,
    )
