"""Shareable web maps — self-contained MapLibre GL JS viewer export.

``export_map_html()`` writes a single HTML file that displays a
KyFromAbove product (optionally through a server-side terrain algorithm)
over an OpenStreetMap basemap. The file needs no build step or server —
open it in a browser, embed it in a report, or host it anywhere static.
"""

from __future__ import annotations

import json
from pathlib import Path
from string import Template

_MAPLIBRE_VERSION = "4.7.1"

# Kentucky statewide default view
_KY_CENTER = (-85.3, 37.8)
_KY_ZOOM = 7.0

_TEMPLATE = Template(
    """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>$title_html</title>
  <script src="https://unpkg.com/maplibre-gl@$maplibre_version/dist/maplibre-gl.js"></script>
  <link href="https://unpkg.com/maplibre-gl@$maplibre_version/dist/maplibre-gl.css"
        rel="stylesheet" />
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: system-ui, sans-serif; }
    #map { width: 100vw; height: 100vh; }
    .overlay {
      position: absolute;
      top: 10px;
      left: 10px;
      background: rgba(255, 255, 255, 0.9);
      padding: 10px 14px;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.15);
      z-index: 1;
      max-width: 320px;
    }
    .overlay h3 { font-size: 14px; margin-bottom: 4px; }
    .overlay p { font-size: 12px; color: #555; }
  </style>
</head>
<body>
  <div id="map"></div>
  <div class="overlay">
    <h3>$title_html</h3>
    <p>$subtitle_html</p>
  </div>

  <script>
    var TILEJSON_URL = $tilejson_url_js;
    var CENTER = $center_js;
    var ZOOM = $zoom_js;
    var BOUNDS = $bounds_js;

    var map = new maplibregl.Map({
      container: 'map',
      style: {
        version: 8,
        sources: {
          osm: {
            type: 'raster',
            tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
            tileSize: 256,
            attribution: '&copy; OpenStreetMap contributors | KyFromAbove'
          }
        },
        layers: [{ id: 'osm', type: 'raster', source: 'osm' }]
      },
      center: CENTER,
      zoom: ZOOM
    });

    map.addControl(new maplibregl.NavigationControl(), 'top-right');
    map.addControl(new maplibregl.ScaleControl({ unit: 'imperial' }));

    map.on('load', function () {
      map.addSource('kyfromabove', { type: 'raster', url: TILEJSON_URL, tileSize: 256 });
      map.addLayer({ id: 'kyfromabove', type: 'raster', source: 'kyfromabove' });
      if (BOUNDS) {
        map.fitBounds(BOUNDS, { padding: 24, duration: 0 });
      }
    });
  </script>
</body>
</html>
"""
)


def _js(value: object) -> str:
    """JSON-encode a value for safe embedding inside a <script> block."""
    return json.dumps(value).replace("</", "<\\/")


def _html_escape(value: str) -> str:
    """Escape a string for HTML text context."""
    return (
        value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    )


def export_map_html(
    output: str | Path,
    product: str = "dem_phase3",
    bbox: tuple[float, float, float, float] | None = None,
    county: str | None = None,
    algorithm: str | None = None,
    title: str = "KyFromAbove Viewer",
    **tile_kwargs: str,
) -> Path:
    """Write a self-contained MapLibre GL JS viewer HTML file.

    Parameters
    ----------
    output : str or Path
        Output ``.html`` path.
    product : str
        Product key (e.g., ``"dem_phase3"``, ``"ortho_phase3"``).
    bbox : tuple, optional
        (xmin, ymin, xmax, ymax) in EPSG:4326. The map fits to this
        extent.
    county : str, optional
        Kentucky county name; resolved to a bbox (overrides ``bbox``).
    algorithm : str, optional
        Server-side terrain algorithm: ``"hillshade"``, ``"slope"``,
        ``"contours"``, or ``"terrainrgb"``.
    title : str
        Page and overlay title.
    **tile_kwargs
        Extra TiTiler query parameters (colormap_name, rescale, ...).

    Returns
    -------
    Path
        Path to the written HTML file.

    Raises
    ------
    ValueError
        If ``algorithm`` is not a known terrain algorithm.
    CountyError
        If ``county`` cannot be resolved.
    """
    from abovepy.viz._urls import _resolve_bbox, tile_url

    resolved_bbox = _resolve_bbox(bbox, county)
    tilejson_url = tile_url(
        product=product,
        bbox=resolved_bbox,
        algorithm=algorithm,
        **tile_kwargs,
    )

    if resolved_bbox is not None:
        center = (
            (resolved_bbox[0] + resolved_bbox[2]) / 2,
            (resolved_bbox[1] + resolved_bbox[3]) / 2,
        )
        bounds: list[list[float]] | None = [
            [resolved_bbox[0], resolved_bbox[1]],
            [resolved_bbox[2], resolved_bbox[3]],
        ]
        zoom = 11.0
    else:
        center = _KY_CENTER
        bounds = None
        zoom = _KY_ZOOM

    subtitle = f"{product}" + (f" · {algorithm}" if algorithm else "")

    html = _TEMPLATE.substitute(
        title_html=_html_escape(title),
        subtitle_html=_html_escape(subtitle),
        maplibre_version=_MAPLIBRE_VERSION,
        tilejson_url_js=_js(tilejson_url),
        center_js=_js(list(center)),
        zoom_js=_js(zoom),
        bounds_js=_js(bounds),
    )

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    return output
