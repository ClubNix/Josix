-- Obtained from https://www.appsloveworld.com/postgresql/100/80/sort-tables-in-order-of-dependency-postgres
-- https://stackoverflow.com/questions/51279588/sort-tables-in-order-of-dependency-postgres

WITH RECURSIVE fk_tree AS (
    -- All tables not referencing anything else
    SELECT t.oid as reloid,
  	       t.relname AS table_name,
  	       s.nspname AS schema_name,
  	       null::text COLLATE "en_US" AS referenced_table_name,
  	       null::text COLLATE "en_US" AS referenced_schema_name,
  	       1 AS level

    FROM pg_class t JOIN pg_namespace s ON s.oid = t.relnamespace
    WHERE relkind = 'r' AND NOT EXISTS (SELECT *
  				                        FROM pg_constraint
  				                        WHERE contype = 'f'
  				                        AND conrelid = t.oid)
  	AND s.nspname = 'josix' -- limit to one schema 

    UNION ALL 
    SELECT ref.oid,
           ref.relname,
           rs.nspname,
           p.table_name,
           p.schema_name,
           p.level + 1
    FROM pg_class ref JOIN pg_namespace rs ON rs.oid = ref.relnamespace
    		          JOIN pg_constraint c ON c.contype = 'f' AND c.conrelid = ref.oid
    		          JOIN fk_tree p ON p.reloid = c.confrelid
    WHERE ref.oid != p.reloid  -- do not enter to tables referencing theirselves.
), all_tables AS (
    -- this picks the highest level for each table
    SELECT schema_name,
           table_name,
           level, 
           row_number() OVER (PARTITION BY schema_name, table_name ORDER BY level DESC) AS last_table_row
    FROM fk_tree
)
SELECT table_name, schema_name, level
FROM all_tables at
WHERE last_table_row = 1
ORDER BY level;