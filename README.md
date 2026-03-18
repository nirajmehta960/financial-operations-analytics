# Financial Operations Analytics — U.S. Superstore

## Executive Summary

Retail businesses need to understand not just revenue but **where they make or lose money**. This project analyzes **4 years of transactional data (2014–2017)** from a U.S. Superstore (Furniture, Office Supplies, Technology) across all 50 states to build a **Financial Operations Analytics Suite** with three pillars:

1. **Revenue analysis & forecasting** — trends, decomposition, 3–6 month forecast  
2. **Profitability deep-dive** — sub-category P&L, discount–profit analysis, regional/segment performance  
3. **Customer churn prediction** — churn rate (365-day inactivity), drivers, classification model (AUC-ROC target ≥ 0.70)

The dataset includes **actual profit per transaction**, enabling true P&L analysis (not just revenue tracking).

> **Bottom line:** Capping standard discounts at 20% and addressing loss-making sub-categories could improve annual profit by an estimated **$50K–$80K+**.

---

## Key Findings

| #   | Finding                                                                 | Detail                                                                 |
| --- | ----------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| 1   | **~$2.3M sales, ~$286K profit**                                        | ~12.5% margin; three sub-categories (Tables, Bookcases, Supplies) at net loss |
| 2   | **Discount cliff**                                                      | Beyond ~20% discount, profit margins collapse; 40%+ discounts largely unprofitable |
| 3   | **Churn drivers**                                                       | Order frequency, category breadth, discount level, segment              |
| 4   | **Top recommendation**                                                  | Cap standard discounts at 20%; estimated profit improvement $50K–$80K/year |

---

## Exploratory Data Analysis (EDA)

EDA charts are generated when you run **notebook 04 (EDA)** after the data pipeline. They are saved under `images/eda_charts/`.

### Churn Overview (Target Variable)

Customer churn is defined as no purchase in the last 365 days. The distribution of active vs. churned customers is the target for the classification model.

![Churn Overview](images/eda_charts/churn_overview.png)

### Monthly Revenue & Profit Trend

Revenue and profit over time show growth and seasonality (e.g. Q4 peaks).

![Revenue & Profit Trend](images/eda_charts/revenue_profit_trend.png)

### Sub-Category P&L

Sales vs. profit by sub-category highlights loss-making lines (Tables, Bookcases, Supplies) and strong performers (e.g. Copiers, Paper).

![Sub-Category P&L](images/eda_charts/subcategory_pl.png)

### Discount vs. Profit

Transaction-level scatter of discount % vs. profit shows the “discount cliff” — high discounts erode margin.

![Discount vs Profit](images/eda_charts/discount_vs_profit.png)

### Discount Band Analysis (PRD Section 4)

Per-band metrics (No Discount, Light 1–10%, Moderate 11–20%, Heavy 21–30%, Extreme 31%+) support the recommendation to cap discounts at 20%.

![Discount Band Analysis](images/eda_charts/discount_band_analysis.png)

### Regional & Segment Profitability

Profit margin by region and by segment (Consumer, Corporate, Home Office) supports targeting and resource allocation.

![Region Profitability](images/eda_charts/region_profitability.png)  
![Segment Profitability](images/eda_charts/segment_profitability.png)

### Correlation Matrix

Customer-level feature correlations inform the churn model and multicollinearity.

![Correlation Matrix](images/eda_charts/correlation_matrix.png)

---

## Model Performance

### Churn Prediction

Three models are trained: **Logistic Regression**, **Random Forest**, and **Gradient Boosting**. Target metric: AUC-ROC ≥ 0.70. `recency_days` is excluded from features to avoid data leakage (it directly defines the target).

### ROC Curve Comparison

![ROC Comparison](images/eda_charts/roc_comparison.png)

### Confusion Matrices

![Confusion Matrices](images/eda_charts/confusion_matrices.png)

### Feature Importance

Top churn predictors from the best tree-based model (e.g. order count, category breadth, discount, segment).

![Feature Importance](images/eda_charts/feature_importance.png)

---

## Interactive Dashboard (Power BI)

Five-page executive dashboard built in Power BI Service with star-schema data model (fact + dimension tables) and DAX measures.

### Page 1: Financial KPI Overview
![KPI Overview](images/dashboard/01_financial_kpi_overview.png)

### Page 2: Profitability Deep Dive
![Profitability](images/dashboard/02_profitability_deep_dive.png)

### Page 3: Regional & Segment Performance
![Regional](images/dashboard/03_regional_segment_performance.png)

### Page 4: Customer Retention & Churn
![Churn](images/dashboard/04_customer_retention_churn.png)

### Page 5: Executive Recommendations
![Recommendations](images/dashboard/05_executive_recommendations.png)

---

## SQL ETL & Analytics Pipeline

This project includes a production-style **SQL-first ETL pipeline** built in **SQLite** (mirroring the approach used in the diabetes reference project). It loads the raw `superstore.csv` into a SQLite database, transforms it into a curated star-schema-like model, and exposes BI-ready marts.

### 1. Data architecture
The pipeline follows a tiered architecture:
- **Raw (`superstore_raw`)**: raw CSV loaded into SQLite (all columns as text).
- **Staging (`stg_line_items`)**: typed fields, normalized dates, basic validity filters, and derived fields (shipping days, profit margin, month/year/quarter).
- **Dimensions**: natural-key dimensions derived from staging:
  - `dim_customer`, `dim_product`, `dim_geo`, `dim_ship_mode`, `dim_segment`
- **Facts**:
  - `fct_line_items`: transaction grain
  - `fct_orders`: one row per order (aggregations similar to Python feature engineering)
  - `fct_customers`: one row per customer, including churn label (365-day inactivity relative to dataset end date)
- **Marts (Views)**: consumption-ready analytics views:
  - `mart_financial_kpis`, `mart_monthly_revenue_profit`, `mart_subcategory_pl`, `mart_discount_band`, `mart_region_segment_profitability`, `mart_churn_kpis`

### 2. How to run the SQL pipeline

**Step A: Place the data**
- Put `superstore.csv` into `data/raw/` (encoding may be `latin-1`).

**Step B: Run the SQL-first ETL (recommended one-command runner)**

```bash
python3 -m src.sql_pipeline.run_pipeline
```

This will:
1) Load `data/raw/superstore.csv` → SQLite table `superstore_raw`  
2) Execute all scripts in `sql/etl/` (00 → 50) against `data/superstore.sqlite`

### 3. Python-first Analytics Pipeline

Alternatively, you can run the Python-native pipeline which includes cleaning, feature engineering, and churn modeling logic.

**How to run the Python pipeline:**

```bash
python3 -m src.python_pipeline.run_pipeline
```

This will:
1) Clean raw data → `data/preprocessed/`
2) Build order & customer features → `data/featured/`
3) Prepare a target-ready dataset for ML → `data/featured/model_ready.csv`

---

## Business Recommendations

| #   | Action                                                | Expected Impact                    |
| --- | ----------------------------------------------------- | ---------------------------------- |
| 1   | Cap standard discounts at 20%; VP approval above 20%  | Reduce margin erosion; +$50K–$80K/year est. |
| 2   | Address loss-making sub-categories (Tables, Bookcases, Supplies) | Reprice or reduce exposure; eliminate P&L drag |
| 3   | Use churn model to flag at-risk customers             | Reactivation campaigns, loyalty programs |
| 4   | Invest in high-margin regions/segments; review Texas, Ohio | Targeted margin improvement       |
| 5   | Promote high-margin sub-categories (Copiers, Paper, Labels) | Shift mix toward profitable lines |

### Profit Impact Summary

![Profit Impact Summary](images/eda_charts/profit_impact_summary.png)

---

## Project Structure

```
financial-operations-analytics/
│
├── README.md
├── requirements.txt
├── .gitignore
│
├── data/
│   ├── raw/                         # superstore.csv (original)
│   ├── preprocessed/                 # Cleaned transaction-level data
│   └── featured/                    # Order-level, customer-level, model_ready.csv
│
├── docs/
│   └── data_dictionary.md           # Dataset documentation and column definitions
│
├── sql/
│   ├── 01_data_profiling.sql
│   └── 02_revenue_profitability_churn.sql
│
├── notebooks/
│   ├── 01_data_profiling.ipynb
│   ├── 02_data_cleaning.ipynb
│   ├── 03_feature_engineering.ipynb
│   ├── 04_eda.ipynb                 # Generate all EDA charts → images/eda_charts
│   ├── 05_revenue_forecasting.ipynb
│   ├── 06_profitability_analysis.ipynb
│   ├── 07_churn_prediction.ipynb
│   └── 08_insights_recommendations.ipynb
│
├── src/
│   ├── __init__.py
│   ├── python_pipeline/             # Python-native ETL & ML logic
│   │   ├── __init__.py
│   │   ├── data_cleaning.py
│   │   ├── feature_engineering.py
│   │   ├── forecasting.py           # Revenue/Profit time series
│   │   ├── modeling.py              # Churn classification
│   │   ├── visualizations.py        # EDA & Model plots
│   │   └── run_pipeline.py          # Python E2E Runner
│   └── sql_pipeline/                # SQL-first ETL (SQLite)
│       ├── __init__.py
│       ├── load_raw.py
│       ├── run_etl.py
│       └── run_pipeline.py          # SQL E2E Runner
├── model/                            # best_model.pkl, scaler.pkl
├── tests/
│   ├── test_cleaning.py
│   ├── test_feature_engineering.py
│   └── test_modeling.py
│
└── images/
    ├── eda_charts/                   # EDA and model evaluation charts
    │   ├── churn_overview.png
    │   ├── revenue_profit_trend.png
    │   ├── subcategory_pl.png
    │   ├── discount_vs_profit.png
    │   ├── discount_band_analysis.png
    │   ├── region_profitability.png
    │   ├── segment_profitability.png
    │   ├── correlation_matrix.png
    │   ├── profit_impact_summary.png
    │   ├── roc_comparison.png
    │   ├── confusion_matrices.png
    │   └── feature_importance.png
    └── dashboard/                    # Power BI dashboard screenshots
```

---

## Tools & Technologies

| Category       | Tools                                                                 |
| -------------- | --------------------------------------------------------------------- |
| **Languages**  | Python, SQL                                                           |
| **Data**       | Pandas, NumPy                                                         |
| **ML**         | Scikit-learn (Logistic Regression, Random Forest, Gradient Boosting)  |
| **Visualization** | Matplotlib, Seaborn                                                |
| **Dashboard**  | Tableau / Power BI (5-page dashboard per BRD)                         |
| **Environment** | Jupyter Lab                                                          |

---

## How to Run This Project

### 1. Clone or open the project

```bash
cd financial-operations-analytics
```

### 2. Set up a virtual environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Add the data

Place **superstore.csv** in `data/raw/`. Columns expected: Order ID, Order Date, Ship Date, Ship Mode, Customer ID, Segment, Region, State, Category, Sub-Category, Sales, Quantity, Discount, Profit (and others per data dictionary). The CSV may use **latin-1** encoding (non-breaking spaces in Product Name).

python3 -m src.python_pipeline.run_pipeline
```

Outputs:  
`data/preprocessed/superstore_preprocessed.csv`  
`data/featured/superstore_orders.csv`, `superstore_customers.csv`, `model_ready.csv`

### 5. Train the churn model (optional)

```bash
python3 -m src.python_pipeline.modeling
```

Saves **model/best_model.pkl** and **model/scaler.pkl**, and writes ROC, confusion matrices, and feature importance to **images/eda_charts/**.

### 6. Run notebooks (in order)

Run notebooks in order:

1. `01_data_profiling.ipynb` — Explore raw data  
2. `02_data_cleaning.ipynb` — Run cleaning  
3. `03_feature_engineering.ipynb` — Build order/customer features and churn label  
4. `04_eda.ipynb` — Generate all EDA charts to `images/eda_charts/`  
5. `05_revenue_forecasting.ipynb` — Revenue/profit trends and forecast  
6. `06_profitability_analysis.ipynb` — P&L, discount, region/segment  
7. `07_churn_prediction.ipynb` — Train and evaluate models; saves ROC/confusion/feature importance to `images/eda_charts/`  
8. `08_insights_recommendations.ipynb` — Summary and recommendations  

### 7. Run tests

```bash
python -m pytest tests/ -v
```

### 8. Images and reports

- **Charts:** EDA and model charts are under **images/eda_charts/** after running notebooks **04_eda** and **07_churn_prediction** (or `modeling.py`).
- **Dashboard:** View the 5-page Interactive Power BI dashboard screenshots under **images/dashboard/**.

---

## Data Source

**Superstore Sales Dataset** — Kaggle / Tableau sample data

- 9,993 transaction line items (after cleaning) | 21 columns | Jan 2014 – Dec 2017  
- 793 unique customers | 5,009 unique orders | 4 regions, 50 states  
- **Profit** per transaction is included — essential for financial operations analysis.  
- [Kaggle dataset](https://www.kaggle.com/datasets/vivek468/superstore-dataset-final) | [Data Dictionary](docs/data_dictionary.md)

---

## Estimated Profit Impact

```
Discount cap at 20%:                    +$50,000 – $80,000/year
Loss sub-category elimination:          +$5,000 – $10,000/year
Churn recovery (reactivation):          +$15,000 – $25,000/year (illustrative)
────────────────────────────────────────────────────────────────
Conservative total improvement:         ~$70,000 – $115,000/year
```
