"""Offline: RIS JSON envelope -> flat records, using saved live fixtures."""

import json
from pathlib import Path

import pytest

from ris_client import citations, mapping

FIX = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def brkons_envelope():
    return json.loads((FIX / "brkons_search.json").read_text(encoding="utf-8"))


@pytest.fixture
def justiz_envelope():
    return json.loads((FIX / "justiz_search.json").read_text(encoding="utf-8"))


def test_parse_hits_total(brkons_envelope):
    results, refs = mapping.iter_references(brkons_envelope)
    total, page_number, page_size = mapping.parse_hits_total(results)
    assert total > 0
    assert page_number == 1
    assert page_size == 10
    assert len(refs) > 0


def test_map_law_record_fields(brkons_envelope):
    _, refs = mapping.iter_references(brkons_envelope)
    rec = mapping.map_law_record(refs[0])
    assert rec.id.startswith("NOR")
    assert rec.applikation == "BrKons"
    assert rec.kurztitel == "Abschlussprüfer-Aufsichtsgesetz"
    assert rec.abschnitt == "§ 17"
    assert rec.typ == "BG"
    assert rec.eli_uri and "eli/bgbl" in rec.eli_uri
    assert rec.content_urls.get("html", "").endswith(".html")
    assert rec.content_urls.get("xml", "").endswith(".xml")


def test_law_citation_built(brkons_envelope):
    _, refs = mapping.iter_references(brkons_envelope)
    rec = mapping.map_law_record(refs[0])
    cit = citations.law_citation(rec.kurztitel, rec.kundmachungsorgan, rec.abschnitt)
    assert "Abschlussprüfer-Aufsichtsgesetz" in cit
    assert "§ 17" in cit


def test_map_case_record_fields(justiz_envelope):
    _, refs = mapping.iter_references(justiz_envelope)
    rec = mapping.map_case_record(refs[0])
    assert rec.id.startswith(("JJT", "JJR"))
    assert rec.applikation == "Justiz"
    assert rec.gericht
    assert rec.geschaeftszahl
    assert rec.ecli and rec.ecli.startswith("ECLI:AT:")
    assert rec.content_urls.get("html", "").endswith(".html")


def test_case_citation_built(justiz_envelope):
    _, refs = mapping.iter_references(justiz_envelope)
    rec = mapping.map_case_record(refs[0])
    cit = citations.case_citation(rec.gericht, rec.entscheidungsdatum, rec.geschaeftszahl)
    assert rec.geschaeftszahl in cit


def test_single_reference_normalised_to_list():
    # OgdDocumentReference may be a single dict, not a list.
    envelope = {
        "OgdSearchResult": {
            "OgdDocumentResults": {
                "Hits": {"@pageNumber": "1", "@pageSize": "10", "#text": "1"},
                "OgdDocumentReference": {
                    "Data": {
                        "Metadaten": {
                            "Technisch": {"ID": "NOR1", "Applikation": "BrKons"},
                            "Allgemein": {},
                            "Bundesrecht": {"Kurztitel": "X", "BrKons": {"Typ": "BG"}},
                        },
                        "Dokumentliste": {},
                    }
                },
            }
        }
    }
    results, refs = mapping.iter_references(envelope)
    assert len(refs) == 1
    assert mapping.map_law_record(refs[0]).id == "NOR1"


@pytest.fixture
def begut_envelope():
    return json.loads((FIX / "begut_search.json").read_text(encoding="utf-8"))


@pytest.fixture
def regv_envelope():
    return json.loads((FIX / "regv_search.json").read_text(encoding="utf-8"))


def test_map_begut_record(begut_envelope):
    _, refs = mapping.iter_references(begut_envelope)
    rec = mapping.map_law_record(refs[0])
    assert rec.id.startswith("BEGUT")
    assert rec.applikation == "Begut"
    assert rec.kurztitel
    assert rec.content_urls.get("html", "").endswith(".html")


def test_map_regv_record(regv_envelope):
    _, refs = mapping.iter_references(regv_envelope)
    rec = mapping.map_law_record(refs[0])
    assert rec.id.startswith("REGV")
    assert rec.applikation == "RegV"
    assert rec.kurztitel


def test_soap_history_envelope_and_records():
    xml = (FIX / "history_bundesnormen_soap.xml").read_text(encoding="utf-8")
    env = mapping.soap_body_to_envelope(xml)
    results, refs = mapping.iter_references(env)
    total, page_number, page_size = mapping.parse_hits_total(results)
    assert total > 0
    assert page_number == 1
    assert page_size == 10
    assert len(refs) == 10
    rec = mapping.map_change_record(refs[0])
    assert rec.id.startswith("NOR")
    assert rec.applikation == "BrKons"
    assert rec.geaendert
    # this window has retrievable docs -> not flagged deleted
    assert rec.deleted is False
    assert rec.content_urls.get("html", "").endswith(".html")


def test_change_record_deleted_when_no_content():
    ref = {
        "Data": {
            "Metadaten": {
                "Technisch": {"ID": "NORDEL", "Applikation": "Bundesnormen"},
                "Allgemein": {"Geaendert": "2026-07-20"},
                "Bundesrecht": {"Kurztitel": "Weg"},
            },
            "Dokumentliste": {},
        }
    }
    rec = mapping.map_change_record(ref)
    assert rec.deleted is True
    assert rec.content_urls == {}


def test_soap_fault_yields_empty_envelope():
    fault = (
        '<?xml version="1.0"?><soap:Envelope '
        'xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body>'
        "<soap:Fault><faultstring>boom</faultstring></soap:Fault>"
        "</soap:Body></soap:Envelope>"
    )
    env = mapping.soap_body_to_envelope(fault)
    results, refs = mapping.iter_references(env)
    assert refs == []


# --- v0.3: generic law mapping across endpoints ---------------------------
@pytest.mark.parametrize("fixture,applikation,id_prefix", [
    ("lrkons_search.json", "LrKons", "LNO"),
    ("erlaesse_search.json", "Erlaesse", "ERL"),
    ("bvb_search.json", "Bvb", "BVB"),
    ("gr_search.json", "Gr", "GEMRE"),
])
def test_map_law_record_across_endpoints(fixture, applikation, id_prefix):
    env = json.loads((FIX / fixture).read_text(encoding="utf-8"))
    _, refs = mapping.iter_references(env)
    rec = mapping.map_law_record(refs[0])
    assert rec.applikation == applikation
    assert rec.id.startswith(id_prefix)
    assert rec.kurztitel or rec.titel
    assert rec.source_url


def test_map_lrkons_has_bundesland_and_abschnitt():
    env = json.loads((FIX / "lrkons_search.json").read_text(encoding="utf-8"))
    _, refs = mapping.iter_references(env)
    rec = mapping.map_law_record(refs[0])
    assert rec.bundesland  # e.g. "Niederösterreich"
    assert rec.abschnitt and rec.abschnitt.startswith("§")


def test_map_gemeinde_has_gemeinde_and_geschaeftszahl():
    env = json.loads((FIX / "gr_search.json").read_text(encoding="utf-8"))
    _, refs = mapping.iter_references(env)
    rec = mapping.map_law_record(refs[0])
    assert rec.bundesland
    assert rec.gemeinde
    assert rec.geschaeftszahl


def test_map_erv_record():
    env = json.loads((FIX / "erv_search.json").read_text(encoding="utf-8"))
    _, refs = mapping.iter_references(env)
    rec = mapping.map_law_record(refs[0])
    assert rec.applikation == "Erv"
    assert rec.id.startswith("ERV")
    assert rec.titel  # e.g. "Administrative Penal Act 1991 – VStG"
    assert rec.source_url
