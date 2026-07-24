"""Offline: HTML/XML -> Markdown + raw passthrough, using saved fixtures."""

from pathlib import Path

import pytest

from ris_client.textparse import html_to_markdown, to_markdown

FIX = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def law_html():
    return (FIX / "nor_law.html").read_text(encoding="utf-8")


@pytest.fixture
def case_html():
    return (FIX / "case_text.html").read_text(encoding="utf-8")


def test_law_markdown_has_content_no_css(law_html):
    md = html_to_markdown(law_html)
    assert "Abschlussprüfer-Aufsichtsgesetz" in md
    # CSS/boilerplate must be gone.
    assert "page-break-before" not in md
    assert "<style" not in md
    assert "eRechtXML2XHTML11" not in md
    # Markdown headings emitted.
    assert md.startswith("## ") or "\n## " in md


def test_law_markdown_strips_sr_only_duplicates(law_html):
    md = html_to_markdown(law_html)
    # The visible "§ 17" is kept; the sr-only "Paragraph 17" is removed.
    assert "§ 17" in md
    assert "Paragraph 17" not in md


def test_markdown_much_smaller_than_source(law_html):
    md = html_to_markdown(law_html)
    assert len(md) < len(law_html) / 2


def test_case_html_parses(case_html):
    md = html_to_markdown(case_html)
    assert len(md) > 50
    assert "<style" not in md


def test_to_markdown_xml_dispatch():
    xml = "<root><Absatz>Hallo Welt</Absatz></root>"
    out = to_markdown(xml, "https://www.ris.bka.gv.at/x/y.xml")
    assert "Hallo Welt" in out
