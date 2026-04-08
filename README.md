# geointent

Natural language → spatial geometry: turn plain-language location questions into **PostGIS** SQL, **GeoPandas** / **Shapely** code, **GeoJSON**-style filters, or **DuckDB** spatial SQL.

**Install**

```bash
pip install geointent
```

```python
import geointent
from geointent import Dialect

engine = geointent.Engine(
    llm="claude",
    context=geointent.SpatialContext(
        schema=geointent.Schema.from_dict({...}),
        domain="utility_network",
        units="feet",
        srid=2965,
    ),
)
result = engine.translate("manholes within 50 feet of a gas line")
print(result.query)
```

- **PyPI:** [geointent](https://pypi.org/project/geointent/)  
- **Source:** [github.com/FultonGeo/geointent](https://github.com/FultonGeo/geointent)

Optional extras: `pip install geointent[postgis]`, `[duckdb]`, `[geopandas]`.

## Three common use cases

1. **Utility / asset network (PostGIS)** — Projected CRS (e.g. state plane), mains and structures: `Dialect.POSTGIS` (default), parameterized SQL, optional `Engine.execute` with your SQLAlchemy connection.
2. **Parcels & zones** — `Dialect.GEOJSON` or `Dialect.GEOPANDAS` for polygon relationships and buffers.
3. **Overture / GeoParquet (DuckDB)** — `Dialect.DUCKDB` for bbox-safe SQL against remote Parquet.

Runnable demos (mock LLM, no API keys): `python examples/utility_network.py`, `examples/overture_duckdb.py`, `examples/parcel_analysis.py`.

## Development (venv)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev,postgis,geopandas]"
python -m pytest tests/ -m "not integration and not live and not realdata"
```

On macOS/Linux: `source .venv/bin/activate`.

See `TESTING.md` for PostGIS Docker setup and pytest tiers.
