# TiTiler URL Helpers

Generate tile, preview, and statistics URLs for use with a
[TiTiler](https://developmentseed.org/titiler/) instance.

!!! info
    abovepy does **not** depend on TiTiler. These helpers only construct
    URLs — you bring your own TiTiler deployment (or use the public
    endpoint at `https://titiler.xyz`).

```python
from abovepy.titiler import cog_tile_url

url = cog_tile_url("https://kyfromabove.s3.amazonaws.com/dem-phase3/N123E456.tif")
# Use the returned TileJSON URL in MapLibre GL JS or Leaflet
```

::: abovepy.titiler
    options:
      members:
        - cog_tile_url
        - cog_preview_url
        - cog_stats_url
