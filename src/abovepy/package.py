"""Deliverable packaging for abovepy search results.

Produces a self-contained folder with data tiles, footprint index,
checksums, provenance metadata, preview image, and optional QGIS project.
"""

from __future__ import annotations

import hashlib
import httpx
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path

logger = logging.getLogger(__name__)

_CHUNK_SIZE = 256 * 1024  # 256 KB


@dataclass
class Package:
    """A completed deliverable package."""

    output_dir: Path
    files: list[Path]
    manifest: dict
    tile_count: int
    total_size_mb: float
    has_qgis_project: bool

    def __repr__(self) -> str:
        return (
            f"Package({self.output_dir.name!r}, "
            f"{self.tile_count} tile(s), "
            f"{self.total_size_mb} MB, "
            f"qgis={self.has_qgis_project})"
        )


def _sha256_file(path: Path) -> str:
    """Compute SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(_CHUNK_SIZE):
            h.update(chunk)
    return h.hexdigest()


def _compute_checksums(
    files: list[Path],
    base_dir: Path,
    max_workers: int = 4,
) -> dict[str, str]:
    """SHA-256 checksums computed in parallel.

    Returns {relative_path: hex_digest}.
    """
    if not files:
        return {}

    results: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(_sha256_file, f): f.relative_to(base_dir).as_posix()
            for f in files
        }
        for future in as_completed(futures):
            rel_path = futures[future]
            try:
                results[rel_path] = future.result()
            except OSError:
                logger.warning("Failed to checksum %s", rel_path)
                results[rel_path] = ""
    return results


def _render_disclaimer(
    product_display_name: str,
    tile_count: int,
) -> str:
    """Render the DISCLAIMER.txt template with package metadata."""
    template_text = (
        resources.files("abovepy.templates")
        .joinpath("DISCLAIMER.txt")
        .read_text(encoding="utf-8")
    )
    return template_text.format(
        timestamp=datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        product_display_name=product_display_name,
        tile_count=tile_count,
    )


def _build_manifest(
    output_dir: Path,
    data_files: list[Path],
    checksums: dict[str, str],
    product_key: str,
    display_name: str,
    crs: str,
    aoi_bbox: tuple[float, float, float, float],
    aoi_wkt: str,
    query_params: dict,
    acquisition_period: str,
) -> dict:
    """Build the manifest.json contents."""
    from abovepy._version import __version__

    files = []
    for f in data_files:
        rel = f.relative_to(output_dir).as_posix()
        files.append({
            "path": rel,
            "sha256": checksums.get(rel) or None,
            "size_bytes": f.stat().st_size,
        })

    total_bytes = sum(entry["size_bytes"] for entry in files)

    return {
        "abovepy_version": __version__,
        "created_at": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "product": product_key,
        "display_name": display_name,
        "crs": crs,
        "tile_count": len(data_files),
        "total_size_mb": round(total_bytes / (1024 * 1024), 1),
        "aoi_bbox": list(aoi_bbox),
        "aoi_wkt": aoi_wkt,
        "query": query_params,
        "acquisition_period": acquisition_period,
        "source_program": "KyFromAbove",
        "files": files,
    }


def _generate_preview(
    search_result: object,
    output_path: Path,
    width: int = 1024,
    height: int = 1024,
) -> Path | None:
    """Generate a preview image. TiTiler first, then matplotlib fallback.

    Returns path to written file, or None if preview could not be generated.
    """
    # Try TiTiler
    try:
        from abovepy.viz import preview_url

        url = preview_url(
            product=search_result.product.key,  # type: ignore[attr-defined]
            bbox=search_result.bbox,  # type: ignore[attr-defined]
            width=width,
            height=height,
        )
        resp = httpx.get(url, timeout=30, follow_redirects=True)
        if resp.status_code == 200 and len(resp.content) > 0:
            output_path.write_bytes(resp.content)
            return output_path
    except Exception:
        logger.debug("TiTiler preview failed, trying matplotlib fallback")

    # Matplotlib fallback
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
        import rasterio

        tiles_gdf = search_result.tiles  # type: ignore[attr-defined]
        first_url = tiles_gdf.iloc[0]["asset_url"]

        with rasterio.open(first_url) as src:
            data = src.read()
            profile = dict(src.profile)

        product_type = search_result.product.product_type.value  # type: ignore[attr-defined]
        if product_type == "dem":
            from abovepy.terrain import hillshade
            hs, _ = hillshade(data, profile)
            plt.imsave(str(output_path), hs[0], cmap="gray")
        else:
            rgb = np.moveaxis(data[:3], 0, -1)
            plt.imsave(str(output_path), rgb)

        return output_path
    except Exception:
        logger.warning("Preview generation failed (both TiTiler and matplotlib)")
        return None
