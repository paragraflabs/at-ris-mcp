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


class StateLawApplikation(str, Enum):
    """Landesrecht sub-applications (OGD_Landesrecht_Request.xsd)."""

    LrKons = "LrKons"       # konsolidiertes Landesrecht (default)
    LgblAuth = "LgblAuth"   # Landesgesetzblätter authentisch
    Lgbl = "Lgbl"           # Landesgesetzblätter (nicht authentisch)
    LgblNO = "LgblNO"       # Niederösterreich bis 2014
    Vbl = "Vbl"             # Verordnungsblätter der Länder


class MiscApplikation(str, Enum):
    """Sonstige applications (OGD_Sonstige_Request.xsd). v0.3 exposes the
    generic ones; app-specific narrow filters can be added later."""

    Erlaesse = "Erlaesse"   # Erlässe der Bundesministerien
    Avsv = "Avsv"           # Amtl. Verlautbarungen der Sozialversicherung
    Avn = "Avn"             # Amtliche Veterinärnachrichten
    Spg = "Spg"             # Strukturpläne Gesundheit
    KmGer = "KmGer"         # Kundmachungen der Gerichte
    Upts = "Upts"           # Unabh. Parteien-Transparenz-Senat
    Mrp = "Mrp"             # Ministerratsprotokolle
    PruefGewO = "PruefGewO" # Prüfungsordnungen GewO


class DistrictApplikation(str, Enum):
    """Bezirke applications (OGD_Bezirke_Request.xsd)."""

    Bvb = "Bvb"             # Kundmachungen der Bezirksverwaltungsbehörden


class MunicipalityApplikation(str, Enum):
    """Gemeinden applications (OGD_Gemeinden_Request.xsd)."""

    Gr = "Gr"               # Gemeinderecht
    GrA = "GrA"             # Gemeinderecht authentisch


class Bundesland(str, Enum):
    """The nine Austrian states, as used by the ``Bundesland`` scalar filter
    (Bezirke/Gemeinden) - values verbatim from OGD_Request_Types.xsd."""

    Burgenland = "Burgenland"
    Kaernten = "Kaernten"
    Niederoesterreich = "Niederoesterreich"
    Oberoesterreich = "Oberoesterreich"
    Salzburg = "Salzburg"
    Steiermark = "Steiermark"
    Tirol = "Tirol"
    Vorarlberg = "Vorarlberg"
    Wien = "Wien"


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


class StateLawSearchRequest(BaseModel):
    """Landesrecht search (endpoint /Landesrecht)."""

    model_config = ConfigDict(use_enum_values=True)

    suchworte: str | None = None
    titel: str | None = None
    applikation: StateLawApplikation = StateLawApplikation.LrKons.value
    # LrKons uses per-state boolean flags (Bundesland.SucheIn<Land>=true).
    bundeslaender: list[Bundesland] = Field(default_factory=list)
    paragraph: str | None = None
    artikel: str | None = None
    anlage: str | None = None
    fassung_vom: str | None = None
    in_kraft_von: str | None = None
    in_kraft_bis: str | None = None
    geaendert_seit: ChangeSetInterval | None = None
    gesetzesnummer: str | None = None
    index: str | None = None
    typ: str | None = None
    kundmachungsorgan: str | None = None
    page_size: PageSize = PageSize.Twenty.value
    page_number: int = 1


class MiscSearchRequest(BaseModel):
    """Sonstige search (endpoint /Sonstige): Erlässe, Avsv, ..."""

    model_config = ConfigDict(use_enum_values=True)

    suchworte: str | None = None
    titel: str | None = None
    applikation: MiscApplikation = MiscApplikation.Erlaesse.value
    # Common-ish filters (mainly Erlaesse).
    geschaeftszahl: str | None = None
    norm: str | None = None
    bundesministerium: str | None = None
    fassung_vom: str | None = None
    geaendert_seit: ChangeSetInterval | None = None
    page_size: PageSize = PageSize.Twenty.value
    page_number: int = 1


class DistrictSearchRequest(BaseModel):
    """Bezirke search (endpoint /Bezirke): BVB-Kundmachungen."""

    model_config = ConfigDict(use_enum_values=True)

    suchworte: str | None = None
    titel: str | None = None
    applikation: DistrictApplikation = DistrictApplikation.Bvb.value
    bundesland: Bundesland | None = None
    bezirksverwaltungsbehoerde: str | None = None
    kundmachungsnummer: str | None = None
    kundmachung_von: str | None = None      # -> Kundmachungsdatum.Von
    kundmachung_bis: str | None = None      # -> Kundmachungsdatum.Bis
    geaendert_seit: ChangeSetInterval | None = None
    page_size: PageSize = PageSize.Twenty.value
    page_number: int = 1


class MunicipalitySearchRequest(BaseModel):
    """Gemeinden search (endpoint /Gemeinden): Gemeinderecht."""

    model_config = ConfigDict(use_enum_values=True)

    suchworte: str | None = None
    titel: str | None = None
    applikation: MunicipalityApplikation = MunicipalityApplikation.Gr.value
    bundesland: Bundesland | None = None
    gemeinde: str | None = None
    geschaeftszahl: str | None = None
    fassung_vom: str | None = None          # Gr -> FassungVom
    kundmachung_von: str | None = None      # GrA -> Kundmachungsdatum.Von
    kundmachung_bis: str | None = None      # GrA -> Kundmachungsdatum.Bis
    geaendert_seit: ChangeSetInterval | None = None
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
    bundesland: str | None = None         # Landesrecht/Bezirke/Gemeinden
    gemeinde: str | None = None           # Gemeinden
    geschaeftszahl: str | None = None     # Gemeinden/Erlaesse
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
