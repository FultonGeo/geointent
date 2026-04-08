"""Shared Pydantic models and enums for nlgeo."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

ALLOWED_SRIDS: frozenset[int] = frozenset({4326, 2965, 3857})


class Dialect(str, Enum):
    POSTGIS = "POSTGIS"
    GEOPANDAS = "GEOPANDAS"
    GEOJSON = "GEOJSON"
    CQL2 = "CQL2"
    DUCKDB = "DUCKDB"


class TableMeta(BaseModel):
    name: str
    geom_column: str = "geom"
    geom_type: str
    srid: int
    columns: list[str] = Field(default_factory=list)
    description: str | None = None


class Schema(BaseModel):
    tables: list[TableMeta]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Schema:
        from nlgeo.schema import schema_from_dict

        return schema_from_dict(data)

    @classmethod
    def from_postgis(cls, conn: Any) -> Schema:
        from nlgeo.schema import from_postgis as fp

        return fp(conn)

    def to_prompt_str(self) -> str:
        from nlgeo.schema import schema_to_prompt_str

        return schema_to_prompt_str(self)


class SpatialContext(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    # ``schema`` is the public name for input/output JSON; ``db_schema`` avoids shadowing BaseModel.schema.
    db_schema: Schema = Field(alias="schema")
    domain: str = "utility_network"
    units: str = "meters"
    srid: int = 4326
    bbox: tuple[float, float, float, float] | None = None

    @property
    def schema(self) -> Schema:
        """Table/column metadata (same as :attr:`db_schema`)."""
        return self.db_schema

    @field_validator("srid")
    @classmethod
    def validate_srid(cls, v: int) -> int:
        if v not in ALLOWED_SRIDS:
            allowed = ", ".join(str(s) for s in sorted(ALLOWED_SRIDS))
            raise ValueError(f"Unknown SRID {v}; allowed: {allowed}")
        return v


class TranslationResult(BaseModel):
    query: str
    dialect: Dialect
    assumptions: dict[str, str] = Field(default_factory=dict)
    alternatives: list[TranslationResult] = Field(default_factory=list)
    confidence: float = 0.8
    bind_params: list[Any] = Field(default_factory=list)


class IntentResult(BaseModel):
    """Structured intent returned by the LLM (or mock) for codegen."""

    predicate: str
    subject_table: str
    ref_table: str | None = None
    distance: float | None = None
    distance_unit: str | None = "meters"
    filters: dict[str, Any] = Field(default_factory=dict)
    assumptions: dict[str, str] = Field(default_factory=dict)


class LLMError(Exception):
    """Raised when the configured LLM backend fails after retries."""

    pass


class ResolvedSpatialTerm(BaseModel):
    """Output of an ambiguity resolver for one spatial term."""

    predicate: str
    distance_meters: float | None = None
    assumption: str
