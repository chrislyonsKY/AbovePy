"""Surface mine volume estimation for eastern Kentucky.

Estimates cut/fill volumes within active mine permit boundaries
using:
- DEM Phase 2 (2ft) from KyFromAbove via abovepy
- Mine permit boundaries from KyGeoNet REST services

For each mine permit polygon:
1. Extract DEM pixels within the boundary
2. Estimate a reference surface from the polygon edge elevations
3. Compute volume difference (reference - actual = cut volume)

Outputs:
    Console table of permit volumes
    output/mine_volumes.png — Visualization of one permit area

Data sources:
    DEM: KyFromAbove Phase 2 (STAC API via abovepy)
    Mine permits: KyGeoNet MapServer
        Ky_Permitted_Mine_Boundaries_WGS84WM/MapServer/0

Usage:
    python mine_volume_estimate.py

Requires:
    pip install abovepy[viz] scipy
"""

from pathlib import Path

import geopandas as gpd
import httpx
import numpy as np
import rasterio
import rasterio.mask
from scipy.interpolate import griddata
from shapely.geometry import mapping

import abovepy

# Perry County area — eastern KY coal country
BBOX = (-83.30, 37.20, -83.10, 37.40)

PERMITS_URL = (
    "https://kygisserver.ky.gov/arcgis/rest/services"
    "/WGS84WM_Services"
    "/Ky_Permitted_Mine_Boundaries_WGS84WM"
    "/MapServer/0/query"
)


def fetch_mine_permits(bbox):
    """Fetch active mine permit polygons from KyGeoNet."""
    xmin, ymin, xmax, ymax = bbox
    params = {
        "where": "Type_Flag='ACT'",
        "geometry": f"{xmin},{ymin},{xmax},{ymax}",
        "geometryType": "esriGeometryEnvelope",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "PermitNo,Calc_Acres,PER_NAME,Type_Flag",
        "f": "geojson",
        "outSR": "4326",
    }
    resp = httpx.get(PERMITS_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("features"):
        raise RuntimeError("No active permits found in bbox")
    gdf = gpd.GeoDataFrame.from_features(data["features"], crs="EPSG:4326")
    print(f"Fetched {len(gdf)} active mine permits")
    return gdf


def estimate_volume(dem_path, polygon, pixel_area_sqft):
    """Estimate cut volume for a single permit polygon.

    Returns volume in cubic yards (positive = material removed).
    """
    geom = [mapping(polygon)]
    with rasterio.open(str(dem_path)) as src:
        try:
            clipped, clipped_tf = rasterio.mask.mask(src, geom, crop=True, nodata=np.nan)
        except ValueError:
            return np.nan, None, None
        clipped = clipped[0]

    valid = ~np.isnan(clipped) & (clipped > 0)
    if valid.sum() < 100:
        return np.nan, None, None

    # Build edge mask: pixels within 2 cells of the border
    from scipy.ndimage import binary_erosion

    eroded = binary_erosion(valid, iterations=2)
    edge_mask = valid & ~eroded

    rows, cols = np.where(edge_mask)
    edge_vals = clipped[edge_mask]
    if len(edge_vals) < 10:
        return np.nan, None, None

    # Interpolate reference surface from edge elevations
    all_rows, all_cols = np.where(valid)
    reference = griddata(
        (rows, cols),
        edge_vals,
        (all_rows, all_cols),
        method="linear",
        fill_value=np.nanmedian(edge_vals),
    )

    actual = clipped[valid]
    diff = reference - actual  # positive = cut
    cut_vol_sqft = float(np.sum(diff[diff > 0]) * pixel_area_sqft)
    # Convert cubic feet to cubic yards
    cut_vol_yd3 = cut_vol_sqft / 27.0

    # Build full grids for visualization
    ref_grid = np.full_like(clipped, np.nan)
    ref_grid[valid] = reference
    depth_grid = np.full_like(clipped, np.nan)
    depth_grid[valid] = reference - actual

    return cut_vol_yd3, ref_grid, depth_grid


def visualize(dem_path, polygon, depth_grid, permit_no, out):
    """Save cut-depth visualization for one permit."""
    import matplotlib.pyplot as plt

    geom = [mapping(polygon)]
    with rasterio.open(str(dem_path)) as src:
        clipped, _ = rasterio.mask.mask(src, geom, crop=True, nodata=np.nan)
        dem = clipped[0]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    im0 = axes[0].imshow(dem, cmap="terrain")
    axes[0].set_title(f"DEM — Permit {permit_no}")
    axes[0].axis("off")
    fig.colorbar(im0, ax=axes[0], label="Elevation (ft)")

    vmax = np.nanpercentile(depth_grid, 95) if (np.any(~np.isnan(depth_grid))) else 1
    im1 = axes[1].imshow(depth_grid, cmap="RdYlBu", vmin=-vmax, vmax=vmax)
    axes[1].set_title("Cut Depth (ref − actual)")
    axes[1].axis("off")
    fig.colorbar(im1, ax=axes[1], label="Depth (ft)")

    plt.tight_layout()
    plt.savefig(str(out), dpi=150, bbox_inches="tight")
    print(f"Visualization saved: {out}")
    plt.close()


def main():
    output_dir = Path("./output/mine_volumes")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Fetch mine permit boundaries
    print("Fetching active mine permits in Perry County...")
    permits = fetch_mine_permits(BBOX)

    # 2. Search and download DEM tiles
    print("\nSearching for DEM Phase 2 tiles...")
    tiles = abovepy.search(bbox=BBOX, product="dem_phase2")
    print(f"Found {len(tiles)} DEM tiles")

    print("Downloading DEM tiles...")
    paths = abovepy.download(tiles, output_dir=output_dir / "tiles")

    # 3. Mosaic into single raster
    print("Building mosaic...")
    mosaic_path = abovepy.mosaic(paths, output=output_dir / "perry_dem.vrt")

    # Pixel area: DEM Phase 2 is 2ft resolution
    pixel_area = 2.0 * 2.0  # square feet

    # 4. Estimate volume for each permit
    print("\n{:<12} {:>10} {:>18}".format("Permit", "Acres", "Cut Vol (yd³)"))
    print("-" * 44)

    results = []
    for _, row in permits.iterrows():
        vol, _, depth = estimate_volume(mosaic_path, row.geometry, pixel_area)
        permit_no = row.get("PermitNo", "N/A")
        acres = row.get("Calc_Acres", 0) or 0
        results.append((permit_no, acres, vol, depth, row))
        vol_str = f"{vol:,.0f}" if not np.isnan(vol) else "N/A"
        print(f"{permit_no:<12} {acres:>10.1f} {vol_str:>18}")

    # 5. Visualize the largest permit area
    valid = [(p, a, v, d, r) for p, a, v, d, r in results if not np.isnan(v)]
    if valid:
        biggest = max(valid, key=lambda x: x[2])
        permit_no, _, _, depth_grid, row = biggest
        print(f"\nVisualizing permit {permit_no}...")
        try:
            visualize(
                mosaic_path,
                row.geometry,
                depth_grid,
                permit_no,
                output_dir / "mine_volumes.png",
            )
        except ImportError:
            print("Install matplotlib for visualization: pip install abovepy[viz]")


if __name__ == "__main__":
    main()

# Expected output (values will vary with actual data):
# --------------------------------------------------
# Fetching active mine permits in Perry County...
# Fetched 12 active mine permits
#
# Searching for DEM Phase 2 tiles...
# Found 28 DEM tiles
# Downloading DEM tiles...
# Building mosaic...
#
# Permit         Acres     Cut Vol (yd³)
# --------------------------------------------
# 861-0123         45.2          312,400
# 861-0456        120.8        1,045,200
# 861-0789         23.1           87,600
# ...
#
# Visualizing permit 861-0456...
# Visualization saved: output/mine_volumes/mine_volumes.png
