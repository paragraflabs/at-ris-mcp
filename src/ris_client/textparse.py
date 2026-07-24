"""Convert RIS full-text HTML/XML into clean Markdown, or pass raw text through.

RIS documents wrap the content in ``<div class="paperw">`` with many
``<div class="contentBlock">`` sections. Each block is a heading
(``h1.Titel``) plus paragraphs (``p.ErlText`` / ``p.Abs`` ...). The markup is
polluted with ~40 KB of CSS and duplicate accessibility spans
(``span.sr-only`` mirrors ``span[aria-hidden]``); both are stripped so the LLM
sees only the legal text (PLAN.md §6).

``raw`` returns the untouched source (court-proof original).
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 at-ris-mcp contributors

from __future__ import annotations

from bs4 import BeautifulSoup


def _clean_soup(soup: BeautifulSoup) -> None:
    # Drop non-content elements entirely.
    for tag in soup(["style", "script", "head", "meta", "link"]):
        tag.decompose()
    # RIS renders each label twice: a visual span[aria-hidden="true"] and a
    # screen-reader span.sr-only with the expanded form. Keep the visual one.
    for sr in soup.select("span.sr-only"):
        sr.decompose()


def _text_of(node) -> str:
    return " ".join(node.get_text(" ", strip=True).split())


def html_to_markdown(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    _clean_soup(soup)

    root = soup.select_one("div.paperw") or soup.body or soup
    lines: list[str] = []

    blocks = root.select("div.contentBlock")
    if blocks:
        for block in blocks:
            heading = block.find(["h1", "h2", "h3"])
            head_txt = _text_of(heading) if heading else ""
            if heading:
                heading.extract()
            body_txt = _text_of(block)
            if head_txt:
                lines.append(f"## {head_txt}")
            if body_txt:
                lines.append(body_txt)
            lines.append("")
    else:
        # Fallback: no contentBlock structure (e.g. Judikatur variants).
        for el in root.find_all(["h1", "h2", "h3", "p"]):
            txt = _text_of(el)
            if not txt:
                continue
            if el.name in ("h1", "h2", "h3"):
                lines.append(f"## {txt}")
            else:
                lines.append(txt)
            lines.append("")

    md = "\n".join(lines).strip()
    # Collapse excessive blank lines.
    while "\n\n\n" in md:
        md = md.replace("\n\n\n", "\n\n")
    return md


def xml_to_text(xml: str) -> str:
    soup = BeautifulSoup(xml, "xml")
    for tag in soup(["style", "script"]):
        tag.decompose()
    return "\n".join(
        line for line in (l.strip() for l in soup.get_text("\n").splitlines()) if line
    )


def to_markdown(content: str, source_url: str) -> str:
    """Dispatch on the source URL extension."""
    lower = source_url.lower()
    if lower.endswith(".xml"):
        return xml_to_text(content)
    return html_to_markdown(content)


def extract_law_citation(html: str) -> str | None:
    """Best-effort human-readable citation from a RIS law HTML document.

    RIS renders labelled contentBlocks ("Kurztitel", "Kundmachungsorgan",
    "§/Artikel/Anlage"). We stitch those into
    "<Kurztitel> <§>, <Kundmachungsorgan>". Returns None if nothing usable.
    """
    soup = BeautifulSoup(html, "lxml")
    _clean_soup(soup)
    fields: dict[str, str] = {}
    for block in soup.select("div.contentBlock"):
        heading = block.find(["h1", "h2", "h3"])
        if not heading:
            continue
        label = _text_of(heading)
        heading.extract()
        value = _text_of(block)
        if label and value:
            fields[label] = value

    kurztitel = fields.get("Kurztitel") or fields.get("Titel")
    kundm = fields.get("Kundmachungsorgan")
    abschnitt = None
    for key, val in fields.items():
        if "Artikel" in key or "Anlage" in key or key.startswith("§"):
            abschnitt = val
            break

    parts: list[str] = []
    if kurztitel:
        parts.append(f"{kurztitel} {abschnitt}" if abschnitt else kurztitel)
    elif abschnitt:
        parts.append(abschnitt)
    if kundm:
        parts.append(kundm)
    return ", ".join(parts) if parts else None
