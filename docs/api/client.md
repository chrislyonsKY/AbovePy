# Client

The `KyFromAboveClient` class provides the same functionality as the
top-level functions but lets you manage STAC connections and configuration
explicitly.

```python
from abovepy import KyFromAboveClient

client = KyFromAboveClient()
tiles = client.search(county="Pike", product="dem_phase3")
```

::: abovepy.client.KyFromAboveClient
    options:
      show_root_heading: true
      members_order: source
