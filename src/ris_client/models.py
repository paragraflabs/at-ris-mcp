"""Pydantic models: request parameters and flattened response records.

The request models mirror the official RIS XSD request schemas
(reference/xsd-request-schema/*.xsd). Enum values are taken verbatim from
OGD_Request_Types.xsd and must not be invented.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


# ---------------------------------------------------------------------------
# Enums (verbatim from the official XSD)
# ---------------------------------------------------------------------------
class PageSize(str, Enum):
    Ten = "Ten"
    Twenty = "Twenty"
    Fifty = "Fifty"
    OneHundred = "OneHundred"


class ChangeSetInterval(str, Enum):
    EinerWoche = "EinerWoche"
    ZweiWochen = "ZweiWochen"
    EinemMonat = "EinemMonat"
    DreiMonaten = "DreiMonaten"
    SechsMonaten = "SechsMonaten"
    EinemJahr = "EinemJahr"


class NormabschnittTyp(str, Enum):
    Alle = "Alle"
    Artikel = "Artikel"
    Paragraph = "Paragraph"
    Anlage = "Anlage"


class SortDirection(str, Enum):
    Ascending = "Ascending"
    Descending = "Descending"


class LawApplikation(str, Enum):
    """Bundesrecht sub-applications (OGD_Bundesrecht_Request.xsd)."""

    BrKons = "BrKons"       # konsolidiertes geltendes Recht (default)
    BgblAuth = "BgblAuth"   # Bundesgesetzblatt authentisch ab 2004
    BgblPdf = "BgblPdf"     # 1945-2003
    BgblAlt = "BgblAlt"     # 1848-1940
    Begut = "Begut"         # Begutachtungsentwürfe
    RegV = "RegV"           # Regierungsvorlagen
    Erv = "Erv"             # Rechtsvorschriften in englischer Sprache


class CourtApplikation(str, Enum):
    """Judikatur applications / courts (OGD_Judikatur_Request.xsd)."""

    Justiz = "Justiz"
    Vfgh = "Vfgh"
    Vwgh = "Vwgh"
    Bvwg = "Bvwg"
    Lvwg = "Lvwg"
    Dsk = "Dsk"
    Dok = "Dok"
    Pvak = "Pvak"
    Gbk = "Gbk"
    Uvs = "Uvs"
    AsylGH = "AsylGH"
    Ubas = "Ubas"
    Umse = "Umse"
    Bks = "Bks"
    Verg = "Verg"
    Normenliste = "Normenliste"


class TextFormat(str, Enum):
    markdown = "markdown"
    html = "html"
    xml = "xml"
    raw = "raw"  # unaltered original text (of whatever content_url points at)


class HistoryApplikation(str, Enum):
    """Applications valid for the History (Änderungen) query.

    Verbatim from OGD_History_Request.xsd (HistoryRequestApplicationType).
    NB: consolidated federal law is queried as ``Bundesnormen`` here (not
    ``BrKons``), and consolidated state law as ``Landesnormen``.
    """

    AsylGH = "AsylGH"
    Avn = "Avn"
    Avsv = "Avsv"
    Begut = "Begut"
    BgblAlt = "BgblAlt"
    BgblAuth = "BgblAuth"
    BgblPdf = "BgblPdf"
    Bks = "Bks"
    Bundesnormen = "Bundesnormen"
    Bvb = "Bvb"
    Bvwg = "Bvwg"
    Dok = "Dok"
    Dsk = "Dsk"
    Erlaesse = "Erlaesse"
    Erv = "Erv"
    Gbk = "Gbk"
    Gemeinderecht = "Gemeinderecht"
    GemeinderechtAuth = "GemeinderechtAuth"
    Justiz = "Justiz"
    KmGer = "KmGer"
    Lgbl = "Lgbl"
    LgblAuth = "LgblAuth"
    LgblNO = "LgblNO"
    Landesnormen = "Landesnormen"
    Lvwg = "Lvwg"
    Mrp = "Mrp"
    Normenliste = "Normenliste"
    PruefGewO = "PruefGewO"
    Pvak = "Pvak"
    RegV = "RegV"
    Spg = "Spg"
    Ubas = "Ubas"
    Umse = "Umse"
    Upts = "Upts"
    Uvs = "Uvs"
    Vbl = "Vbl"
    Verg = "Verg"
    Vfgh = "Vfgh"
    Vwgh = "Vwgh"


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------
class LawSearchRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    suchworte: str | None = None
    titel: str | None = None
    applikation: LawApplikation = LawApplikation.BrKons.value
    # Abschnitt (BrKons only)
    paragraph: str | None = None   # -> Abschnitt.Typ=Paragraph & Von/Bis
    artikel: str | None = None     # -> Abschnitt.Typ=Artikel & Von/Bis
    anlage: str | None = None      # -> Abschnitt.Typ=Anlage & Von/Bis
    # Fassung
    fassung_vom: str | None = None          # Stichtag  -> Fassung.FassungVom
    in_kraft_von: str | None = None         # -> Fassung.VonInkrafttretensdatum
    in_kraft_bis: str | None = None         # -> Fassung.BisInkrafttretensdatum
    geaendert_seit: ChangeSetInterval | None = None  # -> ImRisSeit
    gesetzesnummer: str | None = None
    index: str | None = None
    typ: str | None = None
    kundmachungsorgan: str | None = None
    kundmachungsorgannummer: str | None = None
    # Begut / RegV specific filters (OGD_Bundesrecht_Request.xsd).
    einbringende_stelle: str | None = None       # Begut, RegV, BgblAuth
    in_begutachtung_am: str | None = None        # Begut -> InBegutachtungAm (date)
    beschluss_von: str | None = None             # RegV -> BeschlussdatumVon (date)
    beschluss_bis: str | None = None             # RegV -> BeschlussdatumBis (date)
    sort_direction: SortDirection | None = None
    page_size: PageSize = PageSize.Twenty.value
    page_number: int = 1


class CaseSearchRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    suchworte: str | None = None
    gericht: CourtApplikation = CourtApplikation.Justiz.value
    norm: str | None = None
    geschaeftszahl: str | None = None
    entscheidung_von: str | None = None   # -> EntscheidungsdatumVon
    entscheidung_bis: str | None = None   # -> EntscheidungsdatumBis
    # Both default true, otherwise RIS returns only Rechtssätze (OGD-FAQ).
    rechtssaetze: bool = True
    entscheidungstexte: bool = True
    geaendert_seit: ChangeSetInterval | None = None  # -> ImRisSeit
    page_size: PageSize = PageSize.Twenty.value
    page_number: int = 1


class HistoryRequest(BaseModel):
    """Change/early-warning feed (RIS History), sent via the OGD SOAP POST."""

    model_config = ConfigDict(use_enum_values=True)

    anwendung: HistoryApplikation
    von: str | None = None                 # -> AenderungenVon (date)
    bis: str | None = None                 # -> AenderungenBis (date)
    include_deleted: bool = False
    page_size: PageSize = PageSize.Twenty.value
    page_number: int = 1


# ---------------------------------------------------------------------------
# Flattened response records
# ---------------------------------------------------------------------------
class LawRecord(BaseModel):
    id: str
    applikation: str | None = None
    kurztitel: str | None = None
    titel: str | None = None
    typ: str | None = None
    abschnitt: str | None = None          # e.g. "§ 17"
    kundmachungsorgan: str | None = None
    bgblnummer: str | None = None
    gesetzesnummer: str | None = None
    inkrafttreten: str | None = None
    ausserkrafttreten: str | None = None
    geaendert: str | None = None
    eli_uri: str | None = None
    human_readable_citation: str | None = None
    source_url: str | None = None
    content_urls: dict[str, str] = Field(default_factory=dict)


class CaseRecord(BaseModel):
    id: str
    applikation: str | None = None
    gericht: str | None = None
    dokumenttyp: str | None = None        # "Text" | "Rechtssatz"
    geschaeftszahl: str | None = None
    entscheidungsdatum: str | None = None
    entscheidungsart: str | None = None
    norm: str | None = None
    rechtsgebiet: str | None = None
    ecli: str | None = None
    human_readable_citation: str | None = None
    source_url: str | None = None
    content_urls: dict[str, str] = Field(default_factory=dict)


class SearchResult(BaseModel):
    total: int
    page_number: int
    page_size: int
    items: list[LawRecord] | list[CaseRecord]
    request_url: str
    attribution: str
    legal_notice: str


class ChangeRecord(BaseModel):
    """A single changed/new/deleted document from the History feed."""

    id: str
    applikation: str | None = None
    titel: str | None = None
    geaendert: str | None = None
    veroeffentlicht: str | None = None
    deleted: bool = False
    eli_uri: str | None = None
    source_url: str | None = None
    content_urls: dict[str, str] = Field(default_factory=dict)


class ChangesResult(BaseModel):
    total: int
    page_number: int
    page_size: int
    anwendung: str
    items: list[ChangeRecord]
    attribution: str
    legal_notice: str


class TextResult(BaseModel):
    content: str
    format: str
    source_url: str
    citation: str | None = None
    eli_uri: str | None = None
    ecli: str | None = None
    attribution: str
    legal_notice: str
