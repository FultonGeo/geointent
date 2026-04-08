"""Unit conversion tests."""

from __future__ import annotations

import pytest

from geointent.units import to_meters


def test_unit_converter():
    assert to_meters(100, "feet") == pytest.approx(30.48)
    assert to_meters(1, "miles") == pytest.approx(1609.344, rel=1e-5)
