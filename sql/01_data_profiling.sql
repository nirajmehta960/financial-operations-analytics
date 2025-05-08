-- Data Profiling — Superstore
-- Run after loading superstore.csv into a table (e.g. superstore_raw).
-- SQLite-friendly.

-- Row counts
SELECT COUNT(*) AS total_rows FROM superstore_raw;

-- Column list and sample
SELECT * FROM superstore_raw LIMIT 5;

-- Missing values per column (SQLite: empty string or NULL)
SELECT
  SUM(CASE WHEN "Order ID" IS NULL OR "Order ID" = '' THEN 1 ELSE 0 END) AS order_id_nulls,
  SUM(CASE WHEN "Order Date" IS NULL OR "Order Date" = '' THEN 1 ELSE 0 END) AS order_date_nulls,
  SUM(CASE WHEN "Ship Date" IS NULL OR "Ship Date" = '' THEN 1 ELSE 0 END) AS ship_date_nulls,
  SUM(CASE WHEN "Customer ID" IS NULL OR "Customer ID" = '' THEN 1 ELSE 0 END) AS customer_id_nulls,
  SUM(CASE WHEN Sales IS NULL THEN 1 ELSE 0 END) AS sales_nulls,
  SUM(CASE WHEN Profit IS NULL THEN 1 ELSE 0 END) AS profit_nulls,
  SUM(CASE WHEN Discount IS NULL THEN 1 ELSE 0 END) AS discount_nulls
FROM superstore_raw;

-- Exact duplicate rows
SELECT COUNT(*) - COUNT(DISTINCT "Row ID") AS duplicate_row_ids
FROM superstore_raw;
-- Or full row duplicates:
-- SELECT *, COUNT(*) FROM superstore_raw GROUP BY "Order ID", "Order Date", "Customer ID", "Product ID", Sales, Quantity, Discount, Profit
-- HAVING COUNT(*) > 1;

-- Unique entities
SELECT
  COUNT(DISTINCT "Order ID") AS unique_orders,
  COUNT(DISTINCT "Customer ID") AS unique_customers,
  COUNT(DISTINCT "Product ID") AS unique_products;

-- Date range
SELECT MIN("Order Date") AS min_date, MAX("Order Date") AS max_date FROM superstore_raw;

-- Numeric ranges
SELECT
  MIN(Sales) AS min_sales, MAX(Sales) AS max_sales, AVG(Sales) AS avg_sales,
  MIN(Profit) AS min_profit, MAX(Profit) AS max_profit, AVG(Profit) AS avg_profit,
  MIN(Discount) AS min_discount, MAX(Discount) AS max_discount, AVG(Discount) AS avg_discount,
  MIN(Quantity) AS min_qty, MAX(Quantity) AS max_qty
FROM superstore_raw;

-- Categorical value counts
SELECT "Segment", COUNT(*) AS cnt FROM superstore_raw GROUP BY "Segment";
SELECT "Region", COUNT(*) AS cnt FROM superstore_raw GROUP BY "Region";
SELECT "Category", COUNT(*) AS cnt FROM superstore_raw GROUP BY "Category";
SELECT "Ship Mode", COUNT(*) AS cnt FROM superstore_raw GROUP BY "Ship Mode";

-- Loss-making transactions
SELECT SUM(CASE WHEN Profit < 0 THEN 1 ELSE 0 END) AS loss_count,
       COUNT(*) AS total,
       ROUND(100.0 * SUM(CASE WHEN Profit < 0 THEN 1 ELSE 0 END) / COUNT(*), 1) AS loss_pct
FROM superstore_raw;
