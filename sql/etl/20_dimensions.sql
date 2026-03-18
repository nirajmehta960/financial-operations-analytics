-- ============================================================
-- SQL ETL PIPELINE (SQLite) — DIMENSIONS
-- Natural-key dimensions (BI-friendly) derived from staged data.
-- ============================================================

DROP TABLE IF EXISTS dim_customer;
DROP TABLE IF EXISTS dim_product;
DROP TABLE IF EXISTS dim_geo;
DROP TABLE IF EXISTS dim_ship_mode;
DROP TABLE IF EXISTS dim_segment;

CREATE TABLE dim_customer AS
SELECT DISTINCT
  customer_id,
  COALESCE(NULLIF(segment, ''), 'Unknown') AS segment,
  COALESCE(NULLIF(region, ''), 'Unknown') AS region,
  COALESCE(NULLIF(state, ''), 'Unknown') AS state,
  COALESCE(NULLIF(city, ''), 'Unknown') AS city
FROM stg_line_items;

CREATE TABLE dim_product AS
SELECT DISTINCT
  product_id,
  COALESCE(NULLIF(category, ''), 'Unknown') AS category,
  COALESCE(NULLIF(sub_category, ''), 'Unknown') AS sub_category,
  COALESCE(NULLIF(product_name, ''), 'Unknown') AS product_name
FROM stg_line_items;

CREATE TABLE dim_geo AS
SELECT DISTINCT
  COALESCE(NULLIF(region, ''), 'Unknown') AS region,
  COALESCE(NULLIF(state, ''), 'Unknown') AS state,
  COALESCE(NULLIF(city, ''), 'Unknown') AS city
FROM stg_line_items;

CREATE TABLE dim_ship_mode AS
SELECT DISTINCT
  COALESCE(NULLIF(ship_mode, ''), 'Unknown') AS ship_mode
FROM stg_line_items;

CREATE TABLE dim_segment AS
SELECT DISTINCT
  COALESCE(NULLIF(segment, ''), 'Unknown') AS segment
FROM stg_line_items;

CREATE INDEX IF NOT EXISTS idx_dim_customer ON dim_customer(customer_id);
CREATE INDEX IF NOT EXISTS idx_dim_product ON dim_product(product_id);

