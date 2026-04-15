"""QGIS project generation and interoperability.

Generates .qgs project files with pre-configured layers and styles.
Uses PyQGIS when available, falls back to XML template substitution.
"""

from __future__ import annotations

import logging
import uuid
from importlib import resources
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import geopandas as gpd

from abovepy.products import Product

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
    keep = ["tile_id", "product", "datetime", "asset_url", "geometry"]
    cols = [c for c in keep if c in gdf.columns]
    out_gdf = gdf[cols].copy()
    out_gdf = out_gdf.to_crs(target_crs)
    out_gdf.to_file(output_path, driver="GPKG", layer="tiles")
    return output_path


def generate_project(
    package_dir: Path,
    tiles: list[Path],
    footprints_path: Path,
    product: Product,
    extent: tuple[float, float, float, float],
    styles_dir: Path,
) -> Path:
    """Generate a .qgs project file.

    Uses PyQGIS if available, otherwise falls back to XML template.
    """
    try:
        return _generate_pyqgis(package_dir, tiles, footprints_path, product, extent, styles_dir)
    except ImportError:
        logger.debug("PyQGIS not available, using XML template fallback")
    except Exception:
        logger.warning("PyQGIS generation failed, falling back to XML template")

    return _generate_xml(package_dir, tiles, footprints_path, product, extent)


def _generate_pyqgis(
    package_dir: Path,
    tiles: list[Path],
    footprints_path: Path,
    product: Product,
    extent: tuple[float, float, float, float],
    styles_dir: Path,
) -> Path:
    """Generate project using PyQGIS API."""
    from qgis.core import (  # type: ignore[import-not-found]
        QgsCoordinateReferenceSystem,
        QgsProject,
        QgsRasterLayer,
        QgsRectangle,
        QgsVectorLayer,
    )

    project = QgsProject.instance()
    project.clear()
    project.setTitle(package_dir.name)
    crs = QgsCoordinateReferenceSystem("EPSG:3089")
    project.setCrs(crs)

    root = project.layerTreeRoot()

    data_group = root.addGroup("Data")
    for tile_path in tiles:
        layer = QgsRasterLayer(str(tile_path), tile_path.stem)
        if layer.isValid():
            project.addMapLayer(layer, False)
            data_group.addLayer(layer)
            is_dem = product.product_type.value == "dem"
            style_name = "dem_hillshade.qml" if is_dem else "ortho_rgb.qml"
            style_path = styles_dir / style_name
            if style_path.exists():
                layer.loadNamedStyle(str(style_path))

    index_group = root.addGroup("Index")
    vlayer = QgsVectorLayer(f"{footprints_path}|layername=tiles", "footprints", "ogr")
    if vlayer.isValid():
        project.addMapLayer(vlayer, False)
        index_group.addLayer(vlayer)
        style_path = styles_dir / "footprints_outline.qml"
        if style_path.exists():
            vlayer.loadNamedStyle(str(style_path))

    canvas_extent = QgsRectangle(*extent)
    project.viewSettings().setDefaultViewExtent(canvas_extent)

    output_path = package_dir / f"{package_dir.name}.qgs"
    project.write(str(output_path))
    project.clear()
    return output_path


def _generate_xml(
    package_dir: Path,
    tiles: list[Path],
    footprints_path: Path,
    product: Product,
    extent: tuple[float, float, float, float],
) -> Path:
    """Generate project using XML template substitution."""
    template_text = (
        resources.files("abovepy.templates").joinpath("project.qgs").read_text(encoding="utf-8")
    )

    crs = product.native_crs or "EPSG:3089"

    raster_layers = []
    raster_tree = []
    for tile_path in tiles:
        layer_id = f"{tile_path.stem}_{uuid.uuid4().hex[:8]}"
        rel_path = f"./data/{tile_path.name}"
        raster_layers.append(
            f'    <maplayer type="raster" name="{tile_path.stem}">\n'
            f"      <id>{layer_id}</id>\n"
            f"      <datasource>{rel_path}</datasource>\n"
            f"      <provider>gdal</provider>\n"
            f"      <srs><spatialrefsys><authid>{crs}</authid></spatialrefsys></srs>\n"
            f"    </maplayer>"
        )
        raster_tree.append(
            f'      <layer-tree-layer id="{layer_id}" name="{tile_path.stem}" '
            f'source="{rel_path}" providerKey="gdal" expanded="0"/>'
        )

    fp_id = f"footprints_{uuid.uuid4().hex[:8]}"
    fp_rel = f"./data/{footprints_path.name}"
    vector_layers = (
        f'    <maplayer type="vector" name="footprints">\n'
        f"      <id>{fp_id}</id>\n"
        f"      <datasource>{fp_rel}|layername=tiles</datasource>\n"
        f"      <provider>ogr</provider>\n"
        f"      <srs><spatialrefsys><authid>{crs}</authid></spatialrefsys></srs>\n"
        f"    </maplayer>"
    )
    vector_tree = (
        f'      <layer-tree-layer id="{fp_id}" name="footprints" '
        f'source="{fp_rel}|layername=tiles" providerKey="ogr" expanded="0"/>'
    )

    output = template_text.replace("{{PROJECT_NAME}}", package_dir.name)
    output = output.replace("{{CRS_AUTHID}}", crs)
    output = output.replace("{{EXTENT_XMIN}}", str(extent[0]))
    output = output.replace("{{EXTENT_YMIN}}", str(extent[1]))
    output = output.replace("{{EXTENT_XMAX}}", str(extent[2]))
    output = output.replace("{{EXTENT_YMAX}}", str(extent[3]))
    output = output.replace("{{RASTER_LAYERS}}", "\n".join(raster_layers))
    output = output.replace("{{VECTOR_LAYERS}}", vector_layers)
    output = output.replace("{{LAYER_TREE_RASTERS}}", "\n".join(raster_tree))
    output = output.replace("{{LAYER_TREE_VECTORS}}", vector_tree)

    output_path = package_dir / f"{package_dir.name}.qgs"
    output_path.write_text(output, encoding="utf-8")
    return output_path
