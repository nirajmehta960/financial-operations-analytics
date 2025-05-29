# Data Dictionary

This dictionary documents the three output datasets generated in Phase 3 feature engineering:
- `data/featured/superstore_orders.csv`
- `data/featured/superstore_customers.csv`
- `data/featured/model_ready.csv`

Date coverage in current dataset:
- `min_order_date`: `2014-01-03`
- `max_order_date`: `2017-12-30`

## 1) Orders Dataset
File: `data/featured/superstore_orders.csv`
Grain: one row per `Order ID`

| Column | Type | Definition | How Calculated |
|---|---|---|---|
| `Order ID` | string | Order identifier | Group key |
| `order_total_sales` | float | Total sales for the order | Sum of `Sales` across line items |
| `order_total_profit` | float | Total profit for the order | Sum of `Profit` across line items |
| `order_avg_discount` | float | Average discount in the order | Mean of `Discount` across line items |
| `avg_shipping_days` | float | Average shipping time (days) for the order | Mean of line-level `shipping_days` |
| `order_items_count` | int | Number of line items in the order | Count of rows per `Order ID` |
| `order_date` | datetime | Reference order date | First `Order Date` per `Order ID` |
| `order_month` | string | Order month period | `order_date` to monthly period |
| `order_quarter` | string | Order quarter period | `order_date` to quarterly period |
| `order_year` | int | Order year | Year extracted from `order_date` |
| `order_profit_margin` | float | Profit margin (%) at order level | `order_total_profit / order_total_sales * 100` when sales > 0 |
| `Customer ID` | string | Customer identifier | Attached from first row per `Order ID` |
| `Segment` | string | Customer segment | Attached from first row per `Order ID` |
| `Region` | string | Region | Attached from first row per `Order ID` |
| `State` | string | State | Attached from first row per `Order ID` |
| `Ship Mode` | string | Shipping mode | Attached from first row per `Order ID` |

## 2) Customers Dataset
File: `data/featured/superstore_customers.csv`
Grain: one row per `Customer ID`

Reference date policy:
- `reference_date = max(order_date)` if not explicitly passed.
- In current data, that is `2017-12-30`.

| Column | Type | Definition | How Calculated |
|---|---|---|---|
| `Customer ID` | string | Customer identifier | Group key |
| `first_order_date` | datetime | Earliest observed order date | Min `order_date` per customer |
| `last_order_date` | datetime | Most recent observed order date | Max `order_date` per customer |
| `order_count` | int | Number of unique orders | `nunique(Order ID)` per customer |
| `total_spent` | float | Total customer spend | Sum of `order_total_sales` |
| `total_profit` | float | Total customer profit | Sum of `order_total_profit` |
| `avg_discount` | float | Mean discount across customer orders | Mean of `order_avg_discount` |
| `avg_shipping_days` | float | Mean shipping days across customer orders | Mean of `avg_shipping_days` |
| `avg_order_value` | float | Average value per order | `total_spent / order_count` |
| `avg_profit_margin` | float | Profit margin (%) at customer level | `total_profit / total_spent * 100` when spent > 0 |
| `tenure_days` | int | Active span in days | `last_order_date - first_order_date` |
| `recency_days` | int | Days since last order at reference date | `reference_date - last_order_date` |
| `is_churned` | int (`0/1`) | Churn target | `1` if `recency_days > 365`, else `0` |
| `Segment` | string | Most frequent segment | Mode of order-level `Segment` per customer |
| `preferred_ship_mode` | string | Most frequent shipping mode | Mode of order-level `Ship Mode` per customer |
| `unique_categories` | int | Product-category breadth | Number of unique `Category` values per customer |
| `unique_subcategories` | int | Product-subcategory breadth | Number of unique `Sub-Category` values per customer |

Notes:
- For mode ties, implementation takes the first mode returned.

## 3) Model-Ready Dataset
File: `data/featured/model_ready.csv`
Grain: one row per `Customer ID` equivalent record (identifier removed)
Purpose: direct input to ML training

### Transformations from customers dataset
- Drop identifier and leakage-prone columns:
  - `Customer ID`
  - `first_order_date`
  - `last_order_date`
  - `recency_days` (target leakage, because `is_churned` is derived from it)
- One-hot encode categorical variables (if present):
  - `Segment`
  - `preferred_ship_mode`
- Fill missing numeric values with `0`.
- Keep `is_churned` as the final column.

### Feature groups in model-ready
- Numerical features typically include:
  - `order_count`, `total_spent`, `total_profit`, `avg_discount`, `avg_shipping_days`,
  - `avg_order_value`, `avg_profit_margin`, `tenure_days`,
  - `unique_categories`, `unique_subcategories`
- Encoded categorical features include columns like:
  - `Segment_*`
  - `preferred_ship_mode_*`
- Target:
  - `is_churned`

## Quality and Interpretation Notes
- Discount is represented as decimal fraction in source data (for example, `0.20` = 20%).
- Churn label in this project is a snapshot label relative to dataset end date, not current real-time churn.
- Keep dataset grain in mind during analysis:
  - Orders table for order behavior,
  - Customers table for customer behavior,
  - Model-ready for ML only.
