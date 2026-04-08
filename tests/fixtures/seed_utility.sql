CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS gas_lines (
    id SERIAL PRIMARY KEY,
    name TEXT,
    material TEXT,
    install_year INT,
    geom GEOMETRY(LINESTRING, 2965)
);

CREATE TABLE IF NOT EXISTS water_mains (
    id SERIAL PRIMARY KEY,
    diameter_in FLOAT,
    pressure_zone TEXT,
    last_inspection DATE,
    geom GEOMETRY(LINESTRING, 2965)
);

CREATE TABLE IF NOT EXISTS manholes (
    id SERIAL PRIMARY KEY,
    asset_id TEXT,
    condition_score INT,
    last_inspection DATE,
    geom GEOMETRY(POINT, 2965)
);

TRUNCATE gas_lines, water_mains, manholes RESTART IDENTITY;

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

CREATE INDEX IF NOT EXISTS gas_lines_geom_idx ON gas_lines USING GIST (geom);
CREATE INDEX IF NOT EXISTS water_mains_geom_idx ON water_mains USING GIST (geom);
CREATE INDEX IF NOT EXISTS manholes_geom_idx ON manholes USING GIST (geom);
