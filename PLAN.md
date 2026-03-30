# abovepy Product Roadmap — Now / Next / Later

**Core promise:** "Give me the right Kentucky data for this site, in the right CRS/units, packaged cleanly."

## Validation of direction

The codebase is strong — SearchResult, concurrent downloads, COPC reads, TiTiler integration, oblique discovery, ArcGIS toolbox, 318 tests. The product thesis (Kentucky-specific workbench, not generic STAC wrapper) is correct and the code already reflects it.

**What the code fights in the proposed roadmap:**
1. **CRS:** Everything works in EPSG:4326 internally. EPSG:3089 is metadata-only. Feet-based buffering uses a rough miles-to-degrees hack. No corridor/polygon clip support.
2. **Packaging:** Export has 3 format writers but zero packaging concept — no manifest, no provenance, no multi-file bundles.
3. **Obliques:** Direction+season enumeration only. JSON sidecars (which contain georeferencing/metadata) are URL-only, never fetched or parsed.
4. **Product metadata:** No acquisition dates, source attribution, QA flags — just product type/format/resolution.
5. **Download integrity:** Basename-only naming (collision risk), no content-length validation, no checksums.
6. **CI security:** Actions on floating tags, API token auth (not Trusted Publishing), no CodeQL.

None of these are blocking — they're all additive changes on a solid foundation.

---

## NOW — v2.1 (ship within 2 weeks)

Highest-value slice that doesn't over-expand scope. All are code changes to existing modules.

### 1. Kentucky Engineering Geometry (utils/crs.py, client.py)
- `buffer_feet(geometry, feet, crs="EPSG:3089")` — reproject to 3089, buffer, reproject back
- `corridor_buffer(line, width_feet)` — LineString + width in feet → polygon
- Update `client.search()`: accept `buffer_feet=` alongside existing `buffer_miles=`
- Add `crs="EPSG:3089"` option to `search()` that keeps bbox/geometry in native CRS
- Explicit CRS/units warnings when mixing coordinate systems

### 2. QA / Provenance on SearchResult (result.py, products.py)
- Add to `Product` dataclass: `acquisition_year_start`, `acquisition_year_end`, `source_program`
- New `SearchResult.provenance()` → dict with: source URLs, acquisition dates, CRS, tile count, estimated size, AOI record, mixed-phase warnings, coverage gap detection
- New `SearchResult.validate()` → list of warnings (mixed phases, nodata, coverage gaps, CRS mismatches)

### 3. Download Integrity (_download.py)
- Validate `Content-Length` header against downloaded bytes
- Hierarchical filenames: `{product}/{tile_id}.ext` instead of basename-only
- Log warnings for size mismatches

### 4. Remote Read Safety (io/pointcloud.py, io/cog.py)
- HEAD request size check in `_read_remote()` before full download
- Configurable `max_remote_size_mb` (default 500)
- URL allowlist: default to `*.s3.amazonaws.com`, `*.execute-api.us-west-2.amazonaws.com`
- Auto-fallback to `read_copc()` for COPC files instead of full download

### 5. CI Hardening (.github/workflows/)
- Pin all actions to commit SHAs
- Add CodeQL workflow
- Add dependency review on PRs
- Migrate PyPI publish to Trusted Publishing (OIDC)

**Surfaces:** Python, CLI (--buffer-feet, provenance output)
**Tests:** ~40 new tests
**Breaking:** None

---

## NEXT — v2.2 (4-6 weeks)

### 6. Deliverable Packaging (new: package.py, result.py)
- `SearchResult.package(output_dir, clip_bbox=None, include_preview=True)` → `Package`
- `Package` dataclass: files, manifest.json, footprints.gpkg, preview.png, provenance.json, DISCLAIMER.txt
- Manifest schema: file paths, checksums (SHA-256), CRS, acquisition dates, tile count, AOI WKT
- Outputs consumable by Python, ArcGIS Pro, QGIS (GeoPackage index, COG rasters)
- CLI: `abovepy package --county Franklin -o ./delivery`

### 7. Oblique Intelligence (obliques/_s3.py, new: obliques/_spatial.py)
- Fetch and cache JSON sidecar metadata (camera params, footprint, timestamp)
- Spatial search: `search_obliques(point=(-84.85, 38.19), radius_feet=500)`
- Nearest-frame selection by point/AOI
- 4-direction bundle grouping: given a point, return best Bwd/Fwd/Left/Right frame set
- Rich `ObliqueFrame` dataclass with parsed metadata

### 8. QGIS Interoperability
- GeoPackage outputs with proper layer names and CRS metadata
- GeoParquet tile indexes
- QGIS-friendly package structure (data/ + styles/ + project.qgs template)
- Documentation: "Using abovepy with QGIS" tutorial

### 9. Richer STAC Asset Handling (stac.py)
- Expose all STAC assets (not just primary) — thumbnail, metadata, alternate formats
- Runtime conformance check against `/api` endpoint
- Graceful fallback when CQL2 not supported

**Surfaces:** Python, CLI, QGIS (file interop)
**Tests:** ~60 new tests

---

## LATER — v2.3+ (8+ weeks)

### 10. Lazy Analysis Bridge
- Optional `SearchResult.to_xarray()` via `stackstac` or `odc-stac`
- `SearchResult.to_dask()` for parallel array operations
- Keep optional — `pip install abovepy[xarray]`

### 11. Advanced Analysis APIs
- `abovepy.sample(point, product)` — elevation at a point
- `abovepy.profile(line, product)` — elevation along a transect
- `abovepy.zonal_stats(polygon, product)` — statistics within a polygon
- `abovepy.cut_fill(polygon, reference_elevation)` — volume calculation
- `abovepy.change_detection(bbox, product_before, product_after)` — difference map
- These wrap the existing terrain.py functions with search+read orchestration

### 12. Parcel / Route Search (if validated)
- Parcel-number search (requires county parcel data — external dependency)
- Route/corridor search by road name or line geometry
- Would need bundled or fetched lookup data

### 13. Web Viewer Templates
- Shareable MapLibre GL JS viewer HTML
- Configurable for DEM, ortho, oblique, or multi-product views
- Embeddable in reports

---

## Feature × Persona Matrix

| Feature | Surveyor | Civil Eng. | GIS Analyst | Planner | Emergency Mgmt |
|---------|----------|------------|-------------|---------|----------------|
| EPSG:3089 + feet buffers | **critical** | **critical** | high | medium | medium |
| Deliverable packaging | **critical** | **critical** | high | high | medium |
| QA / provenance | **critical** | **critical** | medium | low | medium |
| Corridor buffer search | medium | **critical** | medium | medium | low |
| Oblique inspection | high | high | medium | medium | **critical** |
| QGIS interop | medium | medium | **critical** | high | high |
| Lazy xarray loading | low | low | high | low | low |
| Phase comparison | medium | high | **critical** | medium | medium |
| Flood/cut-fill analysis | low | **critical** | medium | high | **critical** |

## Feature × Surface Matrix

| Feature | Python | CLI | ArcGIS Pro | QGIS |
|---------|--------|-----|------------|------|
| Feet-based buffers | v2.1 | v2.1 | v2.1 (params) | via file |
| Provenance / validate | v2.1 | v2.1 (--provenance) | v2.2 (tool output) | via manifest |
| Deliverable packaging | v2.2 | v2.2 (package cmd) | v2.2 (tool) | v2.2 (native) |
| Oblique spatial search | v2.2 | v2.2 | v2.2 (tool) | via file |
| QGIS packaging | v2.2 | v2.2 | — | v2.2 |
| xarray bridge | v2.3 | — | — | — |
| Analysis APIs | v2.3 | v2.3 | v2.3 (tools) | via file |

## Highest-Value First Slice (v2.1 MVP)

Ship `buffer_feet()`, `corridor_buffer()`, `SearchResult.provenance()`, `SearchResult.validate()`, download integrity, and CI hardening. This gives surveyors and engineers the CRS handling they need, adds the QA layer they expect, and hardens the project for government adoption — all without touching the package/oblique/QGIS layers that need more design.

**Estimated scope:** ~15 files modified, ~40 tests added, 0 breaking changes.

## Structural Changes Needed

1. **Remove `__slots__` from SearchResult** — blocks adding `.provenance()`, `.validate()`, `.package()` attributes
2. **Extend Product dataclass** — add acquisition dates, source metadata, QA status
3. **Factor CRS utilities** — `_reproject_bbox` lives in io/cog.py but should be in utils/crs.py for reuse
4. **URL allowlist module** — new `_security.py` with host validation for remote reads
5. **Package output module** — new `package.py` with `Package` dataclass and manifest schema
