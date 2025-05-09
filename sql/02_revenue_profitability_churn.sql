-- Revenue, Profitability & Churn — Superstore
-- Assumes table superstore_raw with columns: Order ID, Order Date, Ship Date, Customer ID, Segment, Region, State, Category, Sub-Category, Sales, Quantity, Discount, Profit

-- Revenue & profit totals
SELECT
  SUM(Sales) AS total_sales,
  SUM(Profit) AS total_profit,
  ROUND(100.0 * SUM(Profit) / NULLIF(SUM(Sales), 0), 2) AS profit_margin_pct,
  COUNT(DISTINCT "Order ID") AS total_orders,
  COUNT(DISTINCT "Customer ID") AS unique_customers
FROM superstore_raw;

-- Monthly revenue and profit trend
SELECT
  strftime('%Y-%m', "Order Date") AS order_month,
  SUM(Sales) AS sales,
  SUM(Profit) AS profit,
  COUNT(DISTINCT "Order ID") AS order_count
FROM superstore_raw
GROUP BY strftime('%Y-%m', "Order Date")
ORDER BY order_month;

-- Sub-category P&L (Sales and Profit)
SELECT
  "Sub-Category",
  SUM(Sales) AS total_sales,
  SUM(Profit) AS total_profit,
  ROUND(100.0 * SUM(Profit) / NULLIF(SUM(Sales), 0), 2) AS profit_margin_pct
FROM superstore_raw
GROUP BY "Sub-Category"
ORDER BY total_profit;

-- Discount band vs avg profit (concept: band 0%, 1–10%, 11–20%, 21–30%, 31%+)
SELECT
  CASE
    WHEN Discount = 0 THEN '0%'
    WHEN Discount <= 0.10 THEN '1-10%'
    WHEN Discount <= 0.20 THEN '11-20%'
    WHEN Discount <= 0.30 THEN '21-30%'
    ELSE '31%+'
  END AS discount_band,
  COUNT(*) AS tx_count,
  AVG(Profit) AS avg_profit,
  ROUND(100.0 * SUM(CASE WHEN Profit < 0 THEN 1 ELSE 0 END) / COUNT(*), 1) AS loss_pct
FROM superstore_raw
GROUP BY discount_band
ORDER BY discount_band;

-- Regional profitability
SELECT
  Region,
  SUM(Sales) AS sales,
  SUM(Profit) AS profit,
  ROUND(100.0 * SUM(Profit) / NULLIF(SUM(Sales), 0), 2) AS margin_pct
FROM superstore_raw
GROUP BY Region
ORDER BY profit DESC;

-- Segment profitability
SELECT
  Segment,
  SUM(Sales) AS sales,
  SUM(Profit) AS profit,
  ROUND(100.0 * SUM(Profit) / NULLIF(SUM(Sales), 0), 2) AS margin_pct
FROM superstore_raw
GROUP BY Segment
ORDER BY profit DESC;

-- Churn concept: customers with last order > 365 days before max date
WITH ref AS (
  SELECT MAX("Order Date") AS ref_date FROM superstore_raw
),
last_order AS (
  SELECT "Customer ID", MAX("Order Date") AS last_date
  FROM superstore_raw
  GROUP BY "Customer ID"
)
SELECT
  COUNT(*) AS total_customers,
  SUM(CASE WHEN (julianday(r.ref_date) - julianday(l.last_date)) > 365 THEN 1 ELSE 0 END) AS churned_count,
  ROUND(100.0 * SUM(CASE WHEN (julianday(r.ref_date) - julianday(l.last_date)) > 365 THEN 1 ELSE 0 END) / COUNT(*), 1) AS churn_rate_pct
FROM last_order l
CROSS JOIN ref r;
