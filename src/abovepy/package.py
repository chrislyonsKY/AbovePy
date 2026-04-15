"""Deliverable packaging for abovepy search results.

Produces a self-contained folder with data tiles, footprint index,
checksums, provenance metadata, preview image, and optional QGIS project.
"""

from __future__ import annotations

import hashlib
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib import resources
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

_CHUNK_SIZE = 256 * 1024  # 256 KB


@dataclass
class Package:
    """A completed deliverable package."""

    output_dir: Path
    files: list[Path]
    manifest: dict[str, object]
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
        futures = {pool.submit(_sha256_file, f): f.relative_to(base_dir).as_posix() for f in files}
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
        resources.files("abovepy.templates").joinpath("DISCLAIMER.txt").read_text(encoding="utf-8")
    )
    return template_text.format(
        timestamp=datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
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
    query_params: dict[str, object],
    acquisition_period: str,
) -> dict[str, object]:
    """Build the manifest.json contents."""
    from abovepy._version import __version__

    files = []
    for f in data_files:
        rel = f.relative_to(output_dir).as_posix()
        files.append(
            {
                "path": rel,
                "sha256": checksums.get(rel) or None,
                "size_bytes": f.stat().st_size,
            }
        )

    total_bytes = sum(int(entry["size_bytes"]) for entry in files)

    return {
        "abovepy_version": __version__,
        "created_at": datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
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

            hs, _ = hillshade(data, profile)  # type: ignore[arg-type]
            plt.imsave(str(output_path), hs[0], cmap="gray")
        else:
            rgb = np.moveaxis(data[:3], 0, -1)
            plt.imsave(str(output_path), rgb)

        return output_path
    except Exception:
        logger.warning("Preview generation failed (both TiTiler and matplotlib)")
        return None


# Module-level import so tests can patch abovepy.package.download_tiles
from abovepy._download import download_tiles  # noqa: E402


def build_package(
    search_result: object,
    output_dir: str | Path,
    clip_bbox: tuple[float, float, float, float] | None = None,
    include_preview: bool = True,
    qgis_project: bool = True,
    checksums: bool = True,
    overwrite: bool = False,
    max_workers: int = 4,
) -> Package:
    """Build a deliverable package from a SearchResult."""
    from abovepy._exceptions import PackageError

    output_dir = Path(output_dir)

    if search_result.empty:  # type: ignore[attr-defined]
        raise PackageError("No tiles to package")

    if output_dir.exists() and not overwrite and (output_dir / "manifest.json").exists():
        raise PackageError(
            f"Output directory already contains a package: {output_dir}. "
            "Use overwrite=True to replace."
        )

    data_dir = output_dir / "data"
    styles_dir = output_dir / "styles"
    data_dir.mkdir(parents=True, exist_ok=True)
    styles_dir.mkdir(parents=True, exist_ok=True)

    # 1. Download tiles
    tiles_gdf = search_result.tiles  # type: ignore[attr-defined]
    downloaded = download_tiles(
        tiles_gdf,
        output_dir=data_dir,
        overwrite=overwrite,
        max_workers=max_workers,
    )

    # 2. Build footprints GeoPackage
    from abovepy.qgis import _build_footprints_gpkg

    footprints_path = data_dir / "footprints.gpkg"
    _build_footprints_gpkg(tiles_gdf, footprints_path)

    # 3. Compute checksums
    file_checksums: dict[str, str] = {}
    if checksums and downloaded:
        file_checksums = _compute_checksums(
            downloaded, base_dir=output_dir, max_workers=max_workers
        )

    # 4. Generate preview
    preview_path = output_dir / "preview.png"
    if include_preview:
        _generate_preview(search_result, preview_path)

    # 5. Build and write manifest
    product = search_result.product  # type: ignore[attr-defined]
    query_params = search_result.query_params  # type: ignore[attr-defined]
    bbox = search_result.bbox  # type: ignore[attr-defined]

    from shapely.ops import unary_union

    aoi_geom = unary_union(tiles_gdf.geometry)
    aoi_wkt = aoi_geom.wkt

    acquisition_period = (
        f"{product.acquisition_start}-{product.acquisition_end}"
        if product.acquisition_start
        else "unknown"
    )

    manifest = _build_manifest(
        output_dir=output_dir,
        data_files=downloaded,
        checksums=file_checksums,
        product_key=product.key,
        display_name=product.display_name,
        crs=product.native_crs or "EPSG:3089",
        aoi_bbox=bbox,
        aoi_wkt=aoi_wkt,
        query_params=query_params,
        acquisition_period=acquisition_period,
    )
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, default=str), encoding="utf-8"
    )

    # 6. Write provenance
    provenance = search_result.provenance()  # type: ignore[attr-defined]
    (output_dir / "provenance.json").write_text(
        json.dumps(provenance, indent=2, default=str), encoding="utf-8"
    )

    # 7. Write DISCLAIMER
    disclaimer = _render_disclaimer(
        product_display_name=product.display_name,
        tile_count=len(downloaded),
    )
    (output_dir / "DISCLAIMER.txt").write_text(disclaimer, encoding="utf-8")

    # 8. Copy style files
    templates_dir = resources.files("abovepy.templates")
    for qml_name in ["dem_hillshade.qml", "ortho_rgb.qml", "footprints_outline.qml"]:
        qml_source = templates_dir.joinpath(qml_name)
        if qml_source.is_file():
            (styles_dir / qml_name).write_text(
                qml_source.read_text(encoding="utf-8"),
                encoding="utf-8",
            )

    # 9. Generate QGIS project
    has_qgis = False
    if qgis_project:
        try:
            from abovepy.qgis import generate_project
            from abovepy.utils.crs import transform_bbox

            extent_3089 = transform_bbox(bbox, "EPSG:4326", "EPSG:3089")

            generate_project(
                package_dir=output_dir,
                tiles=downloaded,
                footprints_path=footprints_path,
                product=product,
                extent=extent_3089,
                styles_dir=styles_dir,
            )
            has_qgis = True
        except Exception:
            logger.warning("QGIS project generation failed")

    all_files = sorted(f for f in output_dir.rglob("*") if f.is_file())
    total_bytes = sum(f.stat().st_size for f in downloaded) if downloaded else 0

    return Package(
        output_dir=output_dir,
        files=all_files,
        manifest=manifest,
        tile_count=len(downloaded),
        total_size_mb=round(total_bytes / (1024 * 1024), 1),
        has_qgis_project=has_qgis,
    )
