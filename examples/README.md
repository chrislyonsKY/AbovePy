# Examples

Working examples for abovepy.

## Scripts

| Script | Description |
|---|---|
| `scripts/quickstart.py` | Search, download, and mosaic DEM tiles |
| `scripts/frankfort_hillshade.py` | Full hillshade workflow with visualization |
| `scripts/county_ortho_download.py` | Download orthoimagery by county name |
| `scripts/stream_window.py` | Windowed read from a remote COG (no download) |
| `scripts/explore_products.py` | List all products and tile counts |

## Web

| File | Description |
|---|---|
| `web/titiler_map.html` | MapLibre GL JS viewer for COGs via TiTiler |

## Docker

```bash
docker compose up -d    # Start local TiTiler at http://localhost:8000
```

## Running

```bash
pip install abovepy

# Basic example
python scripts/quickstart.py

# Hillshade (needs matplotlib)
pip install abovepy[viz]
python scripts/frankfort_hillshade.py

# County ortho download
python scripts/county_ortho_download.py --county Pike
```
