# Disclaimer

## Data Accuracy

KyFromAbove data accessed through abovepy is provided **as-is** by the
Commonwealth of Kentucky. The Kentucky Division of Geographic Information and the
KyFromAbove program make no warranties regarding the accuracy, completeness, or
fitness for any particular purpose of the data.

Specific limitations:

- **Elevations are approximate.** DEM and LiDAR-derived elevation values should
  not be treated as survey-grade measurements.
- **Not for legal survey purposes.** This data does not constitute a legal
  boundary survey and should not be used as such.
- **Temporal accuracy.** Orthoimagery and LiDAR data reflect conditions at the
  time of collection. Collection dates vary by phase and region.
- **Spatial accuracy.** Positional accuracy varies by data product and
  collection phase. Consult the metadata for specific accuracy statements.

## Software Warranty

abovepy is distributed under the [GPL-3.0-or-later](LICENSE) license and is
provided **as-is**, without warranty of any kind, express or implied. See the
LICENSE file for the full warranty disclaimer.

## Critical Applications

Users relying on this data for decisions affecting life, safety, property, or
legal matters should:

1. Verify data against authoritative sources
2. Consult licensed professionals (surveyors, engineers) as appropriate
3. Review the metadata and accuracy statements for the specific data products
4. Not rely solely on abovepy outputs for critical determinations

## Third-Party Services

abovepy connects to public AWS endpoints hosting the KyFromAbove STAC API and
data. Availability and performance of these services are outside the control of
the library maintainers.

## Contact

Questions about KyFromAbove data accuracy should be directed to the
[KyFromAbove program](https://kyfromabove.ky.gov). Questions about the library
itself can be filed as [GitHub Issues](https://github.com/chrislyonsKY/AbovePy/issues).
