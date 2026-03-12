# DL-001: httpx over requests for HTTP client

**Date:** 2026-03-11
**Status:** Accepted
**Author:** Chris Lyons

## Context

abovepy needs an HTTP client for STAC API queries and HTTPS tile downloads. The two main options in the Python ecosystem are `requests` and `httpx`.

## Decision

Use `httpx` as the HTTP client library.

## Alternatives Considered

- **requests** — The de facto standard. Mature, well-documented, huge community. However, it lacks native async support (requires `aiohttp` or `httpx` for async), and its API hasn't evolved significantly.
- **aiohttp** — Full async HTTP client. Rejected because it requires an async-only API design, which adds complexity for users who don't need async.

## Consequences

- Enables future async API (`async_find_tiles`, etc.) without changing the HTTP layer
- Modern connection pooling and HTTP/2 support
- Slightly smaller install footprint than requests + urllib3
- Users who vendor `requests` elsewhere in their stack won't get reuse, but `httpx` is increasingly common in the geospatial Python ecosystem
