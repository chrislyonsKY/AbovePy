"""Relative Elevation Model (REM) of the Kentucky River in Frankfort, KY.

Computes height-above-river for the Frankfort area using:
- DEM Phase 3 (2ft) from KyFromAbove via abovepy
- Kentucky River centerline from KyGeoNet REST services

The REM highlights floodplain structure by showing each pixel's
elevation relative to the nearest river surface elevation.

Outputs:
    output/frankfort_rem.tif   -- REM raster (GeoTIFF)
    output/frankfort_rem.png   -- Visualization

Data sources:
    DEM: KyFromAbove Phase 3 (STAC API via abovepy)
    River: KyGeoNet Ky_Rivers_WGS84WM MapServer
           https://kygisserver.ky.gov/arcgis/rest/services/
           WGS84WM_Services/Ky_Rivers_WGS84WM/MapServer/0

Usage:
    python kentucky_river_rem.py

Requires:
    pip install abovepy[viz] scipy httpx
"""

from __future__ import annotations

from pathlib import Path

import httpx
import numpy as np
import rasterio
from scipy.interpolate import griddata
from shapely.geometry import shape as geom_shape
from shapely.ops import linemerge

import abovepy

# Frankfort area bbox (EPSG:4326)
BBOX = (-84.92, 38.15, -84.82, 38.25)
SAMPLE_SPACING_M = 30  # meters between river sample points


def fetch_river_centerline(
    bbox: tuple[float, float, float, float],
):
    """Fetch Kentucky River geometry from KyGeoNet."""
    url = (
        "https://kygisserver.ky.gov/arcgis/rest/services"
        "/WGS84WM_Services/Ky_Rivers_WGS84WM"
        "/MapServer/0/query"
    )
    params = {
        "where": "GNIS_NAME='Kentucky River'",
        "geometry": ",".join(str(c) for c in bbox),
        "geometryType": "esriGeometryEnvelope",
        "inSR": "4326",
        "outSR": "4326",
        "outFields": "GNIS_NAME,GNIS_ID,LENGTHKM",
        "returnGeometry": "true",
        "f": "geojson",
    }
    resp = httpx.get(url, params=params, timeout=30)
    resp.raise_for_status()
    features = resp.json()["features"]
    if not features:
        msg = "No Kentucky River features found in bbox"
        raise ValueError(msg)
    print(f"Fetched {len(features)} river segment(s)")
    geoms = [geom_shape(f["geometry"]) for f in features]
    return linemerge(geoms)


def sample_river_points(
    river, spacing_deg: float
) -> np.ndarray:
    """Sample points along the river at regular intervals.

    Returns array of shape (N, 2) with (x, y) coordinates.
    """
    length = river.length
    distances = np.arange(0, length, spacing_deg)
    points = [river.interpolate(d) for d in distances]
    return np.array([[p.x, p.y] for p in points])


def main():
    output_dir = Path("./output/frankfort_rem")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Fetch river centerline
    print("Fetching Kentucky River centerline...")
    river = fetch_river_centerline(BBOX)

    # 2. Search and download DEM tiles
    print("Searching for DEM tiles...")
    tiles = abovepy.search(bbox=BBOX, product="dem_phase3")
    print(f"Found {len(tiles)} tiles")

    print("Downloading DEM tiles...")
    paths = abovepy.download(
        tiles, output_dir=output_dir / "tiles"
    )

    # 3. Build mosaic and read DEM
    print("Building mosaic...")
    vrt = abovepy.mosaic(paths, output=output_dir / "dem.vrt")

    with rasterio.open(str(vrt)) as src:
        dem = src.read(1).astype(np.float32)
        profile = src.profile.copy()
        transform = src.transform

    # 4. Sample elevations along river centerline
    # Convert spacing from meters to approximate degrees
    spacing_deg = SAMPLE_SPACING_M / 111_000
    river_pts = sample_river_points(river, spacing_deg)

    # Convert river coords to pixel coords, sample DEM
    rows, cols = rasterio.transform.rowcol(
        transform, river_pts[:, 0], river_pts[:, 1]
    )
    rows, cols = np.array(rows), np.array(cols)

    # Keep only points inside the raster extent
    h, w = dem.shape
    mask = (
        (rows >= 0) & (rows < h) & (cols >= 0) & (cols < w)
    )
    rows, cols = rows[mask], cols[mask]
    river_pts = river_pts[mask]
    river_elevations = dem[rows, cols]

    # Drop nodata samples
    valid = river_elevations > 0
    river_pts = river_pts[valid]
    river_elevations = river_elevations[valid]
    print(f"Sampled {len(river_elevations)} river points")

    # 5. Interpolate river surface across the full raster
    print("Interpolating river surface...")
    yy, xx = np.mgrid[0:h, 0:w]
    grid_x = transform.c + xx * transform.a
    grid_y = transform.f + yy * transform.e

    river_surface = griddata(
        river_pts,
        river_elevations,
        (grid_x, grid_y),
        method="linear",
        fill_value=np.nan,
    )
    # Fill remaining NaN with nearest-neighbor
    nan_mask = np.isnan(river_surface)
    if nan_mask.any():
        river_surface_nn = griddata(
            river_pts,
            river_elevations,
            (grid_x[nan_mask], grid_y[nan_mask]),
            method="nearest",
        )
        river_surface[nan_mask] = river_surface_nn

    # 6. Compute REM: DEM minus river surface
    rem = dem - river_surface.astype(np.float32)
    rem = np.clip(rem, 0, None)  # clamp negatives to 0

    # 7. Save REM as GeoTIFF
    rem_path = output_dir / "frankfort_rem.tif"
    profile.update(dtype="float32", count=1, compress="deflate")
    with rasterio.open(str(rem_path), "w", **profile) as dst:
        dst.write(rem, 1)
    print(f"REM saved: {rem_path}")

    # 8. Visualize
    try:
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(12, 10))
        vmax = np.percentile(rem[rem > 0], 98)
        im = ax.imshow(
            rem,
            cmap="RdYlBu_r",
            vmin=0,
            vmax=vmax,
            extent=[
                transform.c,
                transform.c + w * transform.a,
                transform.f + h * transform.e,
                transform.f,
            ],
        )

        # Overlay river centerline
        if river.geom_type == "MultiLineString":
            for line in river.geoms:
                xs, ys = line.xy
                ax.plot(xs, ys, "k-", linewidth=0.8)
        else:
            xs, ys = river.xy
            ax.plot(xs, ys, "k-", linewidth=0.8)

        cbar = fig.colorbar(im, ax=ax, shrink=0.7)
        cbar.set_label("Height above river (ft)")
        ax.set_title(
            "Relative Elevation Model — "
            "Kentucky River, Frankfort"
        )
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")

        png_path = output_dir / "frankfort_rem.png"
        plt.savefig(
            str(png_path), dpi=200, bbox_inches="tight"
        )
        print(f"Visualization saved: {png_path}")
        plt.show()
    except ImportError:
        print(
            "Install matplotlib for visualization: "
            "pip install abovepy[viz]"
        )


if __name__ == "__main__":
    main()

# Expected output:
# Fetching Kentucky River centerline...
# Fetched 3 river segment(s)
# Searching for DEM tiles...
# Found ~12 tiles
# Downloading DEM tiles...
# Building mosaic...
# Sampled ~800 river points
# Interpolating river surface...
# REM saved: output/frankfort_rem/frankfort_rem.tif
# Visualization saved: output/frankfort_rem/frankfort_rem.png
