"""Tests for the CLI (abovepy.cli)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from unittest.mock import patch

import geopandas as gpd
import pytest
from shapely.geometry import box

from abovepy.cli import _build_parser, _parse_bbox, _parse_point, main
from abovepy.products import get_product
from abovepy.result import SearchResult


def _mock_search_result(tiles=None):
    """Create a mock SearchResult for CLI tests."""
    if tiles is None:
        tiles = gpd.GeoDataFrame(
            {
                "tile_id": ["T1"],
                "product": ["dem_phase3"],
                "datetime": [None],
                "asset_url": ["https://example.com/T1.tif"],
                "collection_id": ["dem-phase3"],
            },
            geometry=[box(0, 0, 1, 1)],
            crs="EPSG:4326",
        )
    return SearchResult(tiles, get_product("dem_phase3"), {"county": "Franklin"})


# ---------------------------------------------------------------------------
# Argument parser structure
# ---------------------------------------------------------------------------


class TestBuildParser:
    def test_returns_argument_parser(self):
        parser = _build_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    def test_has_version_flag(self):
        parser = _build_parser()
        args = parser.parse_args(["--version"])
        assert args.version is True

    def test_subcommands_exist(self):
        parser = _build_parser()
        subcommands = [
            "search",
            "download",
            "mosaic",
            "info",
            "products",
            "tile-url",
            "preview",
            "estimate",
        ]
        for cmd in subcommands:
            argv = [cmd] if cmd != "mosaic" else [cmd, "f.tif", "-o", "out.vrt"]
            args = parser.parse_args(argv)
            assert args.command == cmd


# ---------------------------------------------------------------------------
# _parse_bbox / _parse_point
# ---------------------------------------------------------------------------


class TestParseBbox:
    def test_valid_bbox(self):
        result = _parse_bbox("-84.9,38.15,-84.8,38.25")
        assert result == (-84.9, 38.15, -84.8, 38.25)

    def test_wrong_count_raises(self):
        with pytest.raises(argparse.ArgumentTypeError, match="4 comma-separated"):
            _parse_bbox("1,2,3")

    def test_five_values_raises(self):
        with pytest.raises(argparse.ArgumentTypeError, match="4 comma-separated"):
            _parse_bbox("1,2,3,4,5")

    def test_non_numeric_raises(self):
        with pytest.raises(ValueError):
            _parse_bbox("a,b,c,d")


class TestParsePoint:
    def test_valid_point(self):
        result = _parse_point("-84.85,38.19")
        assert result == (-84.85, 38.19)

    def test_wrong_count_raises(self):
        with pytest.raises(argparse.ArgumentTypeError, match="2 comma-separated"):
            _parse_point("1,2,3")


# ---------------------------------------------------------------------------
# main() entry point
# ---------------------------------------------------------------------------


class TestMain:
    def test_no_args_prints_help_and_exits_zero(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main([])
        assert exc_info.value.code == 0

    def test_version_flag_exits_zero(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main(["--version"])
        assert exc_info.value.code == 0

    def test_subcommand_error_prints_to_stderr(self, capsys):
        with patch("abovepy.cli._cmd_products", side_effect=RuntimeError("boom")):
            with pytest.raises(SystemExit) as exc_info:
                main(["products"])
            assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "boom" in captured.err


# ---------------------------------------------------------------------------
# products subcommand
# ---------------------------------------------------------------------------


class TestCmdProducts:
    def test_products_table_format(self, capsys):
        main(["products"])
        out = capsys.readouterr().out
        assert "dem_phase3" in out
        assert "Product" in out

    def test_products_json_format(self, capsys):
        main(["products", "--format", "json"])
        out = capsys.readouterr().out
        data = json.loads(out)
        assert isinstance(data, list)
        keys = {p["key"] for p in data}
        assert "dem_phase3" in keys

    def test_products_filter_by_type(self, capsys):
        main(["products", "--type", "dem"])
        out = capsys.readouterr().out
        assert "dem_phase1" in out
        assert "oblique" not in out

    def test_products_filter_oblique(self, capsys):
        main(["products", "--type", "oblique"])
        out = capsys.readouterr().out
        assert "oblique_phase3_bwd" in out


# ---------------------------------------------------------------------------
# search subcommand (mocked)
# ---------------------------------------------------------------------------


class TestCmdSearch:
    @patch("abovepy.search")
    def test_search_table_format(self, mock_search, capsys):
        mock_search.return_value = _mock_search_result()
        main(["search", "--bbox=-84.9,38.15,-84.8,38.25"])
        out = capsys.readouterr().out
        assert "T1" in out
        assert "Found 1 tile(s)" in out

    @patch("abovepy.search")
    def test_search_json_format(self, mock_search, capsys):
        mock_search.return_value = _mock_search_result()
        main(["search", "--bbox=-84.9,38.15,-84.8,38.25", "-f", "json"])
        out = capsys.readouterr().out
        data = json.loads(out)
        assert isinstance(data, list)

    @patch("abovepy.search")
    def test_search_geojson_format(self, mock_search, capsys):
        mock_search.return_value = _mock_search_result()
        main(["search", "--bbox=-84.9,38.15,-84.8,38.25", "-f", "geojson"])
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["type"] == "FeatureCollection"

    @patch("abovepy.search")
    def test_search_by_county(self, mock_search, capsys):
        mock_search.return_value = _mock_search_result()
        main(["search", "--county", "Franklin"])
        mock_search.assert_called_once()
        assert mock_search.call_args.kwargs["county"] == "Franklin"

    @patch("abovepy.search")
    def test_search_by_point(self, mock_search, capsys):
        mock_search.return_value = _mock_search_result()
        main(["search", "--point=-84.85,38.19", "--buffer", "2"])
        mock_search.assert_called_once()
        assert mock_search.call_args.kwargs["point"] == (-84.85, 38.19)
        assert mock_search.call_args.kwargs["buffer_miles"] == 2.0

    @patch("abovepy.search")
    def test_search_with_ids(self, mock_search, capsys):
        mock_search.return_value = _mock_search_result()
        main(["search", "--ids", "tile-001,tile-002"])
        mock_search.assert_called_once()
        assert mock_search.call_args.kwargs["ids"] == ["tile-001", "tile-002"]

    @patch("abovepy.search")
    def test_search_with_sortby(self, mock_search, capsys):
        mock_search.return_value = _mock_search_result()
        main(["search", "--bbox=-84.9,38.15,-84.8,38.25", "--sortby", "+datetime"])
        assert mock_search.call_args.kwargs["sortby"] == "+datetime"

    @patch("abovepy.search")
    def test_search_with_buffer_feet(self, mock_search, capsys):
        mock_search.return_value = _mock_search_result()
        main(["search", "--point=-84.85,38.19", "--buffer-feet", "500"])
        mock_search.assert_called_once()
        assert mock_search.call_args.kwargs["buffer_feet"] == 500.0

    @patch("abovepy.search")
    def test_search_provenance_format(self, mock_search, capsys):
        mock_search.return_value = _mock_search_result()
        main(["search", "--bbox=-84.9,38.15,-84.8,38.25", "-f", "provenance"])
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "product" in data
        assert "source_program" in data
        assert "tile_count" in data

    @patch("abovepy.search")
    def test_search_table_shows_validation_warnings(self, mock_search, capsys):
        mock_search.return_value = _mock_search_result()
        main(["search", "--bbox=-84.9,38.15,-84.8,38.25"])
        err = capsys.readouterr().err
        # Our fixture has None datetimes, so validate() should warn
        assert "Warning:" in err


# ---------------------------------------------------------------------------
# download subcommand (mocked)
# ---------------------------------------------------------------------------


class TestCmdDownload:
    @patch("abovepy.search")
    def test_download_no_tiles_exits_1(self, mock_search, capsys):
        empty_gdf = gpd.GeoDataFrame(
            columns=["tile_id", "product", "datetime", "geometry", "asset_url", "collection_id"],
            geometry="geometry",
            crs="EPSG:4326",
        )
        mock_search.return_value = SearchResult(empty_gdf, get_product("dem_phase3"), {})
        with pytest.raises(SystemExit) as exc_info:
            main(["download", "--county", "Franklin"])
        assert exc_info.value.code == 1

    @patch("abovepy._download.download_tiles", return_value=["/tmp/a.tif"])
    @patch("abovepy.search")
    def test_download_success(self, mock_search, mock_dl, capsys):
        mock_search.return_value = _mock_search_result()
        main(["download", "--county", "Franklin", "-o", "/tmp/out"])
        out = capsys.readouterr().out
        assert "Downloaded" in out

    @patch("abovepy._download.download_tiles", return_value=["/tmp/a.tif"])
    @patch("abovepy.search")
    def test_download_workers(self, mock_search, mock_dl, capsys):
        mock_search.return_value = _mock_search_result()
        main(["download", "--county", "Franklin", "--workers", "8"])
        call_kwargs = mock_dl.call_args.kwargs
        assert call_kwargs["max_workers"] == 8

    @patch("abovepy._download.download_tiles", return_value=["/tmp/a.tif"])
    @patch("abovepy.search")
    def test_download_with_buffer_feet(self, mock_search, mock_dl, capsys):
        mock_search.return_value = _mock_search_result()
        main(["download", "--point=-84.85,38.19", "--buffer-feet", "1000", "-o", "/tmp/out"])
        assert mock_search.call_args.kwargs["buffer_feet"] == 1000.0


# ---------------------------------------------------------------------------
# info subcommand (mocked)
# ---------------------------------------------------------------------------


class TestCmdInfo:
    @patch("abovepy.info")
    def test_info_dict_table(self, mock_info, capsys):
        mock_info.return_value = {"product": "dem_phase3", "resolution": "2ft"}
        main(["info", "dem_phase3"])
        out = capsys.readouterr().out
        assert "dem_phase3" in out

    @patch("abovepy.info")
    def test_info_dict_json(self, mock_info, capsys):
        mock_info.return_value = {"product": "dem_phase3", "resolution": "2ft"}
        main(["info", "dem_phase3", "-f", "json"])
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["product"] == "dem_phase3"


# ---------------------------------------------------------------------------
# tile-url subcommand (mocked)
# ---------------------------------------------------------------------------


class TestCmdTileUrl:
    @patch("abovepy.viz._urls.collection_tile_url", return_value="https://example.com/tiles")
    def test_tile_url_basic(self, mock_url, capsys):
        main(["tile-url", "--bbox=-84.9,38.15,-84.8,38.25"])
        out = capsys.readouterr().out.strip()
        assert "example.com" in out

    @patch(
        "abovepy.viz._urls._ALGORITHM_BUILDERS",
        {"hillshade": lambda *a, **kw: "https://example.com/hs"},
    )
    def test_tile_url_with_algorithm(self, capsys):
        main(["tile-url", "--bbox=-84.9,38.15,-84.8,38.25", "--algorithm", "hillshade"])
        out = capsys.readouterr().out.strip()
        assert "example.com" in out


# ---------------------------------------------------------------------------
# preview subcommand (mocked)
# ---------------------------------------------------------------------------


class TestCmdPreview:
    @patch("abovepy.viz._urls.collection_bbox_url", return_value="https://example.com/preview.png")
    def test_preview_prints_url(self, mock_url, capsys):
        main(["preview", "--bbox=-84.9,38.15,-84.8,38.25"])
        out = capsys.readouterr().out.strip()
        assert "preview.png" in out


# ---------------------------------------------------------------------------
# mosaic subcommand (mocked)
# ---------------------------------------------------------------------------


class TestCmdMosaic:
    @patch("abovepy.mosaic", return_value="/tmp/out.vrt")
    def test_mosaic_basic(self, mock_mosaic, capsys, tmp_path):
        f = tmp_path / "tile.tif"
        f.write_bytes(b"fake")
        main(["mosaic", str(f), "-o", str(tmp_path / "out.vrt")])
        out = capsys.readouterr().out
        assert "Mosaic written" in out

    def test_mosaic_no_inputs_exits_1(self, capsys, tmp_path):
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        with pytest.raises(SystemExit) as exc_info:
            main(["mosaic", str(empty_dir), "-o", str(tmp_path / "out.vrt")])
        assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# estimate subcommand (mocked)
# ---------------------------------------------------------------------------


class TestCmdEstimate:
    @patch("abovepy.search")
    def test_estimate_table(self, mock_search, capsys):
        mock_search.return_value = _mock_search_result()
        main(["estimate", "--county", "Franklin"])
        out = capsys.readouterr().out
        assert "Tiles:" in out
        assert "Total est:" in out

    @patch("abovepy.search")
    def test_estimate_json(self, mock_search, capsys):
        mock_search.return_value = _mock_search_result()
        main(["estimate", "--county", "Franklin", "-f", "json"])
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "tile_count" in data
        assert "total_mb" in data

    @patch("abovepy.search")
    def test_estimate_with_buffer_feet(self, mock_search, capsys):
        mock_search.return_value = _mock_search_result()
        main(["estimate", "--point=-84.85,38.19", "--buffer-feet", "500"])
        assert mock_search.call_args.kwargs["buffer_feet"] == 500.0


# ---------------------------------------------------------------------------
# CLI entrypoint via subprocess
# ---------------------------------------------------------------------------


class TestSubprocess:
    def test_abovepy_products(self):
        result = subprocess.run(
            [sys.executable, "-m", "abovepy", "products"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert "dem_phase3" in result.stdout


# ---------------------------------------------------------------------------
# sample / profile / export-map (v2.2)
# ---------------------------------------------------------------------------


class TestCmdSample:
    @patch("abovepy.sample", return_value=812.5)
    def test_single_point_table(self, mock_sample, capsys):
        main(["sample", "--point", "-84.85,38.20"])
        out = capsys.readouterr().out
        assert "812.50 ft" in out
        mock_sample.assert_called_once_with((-84.85, 38.20), product="dem_phase3")

    @patch("abovepy.sample", return_value=812.5)
    def test_single_point_json(self, mock_sample, capsys):
        main(["sample", "--point", "-84.85,38.20", "--format", "json"])
        payload = json.loads(capsys.readouterr().out)
        assert payload["elevation"] == 812.5
        assert payload["lon"] == -84.85

    @patch("abovepy.sample", return_value=[810.0, 815.0])
    def test_multiple_points(self, mock_sample, capsys):
        main(["sample", "--point", "-84.85,38.20", "--point", "-84.86,38.21"])
        out = capsys.readouterr().out
        assert "810.00 ft" in out
        assert "815.00 ft" in out
        mock_sample.assert_called_once_with(
            [(-84.85, 38.20), (-84.86, 38.21)], product="dem_phase3"
        )

    def test_bad_point_exits_1(self, capsys):
        with pytest.raises(SystemExit) as excinfo:
            main(["sample", "--point", "not-a-point"])
        assert excinfo.value.code == 1


class TestCmdProfile:
    def _fake_df(self):
        import pandas as pd

        return pd.DataFrame(
            {
                "distance_ft": [0.0, 100.0],
                "elevation": [800.0, 810.0],
                "lon": [-84.85, -84.85],
                "lat": [38.16, 38.17],
            }
        )

    @patch("abovepy.profile")
    def test_profile_table(self, mock_profile, capsys):
        mock_profile.return_value = self._fake_df()
        main(["profile", "--line", "-84.85,38.16 -84.85,38.24"])
        out = capsys.readouterr().out
        assert "distance_ft" in out
        mock_profile.assert_called_once_with(
            [(-84.85, 38.16), (-84.85, 38.24)], product="dem_phase3", n_points=100
        )

    @patch("abovepy.profile")
    def test_profile_csv(self, mock_profile, capsys):
        mock_profile.return_value = self._fake_df()
        main(["profile", "--line", "-84.85,38.16 -84.85,38.24", "--format", "csv"])
        out = capsys.readouterr().out
        assert out.startswith("distance_ft,elevation,lon,lat")

    @patch("abovepy.profile")
    def test_profile_json(self, mock_profile, capsys):
        mock_profile.return_value = self._fake_df()
        main(["profile", "--line", "-84.85,38.16 -84.85,38.24", "--format", "json"])
        records = json.loads(capsys.readouterr().out)
        assert records[0]["elevation"] == 800.0

    @patch("abovepy.profile")
    def test_profile_n_points_forwarded(self, mock_profile, capsys):
        mock_profile.return_value = self._fake_df()
        main(["profile", "--line", "-84.85,38.16 -84.85,38.24", "--n-points", "25"])
        assert mock_profile.call_args.kwargs["n_points"] == 25

    def test_single_vertex_exits_1(self, capsys):
        with pytest.raises(SystemExit) as excinfo:
            main(["profile", "--line", "-84.85,38.16"])
        assert excinfo.value.code == 1


class TestCmdExportMap:
    def test_export_map_writes_html(self, capsys, tmp_path):
        output = tmp_path / "map.html"
        main(["export-map", "-o", str(output), "--bbox", "-84.9,38.15,-84.8,38.25"])
        assert output.exists()
        assert "Map written to" in capsys.readouterr().out

    def test_export_map_with_algorithm(self, tmp_path):
        output = tmp_path / "hillshade.html"
        main(
            [
                "export-map",
                "-o",
                str(output),
                "--bbox",
                "-84.9,38.15,-84.8,38.25",
                "--algorithm",
                "hillshade",
            ]
        )
        assert "hillshade" in output.read_text()

    def test_export_map_requires_output(self):
        with pytest.raises(SystemExit):
            main(["export-map", "--bbox", "-84.9,38.15,-84.8,38.25"])
