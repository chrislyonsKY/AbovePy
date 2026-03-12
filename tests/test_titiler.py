"""Tests for TiTiler URL helpers."""

from abovepy.titiler import cog_preview_url, cog_stats_url, cog_tile_url


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


def test_url_encoding():
    """Special characters in COG URLs should be encoded."""
    cog = "https://s3.amazonaws.com/kyfromabove/dem/tile 1.tif"
    url = cog_tile_url(cog)
    assert "+" in url or "%20" in url  # Space encoded
