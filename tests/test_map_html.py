"""Tests for the MapLibre web-map HTML export."""

import pytest

from abovepy.viz import export_map_html


class TestExportMapHtml:
    def test_writes_file_and_returns_path(self, tmp_path):
        output = tmp_path / "map.html"
        result = export_map_html(output, bbox=(-84.9, 38.15, -84.8, 38.25))
        assert result == output
        assert output.exists()

    def test_contains_maplibre_and_tilejson(self, tmp_path, frankfort_bbox):
        output = export_map_html(tmp_path / "map.html", bbox=frankfort_bbox)
        html = output.read_text()
        assert "maplibre-gl" in html
        assert "TILEJSON_URL" in html
        assert "WebMercatorQuad" in html  # tile URL made it into the page

    def test_algorithm_dispatch(self, tmp_path, frankfort_bbox):
        output = export_map_html(
            tmp_path / "hillshade.html", bbox=frankfort_bbox, algorithm="hillshade"
        )
        html = output.read_text()
        assert "hillshade" in html

    def test_invalid_algorithm_raises(self, tmp_path, frankfort_bbox):
        with pytest.raises(ValueError, match="Unknown algorithm"):
            export_map_html(tmp_path / "bad.html", bbox=frankfort_bbox, algorithm="rainbows")

    def test_county_resolution(self, tmp_path):
        output = export_map_html(tmp_path / "franklin.html", county="Franklin")
        html = output.read_text()
        # County resolves to a bbox → the map fits bounds
        assert "BOUNDS = [[" in html

    def test_statewide_default_view(self, tmp_path):
        output = export_map_html(tmp_path / "state.html")
        html = output.read_text()
        assert "BOUNDS = null" in html
        assert "-85.3" in html  # Kentucky center

    def test_title_injection_escaped(self, tmp_path, frankfort_bbox):
        output = export_map_html(
            tmp_path / "evil.html",
            bbox=frankfort_bbox,
            title='</script><script>alert("x")</script>',
        )
        html = output.read_text()
        assert '</script><script>alert("x")</script>' not in html
        assert "&lt;/script&gt;" in html

    def test_creates_parent_dirs(self, tmp_path, frankfort_bbox):
        output = export_map_html(tmp_path / "deep" / "dir" / "map.html", bbox=frankfort_bbox)
        assert output.exists()
