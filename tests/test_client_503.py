"""Offline: retry behaviour on 503, host restriction, format validation.

Uses respx to mock httpx without touching the network. Rate limit is set to 0.
"""

import httpx
import pytest
import respx

from ris_client.client import RisClient
from ris_client.config import Config
from ris_client.errors import (
    InvalidArgError,
    NotFoundError,
    UnsupportedFormatError,
    UpstreamError,
)
from ris_client.models import LawSearchRequest, TextFormat


def _config(tmp_path):
    return Config(
        rate_ms=0,
        max_retries=3,
        cache_enabled=False,
        cache_path=tmp_path / "c.sqlite",
    )


@pytest.fixture
def cfg(tmp_path):
    return _config(tmp_path)


_EMPTY_ENVELOPE = {
    "OgdSearchResult": {
        "OgdDocumentResults": {
            "Hits": {"@pageNumber": "1", "@pageSize": "10", "#text": "0"}
        }
    }
}


@respx.mock
async def test_retry_then_success_on_503(cfg):
    route = respx.get(url__startswith="https://data.bka.gv.at/ris/api/v2.6/Bundesrecht")
    route.side_effect = [
        httpx.Response(503, text="busy"),
        httpx.Response(200, json=_EMPTY_ENVELOPE),
    ]
    async with RisClient(cfg) as c:
        res = await c.search_law(LawSearchRequest(suchworte="x"))
    assert res.total == 0
    assert route.call_count == 2


@respx.mock
async def test_persistent_503_raises_upstream(cfg):
    respx.get(url__startswith="https://data.bka.gv.at/ris/api/v2.6/Bundesrecht").mock(
        return_value=httpx.Response(503, text="busy")
    )
    async with RisClient(cfg) as c:
        with pytest.raises(UpstreamError):
            await c.search_law(LawSearchRequest(suchworte="x"))


@respx.mock
async def test_404_raises_not_found(cfg):
    respx.get(url__startswith="https://www.ris.bka.gv.at").mock(
        return_value=httpx.Response(404)
    )
    async with RisClient(cfg) as c:
        with pytest.raises(NotFoundError):
            await c.get_text("https://www.ris.bka.gv.at/x/y.html")


async def test_search_law_requires_a_filter(cfg):
    async with RisClient(cfg) as c:
        with pytest.raises(InvalidArgError):
            await c.search_law(LawSearchRequest())


async def test_get_text_rejects_foreign_host(cfg):
    async with RisClient(cfg) as c:
        with pytest.raises(InvalidArgError):
            await c.get_text("https://evil.example.com/x.html")


async def test_get_text_rejects_unsupported_format(cfg):
    async with RisClient(cfg) as c:
        with pytest.raises(UnsupportedFormatError):
            await c.get_text("https://www.ris.bka.gv.at/x/y.pdf")


@respx.mock
async def test_get_text_raw_passthrough(cfg):
    html = "<html><body><div class='paperw'><p class='ErlText'>Hallo</p></div></body></html>"
    respx.get("https://www.ris.bka.gv.at/x/y.html").mock(
        return_value=httpx.Response(200, text=html)
    )
    async with RisClient(cfg) as c:
        res = await c.get_text("https://www.ris.bka.gv.at/x/y.html", TextFormat.raw)
    assert res.format == "raw"
    assert res.content == html


@respx.mock
async def test_get_text_markdown_default(cfg):
    html = "<html><body><div class='paperw'><div class='contentBlock'><h1 class='Titel'>Titel</h1><p class='ErlText'>Hallo Welt</p></div></div></body></html>"
    respx.get("https://www.ris.bka.gv.at/x/y.html").mock(
        return_value=httpx.Response(200, text=html)
    )
    async with RisClient(cfg) as c:
        res = await c.get_text("https://www.ris.bka.gv.at/x/y.html")
    assert res.format == "markdown"
    assert "Hallo Welt" in res.content
    assert "<html" not in res.content


@respx.mock
async def test_get_text_fills_citation_from_html(cfg):
    html = (
        "<html><body><div class='paperw'>"
        "<div class='contentBlock'><h1 class='Titel'>Kurztitel</h1>"
        "<p class='ErlText'>Musterschutzgesetz</p></div>"
        "<div class='contentBlock'><h1 class='Titel'>Kundmachungsorgan</h1>"
        "<p class='ErlText'>BGBl. Nr. 497/1990</p></div>"
        "</div></body></html>"
    )
    respx.get("https://www.ris.bka.gv.at/x/y.html").mock(
        return_value=httpx.Response(200, text=html)
    )
    async with RisClient(cfg) as c:
        res = await c.get_text("https://www.ris.bka.gv.at/x/y.html")
    assert res.citation == "Musterschutzgesetz, BGBl. Nr. 497/1990"


@respx.mock
async def test_get_text_passed_citation_wins(cfg):
    html = "<html><body><div class='paperw'><div class='contentBlock'><h1 class='Titel'>Kurztitel</h1><p class='ErlText'>X</p></div></div></body></html>"
    respx.get("https://www.ris.bka.gv.at/x/y.html").mock(
        return_value=httpx.Response(200, text=html)
    )
    async with RisClient(cfg) as c:
        res = await c.get_text(
            "https://www.ris.bka.gv.at/x/y.html", citation="Explicit citation"
        )
    assert res.citation == "Explicit citation"


async def test_get_text_rejects_unknown_kwarg(cfg):
    # Unknown kwargs must raise loudly, not be silently swallowed.
    async with RisClient(cfg) as c:
        with pytest.raises(TypeError):
            await c.get_text("https://www.ris.bka.gv.at/x/y.html", bogus="oops")
