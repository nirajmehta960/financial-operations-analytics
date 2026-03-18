-- ============================================================
-- SQL ETL PIPELINE (SQLite) — MARTS / ANALYTICS VIEWS
-- Consumption-ready views for BI and analysis.
-- ============================================================

DROP VIEW IF EXISTS mart_financial_kpis;
DROP VIEW IF EXISTS mart_monthly_revenue_profit;
DROP VIEW IF EXISTS mart_subcategory_pl;
DROP VIEW IF EXISTS mart_discount_band;
DROP VIEW IF EXISTS mart_region_segment_profitability;
DROP VIEW IF EXISTS mart_churn_kpis;

-- 1) Overall KPIs
CREATE VIEW mart_financial_kpis AS
SELECT
  COUNT(*) AS line_items,
  COUNT(DISTINCT order_id) AS orders,
  COUNT(DISTINCT customer_id) AS customers,
  ROUND(SUM(sales), 2) AS total_sales,
  ROUND(SUM(profit), 2) AS total_profit,
  ROUND(SUM(profit) * 100.0 / NULLIF(SUM(sales), 0), 2) AS margin_pct
FROM fct_line_items;

-- 2) Monthly revenue & profit trend
CREATE VIEW mart_monthly_revenue_profit AS
SELECT
  order_month,
  ROUND(SUM(sales), 2) AS sales,
  ROUND(SUM(profit), 2) AS profit,
  ROUND(SUM(profit) * 100.0 / NULLIF(SUM(sales), 0), 2) AS margin_pct
FROM fct_line_items
GROUP BY order_month
ORDER BY order_month;

-- 3) Sub-category P&L
CREATE VIEW mart_subcategory_pl AS
SELECT
  category,
  sub_category,
  COUNT(*) AS line_items,
  ROUND(SUM(sales), 2) AS sales,
  ROUND(SUM(profit), 2) AS profit,
  ROUND(SUM(profit) * 100.0 / NULLIF(SUM(sales), 0), 2) AS margin_pct,
  ROUND(AVG(discount) * 100.0, 2) AS avg_discount_pct
FROM fct_line_items
GROUP BY category, sub_category
ORDER BY profit ASC;

-- 4) Discount band analysis (matches python binning intent)
CREATE VIEW mart_discount_band AS
WITH banded AS (
  SELECT
    CASE
      WHEN discount IS NULL THEN 'Unknown'
      WHEN discount = 0 THEN 'No Discount'
      WHEN discount > 0 AND discount <= 0.10 THEN 'Light (1-10%)'
      WHEN discount > 0.10 AND discount <= 0.20 THEN 'Moderate (11-20%)'
      WHEN discount > 0.20 AND discount <= 0.30 THEN 'Heavy (21-30%)'
      WHEN discount > 0.30 THEN 'Extreme (31%+)'
      ELSE 'Unknown'
    END AS discount_band,
    sales,
    profit
  FROM fct_line_items
)
SELECT
  discount_band,
  COUNT(*) AS tx_count,
  ROUND(SUM(sales), 2) AS total_sales,
  ROUND(SUM(profit), 2) AS total_profit,
  ROUND(AVG(profit), 2) AS avg_profit,
  ROUND(100.0 * SUM(CASE WHEN profit < 0 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS loss_pct,
  ROUND(SUM(profit) * 100.0 / NULLIF(SUM(sales), 0), 2) AS margin_pct
FROM banded
GROUP BY discount_band
ORDER BY
  CASE discount_band
    WHEN 'No Discount' THEN 1
    WHEN 'Light (1-10%)' THEN 2
    WHEN 'Moderate (11-20%)' THEN 3
    WHEN 'Heavy (21-30%)' THEN 4
    WHEN 'Extreme (31%+)' THEN 5
    ELSE 6
  END;

-- 5) Region & segment profitability
CREATE VIEW mart_region_segment_profitability AS
SELECT
  region,
  segment,
  ROUND(SUM(sales), 2) AS sales,
  ROUND(SUM(profit), 2) AS profit,
  ROUND(SUM(profit) * 100.0 / NULLIF(SUM(sales), 0), 2) AS margin_pct,
  COUNT(DISTINCT customer_id) AS customers
FROM fct_line_items
GROUP BY region, segment
ORDER BY margin_pct DESC;

-- 6) Churn KPIs from SQL customer fact
CREATE VIEW mart_churn_kpis AS
SELECT
  COUNT(*) AS customers,
  SUM(is_churned) AS churned_customers,
  ROUND(SUM(is_churned) * 100.0 / NULLIF(COUNT(*), 0), 2) AS churn_rate_pct,
  ROUND(AVG(order_count), 2) AS avg_order_count,
  ROUND(AVG(avg_discount), 4) AS avg_discount,
  ROUND(AVG(total_spent), 2) AS avg_total_spent
FROM fct_customers;

