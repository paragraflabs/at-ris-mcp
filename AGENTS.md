# AGENTS.md — at-ris-mcp

Dieses Repo baut **`at-ris-mcp`**: einen eigenständigen, generischen MCP-Server für das österreichische Rechtsinformationssystem (RIS) des Bundeskanzleramts.

## Zuerst lesen
1. **`PLAN.md`** — der vollständige Implementierungsplan. Enthält alle getroffenen Entscheidungen, die Modulstruktur, die 6 Tools und die Roadmap. **Beginne immer hier.** Besonders `§0 Einstieg für einen frischen Agent`.
2. **`reference/`** — die offiziellen RIS-Unterlagen (maßgebliche Quelle):
   - `reference/xsd-request-schema/*.xsd` — offizielle Request-Schemas (alle Parameter, Enums, Punkt-Notation)
   - `reference/examples_get_post.txt` — offizielle GET-Beispiel-URLs (Fixture-Basis für URL-Bau-Tests)
   - `reference/OGD-FAQ.txt` — Lizenz (CC-BY 4.0), Netiquette, Rate-Limits

## Nicht neu erforschen (bereits verifiziert, steht in PLAN.md §0)
- Basis-URL `https://data.bka.gv.at/ris/api/v2.6/`, keyless, CC-BY 4.0, kommerziell erlaubt.
- Parameter in **Punkt-Notation**: `Fassung.FassungVom=`, `Abschnitt.Typ=Paragraph&Abschnitt.Von=&Abschnitt.Bis=`, `Dokumenttyp.SucheInEntscheidungstexten=true`.
- `Applikation=BrKons` = konsolidiertes geltendes Recht (Kern-Mehrwert). Judikatur `Norm=` filtert nach angewandter Norm.
- **`www.ris.bka.gv.at` blockt curl mit HTTP 503**; die JSON-API `data.bka.gv.at` blockt NICHT. Volltext-Abruf → robuster User-Agent + Retry; Browser-Fallback nur als README-Doku.

## Verbindliche Entscheidungen (nicht ohne Rückfrage ändern)
- Sprache **Python 3.11+**, **FastMCP + stdio** (HTTP/SSE erst v2).
- **Zwei Pakete**: `ris_client` (eigenständige, MCP-unabhängige Library) + `ris_mcp` (dünner Wrapper). `server.py` enthält KEINE Logik.
- Lizenz **Apache-2.0** (Code); Daten bleiben CC-BY der Republik → jede Antwort trägt `attribution` + `legal_notice`.
- HTML→Markdown via **beautifulsoup4 + lxml**, mit **`raw`-Schalter** (Originaltext).
- **SQLite-Cache** (TTL); **Audit-Log opt-in** per ENV `RIS_AUDIT_DIR`.
- PyPI-Name **`at-ris-mcp`**.

## Konventionen
- Read-only gegen RIS; keine Client-Daten verlassen die Maschine außer Suchparametern.
- Netiquette einhalten: Rate-Limit 1–2 s/Seite, aussagekräftiger User-Agent (`at-ris-mcp/<version> (+kontakt)`).
- Offline-Tests mit echten Response-Fixtures (`fixtures/`); Live-Smoke-Tests skippbar.
- Commits erst nach ausdrücklicher Freigabe des Users.

## Referenz-MCP zum Gegentesten
Der Konkurrent `at-eli-mcp` läuft bereits in opencode (Config `~/.config/opencode/opencode.jsonc`, MCP-Name `at-eli`) und kann zum Vergleich genutzt werden. `at-ris-mcp` unterscheidet sich durch: konsolidiertes Recht (BrKons), §-genauen Abschnitt-Zugriff, historischen Rechtsstand (FassungVom), Änderungs-Monitoring, Markdown+raw.
