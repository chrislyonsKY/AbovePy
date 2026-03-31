"""AboveQGIS plugin — Plugins menu + Processing provider."""

import subprocess
import sys

from qgis.core import QgsApplication
from qgis.PyQt.QtWidgets import QAction, QMenu, QMessageBox

from .provider import AboveQGISProvider

REQUIRED_PACKAGE = "abovepy"
MIN_VERSION = "2.0.1"


def _check_abovepy():
    """Return True if abovepy is importable and meets minimum version."""
    try:
        import abovepy
        return True
    except ImportError:
        return False


def _install_abovepy(iface):
    """Prompt the user to install abovepy, then install via pip."""
    reply = QMessageBox.question(
        iface.mainWindow(),
        "AboveQGIS — Missing Dependency",
        f"AboveQGIS requires the <b>abovepy</b> package (>= {MIN_VERSION}).\n\n"
        "Would you like to install it now?\n\n"
        f"This will run: pip install {REQUIRED_PACKAGE}",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.Yes,
    )
    if reply != QMessageBox.Yes:
        return False

    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", REQUIRED_PACKAGE],
            timeout=120,
        )
        QMessageBox.information(
            iface.mainWindow(),
            "AboveQGIS",
            "abovepy installed successfully.\n\n"
            "Please restart QGIS to activate the plugin.",
        )
        return True
    except Exception as e:
        QMessageBox.critical(
            iface.mainWindow(),
            "AboveQGIS — Install Failed",
            f"Failed to install abovepy:\n\n{e}\n\n"
            "Try manually: open the OSGeo4W Shell and run:\n"
            f"  pip install {REQUIRED_PACKAGE}",
        )
        return False


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
        # Check dependency before registering anything
        if not _check_abovepy():
            _install_abovepy(self.iface)
            # Re-check after install attempt
            if not _check_abovepy():
                self.iface.messageBar().pushWarning(
                    "AboveQGIS",
                    "abovepy is not installed — plugin tools will not work. "
                    "Restart QGIS after installing.",
                )

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
            if not _check_abovepy():
                _install_abovepy(self.iface)
                return
            import processing
            processing.execAlgorithmDialog(algorithm_id, {})
        return run

    def unload(self):
        if self.menu is not None:
            self.iface.pluginMenu().removeAction(self.menu.menuAction())
            self.menu = None
        self.actions.clear()
        if self.provider is not None:
            QgsApplication.processingRegistry().removeProvider(self.provider)
