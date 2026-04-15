"""Deliverable packaging for abovepy search results.

Produces a self-contained folder with data tiles, footprint index,
checksums, provenance metadata, preview image, and optional QGIS project.
"""

from __future__ import annotations

import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path

logger = logging.getLogger(__name__)

_CHUNK_SIZE = 256 * 1024  # 256 KB


@dataclass
class Package:
    """A completed deliverable package."""

    output_dir: Path
    files: list[Path]
    manifest: dict
    tile_count: int
    total_size_mb: float
    has_qgis_project: bool

    def __repr__(self) -> str:
        return (
            f"Package({self.output_dir.name!r}, "
            f"{self.tile_count} tile(s), "
            f"{self.total_size_mb} MB, "
            f"qgis={self.has_qgis_project})"
        )


def _sha256_file(path: Path) -> str:
    """Compute SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(_CHUNK_SIZE):
            h.update(chunk)
    return h.hexdigest()


def _compute_checksums(
    files: list[Path],
    base_dir: Path,
    max_workers: int = 4,
) -> dict[str, str]:
    """SHA-256 checksums computed in parallel.

    Returns {relative_path: hex_digest}.
    """
    if not files:
        return {}

    results: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(_sha256_file, f): f.relative_to(base_dir).as_posix()
            for f in files
        }
        for future in as_completed(futures):
            rel_path = futures[future]
            try:
                results[rel_path] = future.result()
            except OSError:
                logger.warning("Failed to checksum %s", rel_path)
                results[rel_path] = ""
    return results


def _render_disclaimer(
    product_display_name: str,
    tile_count: int,
) -> str:
    """Render the DISCLAIMER.txt template with package metadata."""
    template_text = (
        resources.files("abovepy.templates")
        .joinpath("DISCLAIMER.txt")
        .read_text(encoding="utf-8")
    )
    return template_text.format(
        timestamp=datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        product_display_name=product_display_name,
        tile_count=tile_count,
    )
