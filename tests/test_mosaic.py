"""Tests for the mosaic module."""

from pathlib import Path

import pytest

from abovepy.mosaic import _resolve_paths


def test_resolve_paths_from_list():
    paths = _resolve_paths(["/a/b.tif", "/c/d.tif"])
    assert paths == [Path("/a/b.tif"), Path("/c/d.tif")]


def test_resolve_paths_from_geodataframe():
    import geopandas as gpd
    from shapely.geometry import Point

    gdf = gpd.GeoDataFrame(
        {"local_path": ["/a.tif", "/b.tif"], "geometry": [Point(0, 0), Point(1, 1)]},
        crs="EPSG:4326",
    )
    paths = _resolve_paths(gdf)
    assert paths == [Path("/a.tif"), Path("/b.tif")]


def test_resolve_paths_from_geodataframe_asset_url():
    import geopandas as gpd
    from shapely.geometry import Point

    gdf = gpd.GeoDataFrame(
        {"asset_url": ["https://a.tif", "https://b.tif"], "geometry": [Point(0, 0), Point(1, 1)]},
        crs="EPSG:4326",
    )
    paths = _resolve_paths(gdf)
    assert len(paths) == 2


def test_resolve_paths_geodataframe_no_valid_column():
    import geopandas as gpd
    from shapely.geometry import Point

    gdf = gpd.GeoDataFrame(
        {"other": [1, 2], "geometry": [Point(0, 0), Point(1, 1)]},
        crs="EPSG:4326",
    )
    with pytest.raises(ValueError, match="local_path"):
        _resolve_paths(gdf)


def test_resolve_paths_empty_list():
    assert _resolve_paths([]) == []


def test_mosaic_tiles_empty_raises():
    from abovepy.mosaic import mosaic_tiles
    with pytest.raises(ValueError, match="No tile paths"):
        mosaic_tiles([])
