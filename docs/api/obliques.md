# Obliques

KyFromAbove Phase 3 oblique imagery access — S3 discovery, JSON sidecar
metadata, spatial search, and 4-direction bundles.

## Quick Reference

```python
import abovepy
from abovepy.obliques import list_oblique_seasons, search_obliques

# Discovery
seasons = list_oblique_seasons()
frames = search_obliques(direction="bwd", season=seasons[-1], max_items=10)

# Spatial search — frames covering a point, nearest first
frames = abovepy.search_obliques(
    point=(-84.85, 38.19), radius_feet=500, direction=None
)

# Best frame per camera direction for a site
bundle = abovepy.oblique_bundle((-84.85, 38.19))
bundle["bwd"], bundle["fwd"], bundle["left"], bundle["right"]

# Sidecar metadata (tolerant parsing; raw payload always preserved)
frame = frames[0]
frame.fetch_metadata()
frame.footprint        # shapely geometry or None
frame.timestamp        # datetime or None
frame.camera           # camera parameter dict or None
frame.camera_position  # (lon, lat) or None
frame.raw              # full sidecar payload

# Backward compatible with the pre-2.2 dict shape
frame["tif_url"]
dict(frame)
```

The oblique sidecar schema is not yet published; parsing tries candidate
key names and returns `None` for anything it cannot interpret — nothing is
lost, since the raw payload stays on `frame.raw`.

## API Reference

::: abovepy.obliques._metadata.ObliqueFrame

::: abovepy.obliques._s3.search_obliques

::: abovepy.obliques._spatial.search_obliques_near

::: abovepy.obliques._spatial.oblique_bundle

::: abovepy.obliques._metadata.fetch_sidecar

::: abovepy.obliques._s3.list_oblique_seasons
