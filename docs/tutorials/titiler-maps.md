# Web Maps with TiTiler

Visualize KyFromAbove COGs in the browser using [TiTiler](https://developmentseed.org/titiler/). This tutorial covers setting up a local TiTiler instance, generating tile URLs from abovepy, building a MapLibre web map, and integrating with Leafmap in Python.

## What is TiTiler?

TiTiler is a dynamic tile server for Cloud-Optimized GeoTIFFs (COGs). It reads COG files on-the-fly from their source (S3, HTTP) and serves standard XYZ map tiles that web mapping libraries (MapLibre GL JS, Leaflet, OpenLayers) can display.

abovepy does **not** depend on TiTiler. It generates TiTiler-compatible URLs that you can use with any TiTiler deployment — local or remote.

!!! note "When to use TiTiler"
    TiTiler is useful when you want to:

    - **View tiles in a web browser** without downloading anything
    - **Share interactive maps** with colleagues who do not have Python or GIS software
    - **Preview data** before committing to a large download

    If you just need to work with the data in Python or ArcGIS Pro, you do not need TiTiler at all. Use `abovepy.read()` for streaming reads or `abovepy.download()` to fetch files directly.

---

## Step 1: Set up a local TiTiler

A `docker-compose.yml` is included in `examples/`:

```bash
cd examples/
docker compose up -d
```

```text
[+] Running 1/1
 ✔ Container examples-titiler-1  Started
```

Verify it is running:

```bash
curl http://localhost:8000/healthz
```

```text
{"status":"ok"}
```

TiTiler is now available at `http://localhost:8000`. You can also open `http://localhost:8000/docs` in a browser to see the interactive Swagger API documentation.

!!! tip "No Docker?"
    If you do not have Docker installed, you can use any publicly available TiTiler instance, or deploy your own on AWS Lambda or Google Cloud Run. The only thing that changes is the `titiler_endpoint` URL in the examples below.

---

## Step 2: Find tiles and generate URLs

```python
import abovepy
from abovepy.titiler import cog_tile_url, cog_tilejson_url

# Find a DEM tile near Frankfort
tiles = abovepy.search(
    bbox=(-84.85, 38.18, -84.82, 38.21),
    product="dem_phase3"
)
print(f"Found {len(tiles)} tiles")

# Get the COG URL for the first tile
cog_url = tiles.iloc[0].asset_url
print(f"COG URL: {cog_url}")
```

```text
Found 2 tiles
COG URL: https://s3.us-west-2.amazonaws.com/kyfromabove/dem-phase3/N1234E5678.tif
```

### Generate a TiTiler XYZ tile URL

This URL template is what web mapping libraries use to request individual map tiles:

```python
tile_url = cog_tile_url(
    cog_url=cog_url,
    titiler_endpoint="http://localhost:8000"
)
print("XYZ Tile URL:")
print(tile_url)
```

```text
XYZ Tile URL:
http://localhost:8000/cog/tiles/{z}/{x}/{y}?url=https%3A%2F%2Fs3.us-west-2.amazonaws.com%2Fkyfromabove%2Fdem-phase3%2FN1234E5678.tif
```

### Generate a TileJSON URL

TileJSON is a metadata format that includes the tile URL template, bounds, min/max zoom, and other information that mapping libraries use to configure a layer automatically:

```python
tilejson_url = cog_tilejson_url(
    cog_url=cog_url,
    titiler_endpoint="http://localhost:8000"
)
print("TileJSON URL:")
print(tilejson_url)
```

```text
TileJSON URL:
http://localhost:8000/cog/tilejson.json?url=https%3A%2F%2Fs3.us-west-2.amazonaws.com%2Fkyfromabove%2Fdem-phase3%2FN1234E5678.tif
```

---

## Step 3: Verify URLs work

Before building a full map, confirm that TiTiler can read the COG. Fetch the TileJSON metadata:

```bash
curl -s "http://localhost:8000/cog/tilejson.json?url=https://s3.us-west-2.amazonaws.com/kyfromabove/dem-phase3/N1234E5678.tif" | python -m json.tool
```

```text
{
    "tilejson": "2.2.0",
    "name": "N1234E5678.tif",
    "version": "1.0.0",
    "scheme": "xyz",
    "tiles": [
        "http://localhost:8000/cog/tiles/{z}/{x}/{y}?url=https%3A%2F%2F..."
    ],
    "minzoom": 10,
    "maxzoom": 18,
    "bounds": [-84.8923, 38.1745, -84.8214, 38.2156],
    "center": [-84.8569, 38.1951, 14]
}
```

You can also request statistics for the COG to understand the data range:

```python
import httpx

stats_url = (
    f"http://localhost:8000/cog/statistics"
    f"?url={cog_url}"
)
response = httpx.get(stats_url)
stats = response.json()

band = stats["b1"]
print(f"Band 1 statistics:")
print(f"  Min:    {band['min']:.1f}")
print(f"  Max:    {band['max']:.1f}")
print(f"  Mean:   {band['mean']:.1f}")
print(f"  StdDev: {band['std']:.1f}")
```

```text
Band 1 statistics:
  Min:    482.3
  Max:    891.7
  Mean:   714.2
  StdDev: 87.4
```

!!! tip "Use statistics for colormap scaling"
    The min/max values from the statistics endpoint tell you the elevation range. Use these to set `rescale` parameters for better visualization:

    ```python
    tile_url = cog_tile_url(
        cog_url=cog_url,
        titiler_endpoint="http://localhost:8000",
        rescale=(482, 892),
        colormap_name="terrain"
    )
    ```

---

## Step 4: MapLibre GL JS web map

Use the TileJSON URL with MapLibre GL JS to create an interactive web map. Save this as an HTML file and open it in a browser:

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>KyFromAbove DEM Viewer</title>
  <script src="https://unpkg.com/maplibre-gl/dist/maplibre-gl.js"></script>
  <link href="https://unpkg.com/maplibre-gl/dist/maplibre-gl.css" rel="stylesheet" />
  <style>
    body { margin: 0; }
    #map { width: 100vw; height: 100vh; }
    #info {
      position: absolute; top: 10px; left: 10px;
      background: rgba(255,255,255,0.9); padding: 10px;
      border-radius: 4px; font-family: sans-serif; font-size: 13px;
    }
  </style>
</head>
<body>
  <div id="map"></div>
  <div id="info">
    <strong>KyFromAbove DEM Phase 3</strong><br/>
    Frankfort, Kentucky — 2ft resolution
  </div>
  <script>
    // Replace with your actual TileJSON URL
    const tilejsonUrl = 'http://localhost:8000/cog/tilejson.json?url=YOUR_COG_URL';

    const map = new maplibregl.Map({
      container: 'map',
      style: {
        version: 8,
        sources: {
          dem: {
            type: 'raster',
            url: tilejsonUrl,
            tileSize: 256
          }
        },
        layers: [{
          id: 'dem-layer',
          type: 'raster',
          source: 'dem',
          paint: {
            'raster-opacity': 0.85
          }
        }]
      },
      center: [-84.85, 38.20],
      zoom: 14
    });

    map.addControl(new maplibregl.NavigationControl());
  </script>
</body>
</html>
```

Replace `YOUR_COG_URL` with the actual S3 URL from `tiles.iloc[0].asset_url`. The URL must be percent-encoded (which `cog_tilejson_url()` does for you).

!!! tip "Ready-made template"
    A complete, ready-to-use HTML map template is included in the repository at `examples/web/titiler_map.html`. It includes a basemap toggle, opacity slider, and layer controls.

---

## Step 5: Generate URLs for multiple tiles

To view multiple tiles as a mosaic in the browser, generate URLs for each tile and add them as separate sources, or use TiTiler's mosaic endpoint:

```python
import abovepy
from abovepy.titiler import cog_tile_url, cog_tilejson_url

tiles = abovepy.search(county="Franklin", product="dem_phase3")
print(f"Generating TiTiler URLs for {len(tiles)} tiles...")

titiler_endpoint = "http://localhost:8000"

for i, row in tiles.head(5).iterrows():
    url = cog_tilejson_url(
        cog_url=row.asset_url,
        titiler_endpoint=titiler_endpoint
    )
    print(f"  Tile {row.tile_id}: {url[:80]}...")
```

```text
Generating TiTiler URLs for 42 tiles...
  Tile N1234E5678: http://localhost:8000/cog/tilejson.json?url=https%3A%2F%2Fs3.us-we...
  Tile N1234E5679: http://localhost:8000/cog/tilejson.json?url=https%3A%2F%2Fs3.us-we...
  Tile N1235E5678: http://localhost:8000/cog/tilejson.json?url=https%3A%2F%2Fs3.us-we...
  Tile N1235E5679: http://localhost:8000/cog/tilejson.json?url=https%3A%2F%2Fs3.us-we...
  Tile N1236E5678: http://localhost:8000/cog/tilejson.json?url=https%3A%2F%2Fs3.us-we...
```

!!! note "Mosaic vs individual tiles"
    For viewing many tiles at once, consider using TiTiler's mosaic endpoint or creating a VRT first and serving that through TiTiler, rather than adding dozens of individual tile layers to the map.

---

## Step 6: Leafmap integration

[Leafmap](https://leafmap.org/) is a Python package for interactive geospatial visualization in Jupyter notebooks. It works well with TiTiler URLs:

```bash
pip install abovepy[viz]
```

```python
import abovepy
from abovepy.titiler import cog_tilejson_url
import leafmap

# Search for tiles
tiles = abovepy.search(county="Franklin", product="dem_phase3")

# Generate TileJSON URL for the first tile
tilejson = cog_tilejson_url(
    cog_url=tiles.iloc[0].asset_url,
    titiler_endpoint="http://localhost:8000"
)
print(f"TileJSON URL: {tilejson[:80]}...")

# Create an interactive map
m = leafmap.Map(center=[38.20, -84.85], zoom=13)
m.add_tile_layer(tilejson, name="DEM Phase 3", attribution="KyFromAbove")
m
```

```text
TileJSON URL: http://localhost:8000/cog/tilejson.json?url=https%3A%2F%2Fs3.us-we...
```

The map displays inline in Jupyter with pan, zoom, and layer controls.

### Add multiple layers

```python
m = leafmap.Map(center=[38.20, -84.85], zoom=13)

# Add DEM layer
dem_tiles = abovepy.search(
    bbox=(-84.9, 38.17, -84.83, 38.22),
    product="dem_phase3"
)
for _, row in dem_tiles.iterrows():
    url = cog_tilejson_url(
        cog_url=row.asset_url,
        titiler_endpoint="http://localhost:8000"
    )
    m.add_tile_layer(url, name=f"DEM {row.tile_id}", attribution="KyFromAbove")

# Add ortho layer
ortho_tiles = abovepy.search(
    bbox=(-84.9, 38.17, -84.83, 38.22),
    product="ortho_phase3"
)
for _, row in ortho_tiles.iterrows():
    url = cog_tilejson_url(
        cog_url=row.asset_url,
        titiler_endpoint="http://localhost:8000"
    )
    m.add_tile_layer(url, name=f"Ortho {row.tile_id}", attribution="KyFromAbove")

print(f"Added {len(dem_tiles)} DEM layers and {len(ortho_tiles)} ortho layers")
m
```

```text
Added 6 DEM layers and 6 ortho layers
```

!!! tip "Leafmap requires the viz extra"
    If you see `ModuleNotFoundError: No module named 'leafmap'`, install it with: `pip install abovepy[viz]`

---

## Step 7: Orthoimagery in the browser

TiTiler works especially well with orthoimagery (aerial photos), which are RGB COGs:

```python
import abovepy
from abovepy.titiler import cog_tilejson_url

# Find Phase 3 ortho tiles (3-inch resolution)
ortho = abovepy.search(
    bbox=(-84.87, 38.19, -84.84, 38.21),
    product="ortho_phase3"
)
print(f"Found {len(ortho)} ortho tiles")

# Generate TileJSON URL — no colormap needed for RGB
url = cog_tilejson_url(
    cog_url=ortho.iloc[0].asset_url,
    titiler_endpoint="http://localhost:8000"
)
print(f"TileJSON URL: {url[:80]}...")
```

```text
Found 2 ortho tiles
TileJSON URL: http://localhost:8000/cog/tilejson.json?url=https%3A%2F%2Fs3.us-we...
```

!!! note "Ortho vs DEM rendering"
    Orthoimagery tiles are RGB (3-band) COGs, so they render naturally as aerial photos without needing a colormap. DEM tiles are single-band (elevation values) and benefit from a colormap like `terrain` or `viridis` to make them visually meaningful.

---

## Using a remote TiTiler

If you have a TiTiler instance deployed (e.g., on AWS Lambda or Google Cloud Run), just change the endpoint:

```python
tile_url = cog_tile_url(
    cog_url=cog_url,
    titiler_endpoint="https://titiler.example.com"
)
print(tile_url)
```

```text
https://titiler.example.com/cog/tiles/{z}/{x}/{y}?url=https%3A%2F%2Fs3.us-west-2.amazonaws.com%2Fkyfromabove%2Fdem-phase3%2FN1234E5678.tif
```

!!! warning "CORS for remote deployments"
    If your TiTiler is hosted on a different domain than your web page, you need to configure CORS (Cross-Origin Resource Sharing) on the TiTiler server. The local Docker deployment includes permissive CORS headers by default.

---

## Quick reference: TiTiler URL patterns

| Endpoint | Purpose | Example |
|----------|---------|---------|
| `/cog/tiles/{z}/{x}/{y}` | XYZ map tiles for web maps | Used by MapLibre, Leaflet |
| `/cog/tilejson.json` | Tile metadata (bounds, zoom range) | Auto-configures map layers |
| `/cog/statistics` | Band statistics (min, max, mean) | Set colormap scale |
| `/cog/preview` | Full-extent PNG preview | Quick look at a tile |
| `/cog/info` | COG metadata (size, CRS, bands) | Inspect file properties |

All endpoints accept a `url` query parameter pointing to the COG file.

---

## Next steps

- [DEM + Hillshade](dem-hillshade.md) — Process DEM data in Python
- [ArcGIS Pro Toolbox](arcgis-pro.md) — Use abovepy inside ArcGIS Pro (does not need TiTiler)
- [Troubleshooting](troubleshooting.md) — Solutions for common issues
