"""Download manager for KyFromAbove tiles.

Handles HTTPS downloads with progress, retry, and local caching.
Uses httpx for connection pooling and async-readiness.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import geopandas as gpd

from abovepy._constants import DOWNLOAD_TIMEOUT, MAX_RETRIES

logger = logging.getLogger(__name__)


def download_tiles(
    tiles: gpd.GeoDataFrame,
    output_dir: str | Path,
    overwrite: bool = False,
) -> list[Path]:
    """Download tiles from asset URLs to a local directory.

    Parameters
    ----------
    tiles : geopandas.GeoDataFrame
        Tile index with 'asset_url' column.
    output_dir : str or Path
        Destination directory.
    overwrite : bool
        Overwrite existing files. Default False.

    Returns
    -------
    list[Path]
        Paths to downloaded files.
    """
    import httpx
    from tqdm import tqdm

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    urls = tiles["asset_url"].dropna().tolist()
    if not urls:
        logger.warning("No asset URLs found in tile index.")
        return []

    downloaded = []
    failed = []
    with httpx.Client(timeout=DOWNLOAD_TIMEOUT) as client:
        for url in tqdm(urls, desc="Downloading tiles", unit="tile"):
            filename = Path(url).name
            dest = output_dir / filename

            if dest.exists() and not overwrite:
                logger.debug("Skipping existing file: %s", dest)
                downloaded.append(dest)
                continue

            try:
                _download_file(client, url, dest)
                downloaded.append(dest)
            except Exception:
                logger.exception("Failed to download %s", url)
                failed.append(url)
                # Clean up partial file
                if dest.exists():
                    dest.unlink()

    if failed:
        logger.warning("Failed to download %d tile(s): %s", len(failed), failed)
    logger.info("Downloaded %d of %d tiles to %s", len(downloaded), len(urls), output_dir)
    return downloaded


def _download_file(client: Any, url: str, dest: Path) -> None:
    """Download a single file with retry logic.

    Parameters
    ----------
    client : httpx.Client
        HTTP client instance.
    url : str
        Source URL.
    dest : Path
        Destination file path.
    """
    from abovepy._exceptions import DownloadError

    for attempt in range(MAX_RETRIES):
        try:
            with client.stream("GET", url) as response:
                response.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in response.iter_bytes(chunk_size=8192):
                        f.write(chunk)
            return
        except Exception as exc:
            if attempt == MAX_RETRIES - 1:
                raise DownloadError(
                    f"Failed to download {url} after {MAX_RETRIES} attempts: {exc}"
                ) from exc
            logger.warning("Retry %d/%d for %s", attempt + 1, MAX_RETRIES, url)
