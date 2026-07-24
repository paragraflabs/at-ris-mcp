"""Live smoke tests against the real RIS API. Skipped unless RIS_SMOKE=1.

Run with:  RIS_SMOKE=1 pytest -m smoke tests/test_smoke.py
"""

import os

import pytest

from ris_client import (
    CaseSearchRequest,
    LawSearchRequest,
    RisClient,
    TextFormat,
)

pytestmark = pytest.mark.smoke

_skip = pytest.mark.skipif(
    os.environ.get("RIS_SMOKE") != "1",
    reason="live smoke test; set RIS_SMOKE=1 to run",
)


@_skip
async def test_live_search_law_brkons():
    async with RisClient() as c:
        res = await c.search_law(
            LawSearchRequest(suchworte="Datenschutzgesetz", page_size="Ten")
        )
    assert res.total > 0
    assert res.items
    first = res.items[0]
    assert first.content_urls.get("html")
    assert first.eli_uri


@_skip
async def test_live_get_law_text_markdown():
    async with RisClient() as c:
        res = await c.search_law(
            LawSearchRequest(suchworte="Datenschutzgesetz", page_size="Ten")
        )
        url = res.items[0].content_urls["html"]
        text = await c.get_text(url, TextFormat.markdown)
    assert text.format == "markdown"
    assert len(text.content) > 100
    assert "<style" not in text.content


@_skip
async def test_live_search_case_justiz_norm():
    async with RisClient() as c:
        res = await c.search_case(
            CaseSearchRequest(norm="ABGB §879", gericht="Justiz", page_size="Ten")
        )
    assert res.total > 0
    assert res.items[0].ecli.startswith("ECLI:AT:")


@_skip
async def test_live_list_changes_bundesnormen():
    from ris_client import HistoryRequest

    async with RisClient() as c:
        res = await c.search_changes(
            HistoryRequest(anwendung="Bundesnormen", von="2026-07-10",
                           bis="2026-07-22", include_deleted=True,
                           page_size="Ten")
        )
    assert res.total > 0
    assert res.items
    assert res.items[0].id


@_skip
async def test_live_search_state_law_bundesland_filter():
    from ris_client import StateLawSearchRequest

    async with RisClient() as c:
        res = await c.search_state_law(
            StateLawSearchRequest(suchworte="Abfall", bundeslaender=["Kaernten"],
                                  page_size="Ten")
        )
    assert res.total > 0
    # the Bundesland filter must actually scope the results to Kärnten
    assert {it.bundesland for it in res.items} == {"Kärnten"}


@_skip
async def test_live_search_misc_erlaesse():
    from ris_client import MiscSearchRequest

    async with RisClient() as c:
        res = await c.search_misc(
            MiscSearchRequest(suchworte="Steuer", applikation="Erlaesse",
                              page_size="Ten")
        )
    assert res.total >= 0
    assert res.request_url.endswith("Seitennummer=1") or "Sonstige" in res.request_url


@_skip
async def test_live_search_municipality():
    from ris_client import MunicipalitySearchRequest

    async with RisClient() as c:
        res = await c.search_municipality(
            MunicipalitySearchRequest(bundesland="Kaernten",
                                      geaendert_seit="EinemJahr", page_size="Ten")
        )
    assert res.total > 0
    assert res.items[0].gemeinde
