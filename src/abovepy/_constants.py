"""KyFromAbove constants — endpoints, CRS, and configuration."""

STAC_URL = "https://spved5ihrl.execute-api.us-west-2.amazonaws.com/"
S3_BUCKET = "kyfromabove"
S3_REGION = "us-west-2"
S3_OBLIQUES_PREFIX = "imagery/obliques/Phase3/"

# KyFromAbove TiTiler endpoints (hosted by Ian Horn / COT-GIS)
TITILER_ENDPOINT = "https://6hp4guqpwe.execute-api.us-west-2.amazonaws.com"
TITILER_PGSTAC_ENDPOINT = "https://vdo05uew72.execute-api.us-west-2.amazonaws.com"
# County mosaic paths (pre-built county-level mosaics on S3)
S3_COUNTY_MOSAIC_MRSID = "imagery/orthos/Phase3/County-Mosaics/MrSIDs/"
S3_COUNTY_MOSAIC_TPKX = "imagery/orthos/Phase3/County-Mosaics/Tile-Packages-tpkx/"
S3_BASE_URL = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com"

NATIVE_CRS = "EPSG:3089"  # Kentucky Single Zone, US Survey Feet
DEFAULT_INPUT_CRS = "EPSG:4326"  # What users typically provide
TILE_SIZE_FT = 5000  # 5000×5000 foot tile grid

# STAC API capabilities (confirmed from live API 2026-03)
STAC_SUPPORTS_CQL2 = True
STAC_SUPPORTS_SEARCH = True
STAC_SUPPORTS_COLLECTION_SEARCH = True

# Oblique sidecar metadata cache TTL (seconds)
SIDECAR_CACHE_TTL = 3600

# HTTP retry configuration
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 0.5
REQUEST_TIMEOUT = 30  # seconds
DOWNLOAD_TIMEOUT = 300  # seconds for large tile downloads

# Download concurrency and chunking
DEFAULT_DOWNLOAD_WORKERS = 8
DOWNLOAD_CHUNK_SIZE = 262144  # 256 KB
