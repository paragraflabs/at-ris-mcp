# Changelog

All notable changes to **at-ris-mcp** are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/), and this
project adheres to [Semantic Versioning](https://semver.org/).

## [1.0.1] - 2026-07-24

### Added
- **Landesrecht fine filters** on `ris_search_state_law`: `lgblnummer` +
  `kundmachung_von`/`bis` (LgblAuth/Lgbl); `einbringer`, `kundmachungsnummer` +
  `kundmachung_von`/`bis` (Vbl); `gliederungszahl` + `ausgabedatum_von`/`bis`
  (LgblNO). Filters are only emitted for the relevant application and use the
  correct per-app date base (`Kundmachung` vs `Kundmachungsdatum` vs
  `Ausgabedatum`).

### Changed
- CI: bumped GitHub Actions to current majors (checkout v7, setup-python v7,
  upload-artifact v7, download-artifact v8), removing the Node.js 20
  deprecation warning.
- Release: the MCP-registry workflow now auto-syncs `server.json` to the tag
  version on tagged builds, so it can no longer drift.

## [1.0.0] - 2026-07-24

### Added
- **English translations (`Erv`)** via `ris_search_law` (`applikation="Erv"`),
  mapping the distinct RIS parameter names (`SearchTerms`/`Title`/`Source`).
- **`Sonstige` fine filters** on `ris_search_misc`: app-specific numbers and
  dates — `avsvnummer`/`dokumentart`/`urheber` (Avsv), `avnnummer` (Avn),
  `spgnummer` (Spg), `gericht` (KmGer), `partei`/`gz` (Upts),
  `einbringer`/`sitzungsnummer`/`gesetzgebungsperiode` (Mrp), plus app-aware
  `kundmachung_von`/`bis` date fields.
- Packaging: `py.typed` markers, richer classifiers/keywords, sdist config,
  `CHANGELOG.md`, MCP-registry `server.json`, GitHub Actions CI
  (test matrix 3.11–3.13 + build/twine check).
- SPDX license headers on all source files.

## [0.3.0] - 2026-07-24

### Added
- **Landesrecht** (`ris_search_state_law`): 9 Bundesländer; `LrKons`,
  `LgblAuth`, `Lgbl`, `LgblNO`, `Vbl`. State selection via `bundeslaender`
  (dotted `Bundesland.SucheIn<Land>` flags — the flat form is ignored by the API
  for `LrKons`).
- **Sonstige** (`ris_search_misc`): `Erlaesse`, `Avsv`, `Spg`, `KmGer`, …
- **Bezirke** (`ris_search_district`): `Bvb`.
- **Gemeinden** (`ris_search_municipality`): `Gr`, `GrA`.
- Generic record mapping across all metadata categories; `LawRecord` gains
  `bundesland`/`gemeinde`/`geschaeftszahl`.

## [0.2.0] - 2026-07-24

### Added
- **History change-feed** (`ris_list_changes`) via the OGD SOAP endpoint,
  incl. `include_deleted`. Consolidated federal law is monitored as
  `Bundesnormen` (not `BrKons`).
- Broader **Begut/RegV** filters (`einbringende_stelle`, `in_begutachtung_am`,
  `beschluss_von`/`bis`).

## [0.1.0] - 2026-07-24

### Added
- Initial release: standalone `ris_client` library + thin `ris_mcp` FastMCP
  wrapper. Tools: `ris_search_law`, `ris_get_law_text`, `ris_search_case`,
  `ris_get_case_text`, `ris_list_collections`. SQLite cache, rate limiting,
  descriptive User-Agent, HTML→Markdown with `raw` switch, CC-BY attribution +
  legal notice on every response.
