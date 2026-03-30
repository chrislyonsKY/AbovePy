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

**Theme: Deliverables, oblique intelligence, design-tool formats**

- `SearchResult.package()` — clipped DEMs, orthos, point clouds bundled with footprints, previews, manifest, provenance, and disclaimer
- **CAD/survey export formats** — LandXML surfaces (Civil 3D / Carlson), contour DXF, LAS point clouds (non-COPC for older tools), GeoTIFF DEMs with survey-grade metadata
- Package outputs consumable by Python, ArcGIS Pro, QGIS, Civil 3D, Carlson, and ORD
- Oblique spatial search by point/AOI with nearest-frame selection
- 4-direction oblique bundles for site inspection
- JSON sidecar parsing for camera metadata, footprints, and timestamps
- QGIS interoperability — GeoPackage outputs, GeoParquet indexes, QGIS-friendly layer packaging
- Richer STAC asset handling — expose all assets, runtime conformance checks, graceful CQL2 fallback
- ArcGIS Pro toolbox — packaging tool, oblique inspection tool

## v2.3 (Long Term)

**Theme: Analysis APIs, Civil 3D plugin, advanced workflows**

- Stable analysis APIs: `sample`, `profile`, `zonal_stats`, `cut_fill`, `change_detection`, `flood_fill`
- Phase comparison workflows (Phase 2 vs Phase 3 elevation change)
- **Civil 3D plugin prototype** — ribbon button / tool palette for "Get KyFromAbove data for this drawing extent." Delivers DEM surface and point cloud directly into the active drawing. Targets AutoCAD App Store distribution.
- Optional xarray/dask bridge for lazy array loading (`pip install abovepy[xarray]`)
- Shareable web viewer templates (MapLibre GL JS)
- Parcel-based and route/corridor-based search (if validated)

## v3.0 (Future)

**Theme: Native design-tool integration**

- **Carlson Software plugin** — menu command for KyFromAbove surface/point cloud import. Targets Carlson's large Kentucky surveyor user base.
- **OpenRoads Designer / MicroStation addin** — .NET addin for terrain import, corridor-aware data retrieval. Targets KYTC and Bentley-shop engineers.
- Unified plugin architecture — shared AOI extraction, product selection dialog, and format negotiation across all platforms
- Offline/cached data support for field use

## Target Users

| Persona | Primary tools | Primary needs |
|---------|---------------|---------------|
| **Surveyor** | Civil 3D, Carlson | EPSG:3089, feet buffers, LandXML surfaces, provenance, clean deliverables |
| **Civil engineer** | Civil 3D, ORD, Carlson | Corridor search, cut/fill, phase comparison, DEM surfaces, LAS import |
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
| **Civil 3D** | — | — | File import (LandXML, DXF) | Plugin prototype | Plugin v1 |
| **Carlson** | — | — | File import (LandXML, DXF) | — | Plugin v1 |
| **ORD / MicroStation** | — | — | File import (GeoTIFF, LAS) | — | Addin v1 |

## Non-Goals

- Generic STAC client functionality (use pystac-client directly)
- Non-Kentucky data sources
- Reimplementing PDAL, stackstac, or TiTiler
- Building CAD/BIM editing features (abovepy delivers data, not design tools)
