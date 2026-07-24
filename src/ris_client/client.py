"""The RIS HTTP client: URL building (dot notation), retry, rate limiting,
caching and full-text retrieval.

This is the standalone, MCP-independent library entry point. The dot-notation
URL construction is the crux (PLAN.md §6) and is exercised against the official
GET examples in tests/test_urlbuild.py.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from urllib.parse import urlencode, urlsplit
from xml.sax.saxutils import escape as _xml_escape

import httpx

from . import citations, mapping
from .cache import Cache
from .config import ALLOWED_TEXT_HOSTS, Config
from .errors import (
    InvalidArgError,
    NotFoundError,
    UnsupportedFormatError,
    UpstreamError,
)
from .models import (
    CaseSearchRequest,
    HistoryRequest,
    LawApplikation,
    LawSearchRequest,
    SearchResult,
    ChangesResult,
    TextFormat,
    TextResult,
)
from .ratelimit import RateLimiter
from .textparse import extract_law_citation, html_to_markdown, to_markdown, xml_to_text

_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def _build_law_params(req: LawSearchRequest) -> list[tuple[str, str]]:
    """Translate a LawSearchRequest into RIS dot-notation query parameters.

    Field->parameter mapping follows OGD_Bundesrecht_Request.xsd and the
    official GET examples (reference/examples_get_post.txt).
    """
    p: list[tuple[str, str]] = [("Applikation", req.applikation)]
    if req.suchworte:
        p.append(("Suchworte", req.suchworte))
    if req.titel:
        p.append(("Titel", req.titel))
    if req.index:
        p.append(("Index", req.index))
    if req.typ:
        p.append(("Typ", req.typ))

    # Abschnitt (Paragraph/Artikel/Anlage) - BrKons only per XSD.
    abschnitt_typ = None
    abschnitt_val = None
    if req.paragraph:
        abschnitt_typ, abschnitt_val = "Paragraph", req.paragraph
    elif req.artikel:
        abschnitt_typ, abschnitt_val = "Artikel", req.artikel
    elif req.anlage:
        abschnitt_typ, abschnitt_val = "Anlage", req.anlage
    if abschnitt_typ:
        von, _, bis = abschnitt_val.partition("-")
        p.append(("Abschnitt.Typ", abschnitt_typ))
        p.append(("Abschnitt.Von", von.strip()))
        p.append(("Abschnitt.Bis", (bis.strip() or von.strip())))

    # Fassung: Stichtag has priority over interval.
    if req.fassung_vom:
        p.append(("Fassung.FassungVom", req.fassung_vom))
    else:
        if req.in_kraft_von:
            p.append(("Fassung.VonInkrafttretensdatum", req.in_kraft_von))
        if req.in_kraft_bis:
            p.append(("Fassung.BisInkrafttretensdatum", req.in_kraft_bis))

    if req.geaendert_seit:
        p.append(("ImRisSeit", req.geaendert_seit))
    if req.gesetzesnummer:
        p.append(("Gesetzesnummer", req.gesetzesnummer))
    if req.kundmachungsorgan:
        p.append(("Kundmachungsorgan", req.kundmachungsorgan))
    if req.kundmachungsorgannummer:
        p.append(("Kundmachungsorgannummer", req.kundmachungsorgannummer))
    # Begut / RegV specific filters.
    if req.einbringende_stelle:
        p.append(("EinbringendeStelle", req.einbringende_stelle))
    if req.in_begutachtung_am:
        p.append(("InBegutachtungAm", req.in_begutachtung_am))
    if req.beschluss_von:
        p.append(("BeschlussdatumVon", req.beschluss_von))
    if req.beschluss_bis:
        p.append(("BeschlussdatumBis", req.beschluss_bis))
    if req.sort_direction:
        p.append(("Sortierung.SortDirection", req.sort_direction))

    p.append(("DokumenteProSeite", req.page_size))
    p.append(("Seitennummer", str(req.page_number)))
    return p


def _build_case_params(req: CaseSearchRequest) -> list[tuple[str, str]]:
    """Translate a CaseSearchRequest into RIS dot-notation query parameters.

    Follows OGD_Judikatur_Request.xsd. Both Dokumenttyp flags default true so
    RIS returns Entscheidungstexte as well as Rechtssätze (OGD-FAQ note).
    """
    p: list[tuple[str, str]] = [("Applikation", req.gericht)]
    if req.suchworte:
        p.append(("Suchworte", req.suchworte))
    # Dokumenttyp.SucheIn* - at least one must be true or RIS returns nothing.
    if req.rechtssaetze:
        p.append(("Dokumenttyp.SucheInRechtssaetzen", "true"))
    if req.entscheidungstexte:
        p.append(("Dokumenttyp.SucheInEntscheidungstexten", "true"))
    if req.geschaeftszahl:
        p.append(("Geschaeftszahl", req.geschaeftszahl))
    if req.norm:
        p.append(("Norm", req.norm))
    if req.entscheidung_von:
        p.append(("EntscheidungsdatumVon", req.entscheidung_von))
    if req.entscheidung_bis:
        p.append(("EntscheidungsdatumBis", req.entscheidung_bis))
    if req.geaendert_seit:
        p.append(("ImRisSeit", req.geaendert_seit))
    p.append(("DokumenteProSeite", req.page_size))
    p.append(("Seitennummer", str(req.page_number)))
    return p


_SOAP_ACTION = "http://ris.bka.gv.at/ogd/V2_6/SearchDocuments"


def build_history_soap(req: HistoryRequest) -> str:
    """Build the SOAP envelope for a History (Änderungen) query.

    The History query is only served by the OGD SOAP endpoint
    (``SearchDocuments`` operation, ``query > Aenderungen(OGDHistoryType)``);
    the REST GET API does not expose it. Structure per the service WSDL and
    OGD_History_Request.xsd.
    """
    lines = [
        '<tns:Anwendung>%s</tns:Anwendung>' % _xml_escape(req.anwendung),
    ]
    if req.von:
        lines.append('<tns:AenderungenVon>%s</tns:AenderungenVon>' % _xml_escape(req.von))
    if req.bis:
        lines.append('<tns:AenderungenBis>%s</tns:AenderungenBis>' % _xml_escape(req.bis))
    lines.append(
        '<tns:IncludeDeletedDocuments>%s</tns:IncludeDeletedDocuments>'
        % ("true" if req.include_deleted else "false")
    )
    lines.append('<tns:DokumenteProSeite>%s</tns:DokumenteProSeite>' % _xml_escape(req.page_size))
    lines.append('<tns:Seitennummer>%d</tns:Seitennummer>' % int(req.page_number))
    body = "".join(lines)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" '
        'xmlns:tns="http://ris.bka.gv.at/ogd/V2_6"><soap:Body>'
        '<tns:SearchDocuments><tns:query><tns:Aenderungen>'
        f"{body}"
        "</tns:Aenderungen></tns:query></tns:SearchDocuments>"
        "</soap:Body></soap:Envelope>"
    )


class RisClient:
    """Async RIS client. Use as an async context manager."""

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config.from_env()
        self._limiter = RateLimiter(self.config.rate_ms)
        self._cache = Cache(self.config.cache_path, self.config.cache_enabled)
        self._http = httpx.AsyncClient(
            timeout=self.config.timeout_s,
            headers={
                "User-Agent": self.config.user_agent,
                "Accept": "application/json, text/html, application/xml;q=0.9, */*;q=0.8",
            },
            follow_redirects=True,
        )

    async def __aenter__(self) -> "RisClient":
        return self

    async def __aexit__(self, *exc) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._http.aclose()
        self._cache.close()

    # -- low-level fetch with rate limit + retry ---------------------------
    async def _fetch(self, url: str, *, expect: str) -> str:
        await self._limiter.acquire()
        last_exc: Exception | None = None
        for attempt in range(self.config.max_retries):
            try:
                resp = await self._http.get(url)
            except httpx.HTTPError as exc:  # network/timeout/read error
                last_exc = UpstreamError(
                    f"network error contacting RIS ({type(exc).__name__}: {exc}) "
                    f"for {url}"
                )
            else:
                if resp.status_code == 404:
                    raise NotFoundError(f"RIS returned 404 for {url}")
                if resp.status_code in _RETRYABLE_STATUS:
                    last_exc = UpstreamError(
                        f"RIS returned HTTP {resp.status_code} for {url}"
                    )
                elif resp.status_code >= 400:
                    raise UpstreamError(
                        f"RIS returned HTTP {resp.status_code} for {url}"
                    )
                else:
                    return resp.text
            # exponential backoff before retry (on top of the rate limit)
            if attempt < self.config.max_retries - 1:
                await asyncio.sleep(min(2 ** attempt, 8))
                await self._limiter.acquire()
        assert last_exc is not None
        raise last_exc


    async def _get_json(self, endpoint: str, params: list[tuple[str, str]],
                        cache_ttl: int) -> tuple[dict, str]:
        query = urlencode(params)
        url = f"{self.config.base_url}/{endpoint}?{query}"
        cache_key = "json:" + hashlib.sha256(url.encode()).hexdigest()
        cached = self._cache.get(cache_key)
        if cached is not None:
            return json.loads(cached), url
        text = await self._fetch(url, expect="json")
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise UpstreamError(f"RIS returned non-JSON response: {exc}") from exc
        self._cache.set(cache_key, text, cache_ttl)
        return data, url

    async def _post_soap(self, body: str, cache_ttl: int) -> str:
        """POST a SOAP envelope to the OGD endpoint with rate limit + retry."""
        cache_key = "soap:" + hashlib.sha256(body.encode()).hexdigest()
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached
        await self._limiter.acquire()
        last_exc: Exception | None = None
        headers = {"Content-Type": "text/xml; charset=utf-8", "SOAPAction": f'"{_SOAP_ACTION}"'}
        for attempt in range(self.config.max_retries):
            try:
                resp = await self._http.post(
                    self.config.soap_url, content=body.encode("utf-8"), headers=headers
                )
            except httpx.HTTPError as exc:
                last_exc = UpstreamError(
                    f"network error contacting RIS SOAP ({type(exc).__name__}: {exc})"
                )
            else:
                text = resp.text
                # SOAP faults come back as HTTP 500 with a <soap:Fault> body.
                if "<soap:Fault>" in text or "<faultstring>" in text:
                    fault = text.split("<faultstring>")[-1].split("</faultstring>")[0]
                    raise UpstreamError(f"RIS SOAP fault: {fault[:300]}")
                if resp.status_code in _RETRYABLE_STATUS:
                    last_exc = UpstreamError(
                        f"RIS SOAP returned HTTP {resp.status_code}"
                    )
                elif resp.status_code >= 400:
                    raise UpstreamError(f"RIS SOAP returned HTTP {resp.status_code}")
                else:
                    self._cache.set(cache_key, text, cache_ttl)
                    return text
            if attempt < self.config.max_retries - 1:
                await asyncio.sleep(min(2 ** attempt, 8))
                await self._limiter.acquire()
        assert last_exc is not None
        raise last_exc

    # -- public: search law ------------------------------------------------
    async def search_law(self, req: LawSearchRequest) -> SearchResult:
        if not (req.suchworte or req.titel or req.gesetzesnummer
                or req.geaendert_seit or req.fassung_vom or req.index):
            raise InvalidArgError(
                "Provide at least one filter (suchworte, titel, gesetzesnummer, "
                "index, fassung_vom or geaendert_seit)."
            )
        params = _build_law_params(req)
        envelope, url = await self._get_json(
            "Bundesrecht", params, self.config.cache_ttl_search_s
        )
        results, refs = mapping.iter_references(envelope)
        total, page_number, page_size = mapping.parse_hits_total(results)
        items = []
        for ref in refs:
            rec = mapping.map_law_record(ref)
            rec.human_readable_citation = citations.law_citation(
                rec.kurztitel, rec.kundmachungsorgan, rec.abschnitt
            )
            items.append(rec)
        return SearchResult(
            total=total,
            page_number=page_number or req.page_number,
            page_size=page_size,
            items=items,
            request_url=url,
            attribution=citations.ATTRIBUTION,
            legal_notice=citations.LEGAL_NOTICE,
        )

    # -- public: search case ----------------------------------------------
    async def search_case(self, req: CaseSearchRequest) -> SearchResult:
        if not (req.suchworte or req.norm or req.geschaeftszahl
                or req.geaendert_seit or req.entscheidung_von):
            raise InvalidArgError(
                "Provide at least one filter (suchworte, norm, geschaeftszahl, "
                "entscheidung_von or geaendert_seit)."
            )
        if not (req.rechtssaetze or req.entscheidungstexte):
            raise InvalidArgError(
                "At least one of rechtssaetze / entscheidungstexte must be true."
            )
        params = _build_case_params(req)
        envelope, url = await self._get_json(
            "Judikatur", params, self.config.cache_ttl_search_s
        )
        results, refs = mapping.iter_references(envelope)
        total, page_number, page_size = mapping.parse_hits_total(results)
        items = []
        for ref in refs:
            rec = mapping.map_case_record(ref)
            rec.human_readable_citation = citations.case_citation(
                rec.gericht, rec.entscheidungsdatum, rec.geschaeftszahl
            )
            items.append(rec)
        return SearchResult(
            total=total,
            page_number=page_number or req.page_number,
            page_size=page_size,
            items=items,
            request_url=url,
            attribution=citations.ATTRIBUTION,
            legal_notice=citations.LEGAL_NOTICE,
        )

    # -- public: history / changes ----------------------------------------
    async def search_changes(self, req: HistoryRequest) -> ChangesResult:
        # Monitoring must stay fresh: use a short cache TTL (1 hour).
        soap_text = await self._post_soap(build_history_soap(req), cache_ttl=3600)
        envelope = mapping.soap_body_to_envelope(soap_text)
        results, refs = mapping.iter_references(envelope)
        total, page_number, page_size = mapping.parse_hits_total(results)
        items = [mapping.map_change_record(ref) for ref in refs]
        return ChangesResult(
            total=total,
            page_number=page_number or req.page_number,
            page_size=page_size,
            anwendung=req.anwendung,
            items=items,
            attribution=citations.ATTRIBUTION,
            legal_notice=citations.LEGAL_NOTICE,
        )

    # -- public: full text -------------------------------------------------
    def _validate_content_url(self, content_url: str) -> str:
        parts = urlsplit(content_url)
        if parts.scheme not in ("http", "https") or not parts.netloc:
            raise InvalidArgError(f"content_url is not a valid URL: {content_url}")
        if parts.netloc.lower() not in ALLOWED_TEXT_HOSTS:
            raise InvalidArgError(
                f"Full text may only be fetched from {ALLOWED_TEXT_HOSTS}; "
                f"got host '{parts.netloc}'."
            )
        lower = parts.path.lower()
        if not (lower.endswith(".html") or lower.endswith(".xml")):
            raise UnsupportedFormatError(
                "content_url must end in .html or .xml."
            )
        return content_url

    async def get_text(
        self,
        content_url: str,
        format: TextFormat | str = TextFormat.markdown,
        *,
        citation: str | None = None,
        eli_uri: str | None = None,
        ecli: str | None = None,
    ) -> TextResult:
        fmt = TextFormat(format) if not isinstance(format, TextFormat) else format
        url = self._validate_content_url(content_url)
        cache_key = "text:" + hashlib.sha256(url.encode()).hexdigest()
        raw = self._cache.get(cache_key)
        if raw is None:
            raw = await self._fetch(url, expect="text")
            self._cache.set(cache_key, raw, self.config.cache_ttl_text_s)

        if fmt in (TextFormat.raw, TextFormat.html, TextFormat.xml):
            content = raw
            out_format = "raw" if fmt is TextFormat.raw else fmt.value
        else:  # markdown
            content = to_markdown(raw, url)
            out_format = "markdown"

        # If the caller did not pass a citation, derive one from the HTML law
        # document (Kurztitel + § + Kundmachungsorgan) so the response stays
        # citable even when the search hit was not threaded through.
        if not citation and url.lower().endswith(".html"):
            citation = extract_law_citation(raw)

        return TextResult(
            content=content,
            format=out_format,
            source_url=url,
            citation=citation,
            eli_uri=eli_uri,
            ecli=ecli,
            attribution=citations.ATTRIBUTION,
            legal_notice=citations.LEGAL_NOTICE,
        )
