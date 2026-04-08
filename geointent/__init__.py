"""geointent — natural language to spatial geometry (`pip install geointent`)."""

from geointent.engine import Engine
from geointent.schema import from_postgis
from geointent.types import (
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

__version__ = "0.1.1"
