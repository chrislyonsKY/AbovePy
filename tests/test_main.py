"""Tests for the __main__ CLI entrypoint."""

from __future__ import annotations

import subprocess
import sys

import abovepy


def test_python_m_abovepy_runs():
    """python -m abovepy should exit 0 and print version."""
    result = subprocess.run(
        [sys.executable, "-m", "abovepy"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0
    assert abovepy.__version__ in result.stdout


def test_python_m_abovepy_lists_products():
    """CLI should list all 9 products."""
    result = subprocess.run(
        [sys.executable, "-m", "abovepy"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert "dem_phase3" in result.stdout
    assert "ortho_phase1" in result.stdout
    assert "laz_phase2" in result.stdout


def test_python_m_abovepy_shows_stac_url():
    """CLI should display the STAC API URL."""
    result = subprocess.run(
        [sys.executable, "-m", "abovepy"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert "spved5ihrl.execute-api" in result.stdout
