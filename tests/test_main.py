"""Tests for the __main__ CLI entrypoint."""

from __future__ import annotations

import subprocess
import sys


def test_python_m_abovepy_runs():
    """python -m abovepy should exit 0 and print help."""
    result = subprocess.run(
        [sys.executable, "-m", "abovepy"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0
    assert "abovepy" in result.stdout


def test_python_m_abovepy_products():
    """python -m abovepy products should list all products."""
    result = subprocess.run(
        [sys.executable, "-m", "abovepy", "products"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0
    assert "dem_phase3" in result.stdout
    assert "ortho_phase1" in result.stdout
    assert "laz_phase2" in result.stdout
