# geointent

**PyPI:** [`geoint`](https://pypi.org/project/geoint/) — `pip install geoint` — **Python import:** `nlgeo`

Natural language to spatial geometry: compile descriptions into PostGIS SQL, GeoPandas, GeoJSON filters, or DuckDB spatial SQL.

Repository: [github.com/FultonGeo/geointent](https://github.com/FultonGeo/geointent).

## Install

```bash
pip install geoint
```

Optional extras: `[postgis]`, `[duckdb]`, `[geopandas]`.

## Three common use cases

1. **Utility / asset network (PostGIS)** — Projected CRS (e.g. Indiana State Plane), manholes and mains: use `Dialect.POSTGIS` (default), parameterized `ST_DWithin` SQL, optional `Engine.execute` with your SQLAlchemy connection.
2. **Parcels & zones (GeoJSON or GeoPandas)** — Cadastral polygons vs flood polygons: `Dialect.GEOJSON` for a JSON filter payload, or `Dialect.GEOPANDAS` for executable `.buffer()` / `.within()` code against `GeoDataFrame`s you load.
3. **Global tiles / Overture (DuckDB)** — Cheap bbox predicates on GeoParquet plus `ST_DWithin`: `Dialect.DUCKDB` for SQL shaped for `httpfs` + spatial against public buckets.

Runnable demos (mock LLM, no API keys): `python examples/utility_network.py`, `examples/overture_duckdb.py`, `examples/parcel_analysis.py`.

## Development (venv)

From the repo root, use a virtual environment so dependencies stay isolated:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev,postgis,geopandas]"   # editable from geointent repo
python -m pytest tests/ -m "not integration and not live and not realdata"
```

On macOS/Linux: `source .venv/bin/activate` instead of the `Activate.ps1` line. The `.venv` directory is gitignored.

## Quick start

```python
import nlgeo
from nlgeo import Dialect

engine = nlgeo.Engine(
    llm="claude",
    context=nlgeo.SpatialContext(
        schema=nlgeo.Schema.from_dict({...}),
        domain="utility_network",
        units="feet",
        srid=2965,
    ),
)
result = engine.translate("manholes within 50 feet of a gas line")
print(result.query)
```

See `examples/` and `TESTING.md` for local PostGIS and pytest tiers.
