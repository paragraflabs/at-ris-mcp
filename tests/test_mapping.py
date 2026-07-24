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
