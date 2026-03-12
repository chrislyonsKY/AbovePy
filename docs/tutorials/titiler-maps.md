# Web Maps with TiTiler

Visualize KyFromAbove COGs in the browser using [TiTiler](https://developmentseed.org/titiler/).

## What is TiTiler?

TiTiler is a dynamic tile server for Cloud-Optimized GeoTIFFs. It reads COG files on-the-fly and serves map tiles that web mapping libraries (MapLibre, Leaflet, OpenLayers) can display.

abovepy does **not** depend on TiTiler. It generates TiTiler-compatible URLs that you can use with any TiTiler deployment.

## Setup a local TiTiler

A `docker-compose.yml` is included in `examples/`:

```bash
cd examples/
docker compose up -d
```

This starts TiTiler at `http://localhost:8000`.

## Generate tile URLs

```python
import abovepy
from abovepy.titiler import cog_tile_url, cog_tilejson_url

# Find a DEM tile
tiles = abovepy.search(
    bbox=(-84.85, 38.18, -84.82, 38.21),
    product="dem_phase3"
)

# Generate TiTiler URLs for the first tile
cog_url = tiles.iloc[0].asset_url

tile_url = cog_tile_url(
    cog_url=cog_url,
    titiler_endpoint="http://localhost:8000"
)

tilejson_url = cog_tilejson_url(
    cog_url=cog_url,
    titiler_endpoint="http://localhost:8000"
)

print(tile_url)
# http://localhost:8000/cog/tiles/{z}/{x}/{y}?url=...

print(tilejson_url)
# http://localhost:8000/cog/tilejson.json?url=...
```

## MapLibre GL JS example

Use the TileJSON URL with MapLibre in an HTML page:

```html
<!DOCTYPE html>
<html>
<head>
  <script src="https://unpkg.com/maplibre-gl/dist/maplibre-gl.js"></script>
  <link href="https://unpkg.com/maplibre-gl/dist/maplibre-gl.css" rel="stylesheet" />
  <style>
    body { margin: 0; }
    #map { width: 100vw; height: 100vh; }
  </style>
</head>
<body>
  <div id="map"></div>
  <script>
    const map = new maplibregl.Map({
      container: 'map',
      style: {
        version: 8,
        sources: {
          dem: {
            type: 'raster',
            url: 'http://localhost:8000/cog/tilejson.json?url=YOUR_COG_URL',
            tileSize: 256
          }
        },
        layers: [{
          id: 'dem-layer',
          type: 'raster',
          source: 'dem'
        }]
      },
      center: [-84.85, 38.20],
      zoom: 14
    });
  </script>
</body>
</html>
```

Replace `YOUR_COG_URL` with the actual S3 URL from `tiles.iloc[0].asset_url`.

## Leafmap integration

```python
import abovepy
from abovepy.titiler import cog_tilejson_url
import leafmap

tiles = abovepy.search(county="Franklin", product="dem_phase3")
url = cog_tilejson_url(
    cog_url=tiles.iloc[0].asset_url,
    titiler_endpoint="http://localhost:8000"
)

m = leafmap.Map(center=[38.20, -84.85], zoom=13)
m.add_tile_layer(url, name="DEM Phase 3")
m
```

!!! tip
    leafmap requires the `viz` extra: `pip install abovepy[viz]`

## Using a remote TiTiler

If you have a TiTiler instance deployed (e.g., on AWS Lambda or Cloud Run), just change the endpoint:

```python
tile_url = cog_tile_url(
    cog_url=cog_url,
    titiler_endpoint="https://titiler.example.com"
)
```

The HTML example in `examples/web/titiler_map.html` is a ready-to-use template.
