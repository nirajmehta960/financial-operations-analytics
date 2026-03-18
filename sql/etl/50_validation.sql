-- ============================================================
-- SQL ETL PIPELINE (SQLite) — VALIDATION
-- Lightweight checks to confirm pipeline produced expected tables.
-- ============================================================

-- Ensure raw table exists
SELECT 'raw_rows' AS check_name, COUNT(*) AS value FROM superstore_raw;

-- Ensure staging produced rows
SELECT 'stg_rows' AS check_name, COUNT(*) AS value FROM stg_line_items;

-- Ensure facts produced rows
SELECT 'fct_line_items_rows' AS check_name, COUNT(*) AS value FROM fct_line_items;
SELECT 'fct_orders_rows' AS check_name, COUNT(*) AS value FROM fct_orders;
SELECT 'fct_customers_rows' AS check_name, COUNT(*) AS value FROM fct_customers;

-- Basic KPI sanity
SELECT 'total_sales' AS check_name, ROUND(SUM(sales), 2) AS value FROM fct_line_items;
SELECT 'total_profit' AS check_name, ROUND(SUM(profit), 2) AS value FROM fct_line_items;

