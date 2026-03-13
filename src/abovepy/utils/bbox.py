"""Bounding box utilities and Kentucky county lookup.

The county lookup enables search(county="Pike", product="dem_phase3") —
the domain-specific convenience that differentiates abovepy from raw pystac-client.

Bboxes are approximate (county envelope in EPSG:4326). Sufficient for
STAC tile queries — not for precise boundary analysis.
"""

from __future__ import annotations

# fmt: off
# Kentucky county bounding boxes (EPSG:4326)
# Source: KY county boundaries dissolved to envelopes
# Format: (xmin, ymin, xmax, ymax) = (west, south, east, north)
KY_COUNTIES: dict[str, tuple[float, float, float, float]] = {
    "Adair":       (-85.44, 37.00, -85.05, 37.21),
    "Allen":       (-86.32, 36.63, -86.04, 36.87),
    "Anderson":    (-85.17, 37.92, -84.85, 38.12),
    "Ballard":     (-89.18, 36.94, -88.81, 37.16),
    "Barren":      (-86.16, 36.78, -85.72, 37.07),
    "Bath":        (-83.98, 38.04, -83.59, 38.29),
    "Bell":        (-83.92, 36.54, -83.46, 36.82),
    "Boone":       (-84.92, 38.77, -84.62, 39.11),
    "Bourbon":     (-84.33, 38.12, -84.05, 38.37),
    "Boyd":        (-82.86, 38.26, -82.56, 38.49),
    "Boyle":       (-84.96, 37.59, -84.65, 37.82),
    "Bracken":     (-84.24, 38.60, -83.95, 38.85),
    "Breathitt":   (-83.67, 37.53, -83.25, 37.84),
    "Breckinridge": (-86.62, 37.60, -86.15, 37.93),
    "Bullitt":     (-85.89, 37.83, -85.52, 38.08),
    "Butler":      (-86.82, 37.00, -86.44, 37.25),
    "Caldwell":    (-87.91, 37.01, -87.53, 37.26),
    "Calloway":    (-88.60, 36.50, -88.22, 36.75),
    "Campbell":    (-84.53, 38.83, -84.23, 39.11),
    "Carlisle":    (-88.98, 36.82, -88.61, 36.99),
    "Carroll":     (-85.23, 38.61, -84.92, 38.81),
    "Carter":      (-83.36, 38.16, -82.96, 38.51),
    "Casey":       (-85.11, 37.24, -84.72, 37.50),
    "Christian":   (-87.70, 36.63, -87.15, 37.07),
    "Clark":       (-84.29, 37.89, -84.05, 38.12),
    "Clay":        (-83.94, 37.06, -83.47, 37.36),
    "Clinton":     (-85.24, 36.63, -84.99, 36.86),
    "Crittenden":  (-88.26, 37.07, -87.90, 37.39),
    "Cumberland":  (-85.62, 36.63, -85.30, 36.89),
    "Daviess":     (-87.33, 37.62, -86.99, 37.92),
    "Edmonson":    (-86.38, 37.07, -86.02, 37.31),
    "Elliott":     (-83.35, 38.08, -83.04, 38.34),
    "Estill":      (-84.01, 37.64, -83.71, 37.88),
    "Fayette":     (-84.62, 37.96, -84.35, 38.16),
    "Fleming":     (-83.91, 38.24, -83.56, 38.49),
    "Floyd":       (-82.93, 37.47, -82.57, 37.83),
    "Franklin":    (-85.06, 38.11, -84.73, 38.40),
    "Fulton":      (-89.42, 36.50, -88.81, 36.68),
    "Gallatin":    (-84.97, 38.70, -84.71, 38.89),
    "Garrard":     (-84.79, 37.58, -84.47, 37.79),
    "Grant":       (-84.77, 38.58, -84.47, 38.81),
    "Graves":      (-88.96, 36.60, -88.47, 36.94),
    "Grayson":     (-86.35, 37.26, -85.89, 37.53),
    "Green":       (-85.74, 37.16, -85.39, 37.42),
    "Greenup":     (-83.18, 38.39, -82.65, 38.71),
    "Hancock":     (-86.93, 37.68, -86.57, 37.90),
    "Hardin":      (-86.16, 37.56, -85.65, 37.87),
    "Harlan":      (-83.44, 36.69, -82.98, 36.99),
    "Harrison":    (-84.58, 38.35, -84.22, 38.62),
    "Hart":        (-86.03, 37.14, -85.64, 37.41),
    "Henderson":   (-87.83, 37.57, -87.36, 37.87),
    "Henry":       (-85.39, 38.39, -85.03, 38.64),
    "Hickman":     (-89.18, 36.50, -88.81, 36.82),
    "Hopkins":     (-87.74, 37.14, -87.29, 37.51),
    "Jackson":     (-84.03, 37.30, -83.72, 37.58),
    "Jefferson":   (-85.95, 38.05, -85.42, 38.38),
    "Jessamine":   (-84.72, 37.76, -84.44, 37.97),
    "Johnson":     (-83.16, 37.67, -82.73, 38.01),
    "Kenton":      (-84.70, 38.87, -84.43, 39.11),
    "Knott":       (-83.18, 37.30, -82.80, 37.59),
    "Knox":        (-84.05, 36.73, -83.58, 37.03),
    "Larue":       (-85.88, 37.45, -85.56, 37.68),
    "Laurel":      (-84.22, 36.94, -83.85, 37.23),
    "Lawrence":    (-83.05, 37.92, -82.57, 38.24),
    "Lee":         (-83.82, 37.52, -83.55, 37.73),
    "Leslie":      (-83.58, 37.01, -83.26, 37.28),
    "Letcher":     (-83.07, 37.00, -82.64, 37.27),
    "Lewis":       (-83.64, 38.38, -83.18, 38.70),
    "Lincoln":     (-84.85, 37.37, -84.47, 37.65),
    "Livingston":  (-88.42, 37.01, -88.04, 37.24),
    "Logan":       (-87.06, 36.64, -86.62, 36.97),
    "Lyon":        (-88.23, 36.91, -87.90, 37.12),
    "Madison":     (-84.55, 37.53, -84.12, 37.86),
    "Magoffin":    (-83.40, 37.63, -83.02, 37.90),
    "Marion":      (-85.57, 37.48, -85.18, 37.73),
    "Marshall":    (-88.50, 36.82, -88.18, 37.04),
    "Martin":      (-82.61, 37.55, -82.32, 37.81),
    "Mason":       (-83.93, 38.49, -83.57, 38.73),
    "McCracken":   (-88.79, 36.93, -88.42, 37.15),
    "McCreary":    (-84.63, 36.54, -84.22, 36.81),
    "McLean":      (-87.38, 37.39, -87.08, 37.64),
    "Meade":       (-86.29, 37.86, -85.88, 38.09),
    "Menifee":     (-83.68, 37.86, -83.38, 38.09),
    "Mercer":      (-85.00, 37.71, -84.68, 37.93),
    "Metcalfe":    (-85.69, 36.85, -85.38, 37.07),
    "Monroe":      (-85.79, 36.63, -85.42, 36.87),
    "Montgomery":  (-84.02, 37.96, -83.82, 38.16),
    "Morgan":      (-83.53, 37.83, -83.15, 38.11),
    "Muhlenberg":  (-87.30, 37.07, -86.93, 37.40),
    "Nelson":      (-85.78, 37.68, -85.35, 37.97),
    "Nicholas":    (-84.24, 38.25, -83.93, 38.48),
    "Ohio":        (-87.01, 37.25, -86.55, 37.59),
    "Oldham":      (-85.62, 38.29, -85.31, 38.52),
    "Owen":        (-84.95, 38.44, -84.61, 38.71),
    "Owsley":      (-83.70, 37.36, -83.41, 37.60),
    "Pendleton":   (-84.59, 38.48, -84.24, 38.72),
    "Perry":       (-83.42, 37.18, -83.03, 37.48),
    "Pike":        (-82.73, 37.38, -82.05, 37.70),
    "Powell":      (-83.91, 37.74, -83.65, 37.96),
    "Pulaski":     (-84.85, 36.85, -84.39, 37.20),
    "Robertson":   (-84.14, 38.43, -83.88, 38.59),
    "Rockcastle":  (-84.46, 37.28, -84.16, 37.53),
    "Rowan":       (-83.61, 38.11, -83.26, 38.35),
    "Russell":     (-85.18, 36.79, -84.85, 37.07),
    "Scott":       (-84.76, 38.25, -84.44, 38.49),
    "Shelby":      (-85.47, 38.13, -85.10, 38.40),
    "Simpson":     (-86.72, 36.63, -86.38, 36.85),
    "Spencer":     (-85.48, 37.92, -85.20, 38.13),
    "Taylor":      (-85.57, 37.32, -85.26, 37.54),
    "Todd":        (-87.27, 36.64, -86.89, 36.93),
    "Trigg":       (-88.10, 36.63, -87.68, 36.97),
    "Trimble":     (-85.46, 38.52, -85.14, 38.73),
    "Union":       (-87.99, 37.55, -87.52, 37.83),
    "Warren":      (-86.64, 36.77, -86.17, 37.07),
    "Washington":  (-85.44, 37.68, -85.09, 37.88),
    "Wayne":       (-85.07, 36.63, -84.72, 36.96),
    "Webster":     (-87.74, 37.42, -87.37, 37.67),
    "Whitley":     (-84.30, 36.63, -83.93, 36.94),
    "Wolfe":       (-83.65, 37.71, -83.32, 37.92),
    "Woodford":    (-84.85, 37.90, -84.60, 38.09),
}
# fmt: on


def get_county_bbox(county: str) -> tuple[float, float, float, float]:
    """Get the bounding box for a Kentucky county.

    Parameters
    ----------
    county : str
        County name (case-insensitive, e.g., "Pike", "franklin").

    Returns
    -------
    tuple
        (xmin, ymin, xmax, ymax) in EPSG:4326.

    Raises
    ------
    ValueError
        If county name is not recognized.
    """
    # Normalize: title case, strip whitespace
    normalized = county.strip().title()
    if normalized not in KY_COUNTIES:
        # Try fuzzy match — check if input is a substring
        matches = [c for c in KY_COUNTIES if normalized.lower() in c.lower()]
        if len(matches) == 1:
            return KY_COUNTIES[matches[0]]
        from abovepy._exceptions import CountyError

        raise CountyError(f"Unknown county '{county}'. Use list_counties() to see valid names.")
    return KY_COUNTIES[normalized]


def list_counties() -> list[str]:
    """List all Kentucky county names.

    Returns
    -------
    list[str]
        Sorted county names.
    """
    return sorted(KY_COUNTIES.keys())


def validate_bbox(bbox: tuple[float, float, float, float]) -> None:
    """Validate a bounding box tuple.

    Parameters
    ----------
    bbox : tuple
        (xmin, ymin, xmax, ymax).

    Raises
    ------
    ValueError
        If bbox is malformed (xmin > xmax, ymin > ymax, or wrong length).
    """
    from abovepy._exceptions import BboxError

    if len(bbox) != 4:
        raise BboxError("Bbox must have 4 elements: (xmin, ymin, xmax, ymax)")
    xmin, ymin, xmax, ymax = bbox
    if xmin >= xmax:
        raise BboxError(f"xmin ({xmin}) must be less than xmax ({xmax})")
    if ymin >= ymax:
        raise BboxError(f"ymin ({ymin}) must be less than ymax ({ymax})")
