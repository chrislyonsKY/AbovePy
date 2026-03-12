"""KyFromAbove constants — endpoints, CRS, and configuration."""

STAC_URL = "https://spved5ihrl.execute-api.us-west-2.amazonaws.com/"
S3_BUCKET = "kyfromabove"
S3_REGION = "us-west-2"
NATIVE_CRS = "EPSG:3089"  # Kentucky Single Zone, US Survey Feet
DEFAULT_INPUT_CRS = "EPSG:4326"  # What users typically provide
TILE_SIZE_FT = 5000  # 5000×5000 foot tile grid

# STAC API capabilities (confirmed from live API 2026-03)
STAC_SUPPORTS_CQL2 = True
STAC_SUPPORTS_SEARCH = True
STAC_SUPPORTS_COLLECTION_SEARCH = True

# HTTP retry configuration
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 0.5
REQUEST_TIMEOUT = 30  # seconds
DOWNLOAD_TIMEOUT = 300  # seconds for large tile downloads
