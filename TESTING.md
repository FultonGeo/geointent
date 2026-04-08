# TESTING.md — geointent testing strategy

## Overview

Testing strategy runs in three tiers: unit (no external deps), integration (local
Docker PostGIS), and real-data (public datasets via DuckDB or OSM). You can develop
and test the entire compiler layer without a PostGIS instance. Real-data tests are
opt-in and require network access.

---

## Tier 1 — Unit Tests (no external dependencies)

These run on every commit. No database, no LLM calls, no network.

### What they cover
- AmbiguityResolver: every spatial term (near, adjacent, along, within, etc.)
  resolved across all domain contexts (utility_network, parcel, environmental)
- CodeGenerator: given a parsed IntentResult, does each dialect produce
  syntactically valid output?
- Schema: from_dict() construction and serialization to prompt format
- SpatialContext: unit construction, unit normalization (feet → meters, etc.)
- TranslationResult: assumptions dict, confidence thresholds, alternatives list

### LLM mocking
Use a fixture that replaces the LLM backend with a deterministic stub. The stub
accepts a prompt and returns a pre-baked IntentResult JSON. This lets you test the
full pipeline without API calls.

```python
# conftest.py
@pytest.fixture
def mock_llm():
    return MockLLMBackend(responses={
        "pipes near river": IntentResult(
            predicate="ST_DWithin",
            subject_table="water_mains",
            reference_table="rivers",
            distance=100.0,
            distance_unit="meters",
            assumptions={"near": "within 100 meters (utility_network default)"}
        )
    })
```

### Snapshot tests for generated SQL
```bash
pytest tests/ --snapshot-update   # update snapshots after intentional changes
pytest tests/                     # fail on diff
```

Keep snapshots in `tests/snapshots/` and commit them. Diffs in PR review are your
first line of defense against SQL regression.

---

## Tier 2 — Integration Tests (local PostGIS via Docker)

These test real PostGIS round-trips: schema introspection, generated SQL execution,
result validation.

### Spin up test PostGIS in 30 seconds
```bash
docker run -d \
  --name nlgeo-test-db \
  -e POSTGRES_PASSWORD=nlgeo \
  -e POSTGRES_DB=nlgeo_test \
  -p 5432:5432 \
  postgis/postgis:16-3.4
```

Connection string for tests:
```
postgresql://postgres:nlgeo@localhost:5432/nlgeo_test
```

### Seed data: two utility-domain test scenarios

**Scenario 1 — Utility network (Indianapolis-ish, Indiana State Plane East SRID 2965)**
```sql
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE gas_lines (
    id SERIAL PRIMARY KEY,
    name TEXT,
    material TEXT,
    install_year INT,
    geom GEOMETRY(LINESTRING, 2965)
);

CREATE TABLE water_mains (
    id SERIAL PRIMARY KEY,
    diameter_in FLOAT,
    pressure_zone TEXT,
    last_inspection DATE,
    geom GEOMETRY(LINESTRING, 2965)
);

CREATE TABLE manholes (
    id SERIAL PRIMARY KEY,
    asset_id TEXT,
    condition_score INT,  -- 1 (poor) to 5 (excellent)
    last_inspection DATE,
    geom GEOMETRY(POINT, 2965)
);

-- Insert some test features in downtown Indy area
-- (projected coords for SRID 2965)
INSERT INTO gas_lines (name, material, install_year, geom) VALUES
  ('Main St Gas', 'steel', 1978,
   ST_GeomFromText('LINESTRING(553000 436000, 553500 436000)', 2965)),
  ('Oak Ave Gas', 'PE', 2005,
   ST_GeomFromText('LINESTRING(553200 435800, 553200 436200)', 2965));

INSERT INTO water_mains (diameter_in, pressure_zone, last_inspection, geom) VALUES
  (8.0, 'Zone A', '2021-03-15',
   ST_GeomFromText('LINESTRING(553050 435900, 553050 436100)', 2965)),
  (12.0, 'Zone B', '2019-11-20',
   ST_GeomFromText('LINESTRING(553400 435950, 553800 435950)', 2965));

INSERT INTO manholes (asset_id, condition_score, last_inspection, geom) VALUES
  ('MH-001', 3, '2020-06-01', ST_GeomFromText('POINT(553060 436000)', 2965)),
  ('MH-002', 2, '2018-01-15', ST_GeomFromText('POINT(553500 436000)', 2965)),
  ('MH-003', 5, '2023-09-10', ST_GeomFromText('POINT(553200 436050)', 2965));

CREATE INDEX ON gas_lines USING GIST (geom);
CREATE INDEX ON water_mains USING GIST (geom);
CREATE INDEX ON manholes USING GIST (geom);
```

**Scenario 2 — Parcel/cadastral (WGS84 SRID 4326)**
```sql
CREATE TABLE parcels (
    id SERIAL PRIMARY KEY,
    parcel_id TEXT,
    owner TEXT,
    zoning TEXT,
    area_sqft FLOAT,
    geom GEOMETRY(POLYGON, 4326)
);

CREATE TABLE flood_zones (
    id SERIAL PRIMARY KEY,
    zone_code TEXT,  -- AE, X, etc.
    geom GEOMETRY(MULTIPOLYGON, 4326)
);

-- Test queries: "parcels inside flood zone AE larger than 5000 sqft"
```

### Integration test examples
```python
import geointent
from geointent.types import SpatialContext

def test_postgis_near_query_executes(postgis_conn, utility_schema):
    engine = geointent.Engine(llm="mock", context=SpatialContext(
        schema=geointent.Schema.from_postgis(postgis_conn),
        domain="utility_network",
        units="feet",
        srid=2965
    ))
    result = engine.translate("manholes within 50 feet of a gas line")
    assert result.confidence > 0.7
    assert "ST_DWithin" in result.query
    # execute and verify it returns rows
    gdf = engine.execute(result, postgis_conn)
    assert len(gdf) >= 1

def test_assumptions_surfaced(postgis_conn, utility_schema):
    engine = geointent.Engine(llm="mock", context=...)
    result = engine.translate("pipes near the river")
    assert "near" in result.assumptions
    assert "meters" in result.assumptions["near"].lower()
```

---

## Tier 3 — Real Data Tests (public datasets, opt-in)

These validate that the library produces meaningful output against real-world schemas
and data at scale. Run manually or in CI with `pytest -m realdata`.

### Option A — Overture Maps via DuckDB (best for development)

Overture publishes global GeoParquet on public S3 — no auth required, no signup.
You can query it directly with DuckDB by installing the spatial and httpfs extensions.

This is the fastest way to get a real spatial dataset with a known schema for testing
your DuckDB dialect output.

```python
# tests/realdata/test_overture_duckdb.py
import duckdb
import pytest

@pytest.mark.realdata
def test_overture_places_indy():
    conn = duckdb.connect()
    conn.execute("INSTALL spatial; LOAD spatial; INSTALL httpfs; LOAD httpfs;")
    conn.execute("SET s3_region='us-west-2';")

    # Indianapolis bbox
    result = conn.execute("""
        SELECT id, names.primary as name, categories.primary as category, geometry
        FROM read_parquet(
          's3://overturemaps-us-west-2/release/2026-03-18.0/theme=places/type=place/*',
          filename=true, hive_partitioning=1
        )
        WHERE bbox.xmin BETWEEN -86.35 AND -85.95
          AND bbox.ymin BETWEEN 39.63 AND 39.95
        LIMIT 500
    """).fetchdf()

    # Now test that geointent can translate against this schema
    # (register the df as a DuckDB table, then run a translation)
    conn.register("indy_places", result)
    # ... geointent Engine with DuckDB dialect against this schema
```

**Available Overture themes for testing:**
- `theme=places/type=place` — POIs, businesses (great for "near" queries)
- `theme=buildings/type=building` — building footprints
- `theme=transportation/type=segment` — roads and paths
- `theme=divisions/type=division_area` — admin boundaries (counties, cities)

All require only `bbox.xmin/ymin` filters to pull down a local subset cheaply.

### Option B — OSM via osm2pgsql + local PostGIS

For PostGIS dialect testing against a real schema with real data:

1. Download an OSM extract for your area from [Geofabrik](https://download.geofabrik.de/)
   - Indiana extract: ~150MB, manageable for local dev
   - Use a small city extract for CI (e.g. Monaco is ~2MB)

2. Load into your Docker PostGIS:
```bash
# install osm2pgsql
brew install osm2pgsql   # or apt-get

# load Indiana extract
osm2pgsql -d nlgeo_test \
  -U postgres \
  -H localhost \
  --hstore \
  indiana-latest.osm.pbf
```

This gives you real tables: `planet_osm_point`, `planet_osm_line`,
`planet_osm_polygon`, `planet_osm_roads` — all with PostGIS geometry columns
and SRID 3857 (Web Mercator). Perfect for testing real spatial queries.

**Example test NL inputs against OSM schema:**
- "all hospitals within 2 miles of a highway"
- "parks larger than 5 acres in Marion County"
- "restaurants near the waterfront"

### Option C — Supabase Free Tier (zero local setup)

Supabase supports PostGIS via the extensions panel on their free tier.
Spin up a free project, enable PostGIS, load the seed SQL from Tier 2 above, and
point your integration tests at the Supabase connection string. Free tier gives you
500MB and is enough for all test data.

```
postgresql://postgres:[password]@[project-ref].supabase.co:5432/postgres
```

This is the easiest option if you don't want Docker locally at all.

---

## Test Fixture Quick Reference

```python
# conftest.py fixtures
import geointent

@pytest.fixture(scope="session")
def postgis_conn():
    """Local Docker PostGIS connection"""
    from sqlalchemy import create_engine
    return create_engine("postgresql://postgres:nlgeo@localhost:5432/nlgeo_test")

@pytest.fixture
def utility_schema():
    """Pre-built Schema for utility network test DB"""
    return geointent.Schema.from_dict({
        "tables": [
            {"name": "gas_lines", "geom_column": "geom", "geom_type": "LINESTRING",
             "srid": 2965, "columns": ["id","name","material","install_year","geom"]},
            {"name": "water_mains", "geom_column": "geom", "geom_type": "LINESTRING",
             "srid": 2965, "columns": ["id","diameter_in","pressure_zone","last_inspection","geom"]},
            {"name": "manholes", "geom_column": "geom", "geom_type": "POINT",
             "srid": 2965, "columns": ["id","asset_id","condition_score","last_inspection","geom"]}
        ]
    })

@pytest.fixture
def utility_context(utility_schema):
    return geointent.SpatialContext(
        schema=utility_schema,
        domain="utility_network",
        units="feet",
        srid=2965,
        bbox=(-86.20, 39.70, -86.10, 39.80)
    )
```

---

## CI Setup (GitHub Actions)

```yaml
# .github/workflows/workflow.yml
jobs:
  unit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -e ".[dev]"
      - run: pytest tests/ -m "not integration and not realdata"

  integration:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgis/postgis:16-3.4
        env:
          POSTGRES_PASSWORD: nlgeo
          POSTGRES_DB: nlgeo_test
        ports: ["5432:5432"]
        options: --health-cmd pg_isready --health-interval 5s
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -e ".[dev,postgis]"
      - run: python tests/seed_db.py   # runs the seed SQL
      - run: pytest tests/ -m integration
        env:
          GEOINTENT_TEST_DB: postgresql://postgres:nlgeo@localhost:5432/nlgeo_test
```

---

## Recommended Test-Driven Development Order

1. Write `test_schema_from_dict` and `test_schema_from_postgis` first — schema is the
   foundation everything else depends on.
2. Write resolver unit tests for the 8 ambiguous terms across 3 domains before
   touching the LLM integration.
3. Write PostGIS codegen snapshot tests with mock IntentResult inputs before
   wiring up the LLM.
4. Only then wire the LLM backend — by this point you know exactly what shape
   the IntentResult needs to be.
5. Add Overture/real-data tests last, once the core pipeline is solid.
