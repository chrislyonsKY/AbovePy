"""Oblique Site Inspection — practical use of oblique imagery.

Demonstrates a real-world workflow: given a location of interest (e.g., a
bridge, building, or construction site), find oblique frames from all four
camera directions and generate a multi-view composite for site inspection.

This is useful for:
  - Infrastructure inspection (bridges, dams, towers)
  - Construction progress monitoring
  - Damage assessment after storms/floods
  - Property assessment and appraisal
  - Environmental monitoring

Usage:
    python oblique_site_inspection.py

Requires:
    pip install abovepy matplotlib httpx
"""

from pathlib import Path

from abovepy.obliques import list_oblique_seasons, search_obliques
from abovepy.products import ProductType, list_products

OUTPUT = Path(__file__).parent.parent / "output"
OUTPUT.mkdir(parents=True, exist_ok=True)

# WCAG 2.1 AA compliant colors
_TITLE_COLOR = "#222222"
_LABEL_COLOR = "#333333"


def _apply_wcag_style(fig, axes_list):
    """Apply WCAG 2.1 AA compliant text colors."""
    fig.patch.set_facecolor("white")
    for text in fig.texts:
        text.set_color(_TITLE_COLOR)
    for ax in axes_list:
        ax.title.set_color(_TITLE_COLOR)
        ax.xaxis.label.set_color(_LABEL_COLOR)
        ax.yaxis.label.set_color(_LABEL_COLOR)
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_color(_LABEL_COLOR)


def main():
    # ---------------------------------------------------------------
    # 1. Show what oblique products are available
    # ---------------------------------------------------------------
    print("=== Oblique Imagery Products ===")
    obliques = list_products(ProductType.OBLIQUE)
    for p in obliques:
        print(f"  {p.key:25s}  {p.display_name}")

    # ---------------------------------------------------------------
    # 2. List available seasons
    # ---------------------------------------------------------------
    print("\n=== Available Acquisition Seasons ===")
    seasons = list_oblique_seasons()
    for s in seasons:
        print(f"  {s}")

    latest = seasons[-1]
    print(f"\n  Using latest: {latest}")

    # ---------------------------------------------------------------
    # 3. Find matching frames from all 4 directions
    # ---------------------------------------------------------------
    print("\n=== Finding Oblique Frames ===")
    directions = ["bwd", "fwd", "left", "right"]
    direction_labels = {
        "bwd": "Backward (South-facing)",
        "fwd": "Forward (North-facing)",
        "left": "Left (West-facing)",
        "right": "Right (East-facing)",
    }

    all_frames = {}
    for d in directions:
        frames = search_obliques(direction=d, season=latest, max_items=5)
        all_frames[d] = frames
        print(f"  {direction_labels[d]:30s}  {len(frames)} frames")
        if frames:
            print(f"    Example: {frames[0]['frame_id']}")

    # ---------------------------------------------------------------
    # 4. Show how frame IDs correspond across directions
    # ---------------------------------------------------------------
    print("\n=== Frame Correspondence ===")
    print("  Frames from the same flight line share a common ID suffix.")
    print("  For example, frame *_10001_18736 from each direction shows")
    print("  the same ground area from 4 different angles.\n")

    # Find a common frame number across directions
    if all(all_frames[d] for d in directions):
        # Extract frame numbers (last part of frame_id)
        bwd_nums = {f["frame_id"].split("_", 1)[1] for f in all_frames["bwd"]}
        common = None
        for f in all_frames["fwd"]:
            num = f["frame_id"].split("_", 1)[1]
            if num in bwd_nums:
                common = num
                break

        if common:
            print(f"  Common frame: {common}")
            for d in directions:
                prefix = d.capitalize() if d != "bwd" else "Bwd"
                if d == "fwd":
                    prefix = "Fwd"
                frame_id = f"{prefix}_{common}"
                matching = [f for f in all_frames[d] if f["frame_id"] == frame_id]
                if matching:
                    print(f"    {direction_labels[d]:30s}  {matching[0]['tif_url']}")

    # ---------------------------------------------------------------
    # 5. Site inspection workflow summary
    # ---------------------------------------------------------------
    print("\n=== Site Inspection Workflow ===")
    print("  1. Identify location of interest (lat/lon or address)")
    print("  2. Search oblique frames from all 4 directions")
    print("  3. Download matching frames:")
    print("       import abovepy")
    print("       data, profile = abovepy.read(frame['tif_url'])")
    print("  4. Create multi-view composite for inspection report")
    print("  5. Compare with DEM/ortho for elevation context:")
    print("       from abovepy.viz import tile_url")
    print("       hillshade = tile_url('dem_phase3', bbox=..., algorithm='hillshade')")
    print()

    # ---------------------------------------------------------------
    # 6. Generate a visual summary (metadata only — no large downloads)
    # ---------------------------------------------------------------
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("  Install matplotlib for visualization: pip install matplotlib")
        return

    print("=== Generating Frame Index Map ===")
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    # Paul Tol colorblind-safe palette
    dir_colors = {
        "bwd": "#0077BB",
        "fwd": "#EE7733",
        "left": "#009988",
        "right": "#CC3311",
    }

    for ax, d in zip(axes.flat, directions, strict=True):
        frames = all_frames[d]
        color = dir_colors[d]

        # Show frame count and sample IDs
        ax.set_facecolor("#f8f8f8")
        frame_text = "\n".join(f["frame_id"] for f in frames[:8])
        if len(frames) > 8:
            frame_text += f"\n... +{len(frames) - 8} more"

        ax.text(
            0.5, 0.5,
            f"{direction_labels[d]}\n\n"
            f"{len(frames)} frames in {latest}\n\n"
            f"{frame_text}",
            ha="center", va="center",
            fontsize=10, color=_TITLE_COLOR,
            transform=ax.transAxes,
            fontfamily="monospace",
        )
        ax.set_title(
            f"{d.upper()} Direction",
            fontsize=13, fontweight="bold", color=color,
        )
        for spine in ax.spines.values():
            spine.set_color(color)
            spine.set_linewidth(2)
        ax.set_xticks([])
        ax.set_yticks([])

    plt.suptitle(
        f"KyFromAbove Oblique Imagery — {latest}\n"
        "4-Direction Frame Index for Site Inspection",
        fontsize=14, color=_TITLE_COLOR,
    )
    _apply_wcag_style(fig, list(axes.flat))
    plt.tight_layout()

    path = OUTPUT / "oblique_site_inspection.png"
    plt.savefig(str(path), dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


if __name__ == "__main__":
    main()
