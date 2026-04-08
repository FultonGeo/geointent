"""Load seed SQL into NLGEO_TEST_DB (or default local PostGIS). Run: python tests/seed_db.py"""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine, text


def main() -> None:
    url = os.environ.get("GEOINTENT_TEST_DB") or os.environ.get(
        "NLGEO_TEST_DB", "postgresql://postgres:nlgeo@localhost:5432/nlgeo_test"
    )
    sql_path = Path(__file__).parent / "fixtures" / "seed_utility.sql"
    raw = sql_path.read_text(encoding="utf-8")
    engine = create_engine(url)
    with engine.connect() as conn:
        conn.execute(text(raw))
        conn.commit()
    print(f"Seeded {url}")


if __name__ == "__main__":
    main()
