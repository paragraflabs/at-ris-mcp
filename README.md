# at-ris-mcp

A generic **MCP server** and standalone **Python client library** for the
Austrian **RIS** (Rechtsinformationssystem des Bundes), the official legal
information system of the Republic of Austria, operated by the Bundeskanzleramt.

It covers **federal law** (Bundesrecht — including *consolidated* law `BrKons`,
the official gazettes, drafts and government bills) and **case law**
(Judikatur — OGH, VfGH, VwGH, BVwG, LVwG and more) via the keyless OGD API at
`https://data.bka.gv.at/ris/api/v2.6/`.

## Why this exists

Compared with existing RIS tooling, `at-ris-mcp` adds:

- **Consolidated law** (`BrKons`) — the currently applicable text, not just the
  gazette novellas.
- **Section-precise access** — retrieve a single `§`/Artikel/Anlage
  (`Abschnitt.*`).
- **Historical version** — the law as it stood on a given date
  (`Fassung.FassungVom`).
- **Clean Markdown** — RIS HTML (≈40 KB of CSS boilerplate per document) is
  stripped to the legal text, with a `raw` switch for the untouched original.

## Two packages, one repo

- **`ris_client`** — a standalone, MCP-independent library. Import it directly.
- **`ris_mcp`** — a thin FastMCP/stdio wrapper exposing 6 tools. Contains no
  logic of its own.

## Install

```bash
pip install at-ris-mcp          # library only
pip install "at-ris-mcp[mcp]"   # + the MCP server (FastMCP)
```

## Run the MCP server (stdio)

```bash
at-ris-mcp
# or
python -m ris_mcp
```

### Tools

| Tool | Purpose |
|---|---|
| `ris_search_law` | Search Bundesrecht (default `BrKons`; also `BgblAuth`, `Begut`, `RegV`, …). Section + Fassung filters. |
| `ris_get_law_text` | Full text of a statute/section (markdown \| html \| xml \| raw). |
| `ris_search_case` | Search Judikatur (default `Justiz`; all courts). Filter by applied `norm`. |
| `ris_get_case_text` | Full text of a decision. |
| `ris_search_state_law` | Search Landesrecht (9 Bundesländer; default `LrKons`). Select states via `bundeslaender`. |
| `ris_search_misc` | Search `Sonstige` (ministerial decrees `Erlaesse`, `Avsv`, …). |
| `ris_search_district` | Search district authority notices (`Bezirke` / `Bvb`). |
| `ris_search_municipality` | Search municipal law (`Gemeinden` / Gemeinderecht `Gr`/`GrA`). |
| `ris_list_collections` | Which endpoints/applications are covered. |
| `ris_list_changes` | Change/early-warning feed (RIS History) via the OGD SOAP endpoint, incl. deleted documents. |

## Library usage

```python
import asyncio
from ris_client import RisClient, LawSearchRequest, TextFormat

async def main():
    async with RisClient() as c:
        res = await c.search_law(LawSearchRequest(suchworte="Datenschutzgesetz",
                                                  page_size="Ten"))
        hit = res.items[0]
        print(hit.human_readable_citation, hit.eli_uri)
        text = await c.get_text(hit.content_urls["html"], TextFormat.markdown)
        print(text.content[:500])

asyncio.run(main())
```

## Configuration (environment variables)

| Variable | Default | Meaning |
|---|---|---|
| `RIS_BASE_URL` | `https://data.bka.gv.at/ris/api/v2.6` | API base (version isolation). |
| `RIS_SOAP_URL` | `https://data.bka.gv.at/ris/ogd/v2.6/` | OGD SOAP endpoint (used by `ris_list_changes`). |
| `RIS_USER_AGENT` | `at-ris-mcp/<version> (+…)` | Descriptive UA (netiquette). |
| `RIS_RATE_MS` | `1200` | Minimum delay between requests (ms). |
| `RIS_TIMEOUT_S` | `30` | HTTP timeout. |
| `RIS_MAX_RETRIES` | `3` | Retries on 429/5xx (incl. 503). |
| `RIS_CACHE_DIR` | `~/.cache/at-ris-mcp` | SQLite cache location. |
| `RIS_CACHE_ENABLED` | `true` | Toggle the cache. |
| `RIS_AUDIT_DIR` | *(unset)* | If set, append a JSONL audit line per call (no full text, no client data). |

## Netiquette & rate limiting

Per the RIS OGD FAQ: a 1–2 s pause per page is enforced by the client; bulk
access should occur outside office hours (18:00–06:00) or on weekends and be
announced to `ris.it@bka.gv.at`. A descriptive User-Agent is sent by default.

## Licensing

- **Code:** Apache-2.0 (see `LICENSE`).
- **Data:** the retrieved documents are provided by the Republic of Austria
  under **CC BY 4.0**. Every tool response carries an `attribution` field:

  > Quelle: RIS – Rechtsinformationssystem des Bundes (data.bka.gv.at), CC BY 4.0

- **No legal advice.** Only the authentic promulgation text
  (Bundesgesetzblatt/Landesgesetzblatt authentisch) is legally binding.
  Consolidated law and all other documents are for information only. Every
  response carries a `legal_notice` to that effect.

## Scope (v0.3)

Covered: `Bundesrecht` (`BrKons`, `BgblAuth`, `BgblPdf`, `BgblAlt`, `Begut`,
`RegV`, `Erv`), `Judikatur` (all courts), the **History change-feed**
(`ris_list_changes`, incl. deleted documents), **Landesrecht** (9 Bundesländer:
`LrKons`, `LgblAuth`, `Lgbl`, `LgblNO`, `Vbl`), **Sonstige** (`Erlaesse`,
`Avsv`, `Spg`, `KmGer`, …), **Bezirke** (`Bvb`) and **Gemeinden** (`Gr`, `GrA`).

> **State-law note:** for consolidated state law (`LrKons`), select the states
> via `bundeslaender` (e.g. `["Kaernten","Tirol"]`); this maps to the dotted
> `Bundesland.SucheIn<Land>=true` flags the API requires (the flat form is
> silently ignored for `LrKons`).

> **History note:** consolidated federal law is monitored under the application
> name `Bundesnormen` (not `BrKons`), consolidated state law under
> `Landesnormen`. The History query uses the OGD **SOAP** endpoint, since it is
> not exposed via the REST GET API.

## Development

```bash
pip install -e ".[dev,mcp]"
pytest                       # offline tests
RIS_SMOKE=1 pytest -m smoke  # live smoke tests against the real API
```
