"""Tests for SearchResult."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import geopandas as gpd
import pytest
from shapely.geometry import box

from abovepy.products import get_product
from abovepy.result import SearchResult


def _has_pyarrow() -> bool:
    try:
        import pyarrow  # noqa: F401

        return True
    except ImportError:
        return False


@pytest.fixture
def sample_product():
    return get_product("dem_phase3")


@pytest.fixture
def sample_gdf():
    return gpd.GeoDataFrame(
        {
            "tile_id": ["T1", "T2", "T3"],
            "product": ["dem_phase3", "dem_phase3", "dem_phase3"],
            "datetime": [None, None, None],
            "asset_url": [
                "https://example.com/T1.tif",
                "https://example.com/T2.tif",
                "https://example.com/T3.tif",
            ],
            "collection_id": ["dem-phase3", "dem-phase3", "dem-phase3"],
        },
        geometry=[box(0, 0, 1, 1), box(1, 1, 2, 2), box(2, 2, 3, 3)],
        crs="EPSG:4326",
    )


@pytest.fixture
def result(sample_gdf, sample_product):
    return SearchResult(sample_gdf, sample_product, {"county": "Franklin"})


@pytest.fixture
def empty_result(sample_product):
    gdf = gpd.GeoDataFrame(
        columns=["tile_id", "product", "datetime", "geometry", "asset_url", "collection_id"],
        geometry="geometry",
        crs="EPSG:4326",
    )
    return SearchResult(gdf, sample_product, {})


# ---------------------------------------------------------------------------
# Construction & properties
# ---------------------------------------------------------------------------


class TestSearchResultProperties:
    def test_tiles_returns_geodataframe(self, result):
        assert isinstance(result.tiles, gpd.GeoDataFrame)
        assert len(result.tiles) == 3

    def test_product_returns_product(self, result, sample_product):
        assert result.product == sample_product

    def test_query_params_returns_copy(self, result):
        params = result.query_params
        assert params == {"county": "Franklin"}
        params["extra"] = True
        assert "extra" not in result.query_params

    def test_bbox(self, result):
        bbox = result.bbox
        assert bbox == (0.0, 0.0, 3.0, 3.0)

    def test_bbox_empty(self, empty_result):
        assert empty_result.bbox == (0.0, 0.0, 0.0, 0.0)

    def test_count(self, result):
        assert result.count == 3

    def test_empty_false(self, result):
        assert not result.empty

    def test_empty_true(self, empty_result):
        assert empty_result.empty


# ---------------------------------------------------------------------------
# Size estimation
# ---------------------------------------------------------------------------


class TestEstimateSize:
    def test_estimate(self, result):
        est = result.estimate_size()
        assert est["tile_count"] == 3
        assert est["avg_tile_mb"] == 5.0
        assert est["total_mb"] == 15.0

    def test_estimate_empty(self, empty_result):
        est = empty_result.estimate_size()
        assert est["tile_count"] == 0
        assert est["total_mb"] == 0.0


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


class TestExport:
    def test_to_geodataframe_is_copy(self, result):
        gdf = result.to_geodataframe()
        assert len(gdf) == 3
        gdf.drop(gdf.index, inplace=True)
        assert result.count == 3  # original unchanged

    def test_to_geojson(self, result):
        import json

        geojson = result.to_geojson()
        data = json.loads(geojson)
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) == 3

    @pytest.mark.skipif(not _has_pyarrow(), reason="pyarrow not installed")
    def test_to_geoparquet(self, result, tmp_path):
        output = tmp_path / "tiles.parquet"
        path = result.to_geoparquet(output)
        assert path.exists()
        assert path == output

    @pytest.mark.skipif(not _has_pyarrow(), reason="pyarrow not installed")
    def test_to_geoparquet_creates_dirs(self, result, tmp_path):
        output = tmp_path / "sub" / "dir" / "tiles.parquet"
        path = result.to_geoparquet(output)
        assert path.exists()


# ---------------------------------------------------------------------------
# Workflow methods
# ---------------------------------------------------------------------------


class TestWorkflows:
    @patch("abovepy._download.download_tiles", return_value=[Path("/tmp/T1.tif")])
    def test_download_delegates(self, mock_dl, result):
        paths = result.download("/tmp/out", overwrite=True, max_workers=2)
        assert paths == [Path("/tmp/T1.tif")]
        mock_dl.assert_called_once()
        call_kwargs = mock_dl.call_args.kwargs
        assert call_kwargs["overwrite"] is True
        assert call_kwargs["max_workers"] == 2

    @patch("abovepy.viz._urls.collection_bbox_url", return_value="https://example.com/preview.png")
    def test_preview(self, mock_url, result):
        url = result.preview()
        assert "example.com" in url

    @patch("abovepy._mosaic.mosaic_tiles", return_value=Path("/tmp/out.vrt"))
    def test_mosaic(self, mock_mosaic, result):
        path = result.mosaic(output="/tmp/out.vrt")
        assert path == Path("/tmp/out.vrt")
        mock_mosaic.assert_called_once()


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------


class TestCompare:
    def test_compare_overlapping(self, sample_gdf, sample_product):
        result1 = SearchResult(sample_gdf, sample_product, {})
        # Overlapping tiles
        gdf2 = gpd.GeoDataFrame(
            {
                "tile_id": ["X1"],
                "product": ["dem_phase2"],
                "datetime": [None],
                "asset_url": ["https://example.com/X1.tif"],
                "collection_id": ["dem-phase2"],
            },
            geometry=[box(0.5, 0.5, 1.5, 1.5)],
            crs="EPSG:4326",
        )
        result2 = SearchResult(gdf2, get_product("dem_phase2"), {})
        overlap = result1.compare(result2)
        assert len(overlap) > 0

    def test_compare_no_overlap(self, sample_gdf, sample_product):
        result1 = SearchResult(sample_gdf, sample_product, {})
        gdf2 = gpd.GeoDataFrame(
            {
                "tile_id": ["X1"],
                "product": ["dem_phase2"],
                "datetime": [None],
                "asset_url": ["https://example.com/X1.tif"],
                "collection_id": ["dem-phase2"],
            },
            geometry=[box(100, 100, 101, 101)],
            crs="EPSG:4326",
        )
        result2 = SearchResult(gdf2, get_product("dem_phase2"), {})
        overlap = result1.compare(result2)
        assert len(overlap) == 0


# ---------------------------------------------------------------------------
# Provenance & validation
# ---------------------------------------------------------------------------


class TestProvenance:
    def test_provenance_keys(self, result):
        prov = result.provenance()
        assert prov["product"] == "dem_phase3"
        assert prov["source_program"] == "KyFromAbove"
        assert prov["tile_count"] == 3
        assert prov["native_crs"] == "EPSG:3089"
        assert "acquisition_period" in prov
        assert "asset_urls" in prov
        assert len(prov["asset_urls"]) == 3

    def test_provenance_acquisition_period(self, result):
        prov = result.provenance()
        assert "2022" in prov["acquisition_period"]
        assert "2025" in prov["acquisition_period"]

    def test_provenance_empty(self, empty_result):
        prov = empty_result.provenance()
        assert prov["tile_count"] == 0
        assert prov["estimated_size_mb"] == 0.0


class TestValidate:
    def test_validate_clean_result(self, result):
        warnings = result.validate()
        # May have datetime warnings since our fixtures use None
        assert isinstance(warnings, list)

    def test_validate_empty_result(self, empty_result):
        warnings = empty_result.validate()
        assert any("empty" in w.lower() for w in warnings)

    def test_validate_missing_asset_urls(self, sample_product):
        gdf = gpd.GeoDataFrame(
            {
                "tile_id": ["T1"],
                "product": ["dem_phase3"],
                "datetime": [None],
                "asset_url": [None],
                "collection_id": ["dem-phase3"],
            },
            geometry=[box(0, 0, 1, 1)],
            crs="EPSG:4326",
        )
        result = SearchResult(gdf, sample_product, {})
        warnings = result.validate()
        assert any("no asset URL" in w for w in warnings)

    def test_validate_null_datetimes(self, result):
        warnings = result.validate()
        assert any("no acquisition date" in w for w in warnings)


# ---------------------------------------------------------------------------
# Subsetting
# ---------------------------------------------------------------------------


class TestSubset:
    def test_filter_by_bbox(self, result):
        filtered = result.filter_by_bbox((0, 0, 1.5, 1.5))
        assert filtered.count == 2  # T1 and T2

    def test_filter_by_bbox_none_match(self, result):
        filtered = result.filter_by_bbox((100, 100, 101, 101))
        assert filtered.count == 0
        assert filtered.empty

    def test_head(self, result):
        h = result.head(2)
        assert h.count == 2
        assert isinstance(h, SearchResult)

    def test_head_preserves_product(self, result, sample_product):
        h = result.head(1)
        assert h.product == sample_product


# ---------------------------------------------------------------------------
# Container protocol
# ---------------------------------------------------------------------------


class TestContainerProtocol:
    def test_len(self, result):
        assert len(result) == 3

    def test_bool_true(self, result):
        assert bool(result) is True

    def test_bool_false(self, empty_result):
        assert bool(empty_result) is False

    def test_iter(self, result):
        rows = list(result)
        assert len(rows) == 3
        assert rows[0]["tile_id"] == "T1"

    def test_repr(self, result):
        r = repr(result)
        assert "dem_phase3" in r
        assert "3 tile(s)" in r
        assert "15.0 MB" in r

    def test_repr_html(self, result):
        html = result._repr_html_()
        assert "<strong>SearchResult</strong>" in html
        assert "DEM Phase 3" in html
