"""CLI entrypoint — `python -m abovepy` prints version and product info."""

from __future__ import annotations

import sys


def main() -> None:
    """Print version and available products."""
    import abovepy

    print(f"abovepy {abovepy.__version__}")
    print(f"Python {sys.version}")
    print()
    print("Available products:")
    for product in abovepy.list_products():
        print(f"  {product.key:<16} {product.display_name} ({product.format})")
    print()
    print(f"STAC API: {abovepy._constants.STAC_URL}")
    print("Docs: https://chrislyonsKY.github.io/AbovePy/")


if __name__ == "__main__":
    main()
