# 👥 Retail Intelligence Platform

An end-to-end retail analytics platform built on the Superstore dataset — 7 interactive Streamlit dashboards covering sales, customers, and products, plus three machine-learning modules for forecasting, customer segmentation, and product recommendations.
![Python](https://img.shields.io/badge/Python-3.12-blue)

![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red)

![SQLite](https://img.shields.io/badge/SQLite-Database-blue)

![PowerBI](https://img.shields.io/badge/PowerBI-Visualization-yellow)

## Dashboard Preview

### Executive Dashboard

![Executive Dashboard](images/1_Executive_Dashboard.png)

### Sales Analysis

![Sales Analysis](images/2_Sales_Dashboard.png)

### Customer Analysis

![Customer Analysis](images/3_Customer_Dashboard.png)

### Product Analysis

![Product Analysis](images/4_Product_Dashboard.png)
---

## 📊 Dataset at a Glance

| Metric | Value |
|---|---|
| Order records | 9,994 |
| Date range | Jan 2014 – Dec 2017 |
| Total Sales | $2.30M |
| Total Profit | $286.4K |
| Unique Customers | 793 |
| Unique Products | 1,862 |
| Categories | Furniture, Office Supplies, Technology |
| Regions | South, West, Central, East |

---

## 🏗️ Architecture

```
Raw CSV (SampleSuperstore.csv)
        │
        ▼
Data Cleaning & Feature Engineering  (notebooks/01, 03)
        │
        ▼
processed_superstore.csv
        │
        ▼
SQLite Database (database/retail.db)   ← src/database/import_data.py
        │
        ▼
Streamlit Multi-Page Dashboard  (src/dashboard/)
        │
        ├── Executive / Sales / Customer / Product Analysis  (descriptive)
        ├── Sales Forecasting          → moving-average time-series model
        ├── Customer Segmentation      → K-Means clustering
        └── Product Recommendation     → rule-based scoring engine
```

All 7 dashboard pages read from the same SQLite database via a shared connection helper (`src/database/db_connection.py`), so the whole platform stays in sync from a single source of truth.

---

## ✨ Features

| # | Dashboard | What it does |
|---|---|---|
| 1 | **Executive Dashboard** | High-level KPIs and trends across the whole business |
| 2 | **Sales Analysis** | Sales performance by region, category, and time |
| 3 | **Customer Analysis** | Customer-level behavior and value breakdown |
| 4 | **Product Analysis** | Product and sub-category performance |
| 5 | **Sales Forecasting** | 12-month sales forecast using a moving-average model |
| 6 | **Customer Segmentation** | K-Means clustering into Low Value / Regular / High Value customer tiers |
| 7 | **Product Recommendation** | Rule-based scoring engine that ranks and recommends products |

### Machine Learning / Analytics Modules

**Sales Forecasting** — aggregates historical sales into a monthly time series and projects the next 12 months using a trailing moving average, with a growth-rate KPI comparing forecast vs. the prior 12 months.

**Customer Segmentation** — aggregates each customer's total Sales, Profit, and Order count, standardizes the features (`StandardScaler`), and clusters them with `KMeans(n_clusters=3)`. Clusters are ranked by average sales and mapped to human-readable tiers (🔴 Low Value / 🟠 Regular / 🟢 High Value) rather than raw cluster numbers, so the labels stay meaningful across re-runs.

**Product Recommendation** — a transparent, rule-based alternative to a black-box recommender. Each product's Sales, Profit, Orders, and Discount are min-max normalized and combined into a weighted score (`0.35×Sales + 0.35×Profit + 0.20×Orders − 0.10×Discount`), rescaled to 0–100. The top 30% of products by score are flagged as **Recommended**; a **Recommendation Accuracy** KPI cross-checks what fraction of recommended products are also independently flagged as High Demand (top quartile by Orders), as a sanity check that the score tracks real customer behavior.

---

## 🛠️ Tech Stack

- **Language:** Python 3.12
- **Dashboard:** Streamlit + Plotly
- **Machine Learning:** scikit-learn (K-Means, StandardScaler)
- **Database:** SQLite
- **Data Prep:** pandas, numpy, Jupyter notebooks
- **BI Tool:** Power BI (`powerbi/`)

---

## 🚀 Getting Started

### 1. Clone and install dependencies

```bash
git clone <your-repo-url>
cd Retail-Intelligence-Platform
pip install -r requirements.txt
```

### 2. Build the database

This loads `data/processed/processed_superstore.csv` into `database/retail.db`:

```bash
python src/database/import_data.py
```

### 3. Run the dashboard

```bash
streamlit run src/dashboard/app.py
```

The app will open at `http://localhost:8501` with all 7 pages available in the sidebar.

---

## 📁 Project Structure

```
Retail-Intelligence-Platform/
├── data/
│   ├── raw/                   # Original Superstore CSV
│   ├── cleaned/                # After data-cleaning notebook
│   └── processed/              # Final, feature-engineered CSV used by the app
├── database/
│   └── retail.db                # SQLite database (built from processed CSV)
├── notebooks/
│   ├── 01_Data_Cleaning.ipynb
│   ├── 02_EDA.ipynb
│   ├── 03_Feature_Engineering.ipynb
│   ├── 04_Sales_Forecasting.ipynb
│   └── 05_Customer_Segmentation.ipynb
├── sql/                        # Schema, queries, views, triggers (see sql/README.md)
├── src/
│   ├── dashboard/
│   │   ├── app.py               # Streamlit entry point
│   │   └── pages/                # 7 dashboard pages
│   └── database/
│       ├── db_connection.py      # Shared SQLite connection helper
│       └── import_data.py        # Loads processed CSV into SQLite
├── powerbi/                    # Power BI companion dashboard
├── reports/                    # Final_Report.pdf, Presentation.pptx
├── images/                     # Dashboard screenshots
├── docs/                       # Data dictionary, schema notes
└── requirements.txt
```

---

## 📄 Reports

- [`reports/Final_Report.pdf`](reports/Final_Report.pdf) — full written analysis: methodology, EDA findings, ML approach, and business recommendations
- [`reports/Presentation.pptx`](reports/Presentation.pptx) — condensed slide deck for a stakeholder audience

---

## 🔭 Future Improvements

- Replace the moving-average forecast with a seasonal model (e.g. Prophet or SARIMA) to capture yearly seasonality
- Extend the recommendation engine with collaborative filtering as a complement to the current rule-based score
- Add automated data-quality checks to the ingestion pipeline