# Roadmap

**Core promise:** The fastest way for Kentucky GIS analysts, surveyors, and engineers to find, inspect, compare, and operationalize KyFromAbove data.

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

**Theme: Engineering-grade CRS, provenance, and safety**

- First-class EPSG:3089 support — feet-based point+buffer, corridor/centerline buffers, polygon clip workflows
- Strong CRS and units validation with explicit warnings
- `SearchResult.provenance()` — source URLs, acquisition dates, CRS, AOI record, tile counts, estimated size
- `SearchResult.validate()` — mixed-phase warnings, coverage gap detection, nodata summaries
- Download integrity — content-length validation, hierarchical filenames to prevent collisions
- Remote read safety — file-size guards, URL allowlist for known KyFromAbove hosts
- Product metadata — acquisition date ranges, source program attribution, QA status
- CI hardening — pin GitHub Actions to SHAs, CodeQL, dependency review, Trusted Publishing

## v2.2 (Mid Term)

**Theme: Deliverables, oblique intelligence, cross-platform**

- `SearchResult.package()` — clipped DEMs, orthos, point clouds bundled with footprints, previews, manifest, provenance, and disclaimer
- Package outputs consumable by Python, ArcGIS Pro, QGIS, and CLI
- Oblique spatial search by point/AOI with nearest-frame selection
- 4-direction oblique bundles for site inspection
- JSON sidecar parsing for camera metadata, footprints, and timestamps
- QGIS interoperability — GeoPackage outputs, GeoParquet indexes, QGIS-friendly layer packaging
- Richer STAC asset handling — expose all assets, runtime conformance checks, graceful CQL2 fallback
- ArcGIS Pro toolbox — packaging tool, oblique inspection tool

## v2.3 (Long Term)

**Theme: Analysis APIs and advanced workflows**

- Stable analysis APIs: `sample`, `profile`, `zonal_stats`, `cut_fill`, `change_detection`, `flood_fill`
- Phase comparison workflows (Phase 2 vs Phase 3 elevation change)
- Optional xarray/dask bridge for lazy array loading (`pip install abovepy[xarray]`)
- Shareable web viewer templates (MapLibre GL JS)
- Parcel-based and route/corridor-based search (if validated)

## Target Users

| Persona | Primary needs |
|---------|---------------|
| **Surveyor** | EPSG:3089, feet-based buffers, provenance, clean deliverables |
| **Civil engineer** | Corridor search, cut/fill, phase comparison, packaging |
| **GIS analyst** | Broad search, QGIS interop, phase comparison, lazy loading |
| **Planner** | County/area search, ortho access, flood screening |
| **Emergency management** | Rapid site assessment, oblique inspection, flood analysis |

## Non-Goals

- Generic STAC client functionality (use pystac-client directly)
- Non-Kentucky data sources
- Reimplementing PDAL, stackstac, or TiTiler
- ArcGIS Pro as the primary surface (supported, not dominant)
