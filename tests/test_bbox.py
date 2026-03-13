"""Tests for bbox utilities and county lookup."""

import pytest

from abovepy.utils.bbox import get_county_bbox, list_counties, validate_bbox


def test_county_lookup_pike():
    bbox = get_county_bbox("Pike")
    assert len(bbox) == 4
    assert bbox[0] < bbox[2]  # xmin < xmax
    assert bbox[1] < bbox[3]  # ymin < ymax


def test_county_lookup_case_insensitive():
    assert get_county_bbox("pike") == get_county_bbox("PIKE")
    assert get_county_bbox("franklin") == get_county_bbox("Franklin")


def test_county_lookup_invalid():
    with pytest.raises(ValueError, match="Unknown county"):
        get_county_bbox("Nonexistent")


def test_list_counties_count():
    counties = list_counties()
    assert len(counties) == 120


def test_list_counties_includes_key_counties():
    counties = list_counties()
    for c in ["Franklin", "Pike", "Fayette", "Jefferson", "Harlan"]:
        assert c in counties


def test_county_lookup_with_whitespace():
    """Leading/trailing spaces should be stripped."""
    assert get_county_bbox("  Pike  ") == get_county_bbox("Pike")


def test_county_fuzzy_match_substring():
    """Single substring match should resolve to the county."""
    # "frank" uniquely matches "Franklin"
    bbox = get_county_bbox("frank")
    assert bbox == get_county_bbox("Franklin")


def test_county_ambiguous_substring_raises():
    """Ambiguous substring match should raise CountyError."""
    # "Bo" matches Boone, Bourbon, Boyd, Boyle
    with pytest.raises(ValueError, match="Unknown county"):
        get_county_bbox("Bo")


def test_county_bbox_values_in_kentucky():
    """All county bboxes should be within Kentucky's approximate extent."""
    for county in list_counties():
        bbox = get_county_bbox(county)
        xmin, ymin, xmax, ymax = bbox
        assert -90.0 < xmin < -81.0, f"{county} xmin out of range: {xmin}"
        assert -90.0 < xmax < -81.0, f"{county} xmax out of range: {xmax}"
        assert 36.0 < ymin < 40.0, f"{county} ymin out of range: {ymin}"
        assert 36.0 < ymax < 40.0, f"{county} ymax out of range: {ymax}"


def test_validate_bbox_valid():
    validate_bbox((-84.5, 38.0, -84.3, 38.2))


def test_validate_bbox_xmin_gt_xmax():
    with pytest.raises(ValueError, match="xmin"):
        validate_bbox((-84.3, 38.0, -84.5, 38.2))


def test_validate_bbox_wrong_length():
    with pytest.raises(ValueError, match="4 elements"):
        validate_bbox((-84.5, 38.0, -84.3))
