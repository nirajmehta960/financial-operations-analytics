-- ============================================================
-- SQL ETL PIPELINE (SQLite) — STAGING
-- Standardizes and types raw fields; derives row-level features.
-- ============================================================

DROP TABLE IF EXISTS stg_line_items;

-- Superstore date fields are typically M/D/YYYY. Normalize to YYYY-MM-DD.
-- If your file uses a different format, adjust the substr() logic below.
CREATE TABLE stg_line_items AS
WITH typed AS (
  SELECT
    -- Identifiers
    "Order ID" AS order_id,
    "Customer ID" AS customer_id,
    "Product ID" AS product_id,

    -- Core dims
    "Ship Mode" AS ship_mode,
    "Segment" AS segment,
    "Region" AS region,
    "State" AS state,
    COALESCE(NULLIF("City", ''), 'Unknown') AS city,
    "Category" AS category,
    "Sub-Category" AS sub_category,
    "Product Name" AS product_name,

    -- Dates (parse from M/D/YYYY or MM/DD/YYYY)
    CASE
      WHEN "Order Date" IS NULL OR "Order Date" = '' THEN NULL
      ELSE date(
        substr("Order Date", length("Order Date") - 3, 4) || '-' ||
        printf('%02d', CAST(substr("Order Date", 1, instr("Order Date", '/') - 1) AS INTEGER)) || '-' ||
        printf('%02d', CAST(substr("Order Date", instr("Order Date", '/') + 1, instr(substr("Order Date", instr("Order Date", '/') + 1), '/') - 1) AS INTEGER))
      )
    END AS order_date,
    CASE
      WHEN "Ship Date" IS NULL OR "Ship Date" = '' THEN NULL
      ELSE date(
        substr("Ship Date", length("Ship Date") - 3, 4) || '-' ||
        printf('%02d', CAST(substr("Ship Date", 1, instr("Ship Date", '/') - 1) AS INTEGER)) || '-' ||
        printf('%02d', CAST(substr("Ship Date", instr("Ship Date", '/') + 1, instr(substr("Ship Date", instr("Ship Date", '/') + 1), '/') - 1) AS INTEGER))
      )
    END AS ship_date,

    -- Metrics
    CAST(NULLIF("Sales", '') AS REAL) AS sales,
    CAST(NULLIF("Profit", '') AS REAL) AS profit,
    CAST(NULLIF("Discount", '') AS REAL) AS discount,
    CAST(NULLIF("Quantity", '') AS INTEGER) AS quantity
  FROM superstore_raw
)
SELECT
  *,
  CAST(julianday(ship_date) - julianday(order_date) AS INTEGER) AS shipping_days,
  CASE WHEN sales > 0 THEN (profit / sales) * 100.0 ELSE NULL END AS profit_margin_pct,
  CASE WHEN profit > 0 THEN 1 ELSE 0 END AS is_profitable,
  strftime('%Y-%m', order_date) AS order_month,
  CAST(strftime('%Y', order_date) AS INTEGER) AS order_year,
  (CAST(strftime('%m', order_date) AS INTEGER) - 1) / 3 + 1 AS order_quarter_num
FROM typed
WHERE sales IS NULL OR sales >= 0
  AND (quantity IS NULL OR quantity > 0)
  AND (discount IS NULL OR (discount >= 0 AND discount <= 1));

CREATE INDEX IF NOT EXISTS idx_stg_line_items_order ON stg_line_items(order_id);
CREATE INDEX IF NOT EXISTS idx_stg_line_items_customer ON stg_line_items(customer_id);
CREATE INDEX IF NOT EXISTS idx_stg_line_items_month ON stg_line_items(order_month);

