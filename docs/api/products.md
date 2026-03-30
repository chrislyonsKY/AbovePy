# Products

Product registry mapping user-friendly keys (e.g. `"dem_phase3"`) to
STAC collection IDs (e.g. `"dem-phase3"`).

```python
from abovepy import list_products

for p in list_products():
    print(f"{p.key}: {p.description}")
```

::: abovepy.products
    options:
      members:
        - Product
        - ProductType
        - list_products
        - get_product
        - PRODUCTS
