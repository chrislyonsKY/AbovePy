# Privacy

## No Telemetry

abovepy does not collect telemetry, analytics, or usage statistics of any kind.
The library contains no tracking code and phones home to no servers.

## No Personal Data Collection

abovepy does not collect, store, or transmit personally identifiable information
(PII). The library has no user accounts, no registration, and no login.

## Network Requests

abovepy makes HTTP requests to the following public endpoints:

- **KyFromAbove STAC API** -- to search and retrieve metadata for geospatial
  data products (public AWS endpoint)
- **KyFromAbove S3 bucket** -- to download LiDAR, DEM, and orthoimagery files
  (public AWS endpoint, no credentials required)
- **TiTiler endpoints** -- to generate map tiles and preview images when using
  visualization features (optional)

These are standard HTTPS requests. No authentication tokens, API keys, or user
identifiers are sent. Request content is limited to spatial queries (bounding
boxes, collection names) and data retrieval.

## Public Data Only

All data accessed through abovepy is publicly available government data from the
KyFromAbove program. The library does not access private, restricted, or
authenticated data sources.

## Dependencies

abovepy's dependencies (httpx, pystac-client, rasterio, geopandas, etc.) have
their own privacy characteristics. We are not aware of any telemetry in the
required dependency chain, but users should review dependency privacy policies
for their own compliance needs.

## Contact

Privacy questions can be directed to **chris.lyons@ky.gov**.
