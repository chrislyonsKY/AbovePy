"""Tests for abovepy deliverable packaging."""

from __future__ import annotations

import pytest

from abovepy._exceptions import AbovepyError, PackageError


class TestPackageError:
    def test_inherits_abovepy_error(self):
        assert issubclass(PackageError, AbovepyError)

    def test_message(self):
        with pytest.raises(PackageError, match="No tiles"):
            raise PackageError("No tiles to package")
