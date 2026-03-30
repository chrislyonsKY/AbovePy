# Roadmap

This roadmap reflects the current direction of abovepy. Priorities can shift based on community feedback and KyFromAbove program updates.

## v2.0 (Current)

- `SearchResult` workflow object replacing bare GeoDataFrame returns
- Enhanced STAC search with CQL2, intersects, sortby, ids, fields
- Kentucky area selectors: point+buffer, custom geometry
- Concurrent and resumable downloads
- Cloud-native COPC reads via laspy CopcReader
- CLI that does real work: estimate, search summaries, concurrent downloads
- Community health documents and docs site parity

## v2.1 (Near Term)

- Stable analysis APIs: `sample`, `profile`, `zonal_stats`, `cut_fill`, `change_detection`, `flood_fill`, `terrain_profile`
- Phase comparison workflows (Phase 2 vs Phase 3 elevation change)
- HUC watershed and USGS quad name area selectors
- Expanded ArcGIS Pro toolbox with terrain and comparison tools

## v2.2 (Mid Term)

- Oblique imagery intelligence: nearest-frame search, multi-direction bundles, contact-sheet previews, camera metadata
- Richer ArcGIS Pro experience: oblique inspection, phase comparison tools
- Shareable web viewer templates
- Optional xarray bridge for array-native workflows

## Long Term

- Integration with Kentucky-specific data programs as they evolve
- Performance optimization for large-area batch workflows
- Plugin architecture for community-contributed analysis modules

## Non-Goals

- Generic STAC client functionality (use pystac-client directly)
- Non-Kentucky data sources
- Reimplementing PDAL, stackstac, or TiTiler
