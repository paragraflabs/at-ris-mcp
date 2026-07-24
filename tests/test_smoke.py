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
