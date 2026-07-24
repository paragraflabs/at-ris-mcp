"""Citation contract: attribution, legal notice and human-readable citations.

Per PLAN.md §2 every response carries a CC-BY attribution and a legal notice.
ELI (for legislation) and ECLI (for case law) come verbatim from RIS and are
never invented.
"""

from __future__ import annotations

ATTRIBUTION = (
    "Quelle: RIS - Rechtsinformationssystem des Bundes (data.bka.gv.at), "
    "CC BY 4.0"
)

LEGAL_NOTICE = (
    "Keine Rechtsauskunft. Rechtsverbindlich ist ausschließlich der authentische "
    "Kundmachungstext (Bundesgesetzblatt/Landesgesetzblatt authentisch). "
    "Konsolidiertes Recht und alle übrigen Dokumente dienen nur der Information; "
    "keine Gewähr für Richtigkeit, Aktualität oder Vollständigkeit."
)


def law_citation(kurztitel: str | None, kundmachungsorgan: str | None,
                 abschnitt: str | None = None) -> str | None:
    """Build a human-readable citation for a Bundesrecht record.

    e.g. "Abschlussprüfer-Aufsichtsgesetz § 17, BGBl. I Nr. 83/2016".
    Returns None if there is nothing meaningful to cite.
    """
    parts: list[str] = []
    if kurztitel:
        head = kurztitel
        if abschnitt:
            head = f"{head} {abschnitt}"
        parts.append(head)
    elif abschnitt:
        parts.append(abschnitt)
    if kundmachungsorgan:
        parts.append(kundmachungsorgan.strip())
    return ", ".join(parts) if parts else None


def case_citation(gericht: str | None, entscheidungsdatum: str | None,
                  geschaeftszahl: str | None) -> str | None:
    """Build a human-readable citation for a Judikatur record.

    e.g. "OGH 2005-01-25, 10Ob84/04g".
    """
    parts: list[str] = []
    if gericht:
        parts.append(gericht)
    if entscheidungsdatum:
        parts.append(entscheidungsdatum)
    head = " ".join(parts)
    if geschaeftszahl:
        return f"{head}, {geschaeftszahl}" if head else geschaeftszahl
    return head or None
