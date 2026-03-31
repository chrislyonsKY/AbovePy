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

### CAD/Survey Export Formats
- **LandXML surface export** — TIN triangulation from DEM via rasterio + scipy, output as LandXML 1.2. This is the universal format Civil 3D, Carlson, and OpenRoads all import natively.
- **Contour DXF export** — contour lines as DXF polylines via ezdxf library. Consumable by every CAD platform.
- **LAS point cloud export** — non-COPC LAS 1.4 for older tools that can't read COPC (laspy)
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
**New dependencies:** `ezdxf` (DXF export), `scipy` (TIN triangulation)
**Tests:** ~60 new tests

## v2.3 (Mid Term)

**Theme: Analysis APIs and Civil 3D prototype**

### Analysis APIs
- `abovepy.sample(point, product)` — elevation at a point
- `abovepy.profile(line, product)` — elevation along a transect
- `abovepy.zonal_stats(polygon, product)` — statistics within a polygon
- `abovepy.cut_fill(polygon, reference_elevation)` — volume calculation
- `abovepy.change_detection(bbox, product_before, product_after)` — difference map
- Phase comparison workflows (Phase 2 vs Phase 3 elevation change)

### Civil 3D Plugin Prototype
- .NET 8.0 C# plugin for AutoCAD Civil 3D 2025+
- Ribbon button: "Get KyFromAbove Data"
- AOI from drawing extent or user-picked polygon/polyline
- Product selector dropdown matching abovepy products
- Calls abovepy CLI via subprocess → generates LandXML + LAS package
- Auto-imports TIN Surface and point cloud into active drawing
- Targets Autodesk App Store distribution

### Other
- Optional `SearchResult.to_xarray()` via `stackstac` or `odc-stac`
- Shareable MapLibre GL JS web viewer templates

**Surfaces:** Python, CLI, ArcGIS Pro, QGIS, Civil 3D (prototype)

## v3.0 (Long Term)

**Theme: Native design-tool integration**

All CAD plugins use a shared file-based architecture: abovepy generates LandXML, LAS, GeoTIFF, and DXF outputs → thin platform wrappers import them into each host application.

### Civil 3D Plugin v1 (.NET C#)
- "AboveC3D" ribbon tab: Get Data, Package Site, Import Surface
- AOI from drawing extent or user-picked polyline/polygon
- Product picker dropdown
- Auto-creates Civil 3D TIN Surface from LandXML, loads point cloud from LAS
- Corridor-aware data retrieval
- Distribution: Autodesk App Store

### Carlson Plugin v1 (AutoLISP + batch)
- "AboveKY" menu in Carlson Survey / Civil / Mining
- Commands: ABOVEKY_SEARCH, ABOVEKY_DOWNLOAD, ABOVEKY_SURFACE
- LISP calls abovepy CLI via shell → imports LandXML DTM
- Distribution: installer package, Carlson reseller channel
- Target: Kentucky's large surveyor user base

### OpenRoads Designer / MicroStation Addin (Python)
- Uses MicroStation 2024+ native Python API
- "KyFromAbove" script category: Get Terrain, Get Imagery, Get Point Cloud
- Calls abovepy directly (pip-installed in MicroStation Python) or via subprocess
- Imports LandXML as terrain model
- Distribution: Bentley Developer Network or manual install

### Cross-Platform Architecture
```
abovepy package CLI
  └── Outputs: LandXML, LAS, GeoTIFF, DXF, manifest.json
       ├── Civil 3D plugin reads LandXML → creates TIN Surface
       ├── Carlson command reads LandXML → creates DTM
       └── ORD script reads LandXML → creates terrain model
```

## Target Users

| Persona | Primary tools | Primary needs |
|---------|---------------|---------------|
| **Surveyor** | Civil 3D, Carlson | EPSG:3089, feet buffers, LandXML surfaces, provenance, clean deliverables |
| **Civil engineer** | Civil 3D, ORD, Carlson | Corridor search, cut/fill, phase comparison, DEM surfaces, LAS import |
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
| **Civil 3D** | — | File import (LandXML) | Plugin prototype | Plugin v1 |
| **Carlson** | — | File import (LandXML) | — | Plugin v1 |
| **ORD / MicroStation** | — | File import (LandXML, LAS) | — | Python scripts |

## Non-Goals

- Generic STAC client functionality (use pystac-client directly)
- Non-Kentucky data sources
- Reimplementing PDAL, stackstac, or TiTiler
- Building CAD/BIM editing features (abovepy delivers data, not design tools)
