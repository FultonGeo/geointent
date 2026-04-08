"""Engine — orchestrates LLM, resolver, and dialect codegen."""

from __future__ import annotations

from typing import Any

from nlgeo.compiler import intent as intent_mod
from nlgeo.compiler.codegen import duckdb as duckdb_codegen
from nlgeo.compiler.codegen import geojson as geojson_codegen
from nlgeo.compiler.codegen import geopandas as geopandas_codegen
from nlgeo.compiler.codegen import postgis as postgis_codegen
from nlgeo.llm.backends.mock import MockLLMBackend
from nlgeo.types import Dialect, IntentResult, SpatialContext, TranslationResult


class Engine:
    def __init__(
        self,
        llm: str = "claude",
        *,
        context: SpatialContext,
        mock: MockLLMBackend | None = None,
    ) -> None:
        self._ctx = context
        self._llm_name = llm
        self._mock = mock
        self._claude = None
        self._openai = None
        self._ollama = None

    @property
    def context(self) -> SpatialContext:
        return self._ctx

    @context.setter
    def context(self, value: SpatialContext) -> None:
        self._ctx = value

    def _backend(self) -> Any:
        if self._llm_name == "mock":
            if self._mock is None:
                raise ValueError("Engine(llm='mock') requires mock=MockLLMBackend(...)")
            return self._mock
        if self._llm_name == "claude":
            if self._claude is None:
                from nlgeo.llm.backends import claude

                self._claude = claude.ClaudeBackend()
            return self._claude
        if self._llm_name == "openai":
            if self._openai is None:
                from nlgeo.llm.backends import openai as openai_be

                self._openai = openai_be.OpenAIBackend()
            return self._openai
        if self._llm_name == "ollama":
            if self._ollama is None:
                from nlgeo.llm.backends import ollama as ollama_be

                self._ollama = ollama_be.OllamaBackend()
            return self._ollama
        raise ValueError(f"Unknown llm backend: {self._llm_name!r}")

    def translate(
        self,
        nl: str,
        dialect: Dialect | None = None,
        *,
        with_alternatives: bool = True,
    ) -> TranslationResult:
        dialect = dialect or Dialect.POSTGIS
        backend = self._backend()

        if self._llm_name == "mock":
            base_intent = backend.complete_intent(nl, self._ctx)
        else:
            from nlgeo.llm import prompt

            sys_prompt = prompt.build_system_prompt(self._ctx)
            raw = backend.complete_json(sys_prompt, nl)
            base_intent = IntentResult.model_validate(raw)

        merged, used_resolver = intent_mod.merge_resolver_into_intent(base_intent, self._ctx)
        confidence = intent_mod.compute_confidence(merged, used_resolver)

        if dialect == Dialect.POSTGIS:
            sql, params = postgis_codegen.render_intent(merged, self._ctx)
            primary = TranslationResult(
                query=sql,
                dialect=dialect,
                assumptions={**merged.assumptions},
                confidence=confidence,
                bind_params=params,
            )
        elif dialect == Dialect.GEOPANDAS:
            code = geopandas_codegen.render_intent(merged, self._ctx)
            primary = TranslationResult(
                query=code,
                dialect=dialect,
                assumptions={**merged.assumptions},
                confidence=confidence,
            )
        elif dialect == Dialect.GEOJSON:
            filt = geojson_codegen.render_intent(merged, self._ctx)
            primary = TranslationResult(
                query=filt,
                dialect=dialect,
                assumptions={**merged.assumptions},
                confidence=confidence,
            )
        elif dialect == Dialect.DUCKDB:
            sql = duckdb_codegen.render_intent(merged, self._ctx)
            primary = TranslationResult(
                query=sql,
                dialect=dialect,
                assumptions={**merged.assumptions},
                confidence=confidence,
            )
        elif dialect == Dialect.CQL2:
            raise NotImplementedError("CQL2 dialect is planned for v2")
        else:
            raise ValueError(f"Unsupported dialect: {dialect}")

        alternatives: list[TranslationResult] = []
        if with_alternatives:
            for alt_intent in intent_mod.build_alternate_intents(merged, self._ctx):
                if dialect == Dialect.POSTGIS:
                    sql_a, params_a = postgis_codegen.render_intent(alt_intent, self._ctx)
                    alternatives.append(
                        TranslationResult(
                            query=sql_a,
                            dialect=dialect,
                            assumptions=dict(alt_intent.assumptions),
                            confidence=max(0.5, confidence - 0.1),
                            bind_params=params_a,
                        )
                    )
                elif dialect == Dialect.GEOPANDAS:
                    alternatives.append(
                        TranslationResult(
                            query=geopandas_codegen.render_intent(alt_intent, self._ctx),
                            dialect=dialect,
                            assumptions=dict(alt_intent.assumptions),
                            confidence=max(0.5, confidence - 0.1),
                        )
                    )

        primary.alternatives = alternatives[:2]
        return primary

    def execute(self, result: TranslationResult, conn: Any) -> Any:
        """Run generated PostGIS or DuckDB SQL; return GeoDataFrame or DataFrame."""
        if result.dialect == Dialect.POSTGIS:
            import geopandas as gpd
            from sqlalchemy import text

            bind = result.bind_params or []
            sql = text(result.query)
            if hasattr(conn, "connect"):
                with conn.connect() as c:
                    return gpd.read_postgis(sql, c, params=bind)
            return gpd.read_postgis(sql, conn, params=bind)
        if result.dialect == Dialect.DUCKDB:
            return conn.execute(result.query).fetchdf()
        raise NotImplementedError(f"execute not supported for dialect {result.dialect}")
