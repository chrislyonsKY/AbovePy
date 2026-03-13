# Exceptions

All abovepy exceptions inherit from `AbovepyError`, so you can catch
any library error with a single handler:

```python
from abovepy import AbovepyError

try:
    tiles = abovepy.search(county="Nonexistent", product="dem_phase3")
except AbovepyError as e:
    print(f"abovepy error: {e}")
```

Exceptions that replaced `ValueError` also inherit from `ValueError`
for backward compatibility.

::: abovepy._exceptions
    options:
      show_root_heading: false
      members:
        - AbovepyError
        - SearchError
        - DownloadError
        - ReadError
        - MosaicError
        - ProductError
        - CountyError
        - BboxError
