# Power BI Dashboard Guide — Financial Operations Analytics

**Platform:** Power BI Service (app.powerbi.com) — browser-based, works on Mac  
**Approach:** Star-schema data model with relationships + DAX measures (industry standard)  
**Dashboard:** 5 pages per BRD

---

## Architecture Overview

**Semantic model (backend):** Data model, relationships, DAX measures, calculated columns  
**Report editor (frontend):** Visuals, charts, slicers, formatting, layout

All formulas and relationships are built in the semantic model. All visuals are built in the report editor. Switch between them using **Open semantic model** (from report) or by finding the report in My Workspace.

---

## Data Model (Star Schema)

```
┌─────────────────────┐
│   Transactions       │  (Fact table — 9,993 rows)
│   superstore_        │
│   preprocessed.csv   │
│                      │
│   Order ID           │
│   Order Date ────────┼──── DateTable (created via DAX)
│   Customer ID ───────┼──── Customers (dimension)
│   Sales, Profit,     │
│   Discount, Quantity  │
│   Category, Sub-Cat  │
│   Region, State      │
│   Ship Mode          │
└─────────────────────┘

┌─────────────────────┐
│   Customers          │  (Dimension — 793 rows)
│   superstore_        │
│   customers.csv      │
└─────────────────────┘

┌─────────────────────┐
│   DateTable          │  (Created via DAX)
│   CALENDAR(2014-2017)│
└─────────────────────┘

┌─────────────────────┐
│   ActionItems        │  (Static — 5 rows, Page 5)
└─────────────────────┘

┌─────────────────────┐
│   ProfitWaterfall    │  (Static — 4 rows, Page 5)
└─────────────────────┘
```

---

## Step 0: Prepare CSV Files

No Python enrichment needed — DAX handles all calculations.

**File 1:** `data/preprocessed/superstore_preprocessed.csv` (9,993 rows, 19 columns)  
**File 2:** `data/featured/superstore_customers.csv` (793 rows, 17 columns)

---

## Step 1: Upload Data

### Upload Transactions table
1. Go to **app.powerbi.com** → **My Workspace**
2. **+ New** → **Semantic model** → **Upload a file** → select `superstore_preprocessed.csv`
3. In Power Query editor, rename the query to **Transactions** (Properties panel → Name)
4. Verify `Order Date` and `Ship Date` show calendar icons (date type)
5. Click **Create a report**

### Add Customers table
1. Click **Open semantic model** from the report
2. Click **Get data** or **Transform data** → add `superstore_customers.csv`
3. In Power Query: click **Use first row as headers** (critical — headers don't auto-promote)
4. Change `first_order_date` and `last_order_date` from Text to **Date** type
5. Click **Save**

**Tip:** If adding a second CSV is difficult in the browser, create an Excel workbook with two sheets:
```python
import pandas as pd
transactions = pd.read_csv('data/preprocessed/superstore_preprocessed.csv')
customers = pd.read_csv('data/featured/superstore_customers.csv')
with pd.ExcelWriter('data/powerbi/superstore_powerbi.xlsx', engine='openpyxl') as writer:
    transactions.to_excel(writer, sheet_name='Transactions', index=False)
    customers.to_excel(writer, sheet_name='Customers', index=False)
```

---

## Step 2: Set Up Relationships & Date Table

### Create relationships (Model view)
1. In semantic model, click **Model view** at the bottom
2. Drag `Customer ID` from **Transactions** → drop on `Customer ID` in **Customers**
   - Type: Many-to-one, Cross-filter: Single
3. A line connects the two tables

### Create Date Table
Click **New table** in the ribbon:

```dax
DateTable = 
ADDCOLUMNS(
    CALENDAR(DATE(2014, 1, 1), DATE(2017, 12, 31)),
    "Year", YEAR([Date]),
    "Quarter", "Q" & QUARTER([Date]),
    "Month", FORMAT([Date], "YYYY-MM"),
    "MonthName", FORMAT([Date], "MMM YYYY"),
    "MonthNum", MONTH([Date]),
    "YearQuarter", FORMAT([Date], "YYYY") & "-Q" & QUARTER([Date])
)
```

**Important:** Use `CALENDAR()` with explicit dates (2014-2017), NOT `CALENDARAUTO()` — the auto version creates dates beyond your data range (2018+) which show up as empty values in slicers.

4. Create relationship: drag `Date` from **DateTable** → `Order Date` in **Transactions**

### Fix Year column for slicers
The `Year` column will default to summing (showing 8062 instead of 2014, 2015, etc.):
1. Click `Year` in DateTable → Properties → change **Data type** from `Whole number` to `Text`

---

## Step 3: Create DAX Measures & Calculated Columns

### Revenue & Profit Measures (on Transactions table → New measure)

```dax
Total Sales = SUM(Transactions[Sales])
```

```dax
Total Profit = SUM(Transactions[Profit])
```

```dax
Profit Margin % = DIVIDE([Total Profit], [Total Sales], 0) * 100
```

```dax
Total Orders = DISTINCTCOUNT(Transactions[Order ID])
```

```dax
Unique Customers = DISTINCTCOUNT(Transactions[Customer ID])
```

```dax
Avg Order Value = DIVIDE([Total Sales], [Total Orders], 0)
```

**Important:** Create measures in dependency order — `Avg Order Value` references `Total Sales` and `Total Orders`, so those must exist first.

### Profitability Measures

```dax
Avg Profit Per Transaction = AVERAGE(Transactions[Profit])
```

```dax
Loss Transaction % = 
DIVIDE(
    COUNTROWS(FILTER(Transactions, Transactions[Profit] < 0)),
    COUNTROWS(Transactions),
    0
) * 100
```

```dax
Avg Discount % = AVERAGE(Transactions[Discount]) * 100
```

### Churn Measures

```dax
Churn Rate % = 
DIVIDE(
    COUNTROWS(FILTER(Customers, Customers[is_churned] = 1)),
    COUNTROWS(Customers),
    0
) * 100
```

```dax
Churned Customers = COUNTROWS(FILTER(Customers, Customers[is_churned] = 1))
```

```dax
Active Customers = COUNTROWS(FILTER(Customers, Customers[is_churned] = 0))
```

```dax
Revenue at Risk = 
CALCULATE(
    [Total Sales],
    FILTER(Customers, Customers[is_churned] = 1)
)
```

```dax
Churn Rate by Context % = 
DIVIDE(
    COUNTROWS(FILTER(Customers, Customers[is_churned] = 1)),
    COUNTROWS(Customers),
    0
) * 100
```

### Time Intelligence Measures

**Note:** Use `SalesCurrent`/`SalesPrior` as variable names — `PreviousYear` is a reserved word in DAX.

```dax
Sales YoY Growth % = 
VAR SalesCurrent = [Total Sales]
VAR SalesPrior = CALCULATE([Total Sales], SAMEPERIODLASTYEAR(DateTable[Date]))
RETURN DIVIDE(SalesCurrent - SalesPrior, SalesPrior, 0) * 100
```

```dax
Profit YoY Growth % = 
VAR ProfitCurrent = [Total Profit]
VAR ProfitPrior = CALCULATE([Total Profit], SAMEPERIODLASTYEAR(DateTable[Date]))
RETURN DIVIDE(ProfitCurrent - ProfitPrior, ProfitPrior, 0) * 100
```

### Calculated Columns (Transactions table → New column, NOT New measure)

**Discount Band:**
```dax
Discount Band = 
SWITCH(
    TRUE(),
    Transactions[Discount] = 0, "1 - No Discount",
    Transactions[Discount] <= 0.10, "2 - Light (1-10%)",
    Transactions[Discount] <= 0.20, "3 - Moderate (11-20%)",
    Transactions[Discount] <= 0.30, "4 - Heavy (21-30%)",
    "5 - Extreme (31%+)"
)
```

**Transaction Profit Margin:**
```dax
Transaction Profit Margin = DIVIDE(Transactions[Profit], Transactions[Sales], 0) * 100
```

**Key distinction:** Measures use aggregation functions like `SUM()`, `AVERAGE()`, `COUNTROWS()`. Calculated columns reference row-level values like `Transactions[Profit]` directly. If you use **New measure** for row-level references, you'll get a "cannot be determined" error.

### Calculated Columns (Customers table → New column)

**Order Count Bin:**
```dax
Order Count Bin = 
SWITCH(
    TRUE(),
    Customers[order_count] <= 2, "1 - 1-2",
    Customers[order_count] <= 4, "2 - 3-4",
    Customers[order_count] <= 6, "3 - 5-6",
    Customers[order_count] <= 8, "4 - 7-8",
    Customers[order_count] <= 10, "5 - 9-10",
    "6 - 11+"
)
```

**Profit Bin:**
```dax
Profit Bin = 
VAR ProfitVal = Customers[total_profit]
RETURN
SWITCH(
    TRUE(),
    ProfitVal < -500, "1 - Below -500",
    ProfitVal < 0, "2 - -500 to 0",
    ProfitVal < 500, "3 - 0 to 500",
    ProfitVal < 1000, "4 - 500 to 1K",
    ProfitVal < 2000, "5 - 1K to 2K",
    ProfitVal < 5000, "6 - 2K to 5K",
    "7 - 5K+"
)
```

**Sorting tip:** Number prefixes (1-, 2-, 3-) force correct alphabetical sort order in visuals. Without them, "Heavy" sorts before "Light" and "5K+" sorts before "500 to 1K".

### Static Tables for Page 5 (New table)

**Action Items:**
```dax
ActionItems = 
DATATABLE(
    "Priority", INTEGER,
    "Action", STRING,
    "Owner", STRING,
    "Expected Impact", STRING,
    {
        {1, "Discount cap at 20%", "CFO / VP Sales", "+$50K-$80K/year"},
        {2, "Reprice loss sub-categories", "Category Management", "+$5K-$10K/year"},
        {3, "Churn reactivation campaign", "VP Marketing", "+$15K-$25K/year"},
        {4, "Regional margin review", "VP Sales", "+$10K-$20K/year"},
        {5, "High-margin promotion", "Marketing", "+$15K-$30K/year"}
    }
)
```

After creating, change `Priority` **Data type** from `Whole number` to `Text` in Properties — otherwise Power BI sums it (showing 15 instead of 1, 2, 3, 4, 5).

**Profit Waterfall:**
```dax
ProfitWaterfall = 
DATATABLE(
    "Step", STRING,
    "Amount", INTEGER,
    "Sort", INTEGER,
    {
        {"1 - Current Profit ($286K)", 286000, 1},
        {"2 - Discount Cap (+$65K)", 65000, 2},
        {"3 - Fix Loss Sub-Cats (+$7.5K)", 7500, 3},
        {"4 - Churn Recovery (+$20K)", 20000, 4}
    }
)
```

---

## Step 4: Build Dashboard Pages

Create 5 pages using the **+** button at the bottom. Double-click each tab to rename.

### Page 1: Financial KPI Overview

**KPI Cards (top row — 5 cards):**

| Card | Measure | Format |
|------|---------|--------|
| Total Sales | `Total Sales` | $ prefix |
| Total Profit | `Total Profit` | $ prefix |
| Profit Margin | `Profit Margin %` | % suffix |
| Total Orders | `Total Orders` | comma |
| Unique Customers | `Unique Customers` | comma |

**Monthly Revenue & Profit Trend:**
1. **Line and Clustered Column Chart**
2. X-axis: `DateTable[Month]` (NOT MonthName — Month is "YYYY-MM" which sorts chronologically)
3. Column values: `Total Sales`
4. Line values: `Total Profit`
5. Sort ascending by Month

**Sales YoY Growth:**
1. **Clustered Column Chart**
2. X-axis: `DateTable[YearQuarter]`
3. Y-axis: `Total Sales`
4. Sort ascending by YearQuarter

**Slicers (4 button slicers):**
- `DateTable[Year]` — shows 2014, 2015, 2016, 2017
- `Transactions[Region]` — Central, East, South, West
- `Transactions[Category]` — Furniture, Office Supplies, Technology
- `Transactions[Segment]` — Consumer, Corporate, Home Office

Use **Button slicer** style. To deselect: Cmd+click or hover and click the eraser icon.

---

### Page 2: Profitability Deep Dive

**Sub-Category P&L:**
1. **Clustered Bar Chart** (horizontal)
2. Y-axis: `Sub-Category`
3. X-axis: `Total Sales` and `Total Profit`
4. Sort by Total Profit ascending (loss-makers at top)

**Profit Margin Ranking:**
1. **Bar Chart**
2. Y-axis: `Sub-Category`
3. X-axis: `Profit Margin %`
4. Sort descending
5. Conditional formatting: Format → Data colors → fx → Rules:
   - If value >= -100 and < 0 → **Red**
   - If value >= 0 and < 100 → **Green/Blue**
   - Use **Number** (not Percentage) for the dropdown

**Discount vs. Profit Scatter:**
1. **Scatter Chart**
2. X-axis: `Discount` → change aggregation to **Don't summarize**
3. Y-axis: `Profit` → change aggregation to **Don't summarize**
4. Legend: `Category`
5. Analytics pane → Constant Line → Y = 0, color red, dashed

**Discount Band Analysis:**
1. **Clustered Column Chart**
2. X-axis: `Discount Band`
3. Y-axis: `Avg Profit Per Transaction`
4. Sort by Discount Band ascending
5. Conditional formatting (Rules, Number):
   - If value >= -10000 and < 0 → **Red**
   - If value >= 0 and < 10000 → **Blue**

**State Profitability Map:**
1. **Filled Map**
2. Location: `State`
3. Color saturation: `Profit Margin %`
4. Format → Fill colors → fx → **Gradient** (not Rules):
   - Minimum: -20, Red
   - Center: 0, Yellow
   - Maximum: 30, Green

---

### Page 3: Regional & Segment Performance

**Region Comparison:**
1. **Line and Clustered Column Chart**
2. X-axis: `Region`
3. Column values: `Total Sales`, `Total Profit`
4. Line values: `Profit Margin %`

**Top/Bottom States Table:**
1. **Table** visual
2. Columns: `State`, `Total Sales`, `Total Profit`, `Profit Margin %`
3. Sort by Total Profit descending
4. Conditional formatting on Profit Margin %: Background color → Rules → red < 0, blue/green >= 0

**Segment Comparison:**
1. **Clustered Column Chart**
2. X-axis: `Segment`
3. Y-axis: `Total Sales`, `Total Profit`

**Ship Mode Analysis:**
1. **Bar Chart**
2. Y-axis: `Ship Mode`
3. X-axis: `Total Sales`

**Category × Region Heatmap:**
1. **Matrix** visual
2. Rows: `Category`
3. Columns: `Region`
4. Values: `Profit Margin %`
5. Conditional formatting → Background color → diverging (red to green)

---

### Page 4: Customer Retention & Churn

**KPI Cards:**

| Card | Measure |
|------|---------|
| Churn Rate | `Churn Rate %` |
| Churned Customers | `Churned Customers` |
| Active Customers | `Active Customers` |
| Revenue at Risk | `Revenue at Risk` |

**Churn by Segment:**
1. **Clustered Column Chart**
2. X-axis: `Customers[Segment]`
3. Y-axis: `Churn Rate by Context %`

**Churn by Order Frequency:**
1. **Clustered Column Chart**
2. X-axis: `Order Count Bin` (calculated column)
3. Y-axis: `Churn Rate by Context %`

**Customer Value Distribution:**
1. **Clustered Column Chart**
2. X-axis: `Profit Bin` (calculated column)
3. Y-axis: `Customer ID` (Count Distinct)
4. Legend: `is_churned`

**Feature Importance (static image):**
1. **Insert** → **Image** → upload `feature_importance.png`
2. Add text box: "Top predictors: tenure_days, order_count, total_spent"

**Model Performance:**
1. **Text box**: "Best Model: Logistic Regression | AUC-ROC: 0.848"
2. Optionally insert `roc_comparison.png`

---

### Page 5: Executive Recommendations

**Profit Improvement Waterfall:**
1. **Waterfall Chart**
2. Category: `ProfitWaterfall[Step]`
3. Y-axis: `ProfitWaterfall[Amount]`
4. Sort by `Step` ascending (number prefixes ensure correct order)

**Action Items Table:**
1. **Table** visual
2. Drag: `Priority`, `Action`, `Owner`, `Expected Impact` from ActionItems
3. Sort by Priority ascending

**Recommendation Text Boxes (Insert → Text box):**
- "Cap discounts at 20%. VP approval above 20%. Est: +$50K-$80K/year."
- "Exit or reprice Tables, Bookcases, Supplies."
- "Deploy churn model for at-risk customers."

**Profit Impact Summary:**
- Insert `profit_impact_summary.png` image

---

## Step 5: Formatting & Polish

### Theme
**View** → **Themes** → choose "Executive" or "Innovation"

### Color Conventions
- **Blue:** Sales / revenue
- **Green:** Profit / positive
- **Red:** Losses / negative
- **Orange:** Secondary metrics

### Titles
Click visual → Format (paint roller) → **Title** → edit text  
Example: "Sub-Category P&L — Sales vs. Profit (2014–2017)"

### Number Formatting
- Currency: $ prefix, no decimals
- Percentages: one decimal + %
- Counts: comma separator

---

## Step 6: Export for Portfolio

### Screenshots
1. Navigate to each page
2. Mac: **Cmd + Shift + 4** → select area
3. Save as:
   - `images/dashboard/01_financial_kpi_overview.png`
   - `images/dashboard/02_profitability_deep_dive.png`
   - `images/dashboard/03_regional_segment_performance.png`
   - `images/dashboard/04_customer_retention_churn.png`
   - `images/dashboard/05_executive_recommendations.png`

