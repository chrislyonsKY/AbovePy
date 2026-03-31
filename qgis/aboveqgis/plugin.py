"""AboveQGIS plugin — registers the Processing provider with QGIS."""

from qgis.core import QgsApplication

from .provider import AboveQGISProvider


class AboveQGISPlugin:
    """Main plugin class — manages the Processing provider lifecycle."""

    def __init__(self, iface):
        self.iface = iface
        self.provider = None

    def initProcessing(self):  # noqa: N802 — QGIS convention
        self.provider = AboveQGISProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):  # noqa: N802 — QGIS convention
        self.initProcessing()

    def unload(self):
        if self.provider is not None:
            QgsApplication.processingRegistry().removeProvider(self.provider)
