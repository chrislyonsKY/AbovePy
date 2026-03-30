# abovepy 1.1.0 — Implementation Plan

**Version bump**: 1.0.1 → 1.1.0

## Feature 1: Terrain Analysis (TiTiler Algorithms)

Add server-side terrain analysis helpers that generate TiTiler algorithm URLs for DEM data. No new dependencies — just URL construction like the existing titiler module.

### New functions in `titiler.py`:

| Function | What it does |
|---|---|
| `hillshade_tile_url()` | Collection tile URL with `algorithm=hillshade` + optional azimuth/altitude params |
| `slope_tile_url()` | Collection tile URL with `algorithm=slope` + optional buffer/z_exaggeration |
| `contour_tile_url()` | Collection tile URL with `algorithm=contours` + optional increment/thickness/minz/maxz |
| `terrain_rgb_tile_url()` | Collection tile URL with `algorithm=terrainrgb` (Mapbox-compatible encoding) |

Each wraps `collection_tile_url()` with the correct `algorithm` param and algorithm-specific parameters. Defaults to `dem_phase3` collection since terrain only makes sense on DEMs.

### Files changed:
- `src/abovepy/titiler.py` — add 4 functions + `_pgstac_algorithm_params()` helper
- `tests/test_titiler.py` — add tests for each terrain function

---

## Feature 2: pgSTAC Search Registration

Add helpers to register persistent virtual mosaics via the TiTiler-pgSTAC `/searches/register` endpoint. This enables saved views and shareable tile URLs.

### New module: `src/abovepy/searches.py`

| Function | What it does |
|---|---|
| `register_search()` | POST to `/searches/register` with a CQL2 filter (collection + bbox + datetime). Returns a search hash ID. |
| `search_tile_url()` | Generate a TileJSON URL from a registered search hash: `/searches/{hash}/{tms}/tilejson.json` |
| `search_map_url()` | Generate a map viewer URL from a registered search hash |
| `search_info_url()` | Info URL for a registered search |
| `search_bbox_url()` | Rendered image URL from a registered search + bbox |

`register_search()` is the only function that makes an HTTP call (POST via httpx). The rest are pure URL builders like the existing titiler helpers.

### Files changed:
- `src/abovepy/searches.py` — new module
- `tests/test_searches.py` — new test file (mock the POST with respx)
- `src/abovepy/__init__.py` — export `register_search`

---

## Feature 3: Visualization Helpers

Two levels: URL-only helpers (always available) + interactive `show()` for notebooks (requires `viz` extra).

### New module: `src/abovepy/viz.py`

**URL helpers (no extra deps):**

| Function | What it does |
|---|---|
| `tile_url()` | Smart dispatcher: takes a product + bbox/county → returns the best TileJSON URL (uses pgSTAC collection endpoint) |
| `preview_url()` | Takes product + bbox → returns a rendered PNG URL |

**Notebook display (requires `leafmap` from `viz` extra):**

| Function | What it does |
|---|---|
| `show()` | Takes product + bbox/county, builds a leafmap Map with the TiTiler tile layer, returns the Map object for Jupyter display. Supports `algorithm=` for terrain overlays. |

### Files changed:
- `src/abovepy/viz.py` — new module
- `tests/test_viz.py` — new tests (mock leafmap import for show())
- `src/abovepy/__init__.py` — export `show` (with lazy import)
- `pyproject.toml` — no new deps (leafmap already in `viz` extra)

---

## Feature 4: Oblique Imagery (Stub Products + S3 Discovery)

Add oblique products to the registry. Since Ian's STAC collection isn't ready yet, provide S3-based discovery as a fallback. The product entries use placeholder collection IDs that will be updated once the STAC collection exists.

### Changes to `products.py`:

Add `OBLIQUE` to `ProductType` enum, then add 4 new products:

| Product key | S3 prefix | Description |
|---|---|---|
| `oblique_phase3_bwd` | `imagery/obliques/Phase3/.../Bwd_*` | Backward oblique, 3-inch |
| `oblique_phase3_fwd` | `imagery/obliques/Phase3/.../Fwd_*` | Forward oblique, 3-inch |
| `oblique_phase3_left` | `imagery/obliques/Phase3/.../Left_*` | Left oblique, 3-inch |
| `oblique_phase3_right` | `imagery/obliques/Phase3/.../Right_*` | Right oblique, 3-inch |

Each product gets a `collection_id` of `"obliques-phase3"` (placeholder — will match Ian's STAC collection when created) and a new optional `s3_prefix` field on the `Product` dataclass.

### New: `src/abovepy/obliques.py`

| Function | What it does |
|---|---|
| `list_oblique_seasons()` | List available seasons from S3 prefix listing |
| `search_obliques()` | Given a direction + season, list available frames from S3. Returns a GeoDataFrame with S3 URLs and metadata parsed from the JSON sidecar files. |

This is a lightweight S3-based fallback. Once Ian's STAC collection is live, `search()` will work with obliques via the normal STAC path and these helpers become convenience wrappers.

### Files changed:
- `src/abovepy/products.py` — add `OBLIQUE` type + 4 products + `s3_prefix` field
- `src/abovepy/obliques.py` — new module for S3-based oblique discovery
- `tests/test_obliques.py` — new tests
- `src/abovepy/_constants.py` — add `S3_OBLIQUES_PREFIX`
- `src/abovepy/__init__.py` — export `search_obliques`

---

## Housekeeping

| File | Change |
|---|---|
| `src/abovepy/_version.py` | `1.0.1` → `1.1.0` |
| `pyproject.toml` | version `1.0.1` → `1.1.0`, add `"oblique"` to keywords |
| `CHANGELOG.md` | Add `[1.1.0]` section |

---

## Implementation Order

1. **Terrain analysis** — smallest scope, extends existing titiler.py
2. **pgSTAC search registration** — new module, self-contained
3. **Visualization helpers** — depends on terrain URLs being done
4. **Oblique imagery** — most exploratory, independent of the other 3
5. **Version bump + changelog** — last step after all features land

---

## What's NOT in scope

- Local numpy-based terrain analysis (user chose TiTiler-only)
- Full ortho/nadir imagery STAC support (already works via existing products)
- Pushing to remote or creating a PR (per user preference)
