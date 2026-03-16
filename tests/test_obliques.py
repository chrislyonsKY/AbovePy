"""Tests for oblique imagery helpers."""

import httpx
import pytest
import respx

from abovepy.obliques import (
    DIRECTIONS,
    S3_BASE_URL,
    list_oblique_seasons,
    search_obliques,
)

# Sample S3 list-objects-v2 XML response
_SEASONS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
  <Name>kyfromabove</Name>
  <Prefix>imagery/obliques/Phase3/</Prefix>
  <Delimiter>/</Delimiter>
  <CommonPrefixes>
    <Prefix>imagery/obliques/Phase3/ExteriorOrientationFiles/</Prefix>
  </CommonPrefixes>
  <CommonPrefixes>
    <Prefix>imagery/obliques/Phase3/KY_KYAPED_2022_Season2_3IN/</Prefix>
  </CommonPrefixes>
  <CommonPrefixes>
    <Prefix>imagery/obliques/Phase3/KY_KYAPED_2023_Season1_3IN/</Prefix>
  </CommonPrefixes>
  <CommonPrefixes>
    <Prefix>imagery/obliques/Phase3/Metadata/</Prefix>
  </CommonPrefixes>
</ListBucketResult>"""

_FRAMES_XML = """<?xml version="1.0" encoding="UTF-8"?>
<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
  <Name>kyfromabove</Name>
  <Contents>
    <Key>imagery/obliques/Phase3/KY_KYAPED_2023_Season1_3IN/Bwd_0_40721.json</Key>
    <Size>1234</Size>
  </Contents>
  <Contents>
    <Key>imagery/obliques/Phase3/KY_KYAPED_2023_Season1_3IN/Bwd_0_40721.tif</Key>
    <Size>88125139</Size>
  </Contents>
  <Contents>
    <Key>imagery/obliques/Phase3/KY_KYAPED_2023_Season1_3IN/Bwd_0_40722.json</Key>
    <Size>1234</Size>
  </Contents>
  <Contents>
    <Key>imagery/obliques/Phase3/KY_KYAPED_2023_Season1_3IN/Bwd_0_40722.tif</Key>
    <Size>88125139</Size>
  </Contents>
</ListBucketResult>"""


def test_directions_mapping():
    assert set(DIRECTIONS.keys()) == {"bwd", "fwd", "left", "right"}


@respx.mock
def test_list_oblique_seasons():
    respx.get(f"{S3_BASE_URL}/").mock(
        return_value=httpx.Response(200, text=_SEASONS_XML)
    )
    seasons = list_oblique_seasons()
    assert "KY_KYAPED_2022_Season2_3IN" in seasons
    assert "KY_KYAPED_2023_Season1_3IN" in seasons
    # Non-KY_ prefixes should be filtered out
    assert "ExteriorOrientationFiles" not in seasons
    assert "Metadata" not in seasons


@respx.mock
def test_search_obliques_basic():
    # First call resolves seasons, second lists frames
    respx.get(f"{S3_BASE_URL}/").mock(
        side_effect=[
            httpx.Response(200, text=_SEASONS_XML),
            httpx.Response(200, text=_FRAMES_XML),
        ]
    )
    results = search_obliques(direction="bwd")
    assert len(results) == 2
    assert results[0]["frame_id"] == "Bwd_0_40721"
    assert results[0]["tif_url"].endswith(".tif")
    assert results[0]["json_url"].endswith(".json")
    assert results[0]["direction"] == "bwd"
    assert "Season1" in results[0]["season"]


@respx.mock
def test_search_obliques_explicit_season():
    respx.get(f"{S3_BASE_URL}/").mock(
        return_value=httpx.Response(200, text=_FRAMES_XML)
    )
    results = search_obliques(
        direction="bwd", season="KY_KYAPED_2023_Season1_3IN",
    )
    assert len(results) == 2


def test_search_obliques_invalid_direction():
    with pytest.raises(ValueError, match="Invalid direction"):
        search_obliques(direction="up")


def test_search_obliques_case_insensitive():
    """Direction should be case-insensitive."""
    # Just test it doesn't raise — actual HTTP would be mocked
    with pytest.raises(ValueError, match="Invalid direction"):
        search_obliques(direction="DIAGONAL")

    # These should not raise ValueError
    import contextlib

    for d in ["BWD", "Fwd", "LEFT", "Right"]:
        # Will fail on HTTP but not on validation
        with contextlib.suppress(httpx.ConnectError, httpx.HTTPError):
            search_obliques(direction=d, season="fake")
