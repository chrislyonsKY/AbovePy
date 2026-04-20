# Roadmap

**Core promise:** The fastest way for Kentucky GIS analysts, surveyors, and engineers to find, inspect, compare, and operationalize KyFromAbove data — in the tools they already use.

Priorities can shift based on community feedback and KyFromAbove program updates.

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
- **QGIS plugin (AboveQGIS)** — Processing toolbox provider with 4 tools (Search, Download, Mosaic, Hillshade). County dropdown (120 counties), product selector, map extent support. Auto-installs abovepy dependency. Available in Plugins menu and Processing Toolbox.

## v2.2 (Near Term)

**Theme: Deliverables, export formats, and oblique intelligence**

### Deliverable Packaging
- `SearchResult.package(output_dir, clip_bbox=None, include_preview=True)` → `Package`
- `Package` dataclass: files, manifest.json, footprints.gpkg, preview.png, provenance.json, DISCLAIMER.txt
- Manifest schema: file paths, checksums (SHA-256), CRS, acquisition dates, tile count, AOI WKT
- CLI: `abovepy package --county Franklin -o ./delivery`

### Export Formats
- **LAS point cloud export** — non-COPC LAS 1.4 for tools that can't read COPC (laspy)
- **GeoTIFF DEM packaging** — survey-grade metadata: EPSG:3089, NAVD88 vertical datum, US survey feet units

### Oblique Intelligence
- Fetch and cache JSON sidecar metadata (camera params, footprint, timestamp)
- Spatial search: `search_obliques(point=(-84.85, 38.19), radius_feet=500)`
- 4-direction bundle grouping: given a point, return best Bwd/Fwd/Left/Right frame set
- Rich `ObliqueFrame` dataclass with parsed metadata

### Platform Integration
- QGIS packaging tool — package output with GeoPackage + QGIS-friendly layer structure
- ArcGIS Pro packaging tool
- Richer STAC asset handling — expose all assets, runtime conformance checks, graceful CQL2 fallback

**Surfaces:** Python, CLI, ArcGIS Pro, QGIS
**Tests:** ~60 new tests

## v2.3 (Mid Term)

**Theme: Analysis APIs**

### Analysis APIs
- `abovepy.sample(point, product)` — elevation at a point
- `abovepy.profile(line, product)` — elevation along a transect
- `abovepy.zonal_stats(polygon, product)` — statistics within a polygon
- `abovepy.cut_fill(polygon, reference_elevation)` — volume calculation
- `abovepy.change_detection(bbox, product_before, product_after)` — difference map
- Phase comparison workflows (Phase 2 vs Phase 3 elevation change)

### Other
- Optional `SearchResult.to_xarray()` via `stackstac` or `odc-stac`
- Shareable MapLibre GL JS web viewer templates

**Surfaces:** Python, CLI, ArcGIS Pro, QGIS

## v3.0 (Long Term)

**Theme: TBD — scope set after v2.2 / v2.3 feedback.**

Candidate directions:
- Deeper analysis: corridor-aware workflows, multi-temporal change detection, volumetric pipelines
- Offline / cached data support for field use
- Server-side processing surfaces (TiTiler extensions, STAC-aware services)

Breaking API cleanup lands here. `to_landxml()` (deprecated in v2.2) is scheduled for removal in v3.0.

## Target Users

| Persona | Primary tools | Primary needs |
|---------|---------------|---------------|
| **Surveyor** | Python, QGIS, ArcGIS Pro | EPSG:3089, feet buffers, provenance, clean deliverables |
| **Civil engineer** | Python, ArcGIS Pro, QGIS | Corridor search, cut/fill, phase comparison, DEM surfaces, LAS import |
| **GIS analyst** | ArcGIS Pro, QGIS, Python | Broad search, QGIS interop, phase comparison, lazy loading |
| **Planner** | ArcGIS Pro, QGIS, web | County/area search, ortho access, flood screening |
| **Emergency management** | ArcGIS Pro, web, mobile | Rapid site assessment, oblique inspection, flood analysis |

## Platform Support

| Platform | v2.1 (Done) | v2.2 | v2.3 | v3.0 |
|----------|-------------|------|------|------|
| **Python library** | Full | Full | Full | Full |
| **CLI** | Full | +package | +analysis | Full |
| **ArcGIS Pro** | Toolbox (5 tools) | +packaging | +analysis | maintained |
| **QGIS** | Plugin v1 (4 tools) | +packaging | +analysis | maintained |

## Non-Goals

- Generic STAC client functionality (use pystac-client directly)
- Non-Kentucky data sources
- Reimplementing PDAL, stackstac, or TiTiler
- Native plugins or add-ins for CAD platforms (Civil 3D, Carlson, OpenRoads Designer, MicroStation). Generic file-format interop (GeoTIFF, LAS, GeoPackage) is in scope; design-tool-specific integration is not.
