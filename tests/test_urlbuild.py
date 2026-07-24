"""Offline: verify args -> correct RIS dot-notation query parameters.

Fixtures are derived from the official GET examples in
reference/examples_get_post.txt (the authoritative parameter source).
"""

from urllib.parse import parse_qs, urlencode

from ris_client.client import (
    _build_case_params,
    _build_district_params,
    _build_law_params,
    _build_misc_params,
    _build_municipality_params,
    _build_state_law_params,
    build_history_soap,
)
from ris_client.models import (
    CaseSearchRequest,
    DistrictSearchRequest,
    HistoryRequest,
    LawSearchRequest,
    MiscSearchRequest,
    MunicipalitySearchRequest,
    StateLawSearchRequest,
)


def _qs(params):
    return parse_qs(urlencode(params), keep_blank_values=True)


def test_brkons_basic_applikation_and_paging():
    p = _build_law_params(LawSearchRequest(suchworte="Datenschutz"))
    d = dict(p)
    assert d["Applikation"] == "BrKons"
    assert d["Suchworte"] == "Datenschutz"
    assert d["DokumenteProSeite"] == "Twenty"
    assert d["Seitennummer"] == "1"


def test_brkons_fassung_vom_dot_notation():
    # Mirrors official example: Applikation=BrKons&Fassung.FassungVom=2021-10-18
    p = _build_law_params(
        LawSearchRequest(suchworte="x", fassung_vom="2021-10-18")
    )
    d = dict(p)
    assert d["Fassung.FassungVom"] == "2021-10-18"


def test_brkons_abschnitt_paragraph_range():
    # Official: Abschnitt.Typ=Anlage&Abschnitt.Von=1&Abschnitt.Bis=5
    p = _build_law_params(LawSearchRequest(titel="x", anlage="1-5"))
    d = dict(p)
    assert d["Abschnitt.Typ"] == "Anlage"
    assert d["Abschnitt.Von"] == "1"
    assert d["Abschnitt.Bis"] == "5"


def test_brkons_paragraph_single_value_fills_bis():
    p = _build_law_params(LawSearchRequest(titel="x", paragraph="17"))
    d = dict(p)
    assert d["Abschnitt.Typ"] == "Paragraph"
    assert d["Abschnitt.Von"] == "17"
    assert d["Abschnitt.Bis"] == "17"


def test_brkons_inkrafttretens_interval():
    p = _build_law_params(
        LawSearchRequest(titel="x", in_kraft_von="1976-01-01",
                         in_kraft_bis="2000-01-01")
    )
    d = dict(p)
    assert d["Fassung.VonInkrafttretensdatum"] == "1976-01-01"
    assert d["Fassung.BisInkrafttretensdatum"] == "2000-01-01"


def test_brkons_fassung_vom_wins_over_interval():
    p = _build_law_params(
        LawSearchRequest(titel="x", fassung_vom="2021-10-18",
                         in_kraft_von="1976-01-01")
    )
    d = dict(p)
    assert d["Fassung.FassungVom"] == "2021-10-18"
    assert "Fassung.VonInkrafttretensdatum" not in d


def test_law_imrisseit_enum():
    p = _build_law_params(
        LawSearchRequest(suchworte="x", geaendert_seit="EinerWoche")
    )
    assert dict(p)["ImRisSeit"] == "EinerWoche"


def test_case_both_dokumenttyp_flags_default_true():
    # OGD-FAQ: both flags must be true to get Entscheidungstexte too.
    p = _build_case_params(CaseSearchRequest(suchworte="agrar"))
    d = dict(p)
    assert d["Applikation"] == "Justiz"
    assert d["Dokumenttyp.SucheInRechtssaetzen"] == "true"
    assert d["Dokumenttyp.SucheInEntscheidungstexten"] == "true"


def test_case_norm_and_gericht():
    # Mirrors official Vwgh example with Norm and date range.
    p = _build_case_params(
        CaseSearchRequest(
            gericht="Vwgh", norm="VwGG §55",
            entscheidung_von="2020-06-01", entscheidung_bis="2020-06-30",
        )
    )
    d = dict(p)
    assert d["Applikation"] == "Vwgh"
    assert d["Norm"] == "VwGG §55"
    assert d["EntscheidungsdatumVon"] == "2020-06-01"
    assert d["EntscheidungsdatumBis"] == "2020-06-30"


def test_case_geschaeftszahl_only():
    p = _build_case_params(
        CaseSearchRequest(gericht="Vwgh", geschaeftszahl="Ra 2023/02/0138",
                          rechtssaetze=False)
    )
    d = dict(p)
    assert d["Geschaeftszahl"] == "Ra 2023/02/0138"
    assert "Dokumenttyp.SucheInRechtssaetzen" not in d
    assert d["Dokumenttyp.SucheInEntscheidungstexten"] == "true"


def test_begut_specific_params():
    p = _build_law_params(
        LawSearchRequest(
            titel="Abfertigung", applikation="Begut",
            einbringende_stelle="BMA", in_begutachtung_am="2021-05-05",
        )
    )
    d = dict(p)
    assert d["Applikation"] == "Begut"
    assert d["EinbringendeStelle"] == "BMA"
    assert d["InBegutachtungAm"] == "2021-05-05"


def test_regv_beschlussdatum_params():
    p = _build_law_params(
        LawSearchRequest(
            suchworte="Pilz", applikation="RegV",
            beschluss_von="2005-01-01", beschluss_bis="2006-01-01",
        )
    )
    d = dict(p)
    assert d["Applikation"] == "RegV"
    assert d["BeschlussdatumVon"] == "2005-01-01"
    assert d["BeschlussdatumBis"] == "2006-01-01"


def test_history_soap_envelope_structure():
    soap = build_history_soap(
        HistoryRequest(
            anwendung="Bundesnormen", von="2026-07-10", bis="2026-07-22",
            include_deleted=True, page_size="Ten", page_number=1,
        )
    )
    assert "SearchDocuments" in soap
    assert "<tns:Aenderungen>" in soap
    assert "<tns:Anwendung>Bundesnormen</tns:Anwendung>" in soap
    assert "<tns:AenderungenVon>2026-07-10</tns:AenderungenVon>" in soap
    assert "<tns:AenderungenBis>2026-07-22</tns:AenderungenBis>" in soap
    assert "<tns:IncludeDeletedDocuments>true</tns:IncludeDeletedDocuments>" in soap
    assert "<tns:DokumenteProSeite>Ten</tns:DokumenteProSeite>" in soap


def test_history_soap_defaults_false_deleted():
    soap = build_history_soap(HistoryRequest(anwendung="Justiz"))
    assert "<tns:IncludeDeletedDocuments>false</tns:IncludeDeletedDocuments>" in soap
    # optional date elements omitted when not given
    assert "AenderungenVon" not in soap


def test_history_invalid_application_rejected():
    import pytest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        HistoryRequest(anwendung="NichtVorhanden")


# --- v0.3: Landesrecht / Sonstige / Bezirke / Gemeinden -------------------
def test_state_law_bundesland_flags_dotted():
    # LrKons requires the dotted Bundesland.SucheIn<Land> form (verified live:
    # the flat form is silently ignored by the API).
    p = _build_state_law_params(
        StateLawSearchRequest(suchworte="Abfall",
                              bundeslaender=["Kaernten", "Tirol"])
    )
    d = dict(p)
    assert d["Applikation"] == "LrKons"
    assert d["Bundesland.SucheInKaernten"] == "true"
    assert d["Bundesland.SucheInTirol"] == "true"
    assert "SucheInKaernten" not in d  # not the flat form


def test_state_law_abschnitt_and_fassung():
    p = _build_state_law_params(
        StateLawSearchRequest(titel="K-AWO", paragraph="38-40",
                              fassung_vom="2004-04-01")
    )
    d = dict(p)
    assert d["Abschnitt.Typ"] == "Paragraph"
    assert d["Abschnitt.Von"] == "38"
    assert d["Abschnitt.Bis"] == "40"
    assert d["Fassung.FassungVom"] == "2004-04-01"


def test_misc_erlaesse_params():
    p = _build_misc_params(
        MiscSearchRequest(suchworte="Delikten", applikation="Erlaesse",
                          bundesministerium="Bundesministerium für Justiz",
                          norm="StPO §172", fassung_vom="2021-11-12")
    )
    d = dict(p)
    assert d["Applikation"] == "Erlaesse"
    assert d["Bundesministerium"] == "Bundesministerium für Justiz"
    assert d["Norm"] == "StPO §172"
    assert d["FassungVom"] == "2021-11-12"


def test_district_bvb_params():
    p = _build_district_params(
        DistrictSearchRequest(suchworte="Hochinzidenz", bundesland="Niederoesterreich",
                             kundmachungsnummer="1/2021",
                             kundmachung_von="2021-11-01", kundmachung_bis="2021-11-05")
    )
    d = dict(p)
    assert d["Applikation"] == "Bvb"
    assert d["Bundesland"] == "Niederoesterreich"
    assert d["Kundmachungsnummer"] == "1/2021"
    assert d["Kundmachungsdatum.Von"] == "2021-11-01"
    assert d["Kundmachungsdatum.Bis"] == "2021-11-05"


def test_municipality_gr_params():
    p = _build_municipality_params(
        MunicipalitySearchRequest(suchworte="plan", applikation="Gr",
                                 bundesland="Kaernten", gemeinde="Afritz am See",
                                 fassung_vom="2021-11-05")
    )
    d = dict(p)
    assert d["Applikation"] == "Gr"
    assert d["Bundesland"] == "Kaernten"
    assert d["Gemeinde"] == "Afritz am See"
    assert d["FassungVom"] == "2021-11-05"


def test_municipality_gra_kundmachung():
    p = _build_municipality_params(
        MunicipalitySearchRequest(suchworte="Widmung", applikation="GrA",
                                 kundmachung_von="2023-11-01", kundmachung_bis="2023-11-07")
    )
    d = dict(p)
    assert d["Applikation"] == "GrA"
    assert d["Kundmachungsdatum.Von"] == "2023-11-01"
