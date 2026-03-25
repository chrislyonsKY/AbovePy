"""Tests for visualization helpers."""

import pytest

from abovepy.viz import preview_url, tile_url

PGSTAC = "https://pgstac.test"


# ---------------------------------------------------------------------------
# tile_url()
# ---------------------------------------------------------------------------


def test_tile_url_basic():
    url = tile_url("dem_phase3", titiler_endpoint=PGSTAC)
    assert "/collections/dem-phase3/" in url
    assert "tilejson.json" in url


def test_tile_url_with_bbox():
    url = tile_url(
        "dem_phase3",
        bbox=(-84.9, 38.15, -84.8, 38.25),
        titiler_endpoint=PGSTAC,
    )
    assert "bbox=" in url


def test_tile_url_with_county():
    url = tile_url("dem_phase3", county="Franklin", titiler_endpoint=PGSTAC)
    assert "bbox=" in url


def test_tile_url_with_hillshade():
    url = tile_url(
        "dem_phase3", algorithm="hillshade", titiler_endpoint=PGSTAC,
    )
    assert "algorithm=hillshade" in url


def test_tile_url_with_slope():
    url = tile_url(
        "dem_phase3", algorithm="slope", titiler_endpoint=PGSTAC,
    )
    assert "algorithm=slope" in url


def test_tile_url_with_contours():
    url = tile_url(
        "dem_phase3", algorithm="contours", titiler_endpoint=PGSTAC,
    )
    assert "algorithm=contours" in url


def test_tile_url_with_terrainrgb():
    url = tile_url(
        "dem_phase3", algorithm="terrainrgb", titiler_endpoint=PGSTAC,
    )
    assert "algorithm=terrainrgb" in url


def test_tile_url_invalid_algorithm():
    with pytest.raises(ValueError, match="Unknown algorithm"):
        tile_url("dem_phase3", algorithm="nope", titiler_endpoint=PGSTAC)


def test_tile_url_extra_params():
    url = tile_url(
        "dem_phase3",
        titiler_endpoint=PGSTAC,
        colormap_name="terrain",
        rescale="0,500",
    )
    assert "colormap_name=terrain" in url


# ---------------------------------------------------------------------------
# preview_url()
# ---------------------------------------------------------------------------


def test_preview_url_with_bbox():
    url = preview_url(
        "dem_phase3",
        bbox=(-84.9, 38.15, -84.8, 38.25),
        titiler_endpoint=PGSTAC,
    )
    assert "/collections/dem-phase3/bbox/" in url
    assert "512x512.png" in url


def test_preview_url_with_county():
    url = preview_url(
        "ortho_phase3", county="Franklin", titiler_endpoint=PGSTAC,
    )
    assert "/collections/orthos-phase3/bbox/" in url


def test_preview_url_custom_size():
    url = preview_url(
        "dem_phase3",
        bbox=(-84.9, 38.15, -84.8, 38.25),
        width=256,
        height=256,
        fmt="jpeg",
        titiler_endpoint=PGSTAC,
    )
    assert "256x256.jpeg" in url


def test_preview_url_requires_bbox():
    with pytest.raises(ValueError, match="requires either bbox= or county="):
        preview_url("dem_phase3", titiler_endpoint=PGSTAC)


# ---------------------------------------------------------------------------
# show() — import checks only (no actual leafmap in CI)
# ---------------------------------------------------------------------------


def test_show_import_error(monkeypatch):
    """show() raises a clear error when leafmap isn't installed."""
    import builtins
    real_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "leafmap":
            raise ImportError("mocked")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)

    from abovepy.viz import show
    with pytest.raises(ImportError, match="leafmap is required"):
        show("dem_phase3")
