# abovepy Product Roadmap — Now / Next / Later

**Core promise:** "Give me the right Kentucky data for this site, in the right CRS/units, in the tools I already use."

> **Scope note:** The engineering-deliverables direction (LandXML/CAD surface
> interchange, LAS export, survey-grade deliverable packaging) was removed
> from the roadmap in v2.2. `to_landxml()` was deleted; see CHANGELOG 2.2.0
> and the Non-Goals section of ROADMAP.md.

## Shipped

### v2.1 — Engineering-grade CRS, provenance, safety, QGIS
`buffer_feet()`/`corridor_buffer()`, `SearchResult.provenance()`/`.validate()`,
download integrity, remote-read safety, security + CI hardening, AboveQGIS
plugin, CLI `--buffer-feet`/provenance output.

### v2.2 — Oblique intelligence, analysis APIs, STAC assets, web maps
- **Obliques:** `ObliqueFrame` (Mapping-compatible, tolerant sidecar parsing),
  `search_obliques(point=, radius_feet=)` spatial search with a three-tier
  fetch strategy (bulk EO index → bounded sidecar fetches → precise footprint
  filter), `oblique_bundle()` 4-direction site-inspection sets.
- **Analysis:** top-level `sample()`, `profile()`, `zonal_stats()`,
  `change_detection()` — streamed windowed reads, no downloads.
- **STAC:** all assets exposed per item (`assets` column); runtime CQL2
  conformance check with actionable `SearchError` fallback.
- **Viz:** `SearchResult.to_xarray()` via odc-stac (`[xarray]` extra);
  `export_map_html()` shareable MapLibre viewers; CLI `sample`/`profile`/
  `export-map`.
- **Removed:** `to_landxml()` (error shim remains through 2.2.x).

## NOW — v2.3 groundwork

1. **Confirm the oblique sidecar schema** against live data (run the
   integration tests; replace tolerant multi-key parsing with the confirmed
   schema; wire the ExteriorOrientationFiles bulk index fast path).
2. **QGIS Processing algorithms** for oblique search and sample/profile,
   built on the now-stable v2.2 APIs.
3. **Phase comparison workflows** — packaged Phase 2 vs Phase 3 change
   summaries on top of `change_detection()`.

## NEXT

- Flood screening helpers (`change_detection` + `zonal_stats` compositions)
- CLI `zonal-stats` with GeoJSON polygon input (if validated)
- Parcel-based and route/corridor-based search (if validated)

## LATER — v3.0

- Breaking API cleanup (drop the `to_landxml` error shim)
- Offline / cached data support for field use
- Server-side processing surfaces (TiTiler extensions, STAC-aware services)

## Structural notes for contributors

- Oblique parsing is isolated in `obliques/_metadata.py` — fixing the schema
  means editing the candidate-key chains in one file; the raw sidecar dict is
  always preserved on `ObliqueFrame.raw`.
- Analysis functions orchestrate `abovepy.search()` + `io/cog.read_cog()`;
  tests mock `abovepy.search` and `abovepy.analysis._read_aoi` with synthetic
  DEM fixtures — no network in the default test run.
- `SearchResult` carries pystac Items (`items=`) to power `to_xarray()`;
  results built from bare GeoDataFrames still work everywhere else.
