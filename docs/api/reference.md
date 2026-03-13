# API Reference

## Top-level Functions

The easiest way to use abovepy — import the package and call these directly.

```python
import abovepy

tiles = abovepy.search(county="Franklin", product="dem_phase3")
paths = abovepy.download(tiles, output_dir="./data")
data, profile = abovepy.read(paths[0])
```

::: abovepy
    options:
      members:
        - search
        - download
        - read
        - mosaic
        - info
        - list_products
        - clear_cache
