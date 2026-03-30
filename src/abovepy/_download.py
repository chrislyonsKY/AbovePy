"""Download manager for KyFromAbove tiles.

Handles HTTPS downloads with progress, retry, and local caching.
Uses httpx for connection pooling and async-readiness.
Supports concurrent downloads and resumable partial transfers.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import geopandas as gpd

from abovepy._constants import (
    DEFAULT_DOWNLOAD_WORKERS,
    DOWNLOAD_CHUNK_SIZE,
    DOWNLOAD_TIMEOUT,
    MAX_RETRIES,
)

logger = logging.getLogger(__name__)


def download_tiles(
    tiles: gpd.GeoDataFrame,
    output_dir: str | Path,
    overwrite: bool = False,
    max_workers: int = DEFAULT_DOWNLOAD_WORKERS,
    resume: bool = True,
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
    max_workers : int
        Maximum number of concurrent download threads. Default 4.
    resume : bool
        Resume incomplete downloads from ``.part`` files. Default True.

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

    downloaded: list[Path] = []
    failed: list[str] = []

    # Build list of (url, dest) pairs, skipping existing files
    work_items: list[tuple[str, Path]] = []
    for url in urls:
        filename = Path(url).name
        dest = output_dir / filename
        if dest.exists() and not overwrite:
            logger.debug("Skipping existing file: %s", dest)
            downloaded.append(dest)
        else:
            work_items.append((url, dest))

    if not work_items:
        logger.info("Downloaded %d of %d tiles to %s", len(downloaded), len(urls), output_dir)
        return downloaded

    with (
        httpx.Client(timeout=DOWNLOAD_TIMEOUT) as client,
        ThreadPoolExecutor(max_workers=max_workers) as executor,
    ):
            future_to_url = {
                executor.submit(_download_file, client, url, dest, resume): (url, dest)
                for url, dest in work_items
            }
            for future in tqdm(
                as_completed(future_to_url),
                total=len(future_to_url),
                desc="Downloading tiles",
                unit="tile",
            ):
                url, dest = future_to_url[future]
                try:
                    future.result()
                    downloaded.append(dest)
                except Exception:
                    logger.exception("Failed to download %s", url)
                    failed.append(url)

    if failed:
        logger.warning("Failed to download %d tile(s): %s", len(failed), failed)
    logger.info("Downloaded %d of %d tiles to %s", len(downloaded), len(urls), output_dir)
    return downloaded


def _download_file(
    client: Any, url: str, dest: Path, resume: bool = True
) -> None:
    """Download a single file with retry logic and resume support.

    Downloads to a ``.part`` temporary file first, then renames to the
    final destination on success.  When *resume* is True and a ``.part``
    file already exists, the download attempts to continue from where it
    left off using an HTTP ``Range`` header.

    Parameters
    ----------
    client : httpx.Client
        HTTP client instance.
    url : str
        Source URL.
    dest : Path
        Destination file path.
    resume : bool
        Attempt to resume from existing ``.part`` file. Default True.
    """
    from abovepy._exceptions import DownloadError

    part_path = dest.with_suffix(dest.suffix + ".part")

    for attempt in range(MAX_RETRIES):
        try:
            headers: dict[str, str] = {}
            existing_size = 0

            if resume and part_path.exists():
                existing_size = part_path.stat().st_size
                if existing_size > 0:
                    headers["Range"] = f"bytes={existing_size}-"

            with client.stream("GET", url, headers=headers) as response:
                response.raise_for_status()

                mode = "ab" if existing_size > 0 and response.status_code == 206 else "wb"

                with open(part_path, mode) as f:
                    for chunk in response.iter_bytes(
                        chunk_size=DOWNLOAD_CHUNK_SIZE
                    ):
                        f.write(chunk)

            # Success — rename .part to final destination
            part_path.rename(dest)
            return

        except Exception as exc:
            if attempt == MAX_RETRIES - 1:
                # Leave .part file intact for later resume
                raise DownloadError(
                    f"Failed to download {url} after {MAX_RETRIES} attempts: {exc}"
                ) from exc
            logger.warning("Retry %d/%d for %s", attempt + 1, MAX_RETRIES, url)
