"""Provenance & Validation — QA workflows for survey deliverables.

Demonstrates how to generate source documentation and check data
quality before including KyFromAbove data in a deliverable:

1. Run validation checks on search results
2. Generate provenance metadata for documentation
3. Compare results across phases

Usage:
    python provenance_and_validation.py
"""

import json

import abovepy


def main():
    # Search for DEM tiles covering Franklin County
    print("=== Searching... ===")
    result = abovepy.search(county="Franklin", product="dem_phase3")
    print(result)

    # --- Validation ---
    # Check for data quality issues before using the data
    print("\n=== Validation Checks ===")
    warnings = result.validate()
    if warnings:
        for w in warnings:
            print(f"  Warning: {w}")
    else:
        print("  No issues found.")

    # --- Provenance ---
    # Generate source metadata for deliverable documentation
    print("\n=== Provenance Metadata ===")
    prov = result.provenance()
    print(f"  Product:      {prov['display_name']}")
    print(f"  Source:        {prov['source_program']}")
    print(f"  Acquisition:  {prov['acquisition_period']}")
    print(f"  Native CRS:   {prov['native_crs']}")
    print(f"  Resolution:   {prov['resolution']}")
    print(f"  Format:        {prov['format']}")
    print(f"  Tile Count:   {prov['tile_count']}")
    print(f"  Est. Size:    {prov['estimated_size_mb']} MB")
    print(f"  Bbox:         {prov['bbox']}")

    # Export full provenance as JSON (for embedding in deliverables)
    print("\n=== Full Provenance JSON ===")
    # Exclude asset_urls for brevity
    prov_summary = {k: v for k, v in prov.items() if k != "asset_urls"}
    print(json.dumps(prov_summary, indent=2, default=str))

    # --- Phase Comparison ---
    # Compare Phase 2 vs Phase 3 coverage for the same area
    print("\n=== Phase Comparison ===")
    phase2 = abovepy.search(county="Franklin", product="dem_phase2")
    phase3 = result
    overlap = phase3.compare(phase2)
    print(f"  Phase 2 tiles: {phase2.count}")
    print(f"  Phase 3 tiles: {phase3.count}")
    print(f"  Overlapping pairs: {len(overlap)}")


if __name__ == "__main__":
    main()

# Expected output:
# === Searching... ===
# SearchResult('dem_phase3', 342 tile(s), ~1710.0 MB)
#
# === Validation Checks ===
#   Warning: 42 tile(s) (12%) have no acquisition date metadata.
#
# === Provenance Metadata ===
#   Product:      DEM Phase 3 (2ft)
#   Source:        KyFromAbove
#   Acquisition:  2022-2025
#   Native CRS:   EPSG:3089
#   Resolution:   2ft
#   Format:        COG
#   Tile Count:   342
#   Est. Size:    1710.0 MB
#   Bbox:         (-85.0, 38.0, -84.6, 38.4)
#
# === Full Provenance JSON ===
# { ... }
#
# === Phase Comparison ===
#   Phase 2 tiles: 340
#   Phase 3 tiles: 342
#   Overlapping pairs: 680
