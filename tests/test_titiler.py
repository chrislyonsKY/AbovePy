"""Tests for TiTiler URL helpers."""

from abovepy._constants import TITILER_ENDPOINT, TITILER_PGSTAC_ENDPOINT
from abovepy.titiler import (
    cog_bounds_url,
    cog_info_url,
    cog_preview_url,
    cog_stats_url,
    cog_tile_url,
    collection_bbox_url,
    collection_info_url,
    collection_map_url,
    collection_point_url,
    collection_tile_url,
    contour_tile_url,
    hillshade_tile_url,
    item_info_url,
    item_preview_url,
    item_statistics_url,
    item_tile_url,
    mosaic_tile_url,
    slope_tile_url,
    terrain_rgb_tile_url,
)


def test_cog_tile_url_default_endpoint():
    url = cog_tile_url("https://example.com/tile.tif")
    assert "tilejson.json" in url
    assert "url=" in url
    assert "example.com" in url


def test_cog_tile_url_custom_endpoint():
    url = cog_tile_url(
        "https://example.com/tile.tif",
        titiler_endpoint="http://localhost:8000",
    )
    assert url.startswith("http://localhost:8000/")


def test_cog_preview_url():
    url = cog_preview_url("https://example.com/tile.tif", max_size=512)
    assert "preview.png" in url
    assert "max_size=512" in url


def test_cog_stats_url():
    url = cog_stats_url("https://example.com/tile.tif")
    assert "statistics" in url


def test_cog_info_url():
    url = cog_info_url("https://example.com/tile.tif")
    assert "/cog/info" in url
    assert "url=" in url


def test_cog_bounds_url():
    url = cog_bounds_url("https://example.com/tile.tif")
    assert "/cog/bounds" in url
    assert "url=" in url


def test_mosaic_tile_url_single():
    url = mosaic_tile_url(["https://example.com/a.tif"])
    assert "/mosaic/tilejson.json" in url
    assert "url=" in url


def test_mosaic_tile_url_multiple():
    urls = ["https://example.com/a.tif", "https://example.com/b.tif"]
    url = mosaic_tile_url(urls)
    assert url.count("url=") == 2
    assert "/mosaic/tilejson.json" in url


def test_mosaic_tile_url_custom_endpoint():
    url = mosaic_tile_url(
        ["https://example.com/a.tif"],
        titiler_endpoint="http://localhost:8000",
    )
    assert url.startswith("http://localhost:8000/")


def test_url_encoding():
    """Special characters in COG URLs should be encoded."""
    cog = "https://s3.amazonaws.com/kyfromabove/dem/tile 1.tif"
    url = cog_tile_url(cog)
    assert "+" in url or "%20" in url  # Space encoded


def test_cog_default_endpoint_is_kyfromabove():
    """COG helpers should default to the KyFromAbove TiTiler."""
    url = cog_tile_url("https://example.com/tile.tif")
    assert url.startswith(TITILER_ENDPOINT)


# ---------------------------------------------------------------------------
# pgSTAC — collection helpers
# ---------------------------------------------------------------------------

PGSTAC = "https://pgstac.test"


def test_collection_tile_url_with_product_key():
    url = collection_tile_url("dem_phase3", titiler_endpoint=PGSTAC)
    assert "/collections/dem-phase3/WebMercatorQuad/tilejson.json" in url


def test_collection_tile_url_with_raw_collection_id():
    url = collection_tile_url("orthos-phase2", titiler_endpoint=PGSTAC)
    assert "/collections/orthos-phase2/" in url


def test_collection_tile_url_with_bbox():
    url = collection_tile_url(
        "dem_phase3",
        bbox=(-84.9, 38.15, -84.8, 38.25),
        titiler_endpoint=PGSTAC,
    )
    assert "bbox=-84.9%2C38.15%2C-84.8%2C38.25" in url


def test_collection_tile_url_default_endpoint():
    url = collection_tile_url("dem_phase3")
    assert url.startswith(TITILER_PGSTAC_ENDPOINT)


def test_collection_tile_url_extra_params():
    url = collection_tile_url(
        "dem_phase3",
        titiler_endpoint=PGSTAC,
        colormap_name="terrain",
        rescale="0,500",
    )
    assert "colormap_name=terrain" in url
    assert "rescale=0%2C500" in url


def test_collection_tile_url_custom_tms():
    url = collection_tile_url(
        "dem_phase3",
        tile_matrix_set="WorldCRS84Quad",
        titiler_endpoint=PGSTAC,
    )
    assert "/WorldCRS84Quad/tilejson.json" in url


def test_collection_map_url():
    url = collection_map_url("ortho_phase3", titiler_endpoint=PGSTAC)
    assert "/collections/orthos-phase3/WebMercatorQuad/map.html" in url


def test_collection_map_url_with_bbox():
    url = collection_map_url(
        "dem_phase3",
        bbox=(-85.0, 38.0, -84.0, 39.0),
        titiler_endpoint=PGSTAC,
    )
    assert "map.html?" in url
    assert "bbox=" in url


def test_collection_info_url():
    url = collection_info_url("dem_phase3", titiler_endpoint=PGSTAC)
    assert url == f"{PGSTAC}/collections/dem-phase3/info"


def test_collection_bbox_url():
    url = collection_bbox_url(
        "dem_phase3",
        bbox=(-84.9, 38.15, -84.8, 38.25),
        width=256,
        height=256,
        fmt="jpeg",
        titiler_endpoint=PGSTAC,
    )
    assert "/collections/dem-phase3/bbox/-84.9,38.15,-84.8,38.25/256x256.jpeg" in url


def test_collection_bbox_url_with_colormap():
    url = collection_bbox_url(
        "dem_phase3",
        bbox=(-84.9, 38.15, -84.8, 38.25),
        titiler_endpoint=PGSTAC,
        colormap_name="viridis",
    )
    assert "colormap_name=viridis" in url


def test_collection_point_url():
    url = collection_point_url(
        "dem_phase3", lon=-84.85, lat=38.2, titiler_endpoint=PGSTAC,
    )
    assert "/collections/dem-phase3/point/-84.85,38.2" in url


# ---------------------------------------------------------------------------
# pgSTAC — item helpers
# ---------------------------------------------------------------------------


def test_item_tile_url():
    url = item_tile_url(
        "dem_phase3", "N123E456", titiler_endpoint=PGSTAC,
    )
    assert "/collections/dem-phase3/items/N123E456/WebMercatorQuad/tilejson.json" in url


def test_item_tile_url_with_assets():
    url = item_tile_url(
        "dem_phase3", "N123E456",
        titiler_endpoint=PGSTAC,
        assets="data",
    )
    assert "assets=data" in url


def test_item_preview_url():
    url = item_preview_url(
        "ortho_phase3", "N123E456",
        titiler_endpoint=PGSTAC,
        max_size=512,
    )
    assert "/collections/orthos-phase3/items/N123E456/preview" in url
    assert "max_size=512" in url


def test_item_info_url():
    url = item_info_url(
        "dem_phase3", "N123E456", titiler_endpoint=PGSTAC,
    )
    assert url == f"{PGSTAC}/collections/dem-phase3/items/N123E456/info"


def test_item_statistics_url():
    url = item_statistics_url(
        "dem_phase3", "N123E456", titiler_endpoint=PGSTAC,
    )
    assert "/collections/dem-phase3/items/N123E456/statistics" in url


def test_item_statistics_url_with_assets():
    url = item_statistics_url(
        "dem_phase3", "N123E456",
        titiler_endpoint=PGSTAC,
        assets="data",
    )
    assert "assets=data" in url


def test_collection_tile_url_no_bbox():
    """No bbox should produce a clean URL without query string."""
    url = collection_tile_url("dem_phase3", titiler_endpoint=PGSTAC)
    assert url == f"{PGSTAC}/collections/dem-phase3/WebMercatorQuad/tilejson.json"


# ---------------------------------------------------------------------------
# Terrain analysis helpers
# ---------------------------------------------------------------------------


def test_hillshade_tile_url_defaults():
    url = hillshade_tile_url(titiler_endpoint=PGSTAC)
    assert "/collections/dem-phase3/" in url
    assert "algorithm=hillshade" in url
    assert "algorithm_params=" in url


def test_hillshade_tile_url_custom_params():
    url = hillshade_tile_url(
        azimuth=270, altitude=30, buffer=5, titiler_endpoint=PGSTAC,
    )
    assert "algorithm=hillshade" in url
    assert "algorithm_params=" in url
    # Params are JSON-encoded then URL-encoded
    from urllib.parse import unquote
    decoded = unquote(url)
    assert '"azimuth":270' in decoded
    assert '"altitude":30' in decoded
    assert '"buffer":5' in decoded


def test_hillshade_tile_url_with_bbox():
    url = hillshade_tile_url(
        bbox=(-84.9, 38.15, -84.8, 38.25), titiler_endpoint=PGSTAC,
    )
    assert "bbox=" in url
    assert "algorithm=hillshade" in url


def test_hillshade_tile_url_custom_collection():
    url = hillshade_tile_url("dem_phase1", titiler_endpoint=PGSTAC)
    assert "/collections/dem-phase1/" in url


def test_slope_tile_url_defaults():
    url = slope_tile_url(titiler_endpoint=PGSTAC)
    assert "algorithm=slope" in url
    assert "/collections/dem-phase3/" in url


def test_slope_tile_url_custom_params():
    url = slope_tile_url(
        buffer=5, z_exaggeration=2.0, titiler_endpoint=PGSTAC,
    )
    assert "algorithm=slope" in url
    assert "algorithm_params=" in url


def test_contour_tile_url_defaults():
    url = contour_tile_url(titiler_endpoint=PGSTAC)
    assert "algorithm=contours" in url
    assert "/collections/dem-phase3/" in url


def test_contour_tile_url_custom_params():
    url = contour_tile_url(
        increment=50, thickness=2, titiler_endpoint=PGSTAC,
    )
    assert "algorithm=contours" in url
    assert "algorithm_params=" in url


def test_terrain_rgb_tile_url_defaults():
    url = terrain_rgb_tile_url(titiler_endpoint=PGSTAC)
    assert "algorithm=terrainrgb" in url
    assert "/collections/dem-phase3/" in url


def test_terrain_rgb_tile_url_with_bbox():
    url = terrain_rgb_tile_url(
        bbox=(-84.9, 38.15, -84.8, 38.25), titiler_endpoint=PGSTAC,
    )
    assert "algorithm=terrainrgb" in url
    assert "bbox=" in url
