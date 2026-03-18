-- ============================================================
-- SQL ETL PIPELINE (SQLite) — FACTS
-- Builds line-item, order-level, and customer-level facts.
-- ============================================================

DROP TABLE IF EXISTS fct_line_items;
DROP TABLE IF EXISTS fct_orders;
DROP TABLE IF EXISTS fct_customers;

-- 1) Line-item fact (transaction grain)
CREATE TABLE fct_line_items AS
SELECT
  order_id,
  order_date,
  ship_date,
  ship_mode,
  customer_id,
  segment,
  region,
  state,
  city,
  product_id,
  category,
  sub_category,
  product_name,
  quantity,
  discount,
  sales,
  profit,
  shipping_days,
  profit_margin_pct,
  is_profitable,
  order_month,
  order_year,
  order_quarter_num
FROM stg_line_items;

CREATE INDEX IF NOT EXISTS idx_fct_line_items_order ON fct_line_items(order_id);
CREATE INDEX IF NOT EXISTS idx_fct_line_items_customer ON fct_line_items(customer_id);

-- 2) Order-level fact (one row per order_id)
CREATE TABLE fct_orders AS
WITH per_order AS (
  SELECT
    order_id,
    MIN(order_date) AS order_date,
    -- attach first-seen dim values for the order
    MIN(customer_id) AS customer_id,
    MIN(segment) AS segment,
    MIN(region) AS region,
    MIN(state) AS state,
    MIN(ship_mode) AS ship_mode,

    SUM(sales) AS order_total_sales,
    SUM(profit) AS order_total_profit,
    AVG(discount) AS order_avg_discount,
    AVG(shipping_days) AS avg_shipping_days,
    COUNT(*) AS order_items_count
  FROM fct_line_items
  GROUP BY order_id
)
SELECT
  *,
  strftime('%Y-%m', order_date) AS order_month,
  (CAST(strftime('%m', order_date) AS INTEGER) - 1) / 3 + 1 AS order_quarter_num,
  CAST(strftime('%Y', order_date) AS INTEGER) AS order_year,
  CASE WHEN order_total_sales > 0 THEN (order_total_profit / order_total_sales) * 100.0 ELSE NULL END AS order_profit_margin_pct
FROM per_order;

CREATE INDEX IF NOT EXISTS idx_fct_orders_customer ON fct_orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_fct_orders_month ON fct_orders(order_month);

-- 3) Customer-level fact (one row per customer_id) + churn label
-- Churn rule: no purchase in last 365 days relative to dataset max order_date.
CREATE TABLE fct_customers AS
WITH ref AS (
  SELECT MAX(order_date) AS reference_date FROM fct_orders
),
cust AS (
  SELECT
    customer_id,
    MIN(order_date) AS first_order_date,
    MAX(order_date) AS last_order_date,
    COUNT(DISTINCT order_id) AS order_count,
    SUM(order_total_sales) AS total_spent,
    SUM(order_total_profit) AS total_profit,
    AVG(order_avg_discount) AS avg_discount,
    AVG(avg_shipping_days) AS avg_shipping_days
  FROM fct_orders
  GROUP BY customer_id
)
SELECT
  c.*,
  (c.total_spent / NULLIF(c.order_count, 0)) AS avg_order_value,
  CASE WHEN c.total_spent > 0 THEN (c.total_profit / c.total_spent) * 100.0 ELSE NULL END AS avg_profit_margin_pct,
  CAST(julianday(c.last_order_date) - julianday(c.first_order_date) AS INTEGER) AS tenure_days,
  CAST(julianday((SELECT reference_date FROM ref)) - julianday(c.last_order_date) AS INTEGER) AS recency_days,
  CASE WHEN (julianday((SELECT reference_date FROM ref)) - julianday(c.last_order_date)) > 365 THEN 1 ELSE 0 END AS is_churned,
  -- attach most frequent segment + ship mode for customer
  (SELECT segment FROM fct_orders o WHERE o.customer_id = c.customer_id GROUP BY segment ORDER BY COUNT(*) DESC, segment LIMIT 1) AS segment_mode,
  (SELECT ship_mode FROM fct_orders o WHERE o.customer_id = c.customer_id GROUP BY ship_mode ORDER BY COUNT(*) DESC, ship_mode LIMIT 1) AS preferred_ship_mode,
  -- category breadth on raw line items
  (SELECT COUNT(DISTINCT category) FROM fct_line_items li WHERE li.customer_id = c.customer_id) AS unique_categories,
  (SELECT COUNT(DISTINCT sub_category) FROM fct_line_items li WHERE li.customer_id = c.customer_id) AS unique_subcategories
FROM cust c;

CREATE INDEX IF NOT EXISTS idx_fct_customers_churn ON fct_customers(is_churned);

