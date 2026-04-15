"""Tests for abovepy deliverable packaging."""

from __future__ import annotations

import json
import pytest
import geopandas as gpd
from shapely.geometry import box
from unittest.mock import MagicMock, patch

from abovepy._exceptions import AbovepyError, PackageError


class TestPackageError:
    def test_inherits_abovepy_error(self):
        assert issubclass(PackageError, AbovepyError)

    def test_message(self):
        with pytest.raises(PackageError, match="No tiles"):
            raise PackageError("No tiles to package")


import hashlib
import tempfile
from pathlib import Path


class TestPackageDataclass:
    def test_construction(self, tmp_path):
        from abovepy.package import Package

        pkg = Package(
            output_dir=tmp_path,
            files=[tmp_path / "a.tif"],
            manifest={"product": "dem_phase3"},
            tile_count=1,
            total_size_mb=5.0,
            has_qgis_project=False,
        )
        assert pkg.tile_count == 1
        assert pkg.total_size_mb == 5.0
        assert pkg.has_qgis_project is False

    def test_repr(self, tmp_path):
        from abovepy.package import Package

        pkg = Package(
            output_dir=tmp_path,
            files=[],
            manifest={},
            tile_count=3,
            total_size_mb=15.0,
            has_qgis_project=True,
        )
        r = repr(pkg)
        assert "3 tile(s)" in r
        assert "15.0 MB" in r


class TestChecksums:
    def test_compute_single_file(self, tmp_path):
        from abovepy.package import _compute_checksums

        f = tmp_path / "test.bin"
        f.write_bytes(b"hello world")
        expected = hashlib.sha256(b"hello world").hexdigest()

        result = _compute_checksums([f], base_dir=tmp_path)
        assert result["test.bin"] == expected

    def test_compute_multiple_files(self, tmp_path):
        from abovepy.package import _compute_checksums

        for name in ["a.tif", "b.tif", "c.tif"]:
            (tmp_path / name).write_bytes(name.encode())

        result = _compute_checksums(
            [tmp_path / "a.tif", tmp_path / "b.tif", tmp_path / "c.tif"],
            base_dir=tmp_path,
        )
        assert len(result) == 3
        assert result["a.tif"] == hashlib.sha256(b"a.tif").hexdigest()

    def test_empty_list(self, tmp_path):
        from abovepy.package import _compute_checksums

        result = _compute_checksums([], base_dir=tmp_path)
        assert result == {}


class TestDisclaimer:
    def test_render_disclaimer(self):
        from abovepy.package import _render_disclaimer

        text = _render_disclaimer(
            product_display_name="DEM Phase 3 (2ft)",
            tile_count=42,
        )
        assert "KyFromAbove" in text
        assert "DEM Phase 3 (2ft)" in text
        assert "42" in text
        assert "Generated:" in text

    def test_write_disclaimer(self, tmp_path):
        from abovepy.package import _render_disclaimer

        text = _render_disclaimer(
            product_display_name="Ortho Phase 3 (1ft)",
            tile_count=10,
        )
        out = tmp_path / "DISCLAIMER.txt"
        out.write_text(text)
        assert out.exists()
        assert "Ortho Phase 3 (1ft)" in out.read_text()


class TestManifest:
    def test_build_manifest_structure(self, tmp_path):
        from abovepy.package import _build_manifest

        data_dir = tmp_path / "data"
        data_dir.mkdir()
        tile = data_dir / "N123_dem_phase3.tif"
        tile.write_bytes(b"fake raster data")

        manifest = _build_manifest(
            output_dir=tmp_path,
            data_files=[tile],
            checksums={"data/N123_dem_phase3.tif": "abc123"},
            product_key="dem_phase3",
            display_name="DEM Phase 3 (2ft)",
            crs="EPSG:3089",
            aoi_bbox=(-85.06, 38.11, -84.73, 38.40),
            aoi_wkt="POLYGON((-85.06 38.11, -84.73 38.11, -84.73 38.40, -85.06 38.40, -85.06 38.11))",
            query_params={"county": "Franklin", "product": "dem_phase3"},
            acquisition_period="2022-2024",
        )

        assert manifest["product"] == "dem_phase3"
        assert manifest["crs"] == "EPSG:3089"
        assert manifest["tile_count"] == 1
        assert len(manifest["files"]) == 1
        assert manifest["files"][0]["sha256"] == "abc123"
        assert manifest["query"] == {"county": "Franklin", "product": "dem_phase3"}
        assert "abovepy_version" in manifest
        assert "created_at" in manifest
        assert manifest["aoi_wkt"].startswith("POLYGON")

    def test_manifest_no_checksums(self, tmp_path):
        from abovepy.package import _build_manifest

        data_dir = tmp_path / "data"
        data_dir.mkdir()
        tile = data_dir / "N123.tif"
        tile.write_bytes(b"data")

        manifest = _build_manifest(
            output_dir=tmp_path,
            data_files=[tile],
            checksums={},
            product_key="dem_phase3",
            display_name="DEM Phase 3 (2ft)",
            crs="EPSG:3089",
            aoi_bbox=(-85.0, 38.0, -84.0, 39.0),
            aoi_wkt="POLYGON((-85 38, -84 38, -84 39, -85 39, -85 38))",
            query_params={},
            acquisition_period="2022-2024",
        )

        assert manifest["files"][0]["sha256"] is None


class TestPreview:
    def test_preview_titiler_success(self, tmp_path):
        from abovepy.package import _generate_preview

        mock_result = MagicMock()
        mock_result.product = MagicMock()
        mock_result.product.key = "dem_phase3"
        mock_result.product.product_type = MagicMock()
        mock_result.product.product_type.value = "dem"
        mock_result.bbox = (-85.0, 38.0, -84.0, 39.0)

        fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        output = tmp_path / "preview.png"

        with patch("abovepy.package.httpx") as mock_httpx:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.content = fake_png
            mock_httpx.get.return_value = mock_resp

            result = _generate_preview(mock_result, output)

        assert result == output
        assert output.exists()

    def test_preview_titiler_failure_skips(self, tmp_path):
        from abovepy.package import _generate_preview

        mock_result = MagicMock()
        mock_result.product = MagicMock()
        mock_result.product.key = "dem_phase3"
        mock_result.product.product_type = MagicMock()
        mock_result.product.product_type.value = "dem"
        mock_result.bbox = (-85.0, 38.0, -84.0, 39.0)

        output = tmp_path / "preview.png"

        with patch("abovepy.package.httpx") as mock_httpx:
            mock_httpx.get.side_effect = Exception("connection failed")

            result = _generate_preview(mock_result, output)

        assert result is None


class TestBuildPackage:
    def _make_search_result(self, tmp_path):
        """Create a mock SearchResult with pre-downloaded tiles."""
        from abovepy.products import get_product

        product = get_product("dem_phase3")

        gdf = gpd.GeoDataFrame(
            {
                "tile_id": ["N123", "N124"],
                "product": ["dem_phase3", "dem_phase3"],
                "datetime": ["2023-01-01", "2023-01-02"],
                "asset_url": [
                    "https://example.com/N123.tif",
                    "https://example.com/N124.tif",
                ],
                "collection_id": ["dem-phase3", "dem-phase3"],
            },
            geometry=[
                box(-85.0, 38.0, -84.9, 38.1),
                box(-84.9, 38.0, -84.8, 38.1),
            ],
            crs="EPSG:4326",
        )

        result = MagicMock()
        result.tiles = gdf
        result.product = product
        result.query_params = {"county": "Franklin", "product": "dem_phase3"}
        result.bbox = (-85.0, 38.0, -84.8, 38.1)
        result.empty = False
        result.provenance.return_value = {"product": "dem_phase3", "tile_count": 2}
        return result

    @patch("abovepy.package._generate_preview", return_value=None)
    @patch("abovepy.package.download_tiles")
    def test_build_package_structure(self, mock_download, mock_preview, tmp_path):
        from abovepy.package import build_package

        data_dir = tmp_path / "output" / "data"
        data_dir.mkdir(parents=True)
        tile1 = data_dir / "N123.tif"
        tile2 = data_dir / "N124.tif"
        tile1.write_bytes(b"raster1")
        tile2.write_bytes(b"raster2")
        mock_download.return_value = [tile1, tile2]

        result = self._make_search_result(tmp_path)
        output_dir = tmp_path / "output"

        pkg = build_package(result, output_dir, include_preview=False, qgis_project=False)

        assert pkg.tile_count == 2
        assert (output_dir / "manifest.json").exists()
        assert (output_dir / "provenance.json").exists()
        assert (output_dir / "DISCLAIMER.txt").exists()
        assert (output_dir / "data" / "footprints.gpkg").exists()

        manifest = json.loads((output_dir / "manifest.json").read_text())
        assert manifest["tile_count"] == 2
        assert manifest["product"] == "dem_phase3"
        assert len(manifest["files"]) == 2

    @patch("abovepy.package._generate_preview", return_value=None)
    @patch("abovepy.package.download_tiles")
    def test_build_package_no_checksums(self, mock_download, mock_preview, tmp_path):
        from abovepy.package import build_package

        data_dir = tmp_path / "output" / "data"
        data_dir.mkdir(parents=True)
        tile = data_dir / "N123.tif"
        tile.write_bytes(b"raster1")
        mock_download.return_value = [tile]

        result = self._make_search_result(tmp_path)
        output_dir = tmp_path / "output"

        pkg = build_package(result, output_dir, checksums=False, include_preview=False, qgis_project=False)

        manifest = json.loads((output_dir / "manifest.json").read_text())
        assert manifest["files"][0]["sha256"] is None

    @patch("abovepy.package._generate_preview", return_value=None)
    @patch("abovepy.package.download_tiles")
    def test_empty_result_raises(self, mock_download, mock_preview, tmp_path):
        from abovepy._exceptions import PackageError
        from abovepy.package import build_package

        result = MagicMock()
        result.empty = True

        with pytest.raises(PackageError, match="No tiles"):
            build_package(result, tmp_path / "out")
