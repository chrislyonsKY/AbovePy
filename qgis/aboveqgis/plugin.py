"""AboveQGIS plugin — Plugins menu + Processing provider."""

from qgis.core import QgsApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMenu

from .provider import AboveQGISProvider


class AboveQGISPlugin:
    """Main plugin class — adds menu entries and Processing provider."""

    def __init__(self, iface):
        self.iface = iface
        self.provider = None
        self.menu = None
        self.actions = []

    def initProcessing(self):  # noqa: N802 — QGIS convention
        self.provider = AboveQGISProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):  # noqa: N802 — QGIS convention
        self.initProcessing()

        # Build Plugins > AboveQGIS menu
        self.menu = QMenu("&AboveQGIS — KyFromAbove", self.iface.mainWindow())

        tools = [
            ("Search KyFromAbove Tiles", "aboveqgis:search_tiles"),
            ("Download KyFromAbove Tiles", "aboveqgis:download_tiles"),
            ("Mosaic KyFromAbove Tiles", "aboveqgis:mosaic_tiles"),
            ("Generate Hillshade Tile URL", "aboveqgis:hillshade_tile_url"),
        ]

        for label, alg_id in tools:
            action = QAction(label, self.iface.mainWindow())
            action.triggered.connect(self._make_runner(alg_id))
            self.menu.addAction(action)
            self.actions.append(action)

        self.iface.pluginMenu().addMenu(self.menu)

    def _make_runner(self, algorithm_id):
        """Return a callback that opens the Processing dialog for an algorithm."""
        def run():
            from processing.gui.AlgorithmDialog import AlgorithmDialog
            from qgis.core import QgsApplication

            alg = QgsApplication.processingRegistry().algorithmById(algorithm_id)
            if alg is not None:
                dlg = AlgorithmDialog(alg.create(), parent=self.iface.mainWindow())
                dlg.show()

        return run

    def unload(self):
        if self.menu is not None:
            self.iface.pluginMenu().removeAction(self.menu.menuAction())
            self.menu = None
        self.actions.clear()
        if self.provider is not None:
            QgsApplication.processingRegistry().removeProvider(self.provider)
