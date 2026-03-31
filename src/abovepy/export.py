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
