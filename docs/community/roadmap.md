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

## v2.1 (Near Term)

**Theme: Engineering-grade CRS, provenance, safety, and QGIS**

- First-class EPSG:3089 support — feet-based point+buffer, corridor/centerline buffers, polygon clip workflows
- Strong CRS and units validation with explicit warnings
- `SearchResult.provenance()` — source URLs, acquisition dates, CRS, AOI record, tile counts, estimated size
- `SearchResult.validate()` — mixed-phase warnings, coverage gap detection, nodata summaries
- Download integrity — content-length validation, hierarchical filenames to prevent collisions
- Remote read safety — file-size guards, URL allowlist for known KyFromAbove hosts
- Product metadata — acquisition date ranges, source program attribution, QA status
- CI hardening — pin GitHub Actions to SHAs, CodeQL, dependency review, Trusted Publishing
- **QGIS plugin (AboveQGIS)** — Processing toolbox provider with tools for search, download, mosaic, and hillshade. Draw extent or pick county from dropdown, select product, get data loaded into your QGIS project. Distributed via QGIS Plugin Repository. Built on abovepy core, no separate codebase to maintain.

## v2.2 (Mid Term)

**Theme: Deliverables, oblique intelligence**

- `SearchResult.package()` — clipped DEMs, orthos, point clouds bundled with footprints, previews, manifest, provenance, and disclaimer
- **Export formats** — LAS point clouds (non-COPC for tools that can't read COPC), GeoTIFF DEMs with survey-grade metadata (EPSG:3089, NAVD88, US survey feet)
- Package outputs consumable by Python, ArcGIS Pro, and QGIS
- Oblique spatial search by point/AOI with nearest-frame selection
- 4-direction oblique bundles for site inspection
- JSON sidecar parsing for camera metadata, footprints, and timestamps
- QGIS interoperability — GeoPackage outputs, GeoParquet indexes, QGIS-friendly layer packaging
- Richer STAC asset handling — expose all assets, runtime conformance checks, graceful CQL2 fallback
- ArcGIS Pro toolbox — packaging tool, oblique inspection tool
- `to_landxml()` deprecation notice (removal scheduled for v3.0)

## v2.3 (Long Term)

**Theme: Analysis APIs, advanced workflows**

- Stable analysis APIs: `sample`, `profile`, `zonal_stats`, `cut_fill`, `change_detection`, `flood_fill`
- Phase comparison workflows (Phase 2 vs Phase 3 elevation change)
- Optional xarray/dask bridge for lazy array loading (`pip install abovepy[xarray]`)
- Shareable web viewer templates (MapLibre GL JS)
- Parcel-based and route/corridor-based search (if validated)

## v3.0 (Future)

**Theme: TBD — scope set after v2.2 / v2.3 feedback.**

Candidate directions:
- Deeper analysis: corridor-aware workflows, multi-temporal change detection, volumetric pipelines
- Offline / cached data support for field use
- Server-side processing surfaces (TiTiler extensions, STAC-aware services)

Breaking API cleanup lands here. `to_landxml()` is scheduled for removal in v3.0.

## Target Users

| Persona | Primary tools | Primary needs |
|---------|---------------|---------------|
| **Surveyor** | Python, QGIS, ArcGIS Pro | EPSG:3089, feet buffers, provenance, clean deliverables |
| **Civil engineer** | Python, ArcGIS Pro, QGIS | Corridor search, cut/fill, phase comparison, DEM surfaces, LAS import |
| **GIS analyst** | ArcGIS Pro, QGIS, Python | Broad search, QGIS interop, phase comparison, lazy loading |
| **Planner** | ArcGIS Pro, QGIS, web | County/area search, ortho access, flood screening |
| **Emergency management** | ArcGIS Pro, web, mobile | Rapid site assessment, oblique inspection, flood analysis |

## Platform Support

| Platform | Current | v2.1 | v2.2 | v2.3 | v3.0 |
|----------|---------|------|------|------|------|
| **Python library** | Full | Full | Full | Full | Full |
| **CLI** | Full | Full | Full | Full | Full |
| **ArcGIS Pro** | Toolbox (5 tools) | +provenance | +packaging, +oblique | +analysis | maintained |
| **QGIS** | File interop | Plugin v1 (Processing tools) | +packaging, +oblique | +analysis | maintained |

## Non-Goals

- Generic STAC client functionality (use pystac-client directly)
- Non-Kentucky data sources
- Reimplementing PDAL, stackstac, or TiTiler
- Native plugins or add-ins for CAD platforms (Civil 3D, Carlson, OpenRoads Designer, MicroStation). Generic file-format interop (GeoTIFF, LAS, GeoPackage) is in scope; design-tool-specific integration is not.
