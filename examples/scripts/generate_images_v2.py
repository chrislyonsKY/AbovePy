"""Generate output images for v2 examples.

Produces sample images demonstrating real-world workflows.
Requires: pip install abovepy[all] matplotlib scipy imageio

Usage:
    python generate_images_v2.py
"""

from pathlib import Path

import numpy as np

import abovepy

OUTPUT = Path(__file__).parent.parent / "output"
OUTPUT.mkdir(parents=True, exist_ok=True)

# WCAG 2.1 AA: dark text (#333) on white bg gives ~12.6:1 contrast
_TITLE_COLOR = "#222222"
_LABEL_COLOR = "#333333"


def _apply_wcag_style(fig, axes_list):
    """Apply WCAG 2.1 AA compliant text colors to all figure text."""
    fig.patch.set_facecolor("white")
    for text in fig.texts:
        text.set_color(_TITLE_COLOR)
    for ax in axes_list:
        ax.title.set_color(_TITLE_COLOR)
        ax.xaxis.label.set_color(_LABEL_COLOR)
        ax.yaxis.label.set_color(_LABEL_COLOR)
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_color(_LABEL_COLOR)


def generate_dem_change_detection():
    """DEM change detection over a mining area — Phase 1 vs Phase 3."""
    import matplotlib.pyplot as plt

    print("=== DEM Change Detection (Mining) ===")
    # Pike County mining area — read full tiles for proper square images
    bbox = (-82.55, 37.50, -82.50, 37.55)

    tiles1 = abovepy.search(bbox=bbox, product="dem_phase1")
    tiles3 = abovepy.search(bbox=bbox, product="dem_phase3")

    if len(tiles1) == 0 or len(tiles3) == 0:
        print("  Missing tiles for one phase, skipping")
        return

    # Read full tiles (no bbox) for proper square images
    data1, p1 = abovepy.read(tiles1.iloc[0].asset_url)
    data3, p3 = abovepy.read(tiles3.iloc[0].asset_url)

    dem1 = data1.squeeze().astype(np.float64)
    dem3 = data3.squeeze().astype(np.float64)
    print(f"  Phase 1: {dem1.shape}, Phase 3: {dem3.shape}")

    # Resample Phase 1 to match Phase 3 resolution
    if dem1.shape != dem3.shape:
        from scipy.ndimage import zoom

        zy = dem3.shape[0] / dem1.shape[0]
        zx = dem3.shape[1] / dem1.shape[1]
        dem1 = zoom(dem1, (zy, zx), order=1)
        print(f"  Resampled Phase 1 to {dem1.shape}")

    # Compute change
    change = dem3 - dem1
    print(f"  Change range: {change.min():.1f} to {change.max():.1f} ft")

    # Plot
    fig, axes = plt.subplots(1, 3, figsize=(18, 6),
                             gridspec_kw={"width_ratios": [1, 1, 1]})

    vmin = min(dem1.min(), dem3.min())
    vmax = max(dem1.max(), dem3.max())

    axes[0].imshow(dem1, cmap="terrain", vmin=vmin, vmax=vmax)
    axes[0].set_title("DEM Phase 1 (5ft)")
    axes[0].axis("off")

    axes[1].imshow(dem3, cmap="terrain", vmin=vmin, vmax=vmax)
    axes[1].set_title("DEM Phase 3 (2ft)")
    axes[1].axis("off")

    # Tighter color scale based on actual data percentiles
    clim = max(np.percentile(np.abs(change), 99), 5)
    im = axes[2].imshow(change, cmap="RdBu", vmin=-clim, vmax=clim)
    axes[2].set_title("Elevation Change (ft)")
    axes[2].axis("off")
    fig.colorbar(im, ax=axes[2], label="Change (ft)\nBlue=cut  Red=fill",
                 shrink=0.8)

    plt.suptitle("DEM Change Detection — Pike County Mining Area",
                 fontsize=14, color=_TITLE_COLOR)
    _apply_wcag_style(fig, list(axes))
    plt.tight_layout()
    path = OUTPUT / "dem_change_detection.png"
    plt.savefig(str(path), dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


def generate_flood_inundation():
    """Flood inundation simulation — animate rising water on DEM."""
    import matplotlib.pyplot as plt

    print("=== Flood Inundation Map ===")
    # Kentucky River at Frankfort — read full tile for proper proportions
    bbox = (-84.89, 38.18, -84.85, 38.22)

    tiles = abovepy.search(bbox=bbox, product="dem_phase3")
    if len(tiles) == 0:
        print("  No tiles found, skipping")
        return

    data, profile = abovepy.read(tiles.iloc[0].asset_url)
    dem = data.squeeze().astype(np.float64)
    print(f"  DEM shape: {dem.shape}")

    # Find approximate river level (low percentile of elevation)
    river_level = np.percentile(dem[dem > 0], 2)
    print(f"  Estimated river level: {river_level:.0f} ft")

    # Generate static image at multiple flood stages
    stages = [0, 5, 10, 20, 30]
    fig, axes = plt.subplots(1, len(stages), figsize=(20, 5))

    for i, rise in enumerate(stages):
        water_level = river_level + rise
        flooded = dem <= water_level
        flooded[dem <= 0] = False  # mask nodata

        display = dem.copy()
        display[flooded] = np.nan

        axes[i].imshow(dem, cmap="terrain", alpha=0.7)
        axes[i].imshow(
            np.where(flooded, 1, np.nan),
            cmap="Blues", vmin=0, vmax=1.5, alpha=0.7,
        )
        pct = flooded.sum() / (dem > 0).sum() * 100
        axes[i].set_title(f"+{rise}ft\n{pct:.1f}% flooded")
        axes[i].axis("off")

    plt.suptitle(
        "Flood Inundation Simulation — Kentucky River, Frankfort",
        fontsize=14, color=_TITLE_COLOR,
    )
    _apply_wcag_style(fig, list(axes))
    plt.tight_layout()
    path = OUTPUT / "flood_inundation.png"
    plt.savefig(str(path), dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


def generate_flood_gif():
    """Generate animated GIF of rising floodwater."""
    import matplotlib.pyplot as plt

    try:
        import imageio.v3 as iio
    except ImportError:
        print("  imageio not installed, skipping GIF")
        return

    print("=== Flood Inundation GIF ===")
    bbox = (-84.89, 38.18, -84.85, 38.22)

    tiles = abovepy.search(bbox=bbox, product="dem_phase3")
    if len(tiles) == 0:
        print("  No tiles found, skipping")
        return

    data, profile = abovepy.read(tiles.iloc[0].asset_url)
    dem = data.squeeze().astype(np.float64)
    river_level = np.percentile(dem[dem > 0], 2)

    frames = []
    rises = list(range(0, 41, 2))  # 0 to 40 ft in 2ft steps

    for rise in rises:
        fig, ax = plt.subplots(figsize=(8, 6))
        water_level = river_level + rise
        flooded = (dem <= water_level) & (dem > 0)

        ax.imshow(dem, cmap="terrain", alpha=0.8)
        ax.imshow(
            np.where(flooded, 1.0, np.nan),
            cmap="Blues", vmin=0, vmax=1.5, alpha=0.7,
        )
        pct = flooded.sum() / (dem > 0).sum() * 100
        ax.set_title(
            f"Flood Simulation — Kentucky River, Frankfort\n"
            f"Water +{rise}ft  |  {pct:.1f}% inundated",
            fontsize=12, color=_TITLE_COLOR,
        )
        ax.axis("off")
        _apply_wcag_style(fig, [ax])
        plt.tight_layout()

        # Render to numpy array
        fig.canvas.draw()
        buf = np.asarray(fig.canvas.buffer_rgba())
        frame = buf[:, :, :3].copy()  # RGBA -> RGB
        frames.append(frame)
        plt.close()

    # Write GIF — hold last frame longer
    path = OUTPUT / "flood_simulation.gif"
    durations = [200] * len(frames)
    durations[-1] = 2000  # pause 2s on final frame
    iio.imwrite(str(path), frames, duration=durations, loop=0)
    print(f"  Saved: {path} ({len(frames)} frames)")


def generate_slope_aspect():
    """Compute slope and aspect maps from DEM."""
    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize

    print("=== Slope & Aspect Map ===")
    bbox = (-84.87, 38.19, -84.86, 38.20)
    tiles = abovepy.search(bbox=bbox, product="dem_phase3")
    if len(tiles) == 0:
        print("  No tiles found, skipping")
        return

    data, profile = abovepy.read(tiles.iloc[0].asset_url)
    dem = data.squeeze().astype(np.float64)
    res = abs(profile["transform"][0])
    print(f"  DEM shape: {dem.shape}, res: {res:.1f} ft")

    # Slope in degrees
    dx, dy = np.gradient(dem, res, res)
    slope_deg = np.degrees(np.arctan(np.sqrt(dx**2 + dy**2)))

    # Aspect in degrees (0=N, 90=E, 180=S, 270=W)
    aspect = np.degrees(np.arctan2(-dy, dx))
    aspect = (90 - aspect) % 360  # convert to compass bearing

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    axes[0].imshow(dem, cmap="terrain")
    axes[0].set_title("Elevation (ft)")
    axes[0].axis("off")

    im1 = axes[1].imshow(slope_deg, cmap="YlOrRd",
                         norm=Normalize(vmin=0, vmax=45))
    axes[1].set_title("Slope (degrees)")
    axes[1].axis("off")
    fig.colorbar(im1, ax=axes[1], shrink=0.8, label="Degrees")

    im2 = axes[2].imshow(aspect, cmap="hsv",
                         norm=Normalize(vmin=0, vmax=360))
    axes[2].set_title("Aspect (compass bearing)")
    axes[2].axis("off")
    fig.colorbar(im2, ax=axes[2], shrink=0.8, label="Degrees (0=N)")

    plt.suptitle("Slope & Aspect Analysis — Frankfort, KY",
                 fontsize=14, color=_TITLE_COLOR)
    _apply_wcag_style(fig, list(axes))
    plt.tight_layout()
    path = OUTPUT / "slope_aspect.png"
    plt.savefig(str(path), dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


def generate_land_use_change():
    """Side-by-side ortho comparison — Phase 1 vs Phase 3."""
    import matplotlib.pyplot as plt

    print("=== Land Use Change ===")
    # Area near Lexington with development activity
    bbox = (-84.52, 38.00, -84.50, 38.02)

    tiles1 = abovepy.search(bbox=bbox, product="ortho_phase1")
    tiles3 = abovepy.search(bbox=bbox, product="ortho_phase3")

    if len(tiles1) == 0 or len(tiles3) == 0:
        print("  Missing ortho tiles, skipping")
        return

    # Read full tiles for proper square images
    data1, p1 = abovepy.read(tiles1.iloc[0].asset_url)
    data3, p3 = abovepy.read(tiles3.iloc[0].asset_url)
    print(f"  Phase 1: {data1.shape}, Phase 3: {data3.shape}")

    fig, axes = plt.subplots(
        1, 2, figsize=(14, 7),
        gridspec_kw={"width_ratios": [1, 1]},
    )

    if data1.shape[0] >= 3:
        rgb1 = np.moveaxis(data1[:3], 0, -1)
        axes[0].imshow(rgb1)
    else:
        axes[0].imshow(data1.squeeze(), cmap="gray")
    axes[0].set_title(f"Ortho Phase 1 (6in)\n{data1.shape[1]}x{data1.shape[2]}px")
    axes[0].axis("off")

    if data3.shape[0] >= 3:
        rgb3 = np.moveaxis(data3[:3], 0, -1)
        axes[1].imshow(rgb3)
    else:
        axes[1].imshow(data3.squeeze(), cmap="gray")
    axes[1].set_title(f"Ortho Phase 3 (3in)\n{data3.shape[1]}x{data3.shape[2]}px")
    axes[1].axis("off")

    plt.suptitle("Land Use Change — Lexington, KY",
                 fontsize=14, color=_TITLE_COLOR)
    _apply_wcag_style(fig, list(axes))
    plt.tight_layout()
    path = OUTPUT / "land_use_change.png"
    plt.savefig(str(path), dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


def generate_contour_map():
    """Generate elevation contour lines over hillshade."""
    import matplotlib.pyplot as plt

    print("=== Contour Map ===")
    bbox = (-84.87, 38.19, -84.86, 38.20)
    tiles = abovepy.search(bbox=bbox, product="dem_phase3")
    if len(tiles) == 0:
        print("  No tiles found, skipping")
        return

    data, profile = abovepy.read(tiles.iloc[0].asset_url)
    dem = data.squeeze().astype(np.float64)
    res = abs(profile["transform"][0])

    # Hillshade for backdrop
    dx, dy = np.gradient(dem, res, res)
    slope = np.sqrt(dx**2 + dy**2)
    aspect = np.arctan2(-dy, dx)
    az, alt = np.radians(315), np.radians(45)
    hs = (np.sin(alt) * np.cos(np.arctan(slope))
          + np.cos(alt) * np.sin(np.arctan(slope)) * np.cos(az - aspect))
    hs = np.clip(hs * 255, 0, 255).astype(np.uint8)

    fig, ax = plt.subplots(figsize=(10, 10))
    ax.imshow(hs, cmap="gray", alpha=0.6)

    # Contour lines every 10ft, bold every 50ft
    levels_minor = np.arange(
        int(dem.min() / 10) * 10, dem.max(), 10,
    )
    levels_major = np.arange(
        int(dem.min() / 50) * 50, dem.max(), 50,
    )
    ax.contour(dem, levels=levels_minor, colors="sienna",
               linewidths=0.3, alpha=0.5)
    cs = ax.contour(dem, levels=levels_major, colors="sienna",
                    linewidths=1.0)
    ax.clabel(cs, inline=True, fontsize=7, fmt="%.0f ft")

    ax.set_title("Elevation Contours over Hillshade — Frankfort, KY",
                 color=_TITLE_COLOR)
    ax.axis("off")
    _apply_wcag_style(fig, [ax])
    plt.tight_layout()
    path = OUTPUT / "contour_map.png"
    plt.savefig(str(path), dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


def generate_multi_county_coverage():
    """Map tile coverage across multiple counties."""
    import matplotlib.pyplot as plt

    print("=== Multi-County Coverage Map ===")
    counties = ["Franklin", "Woodford", "Anderson", "Scott", "Fayette"]
    colors = ["#2196F3", "#4CAF50", "#FF9800", "#9C27B0", "#E91E63"]

    fig, ax = plt.subplots(figsize=(12, 10))

    import matplotlib.patches as mpatches

    handles = []
    for county, color in zip(counties, colors, strict=True):
        tiles = abovepy.search(county=county, product="dem_phase3")
        tiles.plot(
            ax=ax, edgecolor=color, facecolor=color,
            alpha=0.3, linewidth=0.3,
        )
        handles.append(
            mpatches.Patch(color=color, alpha=0.5,
                           label=f"{county} ({len(tiles)})"),
        )
        print(f"  {county}: {len(tiles)} tiles")

    ax.legend(handles=handles, fontsize=10, title="County (tile count)")
    ax.set_title("DEM Phase 3 Coverage — Central Kentucky",
                 fontsize=14, color=_TITLE_COLOR)
    ax.set_xlabel("Longitude", color=_LABEL_COLOR)
    ax.set_ylabel("Latitude", color=_LABEL_COLOR)
    _apply_wcag_style(fig, [ax])
    plt.tight_layout()
    path = OUTPUT / "multi_county_coverage.png"
    plt.savefig(str(path), dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


def generate_elevation_profile():
    """Extract an elevation profile along a transect line."""
    import matplotlib.pyplot as plt

    print("=== Elevation Profile ===")
    # Transect across the Kentucky River valley
    bbox = (-84.89, 38.185, -84.85, 38.215)
    tiles = abovepy.search(bbox=bbox, product="dem_phase3")
    if len(tiles) == 0:
        print("  No tiles found, skipping")
        return

    data, profile = abovepy.read(tiles.iloc[0].asset_url)
    dem = data.squeeze().astype(np.float64)
    transform = profile["transform"]
    print(f"  DEM shape: {dem.shape}")

    # Draw a horizontal transect at the middle row
    mid_row = dem.shape[0] // 2
    elev_profile = dem[mid_row, :]

    # Compute distance in feet along the transect
    res = abs(transform[0])
    distances = np.arange(len(elev_profile)) * res

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(12, 8),
        gridspec_kw={"height_ratios": [2, 1]},
    )

    # Map view with transect line
    ax1.imshow(dem, cmap="terrain")
    ax1.axhline(y=mid_row, color="red", linewidth=2, linestyle="--")
    ax1.set_title("DEM with Transect Line")
    ax1.axis("off")

    # Profile plot
    ax2.fill_between(distances, elev_profile, alpha=0.3, color="teal")
    ax2.plot(distances, elev_profile, color="teal", linewidth=1)
    ax2.set_xlabel("Distance (ft)")
    ax2.set_ylabel("Elevation (ft)")
    ax2.set_title("Elevation Profile — Cross-Valley Transect")
    ax2.grid(True, alpha=0.3)
    ax2.ticklabel_format(style="plain", useOffset=False)

    plt.suptitle(
        "Elevation Profile — Kentucky River Valley, Frankfort",
        fontsize=14, color=_TITLE_COLOR,
    )
    _apply_wcag_style(fig, [ax1, ax2])
    plt.tight_layout()
    path = OUTPUT / "elevation_profile.png"
    plt.savefig(str(path), dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


def generate_multi_product_assessment():
    """Pull DEM + ortho for the same area — multi-product site report."""
    import matplotlib.pyplot as plt

    print("=== Multi-Product Site Assessment ===")
    # Kentucky State Capitol area — read full tiles for proper proportions
    bbox = (-84.878, 38.195, -84.872, 38.200)

    tiles_dem = abovepy.search(bbox=bbox, product="dem_phase3")
    tiles_ortho = abovepy.search(bbox=bbox, product="ortho_phase3")

    if len(tiles_dem) == 0 or len(tiles_ortho) == 0:
        print("  Missing tiles, skipping")
        return

    # Read full tiles for square images
    data_dem, p_dem = abovepy.read(tiles_dem.iloc[0].asset_url)
    data_ortho, p_ortho = abovepy.read(tiles_ortho.iloc[0].asset_url)

    dem = data_dem.squeeze().astype(np.float64)
    res = abs(p_dem["transform"][0])
    dx, dy = np.gradient(dem, res, res)
    slope_deg = np.degrees(np.arctan(np.sqrt(dx**2 + dy**2)))
    # Hillshade
    slope_r = np.sqrt(dx**2 + dy**2)
    aspect = np.arctan2(-dy, dx)
    az, alt = np.radians(315), np.radians(45)
    hs = (np.sin(alt) * np.cos(np.arctan(slope_r))
          + np.cos(alt) * np.sin(np.arctan(slope_r)) * np.cos(az - aspect))
    hs = np.clip(hs * 255, 0, 255).astype(np.uint8)

    print(f"  DEM: {dem.shape}, Ortho: {data_ortho.shape}")

    fig, axes = plt.subplots(2, 2, figsize=(14, 14))

    # Ortho
    if data_ortho.shape[0] >= 3:
        rgb = np.moveaxis(data_ortho[:3], 0, -1)
        axes[0, 0].imshow(rgb)
    axes[0, 0].set_title("Orthoimagery (3in)")
    axes[0, 0].axis("off")

    # DEM
    im1 = axes[0, 1].imshow(dem, cmap="terrain")
    axes[0, 1].set_title("Elevation (ft)")
    axes[0, 1].axis("off")
    fig.colorbar(im1, ax=axes[0, 1], shrink=0.8)

    # Hillshade
    axes[1, 0].imshow(hs, cmap="gray")
    axes[1, 0].set_title("Hillshade")
    axes[1, 0].axis("off")

    # Slope
    im3 = axes[1, 1].imshow(slope_deg, cmap="YlOrRd", vmin=0, vmax=30)
    axes[1, 1].set_title("Slope (degrees)")
    axes[1, 1].axis("off")
    fig.colorbar(im3, ax=axes[1, 1], shrink=0.8)

    plt.suptitle(
        "Multi-Product Site Assessment — KY State Capitol",
        fontsize=14, color=_TITLE_COLOR,
    )
    _apply_wcag_style(fig, list(axes.flat))
    plt.tight_layout()
    path = OUTPUT / "site_assessment.png"
    plt.savefig(str(path), dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


def generate_product_gallery():
    """Gallery showing one tile from each available product type."""
    import matplotlib.pyplot as plt

    print("=== Product Gallery ===")
    # Frankfort area
    bbox = (-84.87, 38.19, -84.86, 38.20)

    products = [
        ("dem_phase1", "DEM Phase 1 (5ft)", "terrain"),
        ("dem_phase2", "DEM Phase 2 (2ft)", "terrain"),
        ("dem_phase3", "DEM Phase 3 (2ft)", "terrain"),
        ("ortho_phase3", "Ortho Phase 3 (3in)", None),
    ]

    fig, axes = plt.subplots(1, len(products), figsize=(20, 6))

    for i, (prod, title, cmap) in enumerate(products):
        tiles = abovepy.search(bbox=bbox, product=prod)
        if len(tiles) == 0:
            axes[i].text(0.5, 0.5, "No data", ha="center", va="center",
                         transform=axes[i].transAxes)
            axes[i].set_title(title)
            axes[i].axis("off")
            continue

        data, profile = abovepy.read(tiles.iloc[0].asset_url, bbox=bbox)
        print(f"  {prod}: {data.shape}")

        if cmap:
            axes[i].imshow(data.squeeze(), cmap=cmap)
        elif data.shape[0] >= 3:
            rgb = np.moveaxis(data[:3], 0, -1)
            axes[i].imshow(rgb)
        else:
            axes[i].imshow(data.squeeze(), cmap="gray")
        axes[i].set_title(title)
        axes[i].axis("off")

    plt.suptitle("KyFromAbove Product Gallery — Frankfort, KY",
                 fontsize=14, color=_TITLE_COLOR)
    _apply_wcag_style(fig, list(axes))
    plt.tight_layout()
    path = OUTPUT / "product_gallery.png"
    plt.savefig(str(path), dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


if __name__ == "__main__":
    import matplotlib
    matplotlib.use("Agg")

    generate_dem_change_detection()
    generate_flood_inundation()
    generate_flood_gif()
    generate_slope_aspect()
    generate_land_use_change()
    generate_contour_map()
    generate_multi_county_coverage()
    generate_elevation_profile()
    generate_multi_product_assessment()
    generate_product_gallery()
    print("\nDone! All v2 images saved to examples/output/")
