"""Export helpers — write data to GIS-standard formats.

Convenience wrappers around rasterio (raster) and geopandas/fiona (vector)
for writing search results and analysis outputs to common GIS formats.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    import geopandas as gpd


def to_geotiff(
    data: np.ndarray,
    profile: dict[str, Any],
    output: str | Path,
    compress: str = "deflate",
) -> Path:
    """Write a numpy array + profile dict to a Cloud-Optimized GeoTIFF.

    Parameters
    ----------
    data : numpy.ndarray
        2D or 3D (bands, height, width) raster array.
    profile : dict
        Rasterio profile dict (from ``abovepy.read()``).
    output : str or Path
        Output file path.
    compress : str
        Compression method. Default ``"deflate"``.

    Returns
    -------
    Path
        Path to the written file.
    """
    import rasterio

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    # Ensure 3D (bands, height, width)
    if data.ndim == 2:
        data = data[np.newaxis, :, :]

    write_profile = dict(profile)
    write_profile.update(
        driver="GTiff",
        count=data.shape[0],
        height=data.shape[1],
        width=data.shape[2],
        dtype=data.dtype.name,
        compress=compress,
        tiled=True,
        blockxsize=256,
        blockysize=256,
    )

    with rasterio.open(output, "w", **write_profile) as dst:
        dst.write(data)

    return output


def to_geopackage(
    gdf: gpd.GeoDataFrame,
    output: str | Path,
    layer: str = "tiles",
) -> Path:
    """Write a GeoDataFrame to GeoPackage.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        Data to write.
    output : str or Path
        Output file path (should end in ``.gpkg``).
    layer : str
        Layer name within the GeoPackage. Default ``"tiles"``.

    Returns
    -------
    Path
        Path to the written file.
    """
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(output, layer=layer, driver="GPKG")
    return output


def to_shapefile(
    gdf: gpd.GeoDataFrame,
    output: str | Path,
) -> Path:
    """Write a GeoDataFrame to Shapefile.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        Data to write.
    output : str or Path
        Output file path (should end in ``.shp``).

    Returns
    -------
    Path
        Path to the written file.
    """
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(output, driver="ESRI Shapefile")
    return output
