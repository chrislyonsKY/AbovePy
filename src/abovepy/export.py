"""Export helpers — write data to GIS-standard formats.

Convenience wrappers around rasterio (raster) and geopandas/fiona (vector)
for writing search results and analysis outputs to common GIS formats.
Includes LandXML surface export for Civil 3D, Carlson, and OpenRoads Designer.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
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


def to_landxml(
    data: np.ndarray,
    profile: dict[str, Any],
    output: str | Path,
    surface_name: str = "KyFromAbove DEM",
    decimate: int = 1,
) -> Path:
    """Write a DEM array to a LandXML 1.2 TIN surface.

    Triangulates the DEM grid using Delaunay triangulation and writes
    the result as a LandXML file importable by Civil 3D, Carlson,
    OpenRoads Designer, and other CAD/survey software.

    Requires scipy (``pip install abovepy[analysis]``).

    Parameters
    ----------
    data : numpy.ndarray
        2D or 3D elevation array (from ``abovepy.read()``).
    profile : dict
        Rasterio profile dict with ``transform``, ``crs``, ``nodata``.
    output : str or Path
        Output file path (should end in ``.xml``).
    surface_name : str
        Name attribute on the LandXML Surface element.
        Default ``"KyFromAbove DEM"``.
    decimate : int
        Sample every Nth pixel to reduce file size. ``1`` = full
        resolution, ``2`` = every other pixel (~25% of points), etc.
        Default ``1``.

    Returns
    -------
    Path
        Path to the written LandXML file.
    """
    try:
        from scipy.spatial import Delaunay
    except ImportError:
        raise ImportError(
            "scipy is required for LandXML export. Install with: pip install abovepy[analysis]"
        ) from None

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    # Squeeze to 2D
    arr = np.squeeze(data)
    if arr.ndim != 2:
        raise ValueError(f"Expected 2D elevation array, got shape {data.shape}")

    transform = profile["transform"]
    nodata = profile.get("nodata")
    crs_str = str(profile.get("crs", ""))

    # Build coordinate arrays for valid (non-nodata) pixels
    rows = np.arange(arr.shape[0]).reshape(-1, 1) * np.ones((1, arr.shape[1]), dtype=np.intp)
    cols = np.ones((arr.shape[0], 1), dtype=np.intp) * np.arange(arr.shape[1]).reshape(1, -1)

    if decimate > 1:
        rows = rows[::decimate, ::decimate]
        cols = cols[::decimate, ::decimate]
        arr = arr[::decimate, ::decimate]

    rows_flat = rows.ravel()
    cols_flat = cols.ravel()
    elevations = arr.ravel()

    # Mask nodata
    if nodata is not None:
        valid = ~np.isnan(elevations) & (elevations != nodata)
    else:
        valid = ~np.isnan(elevations)

    rows_flat = rows_flat[valid]
    cols_flat = cols_flat[valid]
    elevations = elevations[valid]

    if len(elevations) < 3:
        raise ValueError("Not enough valid elevation points for triangulation (need >= 3)")

    # Convert pixel coords to map coords using the affine transform
    cols_f = cols_flat.astype(np.float64)
    rows_f = rows_flat.astype(np.float64)
    xs = np.asarray(transform.a * cols_f + transform.b * rows_f + transform.c)
    ys = np.asarray(transform.d * cols_f + transform.e * rows_f + transform.f)

    # Triangulate
    points_2d = np.column_stack([xs, ys])
    tri = Delaunay(points_2d)

    # Build LandXML
    ns = "http://www.landxml.org/schema/LandXML-1.2"
    root = ET.Element("LandXML", xmlns=ns, version="1.2")

    # Units
    units_el = ET.SubElement(root, "Units")
    if "3089" in crs_str or "foot" in crs_str.lower() or "feet" in crs_str.lower():
        ET.SubElement(
            units_el,
            "Imperial",
            linearUnit="usSurveyFoot",
            areaUnit="squareFoot",
            volumeUnit="cubicFeet",
        )
    else:
        ET.SubElement(
            units_el,
            "Metric",
            linearUnit="meter",
            areaUnit="squareMeter",
            volumeUnit="cubicMeter",
        )

    # Project
    ET.SubElement(root, "Project", name="KyFromAbove Export")

    # Surface
    surfaces = ET.SubElement(root, "Surfaces")
    surface = ET.SubElement(surfaces, "Surface", name=surface_name)
    definition = ET.SubElement(surface, "Definition", surfType="TIN")

    # Points — LandXML uses: northing easting elevation (Y X Z)
    pnts = ET.SubElement(definition, "Pnts")
    for i in range(len(elevations)):
        p = ET.SubElement(pnts, "P", id=str(i + 1))
        p.text = f"{ys[i]:.6f} {xs[i]:.6f} {elevations[i]:.4f}"

    # Faces — 1-indexed triangle vertex IDs
    faces = ET.SubElement(definition, "Faces")
    for simplex in tri.simplices:
        f = ET.SubElement(faces, "F")
        f.text = f"{simplex[0] + 1} {simplex[1] + 1} {simplex[2] + 1}"

    # Write
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(output, xml_declaration=True, encoding="UTF-8")

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
