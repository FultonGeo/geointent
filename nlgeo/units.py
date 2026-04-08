"""Normalize length units to meters for internal reasoning."""

from __future__ import annotations

_FEET_PER_METER = 1.0 / 0.3048
_METERS_PER_MILE = 1609.344
_METERS_PER_KM = 1000.0


def to_meters(value: float, unit: str) -> float:
    """
    Convert a length to meters. Supported units: meters, feet, miles, km, kilometers.
    """
    u = unit.strip().lower()
    if u in ("m", "meter", "meters", "metre", "metres"):
        return float(value)
    if u in ("ft", "foot", "feet"):
        return float(value) * 0.3048
    if u in ("mi", "mile", "miles"):
        return float(value) * _METERS_PER_MILE
    if u in ("km", "kilometer", "kilometers", "kilometre", "kilometres"):
        return float(value) * _METERS_PER_KM
    raise ValueError(f"Unsupported distance unit: {unit!r}")


def from_meters(value_m: float, unit: str) -> float:
    """Convert meters to the requested display unit."""
    u = unit.strip().lower()
    if u in ("m", "meter", "meters", "metre", "metres"):
        return float(value_m)
    if u in ("ft", "foot", "feet"):
        return float(value_m) * _FEET_PER_METER
    if u in ("mi", "mile", "miles"):
        return float(value_m) / _METERS_PER_MILE
    if u in ("km", "kilometer", "kilometers", "kilometre", "kilometres"):
        return float(value_m) / _METERS_PER_KM
    raise ValueError(f"Unsupported distance unit: {unit!r}")
