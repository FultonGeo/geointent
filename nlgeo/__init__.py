"""geointent — natural language to spatial geometry (PyPI: ``geoint``, import: ``nlgeo``)."""

from nlgeo.engine import Engine
from nlgeo.schema import from_postgis
from nlgeo.types import (
    Dialect,
    IntentResult,
    LLMError,
    Schema,
    SpatialContext,
    TranslationResult,
)

__all__ = [
    "Dialect",
    "Engine",
    "IntentResult",
    "LLMError",
    "Schema",
    "SpatialContext",
    "TranslationResult",
    "from_postgis",
]

__version__ = "0.1.0"
