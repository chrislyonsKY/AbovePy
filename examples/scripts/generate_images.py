"""Generate output PNG images for all examples.

Produces sample images that are checked into the repo for documentation.
Requires: pip install abovepy[all] matplotlib

Usage:
    python generate_images.py
"""

from pathlib import Path

import numpy as np

import abovepy

OUTPUT = Path(__file__).parent.parent / "output"
OUTPUT.mkdir(parents=True, exist_ok=True)


def generate_stream_window():
    """Stream a DEM window and save elevation plot."""
    import matplotlib.pyplot as plt

    print("=== Stream Window ===")
    tiles = abovepy.search(
        bbox=(-84.85, 38.18, -84.82, 38.21),
        product="dem_phase3",
    )
    url = tiles.iloc[0].asset_url
    data, profile = abovepy.read(
        url, bbox=(-84.85, 38.18, -84.82, 38.21)
    )
    print(f"  Shape: {data.shape}, range: {data.min():.0f}-{data.max():.0f}")

    # Compute figure size proportional to data aspect ratio
    aspect = data.shape[2] / data.shape[1]
    fig_h = 6
    fig_w = min(fig_h * aspect + 1.5, 16)  # +1.5 for colorbar
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    t = profile["transform"]
    extent = [t[2], t[2] + data.shape[2] * t[0],
              t[5] + data.shape[1] * t[4], t[5]]
    im = ax.imshow(
        data.squeeze(), cmap="terrain", extent=extent
    )
    fig.colorbar(im, ax=ax, label="Elevation (ft)")
    ax.set_title("Streamed DEM Window — Frankfort, KY")
    ax.set_xlabel("Easting (ft, EPSG:3089)")
    ax.set_ylabel("Northing (ft)")
    ax.ticklabel_format(style="plain", useOffset=False)
    plt.tight_layout()
    path = OUTPUT / "stream_window.png"
    plt.savefig(str(path), dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


def generate_ortho_rgb():
    """Extract ortho RGB and save composite."""
    import matplotlib.pyplot as plt

    print("=== Ortho RGB Extract ===")
    tiles = abovepy.search(
        bbox=(-84.876, 38.196, -84.872, 38.200),
        product="ortho_phase3",
    )
    if len(tiles) == 0:
        print("  No ortho tiles found, skipping")
        return

    url = tiles.iloc[0].asset_url
    data, profile = abovepy.read(
        url, bbox=(-84.876, 38.196, -84.872, 38.200)
    )
    print(f"  Shape: {data.shape}")

    if data.shape[0] >= 3:
        rgb = np.moveaxis(data[:3], 0, -1)
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.imshow(rgb)
        ax.set_title("Ortho Phase 3 — KY State Capitol")
        ax.axis("off")
        plt.tight_layout()
        path = OUTPUT / "ortho_rgb.png"
        plt.savefig(str(path), dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  Saved: {path}")


def generate_compare_phases():
    """Compare DEM phases side by side — full tiles."""
    import matplotlib.pyplot as plt

    print("=== Compare DEM Phases ===")
    # Use a point in Frankfort to find overlapping tiles
    bbox = (-84.87, 38.19, -84.86, 38.20)

    tiles1 = abovepy.search(bbox=bbox, product="dem_phase1")
    tiles3 = abovepy.search(bbox=bbox, product="dem_phase3")

    if len(tiles1) == 0 or len(tiles3) == 0:
        print("  Missing tiles, skipping")
        return

    # Read full tiles for proper square images
    data1, p1 = abovepy.read(tiles1.iloc[0].asset_url)
    data3, p3 = abovepy.read(tiles3.iloc[0].asset_url)
    print(f"  Phase 1: {data1.shape}, Phase 3: {data3.shape}")

    fig, axes = plt.subplots(
        1, 3, figsize=(14, 6),
        gridspec_kw={"width_ratios": [1, 1, 0.05]},
    )
    vmin = min(data1.min(), data3.min())
    vmax = max(data1.max(), data3.max())

    axes[0].imshow(
        data1.squeeze(), cmap="terrain",
        vmin=vmin, vmax=vmax,
    )
    axes[0].set_title(
        f"DEM Phase 1 (5ft)\n{data1.shape[1]}x{data1.shape[2]}px"
    )
    axes[0].axis("off")

    im = axes[1].imshow(
        data3.squeeze(), cmap="terrain",
        vmin=vmin, vmax=vmax,
    )
    axes[1].set_title(
        f"DEM Phase 3 (2ft)\n{data3.shape[1]}x{data3.shape[2]}px"
    )
    axes[1].axis("off")

    fig.colorbar(im, cax=axes[2], label="Elevation (ft)")
    plt.suptitle("DEM Phase Comparison — Frankfort, KY")
    plt.tight_layout()
    path = OUTPUT / "compare_dem_phases.png"
    plt.savefig(str(path), dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


def generate_search_map():
    """Plot search results tile boundaries."""
    import matplotlib.pyplot as plt

    print("=== Search Results Map ===")
    tiles = abovepy.search(
        county="Franklin", product="dem_phase3"
    )
    print(f"  Found {len(tiles)} tiles")

    fig, ax = plt.subplots(figsize=(10, 8))
    tiles.plot(
        ax=ax,
        edgecolor="teal",
        facecolor="teal",
        alpha=0.3,
        linewidth=0.5,
    )
    ax.set_title(
        f"Franklin County — {len(tiles)} DEM Phase 3 Tiles"
    )
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    plt.tight_layout()
    path = OUTPUT / "search_results_map.png"
    plt.savefig(str(path), dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


def generate_hillshade():
    """Read a single DEM tile and compute hillshade."""
    import matplotlib.pyplot as plt

    print("=== Hillshade ===")
    bbox = (-84.87, 38.19, -84.86, 38.20)
    tiles = abovepy.search(bbox=bbox, product="dem_phase3")
    if len(tiles) == 0:
        print("  No tiles found, skipping")
        return

    # Read full tile (no bbox) so we get the complete square
    data, profile = abovepy.read(tiles.iloc[0].asset_url)
    dem = data.squeeze().astype(np.float64)
    print(f"  DEM shape: {dem.shape}")

    # Compute hillshade
    res = abs(profile["transform"][0])
    dx, dy = np.gradient(dem, res, res)
    slope = np.sqrt(dx**2 + dy**2)
    aspect = np.arctan2(-dy, dx)
    az = np.radians(315)
    alt = np.radians(45)
    hs = (
        np.sin(alt) * np.cos(np.arctan(slope))
        + np.cos(alt)
        * np.sin(np.arctan(slope))
        * np.cos(az - aspect)
    )
    hs = np.clip(hs * 255, 0, 255).astype(np.uint8)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    axes[0].imshow(dem, cmap="terrain")
    axes[0].set_title("DEM Phase 3 (2ft)")
    axes[0].axis("off")
    axes[1].imshow(hs, cmap="gray")
    axes[1].set_title("Hillshade (az=315, alt=45)")
    axes[1].axis("off")
    plt.suptitle("Frankfort, KY — Hillshade from Streamed DEM")
    plt.tight_layout()
    path = OUTPUT / "hillshade.png"
    plt.savefig(str(path), dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


def generate_rem():
    """Compute a Relative Elevation Model from a single tile."""
    import httpx
    import matplotlib.pyplot as plt
    from scipy.interpolate import griddata
    from shapely.geometry import shape
    from shapely.ops import linemerge

    print("=== Kentucky River REM ===")
    # Smaller bbox that fits within one tile
    bbox = (-84.89, 38.18, -84.85, 38.22)

    # Fetch river centerline from KyGeoNet
    print("  Fetching river centerline...")
    resp = httpx.get(
        "https://kygisserver.ky.gov/arcgis/rest/services/"
        "WGS84WM_Services/Ky_Rivers_WGS84WM/"
        "MapServer/0/query",
        params={
            "where": "GNIS_NAME='Kentucky River'",
            "geometry": f"{bbox[0]},{bbox[1]},"
            f"{bbox[2]},{bbox[3]}",
            "geometryType": "esriGeometryEnvelope",
            "inSR": "4326",
            "outSR": "4326",
            "outFields": "GNIS_NAME",
            "f": "geojson",
        },
        timeout=30,
    )
    features = resp.json().get("features", [])
    if not features:
        print("  No river features found, skipping")
        return

    # Strip Z/M dimensions — service returns XYZM
    def _to_2d(geom_dict):
        coords = geom_dict["coordinates"]
        if geom_dict["type"] == "MultiLineString":
            geom_dict["coordinates"] = [
                [c[:2] for c in part] for part in coords
            ]
        else:
            geom_dict["coordinates"] = [
                c[:2] for c in coords
            ]
        return shape(geom_dict)

    lines = [_to_2d(f["geometry"]) for f in features]
    river = linemerge(lines)
    print(f"  River segments: {len(features)}")

    # Prepare river line and CRS transformer
    from pyproj import Transformer
    to_3089 = Transformer.from_crs(
        "EPSG:4326", "EPSG:3089", always_xy=True
    )

    river_line = (
        max(river.geoms, key=lambda g: g.length)
        if hasattr(river, "geoms")
        else river
    )

    # Read DEM tile — find the one containing the river
    tiles = abovepy.search(bbox=bbox, product="dem_phase3")
    if len(tiles) == 0:
        print("  No DEM tiles found, skipping")
        return

    mid = river_line.interpolate(0.5, normalized=True)
    rpx, rpy = to_3089.transform(mid.x, mid.y)

    data, profile = None, None
    for _, row in tiles.iterrows():
        d, p = abovepy.read(row.asset_url, bbox=bbox)
        t = p["transform"]
        xmin, ymax = t[2], t[5]
        xmax = xmin + d.shape[2] * t[0]
        ymin = ymax + d.shape[1] * t[4]
        if xmin <= rpx <= xmax and ymin <= rpy <= ymax:
            data, profile = d, p
            break

    if data is None:
        print("  No tile contains the river, skipping")
        return

    dem = data.squeeze().astype(np.float64)
    transform = profile["transform"]
    print(f"  DEM shape: {dem.shape}")

    n_pts = max(50, int(river_line.length / 0.0003))
    sample_pts = []
    sample_vals = []
    for i in range(n_pts):
        pt = river_line.interpolate(i / n_pts, normalized=True)
        px, py = to_3089.transform(pt.x, pt.y)
        col = int((px - transform[2]) / transform[0])
        row = int((py - transform[5]) / transform[4])
        if 0 <= row < dem.shape[0] and 0 <= col < dem.shape[1]:
            val = dem[row, col]
            if val > 0:
                sample_pts.append((col, row))
                sample_vals.append(val)

    print(f"  Sampled {len(sample_pts)} river points")
    if len(sample_pts) < 10:
        print("  Not enough sample points, skipping")
        return

    # Interpolate river surface
    rows, cols = np.mgrid[0:dem.shape[0], 0:dem.shape[1]]
    pts = np.array(sample_pts)
    river_surface = griddata(
        pts, sample_vals, (cols, rows), method="linear"
    )
    # Fill NaN with nearest
    mask = np.isnan(river_surface)
    if mask.any():
        nearest = griddata(
            pts, sample_vals, (cols, rows), method="nearest"
        )
        river_surface[mask] = nearest[mask]

    # Compute REM
    rem = dem - river_surface
    rem = np.clip(rem, 0, None)
    print(f"  REM range: {rem.min():.1f} - {rem.max():.1f} ft")

    # Plot
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    axes[0].imshow(dem, cmap="terrain")
    axes[0].set_title("DEM Phase 3 (2ft)")
    axes[0].axis("off")

    im = axes[1].imshow(
        rem, cmap="RdYlBu_r", vmin=0, vmax=80
    )
    # Overlay river (reproject to pixel coords)
    rc = []
    for i in range(201):
        pt = river_line.interpolate(i / 200, normalized=True)
        px, py = to_3089.transform(pt.x, pt.y)
        c = (px - transform[2]) / transform[0]
        r = (py - transform[5]) / transform[4]
        if 0 <= r < dem.shape[0] and 0 <= c < dem.shape[1]:
            rc.append((c, r))
    if rc:
        rx, ry = zip(*rc, strict=False)
        axes[1].plot(rx, ry, "k-", linewidth=1, alpha=0.7)
    axes[1].set_title("REM — Height Above River (ft)")
    axes[1].axis("off")
    fig.colorbar(im, ax=axes[1], label="Feet above river")

    plt.suptitle(
        "Kentucky River REM — Frankfort, KY"
    )
    plt.tight_layout()
    path = OUTPUT / "kentucky_river_rem.png"
    plt.savefig(str(path), dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


def generate_mine_volume():
    """Visualize mine permit area DEM with cut depth."""
    import httpx
    import matplotlib.pyplot as plt
    from scipy.interpolate import griddata
    from scipy.ndimage import binary_erosion
    from shapely.geometry import mapping, shape

    print("=== Mine Volume Estimate ===")
    bbox = (-83.30, 37.25, -83.15, 37.35)

    # Fetch mine permits
    print("  Fetching mine permits...")
    resp = httpx.get(
        "https://kygisserver.ky.gov/arcgis/rest/services/"
        "WGS84WM_Services/"
        "Ky_Permitted_Mine_Boundaries_WGS84WM/"
        "MapServer/0/query",
        params={
            "where": "Type_Flag='ACT'",
            "geometry": f"{bbox[0]},{bbox[1]},"
            f"{bbox[2]},{bbox[3]}",
            "geometryType": "esriGeometryEnvelope",
            "inSR": "4326",
            "outSR": "4326",
            "outFields": "PermitNo,Calc_Acres,Type_Flag",
            "f": "geojson",
        },
        timeout=30,
    )
    features = resp.json().get("features", [])
    print(f"  Found {len(features)} active permits")

    if not features:
        print("  No permits found, skipping")
        return

    # Pick a mid-sized permit (10-500 acres) that fits a tile
    candidates = [
        f for f in features
        if 10 < (f["properties"].get("Calc_Acres") or 0) < 500
    ]
    if not candidates:
        candidates = features[:5]
    best = max(
        candidates,
        key=lambda f: f["properties"].get("Calc_Acres", 0)
        or 0,
    )
    # Strip Z/M dimensions from polygon coords
    bg = best["geometry"]
    if bg["type"] == "Polygon":
        bg["coordinates"] = [
            [c[:2] for c in ring]
            for ring in bg["coordinates"]
        ]
    elif bg["type"] == "MultiPolygon":
        bg["coordinates"] = [
            [[c[:2] for c in ring] for ring in poly]
            for poly in bg["coordinates"]
        ]
    geom = shape(bg)
    props = best["properties"]
    permit = props.get("PermitNo", "unknown")
    acres = props.get("Calc_Acres", 0) or 0
    print(f"  Selected: {permit} ({acres:.0f} acres)")

    # Read DEM covering the permit
    gb = geom.bounds  # (minx, miny, maxx, maxy)
    pad = 0.005
    pbbox = (
        gb[0] - pad,
        gb[1] - pad,
        gb[2] + pad,
        gb[3] + pad,
    )
    tiles = abovepy.search(
        bbox=pbbox, product="dem_phase2"
    )
    if len(tiles) == 0:
        tiles = abovepy.search(
            bbox=pbbox, product="dem_phase3"
        )
    if len(tiles) == 0:
        print("  No DEM tiles found, skipping")
        return

    # Find tile overlapping the permit centroid
    from pyproj import Transformer as Tf
    to_3089m = Tf.from_crs(
        "EPSG:4326", "EPSG:3089", always_xy=True
    )
    cx, cy = to_3089m.transform(
        geom.centroid.x, geom.centroid.y
    )

    data, profile = None, None
    for _, row in tiles.iterrows():
        d, p = abovepy.read(row.asset_url, bbox=pbbox)
        t = p["transform"]
        xmin, ymax = t[2], t[5]
        xmax = xmin + d.shape[2] * t[0]
        ymin = ymax + d.shape[1] * t[4]
        if xmin <= cx <= xmax and ymin <= cy <= ymax:
            data, profile = d, p
            break

    if data is None:
        # Fallback to first tile
        data, profile = abovepy.read(
            tiles.iloc[0].asset_url, bbox=pbbox
        )
    dem = data.squeeze().astype(np.float64)
    transform = profile["transform"]
    print(f"  DEM shape: {dem.shape}")

    # Reproject permit polygon to EPSG:3089 for rasterization
    import rasterio.features
    from shapely.ops import transform as shp_transform

    geom_3089 = shp_transform(to_3089m.transform, geom)
    geojson_geom = mapping(geom_3089)
    mask = rasterio.features.geometry_mask(
        [geojson_geom],
        out_shape=dem.shape,
        transform=rasterio.transform.Affine(*transform[:6]),
        invert=True,
    )

    if mask.sum() < 100:
        print("  Permit too small in raster, skipping")
        return

    # Edge elevations via erosion
    eroded = binary_erosion(mask, iterations=3)
    edge_mask = mask & ~eroded
    edge_rows, edge_cols = np.where(edge_mask)
    edge_vals = dem[edge_mask]

    # Reference surface from edges
    rows, cols = np.mgrid[0:dem.shape[0], 0:dem.shape[1]]
    ref = griddata(
        np.column_stack([edge_cols, edge_rows]),
        edge_vals,
        (cols, rows),
        method="linear",
    )
    nearest = griddata(
        np.column_stack([edge_cols, edge_rows]),
        edge_vals,
        (cols, rows),
        method="nearest",
    )
    nan_mask = np.isnan(ref)
    ref[nan_mask] = nearest[nan_mask]

    # Cut depth
    cut = np.where(mask, ref - dem, 0)
    cut = np.clip(cut, 0, None)

    # Volume in cubic yards (ft resolution, data in ft)
    res = abs(transform[0])
    pixel_area = res * res  # sq ft
    vol_cf = float(np.sum(cut) * pixel_area)
    vol_cy = vol_cf / 27.0
    print(f"  Cut volume: {vol_cy:,.0f} cubic yards")

    # Plot
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    axes[0].imshow(dem, cmap="terrain")
    axes[0].contour(mask.astype(float), levels=[0.5],
                    colors="red", linewidths=1.5)
    axes[0].set_title(f"DEM — Permit {permit}")
    axes[0].axis("off")

    im = axes[1].imshow(
        np.where(mask, cut, np.nan),
        cmap="Reds",
        vmin=0,
        vmax=max(np.percentile(cut[mask], 95), 1),
    )
    axes[1].contour(mask.astype(float), levels=[0.5],
                    colors="red", linewidths=1.5)
    axes[1].set_title(
        f"Cut Depth — {vol_cy:,.0f} yd³"
    )
    axes[1].axis("off")
    fig.colorbar(im, ax=axes[1], label="Cut depth (ft)")

    plt.suptitle(
        f"Mine Volume Estimate — Perry County, KY\n"
        f"Permit {permit} · {acres:.0f} acres"
    )
    plt.tight_layout()
    path = OUTPUT / "mine_volume.png"
    plt.savefig(str(path), dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


if __name__ == "__main__":
    import matplotlib
    matplotlib.use("Agg")

    generate_stream_window()
    generate_ortho_rgb()
    generate_compare_phases()
    generate_search_map()
    generate_hillshade()
    generate_rem()
    generate_mine_volume()
    print("\nDone! All images saved to examples/output/")
