"""AboveQGIS — KyFromAbove data access for QGIS.

Processing toolbox provider with tools for search, download, mosaic,
and hillshade. Powered by abovepy.
"""


def classFactory(iface):  # noqa: N802 — QGIS convention
    """QGIS plugin entry point."""
    from .plugin import AboveQGISPlugin

    return AboveQGISPlugin(iface)
