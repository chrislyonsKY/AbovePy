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


def _stringify_object_columns(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """JSON-encode dict/list columns so OGR/parquet writers accept them.

    The ``assets`` column added in v2.2 holds a dict per tile, which
    GeoPackage, Shapefile, and (reliably) GeoParquet cannot store natively.
    """
    import json

    out = gdf.copy()
    geometry_col = out.geometry.name if out.geometry is not None else None
    for col in out.columns:
        if col == geometry_col:
            continue
        if out[col].map(lambda v: isinstance(v, dict | list)).any():
            out[col] = out[col].map(
                lambda v: json.dumps(v, default=str) if isinstance(v, dict | list) else v
            )
    return out


def to_geopackage(
    gdf: gpd.GeoDataFrame,
    output: str | Path,
    layer: str = "tiles",
) -> Path:
    """Write a GeoDataFrame to GeoPackage.

    Dict-valued columns (e.g. ``assets``) are JSON-encoded to strings.

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
    _stringify_object_columns(gdf).to_file(output, layer=layer, driver="GPKG")
    return output


def to_shapefile(
    gdf: gpd.GeoDataFrame,
    output: str | Path,
) -> Path:
    """Write a GeoDataFrame to Shapefile.

    Dict-valued columns (e.g. ``assets``) are JSON-encoded to strings.

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
    _stringify_object_columns(gdf).to_file(output, driver="ESRI Shapefile")
    return output


def to_stl(
    data: np.ndarray,
    profile: dict[str, Any],
    output: str | Path,
    exaggeration: float = 1.0,
    base_height: float | None = None,
    decimate: int = 1,
) -> Path:
    """Write a DEM array to a binary STL file for 3D printing.

    Converts the DEM grid into a watertight 3D mesh with a flat base,
    suitable for direct import into slicer software (Bambu Studio,
    Cura, PrusaSlicer) or 3D modeling tools (Blender, MeshLab).

    No external dependencies beyond numpy.

    Parameters
    ----------
    data : numpy.ndarray
        2D or 3D elevation array (from ``abovepy.read()``).
    profile : dict
        Rasterio profile dict with ``transform``, ``nodata``.
    output : str or Path
        Output file path (should end in ``.stl``).
    exaggeration : float
        Vertical exaggeration factor. ``1.0`` = true scale,
        ``2.0`` = double height. Default ``1.0``.
    base_height : float or None
        Elevation of the flat base. ``None`` auto-sets to just
        below the minimum elevation. Default ``None``.
    decimate : int
        Sample every Nth pixel. ``1`` = full resolution,
        ``2`` = every other pixel, etc. Default ``1``.

    Returns
    -------
    Path
        Path to the written STL file.
    """
    import struct

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    # Squeeze to 2D
    arr = np.squeeze(data).astype(np.float64)
    if arr.ndim != 2:
        raise ValueError(f"Expected 2D elevation array, got shape {data.shape}")

    nodata = profile.get("nodata")
    transform = profile["transform"]

    # Decimate
    if decimate > 1:
        arr = arr[::decimate, ::decimate]

    nrows, ncols = arr.shape

    # Replace nodata with NaN
    if nodata is not None:
        arr[arr == nodata] = np.nan

    # Fill NaN with minimum elevation so the mesh stays watertight
    valid_mask = ~np.isnan(arr)
    if not valid_mask.any():
        raise ValueError("No valid elevation data — all values are nodata or NaN")

    min_elev = float(np.nanmin(arr))
    arr = np.where(valid_mask, arr, min_elev)

    # Apply exaggeration
    arr = arr * exaggeration

    # Set base height
    if base_height is None:
        base_z = float(np.min(arr)) - abs(float(np.min(arr))) * 0.02 - 1.0
    else:
        base_z = base_height * exaggeration

    # Build coordinate grids — normalize to physical units from (0,0)
    # Use pixel spacing from the transform, scaled by decimate
    dx = abs(transform.a) * decimate
    dy = abs(transform.e) * decimate
    xs = np.arange(ncols, dtype=np.float64) * dx
    ys = np.arange(nrows, dtype=np.float64) * dy

    # --- Build triangles ---
    # Top surface: each grid quad → 2 triangles
    triangles: list[tuple[tuple[float, float, float], ...]] = []

    for r in range(nrows - 1):
        for c in range(ncols - 1):
            # Four corners of the quad
            p00 = (xs[c], ys[r], arr[r, c])
            p10 = (xs[c + 1], ys[r], arr[r, c + 1])
            p01 = (xs[c], ys[r + 1], arr[r + 1, c])
            p11 = (xs[c + 1], ys[r + 1], arr[r + 1, c + 1])

            triangles.append((p00, p10, p11))
            triangles.append((p00, p11, p01))

    # Bottom face (flat base)
    bl = (xs[0], ys[0], base_z)
    br = (xs[-1], ys[0], base_z)
    tl = (xs[0], ys[-1], base_z)
    tr = (xs[-1], ys[-1], base_z)
    triangles.append((bl, tr, br))
    triangles.append((bl, tl, tr))

    # Side walls
    # Front wall (row 0)
    for c in range(ncols - 1):
        top_l = (xs[c], ys[0], arr[0, c])
        top_r = (xs[c + 1], ys[0], arr[0, c + 1])
        bot_l = (xs[c], ys[0], base_z)
        bot_r = (xs[c + 1], ys[0], base_z)
        triangles.append((bot_l, top_r, top_l))
        triangles.append((bot_l, bot_r, top_r))

    # Back wall (last row)
    for c in range(ncols - 1):
        top_l = (xs[c], ys[-1], arr[-1, c])
        top_r = (xs[c + 1], ys[-1], arr[-1, c + 1])
        bot_l = (xs[c], ys[-1], base_z)
        bot_r = (xs[c + 1], ys[-1], base_z)
        triangles.append((bot_l, top_l, top_r))
        triangles.append((bot_l, top_r, bot_r))

    # Left wall (col 0)
    for r in range(nrows - 1):
        top_t = (xs[0], ys[r], arr[r, 0])
        top_b = (xs[0], ys[r + 1], arr[r + 1, 0])
        bot_t = (xs[0], ys[r], base_z)
        bot_b = (xs[0], ys[r + 1], base_z)
        triangles.append((bot_t, top_t, top_b))
        triangles.append((bot_t, top_b, bot_b))

    # Right wall (last col)
    for r in range(nrows - 1):
        top_t = (xs[-1], ys[r], arr[r, -1])
        top_b = (xs[-1], ys[r + 1], arr[r + 1, -1])
        bot_t = (xs[-1], ys[r], base_z)
        bot_b = (xs[-1], ys[r + 1], base_z)
        triangles.append((bot_t, top_b, top_t))
        triangles.append((bot_t, bot_b, top_b))

    # --- Write binary STL ---
    def _normal(
        v0: tuple[float, float, float],
        v1: tuple[float, float, float],
        v2: tuple[float, float, float],
    ) -> tuple[float, float, float]:
        """Compute triangle face normal."""
        u = (v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2])
        v = (v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2])
        nx = u[1] * v[2] - u[2] * v[1]
        ny = u[2] * v[0] - u[0] * v[2]
        nz = u[0] * v[1] - u[1] * v[0]
        length = (nx * nx + ny * ny + nz * nz) ** 0.5
        if length > 0:
            nx /= length
            ny /= length
            nz /= length
        return (nx, ny, nz)

    with open(output, "wb") as f:
        # 80-byte header
        header_text = b"AbovePy DEM STL Export"
        header = header_text + b"\0" * (80 - len(header_text))
        f.write(header)
        # Triangle count
        f.write(struct.pack("<I", len(triangles)))
        # Triangles
        for v0, v1, v2 in triangles:
            n = _normal(v0, v1, v2)
            f.write(struct.pack("<fff", *n))
            f.write(struct.pack("<fff", *v0))
            f.write(struct.pack("<fff", *v1))
            f.write(struct.pack("<fff", *v2))
            f.write(struct.pack("<H", 0))  # attribute byte count

    return output


def __getattr__(name: str) -> Any:
    if name == "to_landxml":
        raise AttributeError(
            "to_landxml() was removed in abovepy 2.2.0 along with the "
            "engineering-deliverables scope. Pin abovepy==2.1.3 if you depend "
            "on LandXML export, or use to_geotiff()/to_stl() for surface interchange."
        )
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
