# Roadmap

**Core promise:** The fastest way for Kentucky GIS analysts, planners, and researchers to find, inspect, compare, and operationalize KyFromAbove data — in the tools they already use.

Priorities can shift based on community feedback and KyFromAbove program updates.

> **Scope note (v2.2):** The engineering-deliverables direction (LandXML/CAD
> surface interchange, LAS export, survey-grade deliverable packaging) has
> been removed from the roadmap. See Non-Goals below.

## v2.0 (Released)

- `SearchResult` workflow object replacing bare GeoDataFrame returns
- Enhanced STAC search with CQL2, intersects, sortby, ids, fields
- Kentucky area selectors: point+buffer, custom geometry
- Concurrent and resumable downloads
- Cloud-native COPC reads via laspy CopcReader
- CLI that does real work: estimate, search summaries, concurrent downloads
- ArcGIS Pro toolbox updated with concurrent downloads and size estimates
- Community health documents and docs site on Zensical

## v2.1 (Released)

**Theme: Engineering-grade CRS, provenance, safety, and QGIS**

- First-class EPSG:3089 support — feet-based point+buffer, corridor/centerline buffers, polygon clip workflows
- Strong CRS and units validation with explicit warnings
- `SearchResult.provenance()` — source URLs, acquisition dates, CRS, AOI record, tile counts, estimated size
- `SearchResult.validate()` — mixed-phase warnings, coverage gap detection, nodata summaries
- Download integrity — content-length validation, hierarchical filenames to prevent collisions
- Remote read safety — file-size guards, URL allowlist for known KyFromAbove hosts
- Product metadata — acquisition date ranges, source program attribution, QA status
- Security hardening — path traversal protection, SSRF prevention, URL injection validation, S3 bucket validation, json.dumps for algorithm params
- CI hardening — all GitHub Actions pinned to SHAs, CodeQL, dependency review
- CLI enhancements — `--buffer-feet` flag, `--format provenance` output, automatic validation warnings
- `buffer_feet()` and `corridor_buffer()` exported at top level
- **QGIS plugin (AboveQGIS)** — Processing toolbox provider with 6 tools. County dropdown (120 counties), product selector, map extent support. Auto-installs abovepy dependency. Available in Plugins menu and Processing Toolbox.

## v2.2 (Released)

**Theme: Oblique intelligence, analysis APIs, richer STAC assets, shareable web maps**

### Oblique Intelligence
- `ObliqueFrame` dataclass with parsed JSON sidecar metadata (camera params, footprint, timestamp) — raw payload always preserved
- Spatial search: `search_obliques(point=(-84.85, 38.19), radius_feet=500)` — nearest-first
- 4-direction bundle grouping: `oblique_bundle(point)` → best Bwd/Fwd/Left/Right frame set
- Bulk per-season exposure-center index when available; bounded concurrent sidecar fetches otherwise
- Trusted-host URL validation on all oblique S3 and sidecar requests

### Analysis APIs (pulled forward from v2.3)
- `abovepy.sample(point)` — elevation at point(s)
- `abovepy.profile(line)` — elevation along a transect, distances in true feet
- `abovepy.zonal_stats(polygon)` — statistics within a polygon
- `abovepy.change_detection(bbox, product_before, product_after)` — difference map with automatic grid alignment

### Richer STAC Assets
- `assets` column exposing every asset per item (thumbnails, metadata, alternates)
- Runtime CQL2 conformance check with actionable errors and offline-safe fallback

### Viz & Interop
- `SearchResult.to_xarray()` via odc-stac (`pip install abovepy[xarray]`)
- `export_map_html()` — self-contained shareable MapLibre GL JS viewers
- CLI: `sample`, `profile`, `export-map` subcommands

### Removed
- `to_landxml()` deleted (see CHANGELOG — engineering scope retracted)

## v2.3 (Near Term)

**Theme: Deeper analysis workflows and platform reach**

- QGIS Processing algorithms for oblique search and sample/profile (once the v2.2 APIs stabilize against the real sidecar schema)
- Oblique sidecar schema hardening — replace tolerant multi-key parsing with the confirmed schema; bulk EO index fast path
- Phase comparison workflows (Phase 2 vs Phase 3 elevation change summaries)
- Flood screening helpers built on `change_detection`/`zonal_stats`
- CLI: `zonal-stats` with GeoJSON polygon input (if validated)
- Parcel-based and route/corridor-based search (if validated)

## v3.0 (Long Term)

**Theme: TBD — scope set after v2.3 feedback.**

Candidate directions:
- Deeper analysis: corridor-aware workflows, multi-temporal change detection
- Offline / cached data support for field use
- Server-side processing surfaces (TiTiler extensions, STAC-aware services)

Breaking API cleanup lands here (the `to_landxml` error shim added in v2.2 is removed).

## Target Users

| Persona | Primary tools | Primary needs |
|---------|---------------|---------------|
| **GIS analyst** | ArcGIS Pro, QGIS, Python | Broad search, QGIS interop, phase comparison, lazy loading |
| **Planner** | ArcGIS Pro, QGIS, web | County/area search, ortho access, flood screening, shareable maps |
| **Emergency management** | ArcGIS Pro, web, mobile | Rapid site assessment, oblique inspection, flood analysis |
| **Researcher** | Python, Jupyter | xarray access, terrain analysis, change detection |
| **Surveyor / civil engineer** | Python, QGIS, ArcGIS Pro | EPSG:3089, feet buffers, provenance (data access only — see Non-Goals) |

## Platform Support

| Platform | v2.1 | v2.2 (Done) | v2.3 | v3.0 |
|----------|------|-------------|------|------|
| **Python library** | Full | Full | Full | Full |
| **CLI** | Full | +sample/profile/export-map | +analysis | Full |
| **ArcGIS Pro** | Toolbox (5 tools) | maintained | maintained | maintained |
| **QGIS** | Plugin v1 (6 tools) | maintained | +oblique/analysis tools | maintained |

## Non-Goals

- Generic STAC client functionality (use pystac-client directly)
- Non-Kentucky data sources
- Reimplementing PDAL, stackstac, or TiTiler
- Native plugins or add-ins for CAD platforms (Civil 3D, Carlson, OpenRoads Designer, MicroStation)
- **Survey/engineering deliverable production** — LandXML/CAD surface interchange, LAS export, survey-grade GeoTIFF metadata, and manifest-based deliverable packaging are out of scope. abovepy provides data *access* for engineering users (EPSG:3089 geometry, provenance); producing stamped deliverables belongs in dedicated tooling.
