"""Tests for pgSTAC search registration helpers."""

import httpx
import pytest
import respx

from abovepy.searches import (
    register_search,
    search_bbox_url,
    search_info_url,
    search_map_url,
    search_tile_url,
)

PGSTAC = "https://pgstac.test"


# ---------------------------------------------------------------------------
# register_search() — mocked HTTP
# ---------------------------------------------------------------------------


@respx.mock
def test_register_search_basic():
    route = respx.post(f"{PGSTAC}/searches/register").mock(
        return_value=httpx.Response(200, json={"id": "abc123hash"})
    )
    result = register_search("dem_phase3", titiler_endpoint=PGSTAC)
    assert result == "abc123hash"
    assert route.called
    body = route.calls[0].request.content
    assert b"dem-phase3" in body


@respx.mock
def test_register_search_with_bbox():
    respx.post(f"{PGSTAC}/searches/register").mock(
        return_value=httpx.Response(200, json={"id": "bbox_hash"})
    )
    result = register_search(
        "dem_phase3",
        bbox=(-84.9, 38.15, -84.8, 38.25),
        titiler_endpoint=PGSTAC,
    )
    assert result == "bbox_hash"


@respx.mock
def test_register_search_with_datetime():
    respx.post(f"{PGSTAC}/searches/register").mock(
        return_value=httpx.Response(200, json={"id": "dt_hash"})
    )
    result = register_search(
        "ortho_phase3",
        datetime="2022-01/2024-01",
        titiler_endpoint=PGSTAC,
    )
    assert result == "dt_hash"


@respx.mock
def test_register_search_http_error():
    respx.post(f"{PGSTAC}/searches/register").mock(
        return_value=httpx.Response(500, json={"detail": "error"})
    )
    with pytest.raises(httpx.HTTPStatusError):
        register_search("dem_phase3", titiler_endpoint=PGSTAC)


# ---------------------------------------------------------------------------
# URL builder tests (pure — no HTTP)
# ---------------------------------------------------------------------------


def test_search_tile_url():
    url = search_tile_url("abc123", titiler_endpoint=PGSTAC)
    assert url == f"{PGSTAC}/searches/abc123/WebMercatorQuad/tilejson.json"


def test_search_tile_url_with_params():
    url = search_tile_url(
        "abc123",
        titiler_endpoint=PGSTAC,
        colormap_name="terrain",
        rescale="0,500",
    )
    assert "colormap_name=terrain" in url
    assert "rescale=" in url


def test_search_tile_url_custom_tms():
    url = search_tile_url(
        "abc123", tile_matrix_set="WorldCRS84Quad", titiler_endpoint=PGSTAC,
    )
    assert "/WorldCRS84Quad/tilejson.json" in url


def test_search_map_url():
    url = search_map_url("abc123", titiler_endpoint=PGSTAC)
    assert url == f"{PGSTAC}/searches/abc123/WebMercatorQuad/map.html"


def test_search_map_url_with_params():
    url = search_map_url(
        "abc123", titiler_endpoint=PGSTAC, assets="data",
    )
    assert "assets=data" in url


def test_search_info_url():
    url = search_info_url("abc123", titiler_endpoint=PGSTAC)
    assert url == f"{PGSTAC}/searches/abc123/info"


def test_search_bbox_url():
    url = search_bbox_url(
        "abc123",
        bbox=(-84.9, 38.15, -84.8, 38.25),
        width=256,
        height=256,
        fmt="jpeg",
        titiler_endpoint=PGSTAC,
    )
    assert "/searches/abc123/bbox/-84.9,38.15,-84.8,38.25/256x256.jpeg" in url


def test_search_bbox_url_with_colormap():
    url = search_bbox_url(
        "abc123",
        bbox=(-84.9, 38.15, -84.8, 38.25),
        titiler_endpoint=PGSTAC,
        colormap_name="viridis",
    )
    assert "colormap_name=viridis" in url
