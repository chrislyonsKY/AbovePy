"""Tests for abovepy deliverable packaging."""

from __future__ import annotations

import pytest

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
