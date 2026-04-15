"""QGIS project generation and interoperability.

Generates .qgs project files with pre-configured layers and styles.
Uses PyQGIS when available, falls back to XML template substitution.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import geopandas as gpd

logger = logging.getLogger(__name__)


def _build_footprints_gpkg(
    gdf: gpd.GeoDataFrame,
    output_path: Path,
    target_crs: str = "EPSG:3089",
) -> Path:
    """Build a GeoPackage footprint index from tile geometries.

    Parameters
    ----------
    gdf : GeoDataFrame
        Tile index with geometry in EPSG:4326.
    output_path : Path
        Where to write the .gpkg file.
    target_crs : str
        Output CRS. Default EPSG:3089.

    Returns
    -------
    Path
        Path to written .gpkg file.
    """
    cols = [c for c in ["tile_id", "product", "datetime", "asset_url", "geometry"] if c in gdf.columns]
    out_gdf = gdf[cols].copy()
    out_gdf = out_gdf.to_crs(target_crs)
    out_gdf.to_file(output_path, driver="GPKG", layer="tiles")
    return output_path
