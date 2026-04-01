"""Tests for county mosaic URL builders."""

import pytest

from abovepy.mosaics import county_mosaic_url, list_county_mosaics


class TestCountyMosaicUrl:
    def test_mrsid_url_structure(self):
        url = county_mosaic_url("Franklin")
        assert url.startswith("https://kyfromabove.s3.us-west-2.amazonaws.com/")
        assert "MrSIDs" in url
        assert "Franklin" in url
        assert url.endswith(".sid")

    def test_tpkx_url_structure(self):
        url = county_mosaic_url("Franklin", fmt="tpkx")
        assert "Tile-Packages-tpkx" in url
        assert "Franklin" in url
        assert url.endswith(".tpkx")

    def test_mrsid_default_year(self):
        url = county_mosaic_url("Pike")
        assert "_2023_" in url

    def test_mrsid_custom_year(self):
        url = county_mosaic_url("Pike", year="2024")
        assert "_2024_" in url

    def test_case_insensitive(self):
        url1 = county_mosaic_url("franklin")
        url2 = county_mosaic_url("FRANKLIN")
        url3 = county_mosaic_url("Franklin")
        assert url1 == url2 == url3

    def test_invalid_county_raises(self):
        with pytest.raises(ValueError):
            county_mosaic_url("NotACounty")

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError, match="Invalid format"):
            county_mosaic_url("Franklin", fmt="geotiff")

    def test_mrsid_filename_format(self):
        url = county_mosaic_url("Shelby")
        assert "KY_KYAPED_Shelby_2023_3IN.sid" in url

    def test_tpkx_filename_format(self):
        url = county_mosaic_url("Shelby", fmt="tpkx")
        assert "Shelby_KyFromAbove_Phase3_3IN.tpkx" in url


class TestListCountyMosaics:
    def test_returns_120_counties(self):
        result = list_county_mosaics()
        assert len(result) == 120

    def test_each_entry_has_keys(self):
        result = list_county_mosaics()
        for entry in result:
            assert "county" in entry
            assert "url" in entry
            assert "format" in entry

    def test_tpkx_format(self):
        result = list_county_mosaics(fmt="tpkx")
        assert all(r["format"] == "tpkx" for r in result)
        assert all(r["url"].endswith(".tpkx") for r in result)
