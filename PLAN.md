# at-ris-mcp — Implementierungsplan
 
 *Erstellt 2026-07-24. Status: PLANUNG (noch kein Code). Ein eigenständiger, generischer MCP-Server für das österreichische Rechtsinformationssystem (RIS) des Bundeskanzleramts.*
 
 ---
 
 ## 0. Einstieg für einen frischen Agent (WICHTIG — zuerst lesen)
 
 Dieser Plan ist self-contained, aber die vollständige technische Grundlage liegt in Referenzdateien. Vor Implementierungsbeginn diese lesen:
 
 **Offizielle RIS-Referenz (im Repo gesichert, `at-ris-mcp/reference/`):**
 - `reference/xsd-request-schema/*.xsd` — **die maßgeblichen offiziellen Request-Schemas** (alle Parameter, Enums, Punkt-Notation). Wichtigste: `OGD_Bundesrecht_Request.xsd`, `OGD_Judikatur_Request.xsd`, `OGD_Request_Types.xsd`, `OGD_History_Request.xsd`.
 - `reference/examples_get_post.txt` — **offizielle GET-Beispiel-URLs** (zeigen die exakte Punkt-Notation, z.B. `Fassung.FassungVom=`, `Abschnitt.Typ=`). = Fixture-Basis für `test_urlbuild.py`.
 - `reference/OGD-FAQ.txt` — offizielle FAQ (Lizenz CC-BY, Netiquette, Rate-Limits, `SucheInEntscheidungstexten`-Hinweis).
 
 **Ergänzende Kontext-Dateien (außerhalb dieses Repos):**
 - `/home/joe/datamoat/ideen/ris-api-features.md` — aufbereitete Feature-Analyse (was der bestehende `at-eli-mcp` NICHT kann, alle Applikationen mit Trefferzahlen, Parameter-Tabellen, GET-Beispiele). **Die beste Schnell-Übersicht.**
 - `/home/joe/datamoat/ideen/at-korridor-entscheidung.md` — der ursprüngliche Business-Use-Case (AT-Steuer/Compliance), der diesen MCP motiviert hat (nur Kontext, nicht nötig zum Bauen).
 
 **Wichtigste bereits verifizierte Fakten (damit nicht neu erforscht werden muss):**
 - Basis-URL: `https://data.bka.gv.at/ris/api/v2.6/` — Endpoints v1: `/Bundesrecht`, `/Judikatur`. Keyless, CC-BY 4.0, kommerziell erlaubt.
 - Parameter nutzen **Punkt-Notation**: `Fassung.FassungVom=2021-10-18`, `Abschnitt.Typ=Paragraph&Abschnitt.Von=2&Abschnitt.Bis=2`, `Dokumenttyp.SucheInEntscheidungstexten=true`, `Sortierung.SortedByColumn=...`.
 - `Applikation=BrKons` = **konsolidiertes geltendes Recht** (der MCP-Kern-Mehrwert); `BgblAuth`/`BgblPdf`/`BgblAlt`/`Begut`/`RegV`/`Erv` = weitere Bundesrecht-Applikationen.
 - Judikatur: `Norm=ABGB §879` filtert nach angewandter Norm; **beide** `SucheInRechtssaetzen`+`SucheInEntscheidungstexten` auf `true`, sonst nur Rechtssätze.
 - **`www.ris.bka.gv.at` blockt curl/simple Clients mit HTTP 503** (Volltext-Host). Die JSON-API `data.bka.gv.at` ist NICHT betroffen. → robuster User-Agent + Retry; Browser-Fallback nur als README-Doku.
 - Enums: `PageSize`(Ten/Twenty/Fifty/OneHundred), `ImRisSeit`(EinerWoche..EinemJahr), `NormabschnittTyp`(Alle/Artikel/Paragraph/Anlage), `WebSortDirection`(Ascending/Descending).
 - Bereits eingebunden & getestet: der KONKURRENZ-MCP `at-eli-mcp` läuft in opencode (config `~/.config/opencode/opencode.jsonc`, MCP-Name `at-eli`) — kann zum Vergleich/Gegentest genutzt werden.
 
 ---
 
 ## 1. Ziel & Leitentscheidungen (bestätigt)
 
 | Frage | Entscheidung |
 |---|---|
 | **Zweck** | Generischer RIS-Zugang für **alle Rechtsgebiete** (nicht nur AT-Steuer). Recherche + möglicher Produktbaustein + Änderungs-Monitoring. |
 | **Herkunft** | **Eigenständiger Neubau** (kein Fork von `at-eli-mcp`). RIS-API als einzige Vorlage. Saubere Basis für kommerzielle Nutzung/Veröffentlichung. |
 | **Sprache** | **Python** (3.11+) |
 | **Framework** | **FastMCP + stdio** (v1). HTTP/SSE-Transport → Roadmap v2. |
 | **Scope v1** | **Solides Fundament**: Bundesrecht (konsolidiert + Gesetzblätter + Begut/RegV) + Judikatur (alle Gerichte). Landesrecht/Sonstige/Bezirke/Gemeinden → v2. |
 | **Volltext** | **Zu sauberem Markdown/Text parsen** (RIS-HTML/XML ist CSS-verseucht → Token-Ersparnis). |
 | **Zitate** | **Voller Citation-Contract**: ELI/ECLI + human-readable + source_url + **CC-BY-4.0-Attribution** in jeder Antwort. |
 | **Ort** | `/home/joe/at-ris-mcp` (eigenes Git-Repo). |
 | **Lizenz/Veröffentlichung** | Beide Wege offen halten (privat ODER PyPI/MCP-Registry). |
 
 ---
 
 ## 2. Rechtlicher & lizenzrechtlicher Rahmen
 
 - **RIS-Daten:** CC BY 4.0 (Namensnennung), **kommerzielle Nutzung erlaubt**, keyless. → In jeder Tool-Antwort ein `attribution`-Feld: *"Quelle: RIS – Rechtsinformationssystem des Bundes (data.bka.gv.at), CC BY 4.0"*.
 - **Rechtsverbindlichkeit:** nur „Bundesgesetzblatt authentisch" / „Landesgesetzblatt authentisch". Konsolidiertes Recht = Information. → Jede Antwort trägt einen `dataset_note`/`legal_notice`: *"Keine Rechtsauskunft; rechtsverbindlich ist nur der authentische Kundmachungstext."*
 - **Kein Fremdcode:** eigenständig geschrieben → keine Apache-2.0-NOTICE-Pflicht von `at-eli-mcp`. Eigene Lizenz frei wählbar (Vorschlag: **MIT** oder **Apache-2.0** für den Code; Daten bleiben CC-BY der Republik).
 - **Netiquette (verbindlich einzuhalten):** 1–2 s Pause pro Seite; Massenabfragen außerhalb 06–18 Uhr / am WE; Massendownload vorab an `ris.it@bka.gv.at`; **aussagekräftiger User-Agent** (`at-ris-mcp/<version> (+kontakt)`).
 
 ---
 
 ## 3. RIS-API — technische Basis (verifiziert)
 
 - Basis-URL: `https://data.bka.gv.at/ris/api/v2.6/`
 - Endpoints v1: **`/Bundesrecht`**, **`/Judikatur`** (v2: `/Landesrecht`, `/Sonstige`, `/Bezirke`, `/Gemeinden`)
 - Antwort: JSON (`OgdSearchResult.OgdDocumentResults`), tief verschachtelt → wird flachgeklopft.
 - Volltext-Dokumente: `https://www.ris.bka.gv.at/Dokumente/.../*.{html,xml,pdf,rtf}` — **⚠ dieser Host blockt curl mit HTTP 503** (Anti-Bot). Die **JSON-API** (`data.bka.gv.at`) ist NICHT betroffen.
   - **Konsequenz für die Architektur:** Volltext-Abruf braucht robuste Header (Browser-ähnlicher User-Agent, Accept), ggf. Retry. Falls RIS auch den API-Volltext blockt → Fallback dokumentieren. (Bei unseren Tests kam der `.xml`/`.html`-Abruf über die MCP-Toolchain durch; für curl war ein UA nötig.)
 - Parameter nutzen **Punkt-Notation** für verschachtelte Felder: `Fassung.FassungVom`, `Abschnitt.Typ`, `Sortierung.SortedByColumn`, `Dokumenttyp.SucheInEntscheidungstexten`.
 
 ### Enums (aus offiziellem XSD)
 - `PageSize`: `Ten | Twenty | Fifty | OneHundred`
 - `ImRisSeit` / `ChangeSetInterval`: `EinerWoche | ZweiWochen | EinemMonat | DreiMonaten | SechsMonaten | EinemJahr`
 - `NormabschnittTyp`: `Alle | Artikel | Paragraph | Anlage`
 - `WebSortDirection`: `Ascending | Descending`
 - Judikatur-Gerichte: `Vfgh, Vwgh, Justiz, Bvwg, Lvwg, Dsk, Dok, Pvak, Gbk, Uvs, AsylGH, Ubas, Umse, Bks, Verg, Normenliste`
 
 ---
 
 ## 4. Tool-Design (MCP-Oberfläche v1)
 
 Bewusst wenige, mächtige Tools (statt einem pro Applikation).
 
 ### `ris_search_law`
 Sucht Bundesrecht.
 - Args: `suchworte?`, `titel?`, `applikation` (default `BrKons`; auch `BgblAuth|BgblPdf|BgblAlt|Begut|RegV|Erv`), `paragraph?`/`artikel?` (→ `Abschnitt.Typ` + `.Von`/`.Bis`), `fassung_vom?` (Stichtag), `in_kraft_von?`/`in_kraft_bis?`, `geaendert_seit?` (`ImRisSeit`), `gesetzesnummer?`, `kundmachungsorgan?`, `sortierung?`, `page_size?`, `page_number?`.
 - Return: `total`, `items[]` (flach: `kurztitel, titel, typ, bgblnummer, eli_uri, human_readable_citation, source_url, content_urls{html,xml,pdf,rtf}, geltungsdatum`), `attribution`, `legal_notice`.
 
 ### `ris_get_law_text`
 Volltext eines Gesetzes/Paragraphen.
 - Args: `content_url` (aus einem Treffer), `format?` (`markdown`(default)|`html`|`xml`), `eli_uri?`, `human_readable_citation?` (Durchreichen für zitierbare Antwort).
 - Return: `citation`, `eli_uri`, `source_url`, `content` (bereinigt), `format`, `fassung_info` (falls erkennbar), `attribution`, `legal_notice`.
 
 ### `ris_search_case`
 Sucht Judikatur.
 - Args: `suchworte?`, `gericht` (default `Justiz`; alle Applikationen), `norm?` (angewandte Norm, z.B. `ABGB §879`), `geschaeftszahl?`, `entscheidung_von?`/`entscheidung_bis?`, `rechtssaetze?`(bool, default true), `entscheidungstexte?`(bool, default true → **beide, sonst nur Rechtssätze!**), `geaendert_seit?`, `sortierung?`, `page_size?`, `page_number?`.
 - Return: `total`, `items[]` (`gericht, geschaeftszahl, entscheidungsdatum, dokumenttyp, norm, ecli, human_readable_citation, source_url, content_urls`), `attribution`, `legal_notice`.
 
 ### `ris_get_case_text`
 Volltext einer Entscheidung. Analog `ris_get_law_text`.
 
 ### `ris_list_changes`
 Änderungs-/Frühwarn-Feed (History).
 - Args: `anwendung` (z.B. `BrKons|BgblAuth|Begut|RegV|Justiz|...`), `von?`/`bis?` (Datum) ODER `zeitraum?` (`ImRisSeit`), `include_deleted?` (bool).
 - Return: geänderte/neue/gelöschte Dokumente seit X. → Basis für BiBuG/EStG/FLAG-Monitoring + Begut/RegV-Frühwarnung.
 
 ### `ris_list_collections`
 Statische Übersicht: welche Endpoints/Applikationen v1 abdeckt + Scope-Hinweis (Landesrecht in v2).
 
 > **Designprinzip:** Der `applikation`/`gericht`-Parameter macht die Tools generisch — ein Tool deckt viele RIS-Applikationen ab, statt 20 Einzeltools.
 
 ---
 
 ## 5. Architektur / Module
 
 **Zwei-Paket-Struktur (Entscheidung: eigenständige Library + dünner MCP):**
 
 ```
 at-ris-mcp/                         # ein Repo, zwei installierbare Pakete
 ├── pyproject.toml               # deps: httpx, pydantic, beautifulsoup4, lxml (+ optional [mcp])
 ├── README.md                    # CC-BY-Attribution, Netiquette, Scope
 ├── LICENSE                      # Apache-2.0 (Code)
 ├── NOTICE                       # Hinweis: Daten = RIS/CC-BY der Republik
 ├── src/
 │   ├── ris_client/              # ── EIGENSTÄNDIGE LIBRARY (MCP-unabhängig) ──
 │   │   ├── __init__.py          #    public API: search_law(), get_law_text(), search_case(), ...
 │   │   ├── client.py            #    httpx: URL-Bau (Punkt-Notation), Retry, Rate-Limit, UA, 503-Handling
 │   │   ├── models.py            #    Pydantic: Requests + flache Response-Records
 │   │   ├── mapping.py           #    RIS-JSON-Envelope → flache Records
 │   │   ├── citations.py         #    ELI/ECLI + human_readable + attribution + legal_notice
 │   │   ├── textparse.py         #    HTML/XML → Markdown (bs4+lxml) | raw-Passthrough
 │   │   ├── ratelimit.py         #    1-2s/Seite; Bürozeiten-Hinweis
 │   │   ├── cache.py             #    SQLite-Cache mit TTL (später FTS5-fähig)
 │   │   └── config.py            #    ENV: BASE_URL, CACHE_DIR, USER_AGENT, RATE_MS, AUDIT_DIR
 │   └── ris_mcp/                 # ── DÜNNER MCP-WRAPPER ──
 │       ├── __init__.py
 │       ├── __main__.py          #    stdio-Entrypoint (python -m ris_mcp)
 │       └── server.py            #    FastMCP: 6 Tools, rufen NUR ris_client auf
 ├── tests/
 │   ├── test_urlbuild.py         #    offline: Args→korrekte Punkt-Notation-URL (Fixtures = offiz. GET-Beispiele)
 │   ├── test_mapping.py          #    offline: Envelope→Record
 │   ├── test_textparse.py        #    offline: HTML→Markdown + raw
 │   ├── test_client_503.py       #    offline: Retry/Fallback-Verhalten (gemockt)
 │   └── test_smoke.py            #    live: echte RIS-Abfragen (skippbar/CI-optional)
 └── fixtures/                    # gespeicherte echte RIS-Responses
 ```
 
 **Warum zwei Pakete:** `ris_client` importierst du **direkt im AT-Steuer-Backend** (ohne MCP-Overhead). `ris_mcp` ist nur die MCP-Oberfläche darauf. Ein Repo; `ris_mcp` hängt von `ris_client` ab; MCP-Deps optional (`pip install ris-client` vs. `[mcp]`).
 
 **Kern-Prinzipien:**
 - `server.py` enthält **keine** Logik — nur Tool-Signaturen → `ris_client`-Aufrufe.
 - **Read-only**, keine Client-Daten verlassen die Maschine außer Suchparametern.
 - **Audit-Log** (JSONL) **opt-in** per ENV (`RIS_AUDIT_DIR`); loggt nur Tool/Params-Hash/Zeit/Trefferzahl (keine Volltexte).
 - Host-Restriction: Volltext nur von `ris.bka.gv.at`/`data.bka.gv.at`.
 - **`raw`-Schalter**: Volltext-Tools geben Default Markdown, `format="raw"` den unveränderten Originaltext.
 
 ---
 
 ## 6. Die kniffligen Stellen (Risiken & Lösungen)
 
 | Problem | Lösung |
 |---|---|
 | **RIS blockt curl mit 503** (statische Dokumente) | Browser-ähnlicher User-Agent + `Accept`-Header + Retry-mit-Backoff im `client.py`. Falls Volltext-Host hart blockt: dokumentierter Fallback (XML statt HTML, oder Hinweis an Nutzer). |
 | **`BrKons` liefert §§ als einzelne NOR-Dokumente**, Suche findet oft Novellen statt konsolidiertem Text | `Abschnitt`-Filter + `applikation=BrKons` gezielt; `mapping.py` bevorzugt konsolidierte NOR-Treffer; Doku im README. |
 | **Judikatur: nur Rechtssätze statt Volltexte** | `entscheidungstexte=true` als Default → beide Flags gesetzt. |
 | **RIS-HTML voller CSS/Boilerplate** (wir sahen ~40 KB CSS) | `textparse.py` extrahiert nur den Inhaltsblock (`contentBlock`/`ErlText`), strippt `<style>`/`<script>`, → Markdown. Fixtures-getestet. |
 | **Verschachtelte Punkt-Notation-Parameter** | zentral in `client.py` gebaut, mit offiziellen GET-Beispielen als Test-Fixtures. |
 | **Rate-Limit/DDOS-Verdacht** bei kommerzieller Last | `ratelimit.py` erzwingt 1-2s/Seite; README: Massendownload vorab melden. |
 | **API-Version 2.6 kann sich ändern** | `BASE_URL` als ENV konfigurierbar; Version in Config isoliert. |
 
 ---
 
 ## 7. Roadmap
 
 - **v0.1 (MVP):** `ris_search_law` (BrKons + Abschnitt + Fassung), `ris_get_law_text` (Markdown), `ris_search_case` (Norm + Volltexte), `ris_get_case_text`, `ris_list_collections`. stdio. Caching + Rate-Limit + UA. Offline-Tests.
 - **v0.2:** `ris_list_changes` (History/ImRisSeit inkl. deleted), `Begut`/`RegV`-Applikationen, Audit-Log.
 - **v0.3:** Landesrecht (9 Bundesländer), `Sonstige` (Erlässe), `Bezirke`/`Gemeinden`.
 - **v1.0:** Härtung, Doku, PyPI + MCP-Registry-Eintrag (falls Veröffentlichung gewählt), `Erv` (engl. Übersetzungen).
 - **v2.0:** HTTP/SSE-Transport (Remote-Service fürs Business-Backend), optional strukturierte Norm-Graph-Ausgabe (Verweise zwischen §§).
 
 ---
 
 ## 8. Geklärte Entscheidungen (2026-07-24)
 
 | Punkt | Entscheidung |
 |---|---|
 | **Code-Lizenz** | **Apache-2.0** (Patent-Schutzklausel, gut für kommerzielle Nutzung). Daten bleiben CC-BY der Republik. |
 | **Core-Library** | **Eigenständige Library** (`ris_client`), MCP-unabhängig → auch direkt im AT-Steuer-Backend nutzbar. `ris_mcp` ist dünner Wrapper darüber. |
 | **Volltext** | Default `markdown` **+ `raw`-Schalter** (unveränderter Originaltext für Gerichtsfestigkeit). |
 | **503-Blocker** | **Fallback dokumentieren** (robuste Header + Retry im Client; Browser-Fallback nur als README-Anleitung, nicht als Dependency). |
 | **Cache/Audit** | siehe Empfehlung §8a unten. |
 | **Paketname** | **`at-ris-mcp`** (final; PyPI-frei geprüft 2026-07-24). `ris-mcp` war belegt (fremder RIS-MCP v0.2.1, SQLite-Mirror). |
 | **HTML-Parser** | **`beautifulsoup4` + `lxml`** (final). Pure-Python-API, installiert sich überall (lxml hat überall Wheels → kein C-Compiler). Performance für Einzeldokument-Parsing ausreichend; max. Installations-Kompatibilität für Veröffentlichung. |
 
 ### §8a. Empfehlung Cache & Audit
 
 **Cache → SQLite (empfohlen).** Begründung:
 - RIS-Netiquette verlangt Schonung (1-2s/Seite, Massenabfragen nur nachts/WE). Ein **persistenter Cache reduziert API-Last drastisch** und macht wiederholte Recherchen schnell.
 - SQLite (statt loser JSON-Dateien), weil: ein File, atomar, TTL-Spalten, später **FTS5-Volltextsuche lokal** möglich (genau das, was der konkurrierende `ris-mcp` macht → wäre unser v2-Upgrade-Pfad). JSON-Dateien skalieren schlecht bei tausenden Normen.
 - TTL differenziert: konsolidiertes Recht/Judikatur ändert sich selten → langer TTL (z.B. 7–30 Tage); `ImRisSeit`/`Begut`/`RegV` (Monitoring) → kurzer/kein Cache.
 
 **Audit-Log → standardmäßig AUS, opt-in per ENV (empfohlen).** Begründung:
 - Reine RIS-Recherche verarbeitet **keine personenbezogenen Daten** (nur öffentliche Rechtsquellen + Suchbegriffe) → Audit ist datenschutzrechtlich unkritisch, aber auch nicht nötig.
 - **Für den späteren Produktiv-/Compliance-Einsatz** (AT-Steuer-Backend) willst du Nachvollziehbarkeit → dann per `RIS_AUDIT_DIR` einschalten. Default aus hält das Recherche-Tool schlank.
 - Wenn an: JSONL, eine Zeile pro Call (Tool, Params-Hash, Zeit, Trefferzahl) — **keine Volltexte/keine Client-Daten** loggen.
 
 ## 8b. Konkurrenz-Landschaft (Positioning)
 
 Es gibt bereits **zwei** RIS-MCPs auf PyPI:
 - **`at-eli-mcp`** (matematicsolutions) — Live-API, ELI/ECLI-Citations, nur `BgblAuth`+Judikatur, **kein konsolidiertes Recht, keine Fassung/Abschnitt/History**. (Der, den wir aktuell nutzen.)
 - **`ris-mcp`** v0.2.1 — **lokaler FTS5-SQLite-Mirror** von Judikatur + Bundesrecht (anderer Ansatz: offline-Volltextsuche statt Live-API).
 
 **Unser Differenzierungspotenzial (Lücke im Markt):** generisch über *alle* Applikationen (BrKons/Begut/RegV/Landesrecht), **§-genauer Zugriff (Abschnitt)**, **historischer Rechtsstand (FassungVom)**, **Änderungs-Monitoring** und **sauberes Markdown + raw** — das bietet keiner der beiden vollständig. Das rechtfertigt einen Neubau statt Fork.
 
 ---
 
 ## 9. Aufwandsschätzung (grob)
 
 | Bereich | Aufwand |
 |---|---|
 | Gerüst (pyproject, FastMCP, config, client, rate-limit) | 0,5 Tag |
 | models + mapping + citations (Envelope→flach) | 1 Tag |
 | textparse (HTML→Markdown, Fixtures) | 0,5–1 Tag |
 | 6 Tools + Verdrahtung | 1 Tag |
 | Tests (offline + smoke) + README/Lizenz | 1 Tag |
 | **v0.1 gesamt** | **~4–5 Tage** |
