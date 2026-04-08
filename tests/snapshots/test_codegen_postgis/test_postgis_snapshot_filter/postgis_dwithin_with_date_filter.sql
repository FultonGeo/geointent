SELECT s.* FROM "manholes" AS s INNER JOIN "gas_lines" AS r ON ST_DWithin(s.geom, r.geom, %s)
WHERE s.last_inspection < %s::date;