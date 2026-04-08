# PLAN.md — geointent build plan

## Overview

Five phases, each ending with a gate test suite that must pass before the next phase
begins. Phases 1–2 have zero LLM calls or network dependencies — the full type system,
resolver logic, and SQL generator are built and tested against mocks before the real
API is wired in Phase 3.

**Stack:** Python · Pydantic · Anthropic API · Shapely · pyproj · PostGIS · DuckDB  
**PyPI / import:** [`geointent`](https://pypi.org/project/geointent/) · **GitHub:** [FultonGeo/geointent](https://github.com/FultonGeo/geointent)  
**Target:** PyPI 0.1.0 publish at end of Phase 5

**Local PostGIS for testing:** Use **Docker Desktop** (or any Docker engine) to run PostgreSQL + PostGIS on `localhost`, load **seed data** from `TESTING.md`, and point integration tests at that instance. That gives repeatable schema introspection and `ST_DWithin` / execution checks without a shared server. CI can use the same image and seed pattern as a service container; developers typically run the equivalent container locally.

---

## Build progress (living doc)

Update this table when phases advance or gates change.

| Phase | Status | Notes |
|-------|--------|--------|
| **1** Foundation | **Done** | `test_schema`, `test_resolver`, `test_units`, `test_types_context`; fixtures in `conftest.py` |
| **2** PostGIS codegen | **Done** | `test_codegen_postgis`, snapshots under `tests/snapshots/`, `test_schema_postgis` + `test_execute_postgis` (**integration**), `MockLLMBackend`, `Engine` |
| **3** LLM backend | **Done** | `prompt.py`, `claude.py`, `intent.py`, `test_prompt`, `test_claude_backend`, `test_engine_integration` (**live**); `test_alternatives_populated` (mock) |
| **4** More dialects | **Done** | `geopandas`, `geojson`, `duckdb` codegen + tests; `test_dialect_routing`, `Engine.execute`; `tests/realdata/test_overture_duckdb.py` (**realdata**) |
| **5** Polish & publish | **Mostly done** | README, `examples/`, `.github/workflows/workflow.yml`, `test_openai_backend`, `test_ollama_backend`; **manual:** TestPyPI / PyPI [`geointent`](https://pypi.org/project/geointent/) |

**Quick verify (local):**

```text
pytest tests/ -m "not integration and not live and not realdata"   # unit
pytest tests/ -m integration                                        # needs PostGIS + seed
pytest tests/ -m live                                               # needs ANTHROPIC_API_KEY
python examples/utility_network.py
```

---

## Phase 1 — Foundation: types, schema, context
**Status:** done  
**Estimate:** ~2 days  
**Dependencies:** none (no LLM, no DB, no network)

### What to build

- `geointent/__init__.py` — public API: `import geointent` (Engine, SpatialContext, Schema, TranslationResult)
- `geointent/types.py` — all Pydantic models and enums (no logic, just shapes)
  - `Dialect` enum: POSTGIS | GEOPANDAS | GEOJSON | CQL2 | DUCKDB
  - `SpatialContext` — domain, bbox, units, srid, schema
  - `Schema` — tables: list[TableMeta]
  - `TranslationResult` — query, dialect, assumptions, alternatives, confidence
- `geointent/schema.py` — Schema.from_dict() and Schema.to_prompt_str()
  - `to_prompt_str()` produces compact JSON for LLM prompt injection
- `geointent/compiler/resolver/terms.py` — AmbiguityResolver stubs for all 8 spatial terms
  - Terms: near, adjacent, along, within, beside, surrounding, inside, outside
  - Each resolver receives SpatialContext and returns resolved predicate + assumption string
- `geointent/compiler/resolver/domains.py` — threshold tables per domain
  - Domains: utility_network, parcel, environmental
  - Each domain has default distances per ambiguous term
- Unit converter utility — feet/miles/km all normalize to meters internally
- `tests/conftest.py` — shared fixtures: utility_schema, parcel_schema, utility_context

### File structure after Phase 1

```
repo root/
  pyproject.toml
  PLAN.md
  TESTING.md
  geointent/              # Python package (import geointent)
    __init__.py
    types.py
    schema.py
    compiler/
      __init__.py
      resolver/
        __init__.py
        terms.py
        domains.py
  tests/
    conftest.py
    test_schema.py
    test_resolver.py
    test_units.py
```

### Gate tests — all must pass before Phase 2

| Test | What it checks |
|------|---------------|
| `test_schema_from_dict` | Round-trips Schema.from_dict → to_prompt_str, asserts tables/columns present |
| `test_resolver_near_utility` | "near" in utility_network returns ~50m, surfaces assumption string |
| `test_resolver_near_parcel` | Same term, parcel domain, different threshold |
| `test_resolver_near_env` | Environmental domain, larger threshold |
| `test_unit_converter` | 100 feet → 30.48m, 1 mile → 1609.34m |
| `test_spatial_context_srid` | SpatialContext rejects unknown SRID, accepts 4326/2965/3857 |

### Cursor prompt
```
Build Phase 1 of geointent: types.py, schema.py, resolver stubs, and all gate tests.
Follow the cursorrules file structure.
```

---

## Phase 2 — PostGIS code generator
**Status:** done  
**Estimate:** ~3 days  
**Dependencies:** Docker Desktop (or Docker Engine) + PostGIS image, database seeded per `TESTING.md`; no LLM calls

### What to build

- `IntentResult` Pydantic model — what the LLM will eventually return as structured JSON
  - Fields: predicate, subject_table, ref_table, distance, distance_unit, filters, assumptions
- `MockLLMBackend` — deterministic stub keyed on NL input string, used for all unit tests
- `geointent/compiler/codegen/postgis.py` — IntentResult → parameterized PostGIS SQL
  - Must use %s placeholders, never f-strings with user values
  - Distance must be in CRS units (convert from meters if CRS is projected)
  - Include SRID comment when unit conversion was applied
- Snapshot test infrastructure via pytest-snapshot, first 3 SQL snapshots committed
- PostGIS container (e.g. `postgis/postgis` via Docker Desktop) seeded with utility schema — follow seed SQL in `TESTING.md`
- `geointent/schema.py` — add Schema.from_postgis(conn) introspection
  - Reads geometry_columns, information_schema.columns, spatial_ref_sys
- Stub Engine class — wires MockLLM → resolver → PostGIS codegen → TranslationResult

### File structure additions

```
geointent/
  compiler/
    codegen/
      __init__.py
      postgis.py
  llm/
    __init__.py
    backends/
      __init__.py
      mock.py
  engine.py
tests/
  snapshots/           ← committed snapshot files
  test_codegen_postgis.py
  test_engine_unit.py
  test_schema_postgis.py   ← integration, requires local PostGIS (Docker Desktop + seed)
```

### Gate tests — all must pass before Phase 3

| Test | What it checks |
|------|---------------|
| `test_postgis_dwithin_basic` | IntentResult(near, manholes, gas_lines, 50ft) → SQL has ST_DWithin, unit converted |
| `test_postgis_contains` | IntentResult(inside, parcels, flood_zones) → SQL has ST_Contains/ST_Within |
| `test_postgis_date_filter` | Adds WHERE last_inspection < date when filter present |
| `test_postgis_parameterized` | Generated SQL has %s placeholders, no raw user values |
| `test_schema_from_postgis` | Introspects seeded local PostGIS, finds manholes table, geom col, SRID 2965 |
| Snapshot tests | 3 SQL snapshots committed; re-run fails on diff |
| `test_generated_sql_executes` | Run SQL against seeded local PostGIS, get rows back (integration) |

### Cursor prompt
```
Build Phase 2 of geointent: IntentResult model, MockLLMBackend, PostGIS codegen,
Schema.from_postgis, stub Engine, and all gate tests including Docker integration tests.
```

---

## Phase 3 — LLM backend: real translations
**Status:** done  
**Estimate:** ~3 days  
**Dependencies:** Anthropic API key, same local PostGIS setup as Phase 2 (Docker Desktop + seeded DB)

### What to build

- `geointent/llm/prompt.py` — system prompt builder
  - Injects: schema JSON + SpatialContext + domain thresholds + JSON output instructions
  - LLM must be instructed to return only valid JSON matching IntentResult shape
- `geointent/llm/backends/claude.py` — Anthropic API call + JSON parse + Pydantic validation
  - Retry with exponential backoff, max 3 attempts
  - Raises `geointent.LLMError` after max retries
- Wire Claude backend into Engine, replacing MockLLMBackend
- Alternatives generation — ask LLM for 2 alternate interpretations at different thresholds
  - Populates TranslationResult.alternatives list
- `geointent/compiler/intent.py` — IntentParser wraps LLM call + resolver pass
  - Resolver overrides LLM distance when domain threshold is more specific
- Confidence scoring — heuristic based on LLM response coherence + resolver agreement

### File structure additions

```
geointent/
  llm/
    prompt.py
    backends/
      claude.py
  compiler/
    intent.py
tests/
  test_prompt.py
  test_claude_backend.py
  test_engine_integration.py   ← live LLM calls, marked with @pytest.mark.live
```

### Gate tests — all must pass before Phase 4

| Test | What it checks |
|------|---------------|
| `test_prompt_contains_schema` | Built prompt includes table names and column names |
| `test_prompt_contains_domain` | Built prompt includes utility_network domain context |
| `test_claude_backend_parses_valid_json` | Mock HTTP response with valid JSON → IntentResult |
| `test_claude_backend_retries_on_failure` | First call raises, second succeeds |
| `test_claude_backend_raises_after_max_retries` | 3 failures → `geointent.LLMError` |
| `test_e2e_manhole_query` (live) | "manholes within 50 feet of a gas line" → SQL with ST_DWithin, confidence > 0.7 |
| `test_alternatives_populated` | result.alternatives has 2 items with different thresholds |

### Cursor prompt
```
Build Phase 3 of geointent: prompt builder, Claude LLM backend with retry, IntentParser,
confidence scoring, alternatives generation, and all gate tests. Keep mock backend
working for unit tests.
```

---

## Phase 4 — Additional dialects
**Status:** done  
**Estimate:** ~2 days  
**Dependencies:** DuckDB + httpfs + spatial extensions, Phase 3 complete

### What to build

- `geointent/compiler/codegen/geopandas.py` — IntentResult → executable Shapely/GeoPandas Python
  - Output string must be exec-able with only geopandas and shapely imported
  - "near" predicate → .buffer() call; "inside" → .within() or spatial join
- `geointent/compiler/codegen/geojson.py` — GeoJSON filter expression per RFC 7946
- `geointent/compiler/codegen/duckdb.py` — DuckDB spatial SQL dialect
  - Targets Overture GeoParquet schema on S3
  - bbox filters for cheap row group pruning; ST_DWithin for precision
- `dialect=` parameter added to Engine.translate() — routes to correct codegen module
- `Engine.execute()` — optional execution helper for PostGIS and DuckDB dialects
  - Caller provides their own connection; library does not manage connections

### File structure additions

```
geointent/
  compiler/
    codegen/
      geopandas.py
      geojson.py
      duckdb.py
tests/
  test_codegen_geopandas.py
  test_codegen_geojson.py
  test_codegen_duckdb.py
  realdata/
    test_overture_duckdb.py    ← marked @pytest.mark.realdata
```

### Gate tests — all must pass before Phase 5

| Test | What it checks |
|------|---------------|
| `test_geopandas_output_executes` | Generated Python string exec'd in clean env, no errors |
| `test_geopandas_uses_buffer` | "near" predicate → .buffer() call present in output |
| `test_geojson_filter_valid` | Output parses as valid JSON, has correct spatial operator |
| `test_duckdb_query_runs` (realdata) | DuckDB query against Overture Indianapolis bbox returns rows |
| `test_dialect_routing` | dialect=GEOPANDAS routes to geopandas codegen, not PostGIS |
| `test_execute_postgis` | Engine.execute(result, conn) against seeded local PostGIS returns GeoDataFrame |

### Cursor prompt
```
Build Phase 4 of geointent: GeoPandas, GeoJSON, and DuckDB codegen dialects, dialect
routing in Engine, Engine.execute(), and all gate tests including a live DuckDB test
against Overture data.
```

---

## Phase 5 — Polish, CI, and publish
**Status:** mostly done (PyPI publish manual)  
**Estimate:** ~2 days  
**Dependencies:** PyPI account, GitHub repo, all phases complete

### What to build

- `README.md` — working code example, 3 main use cases, install instructions
- `examples/` directory — 3 runnable scripts
  - `utility_network.py` — PostGIS, Indiana State Plane, manholes near gas lines
  - `overture_duckdb.py` — DuckDB against Overture S3, no local DB required
  - `parcel_analysis.py` — parcel/flood zone intersection, GeoJSON output
- `.github/workflows/workflow.yml` — CI config (standard name: GitHub discovers any `*.yml` in `.github/workflows/`)
  - Unit suite on every push (no external deps)
  - Integration suite on PR to main (PostGIS service container — same image/seed idea as local Docker Desktop)
- `geointent/llm/backends/openai.py` — OpenAI backend, same interface as Claude
- `geointent/llm/backends/ollama.py` — Ollama local backend, same retry logic
- pyproject.toml finalized for PyPI — version 0.1.0, extras: `[postgis]`, `[duckdb]`
- Publish to TestPyPI first, verify clean install, then publish to PyPI

### Gate tests — release criteria

| Test | What it checks |
|------|---------------|
| `test_openai_backend` | Same interface contract as Claude backend, mock HTTP |
| `test_ollama_backend` | Local endpoint, same retry logic |
| CI green | Unit suite passes on push, integration suite passes on PR |
| Example scripts | `python examples/utility_network.py` exits 0 |
| TestPyPI install | `pip install geointent` in clean venv, `import geointent` works |

### Cursor prompt
```
Build Phase 5 of geointent: OpenAI and Ollama backends, README, example scripts,
GitHub Actions CI config, and prepare pyproject.toml for PyPI publish.
```

---

## Public API surface (target for 0.1.0)

```python
import geointent
from geointent import Dialect

# initialize with schema and context
engine = geointent.Engine(
    llm="claude",       # or "openai", "ollama"
    context=geointent.SpatialContext(
        schema=geointent.Schema.from_postgis(conn),   # or Schema.from_dict({...})
        domain="utility_network",
        units="feet",
        srid=2965,
        bbox=(-86.20, 39.70, -86.10, 39.80)
    )
)

# translate natural language
result = engine.translate("manholes within 50 feet of a gas line not inspected since 2020")
result = engine.translate("parcels inside a flood zone", dialect=Dialect.GEOPANDAS)
result = engine.translate("buildings near the river", dialect=Dialect.DUCKDB)

# inspect result
result.query        # generated SQL or Python string
result.dialect      # which dialect was used
result.assumptions  # {"near": "within 50 meters (utility_network default)"}
result.alternatives # list of 2 alternate interpretations
result.confidence   # 0.0 – 1.0

# optional execution (caller provides connection)
gdf = engine.execute(result, conn)
```

---

## Test running reference

Bring up PostGIS first when running integration tests: see `TESTING.md` for the `docker run` one-liner (Docker Desktop), connection string, and seed scripts.

```bash
# unit tests only (no external deps, fast)
pytest tests/ -m "not integration and not live and not realdata"

# unit + integration (requires PostGIS on localhost:5432 — Docker Desktop + seeded DB per TESTING.md)
pytest tests/ -m "not live and not realdata"

# everything including live LLM calls (requires ANTHROPIC_API_KEY)
pytest tests/ -m "not realdata"

# real data tests (requires network, DuckDB httpfs)
pytest tests/ -m realdata

# update snapshots after intentional SQL changes
pytest tests/ --snapshot-update
```

---

## CI environment variables required

| Variable | Used by |
|----------|---------|
| `ANTHROPIC_API_KEY` | Claude backend (live tests only) |
| `OPENAI_API_KEY` | OpenAI backend (live tests only) |
| `GEOINTENT_TEST_DB` | PostGIS integration tests (legacy: `NLGEO_TEST_DB`) |

---

## What is NOT in v1

- Async / streaming translate
- Feedback loop / correction storage (planned v3)
- Web UI or CLI (separate package)
- Direct database drivers — callers provide connections
- Raster operations
- Vector tile output dialect
- CQL2 dialect (planned v2)
