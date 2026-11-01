import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from database.db_connection import get_connection

st.set_page_config(page_title="Product Recommendation", page_icon="📦", layout="wide")

# Consistent color theme across the dashboard
COLOR_SALES = "#1f77b4"     # Blue
COLOR_PROFIT = "#2ca02c"    # Green
COLOR_CUSTOMER = "#ff7f0e"  # Orange
COLOR_PRODUCT = "#9467bd"   # Purple

COLOR_RECOMMENDED = "#2ca02c"      # Green
COLOR_NOT_RECOMMENDED = "#7f7f7f"  # Grey
COLOR_HIGH_DEMAND = "#d62728"      # Red
COLOR_LOW_DEMAND = "#1f77b4"       # Blue

# Rule-based recommendation weights
W_SALES = 0.35
W_PROFIT = 0.35
W_ORDERS = 0.20
W_DISCOUNT = 0.10  # penalty weight

SCORE_THRESHOLD_QUANTILE = 0.70   # top 30% of products by score -> Recommended
HIGH_DEMAND_QUANTILE = 0.75
LOW_DEMAND_QUANTILE = 0.25

st.markdown("""
<style>
div[data-testid="stPlotlyChart"]{
background:white;
padding:15px;
border-radius:12px;
box-shadow:0 2px 10px rgba(0,0,0,0.12);
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------
# Title
# ------------------------------------------------------------------
st.title("📦 Product Recommendation")
st.caption("A rule-based recommendation engine that scores products using Sales, Profit, Orders, and Discount.")

@st.cache_data
def load_data():
    """Read the Superstore table once and reuse it across reruns."""
    conn = get_connection()
    try:
        return pd.read_sql_query("SELECT * FROM Superstore", conn)
    finally:
        conn.close()


df = load_data()
st.success("Database Connected Successfully!")

df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")

# ------------------------------------------------------------------
# Filters
# ------------------------------------------------------------------
col1, col2, col3 = st.columns(3)

categories = ["All"] + sorted(df["Category"].dropna().unique())
regions = ["All"] + sorted(df["Region"].dropna().unique())
years = ["All"] + sorted(df["Order Year"].dropna().astype(int).unique())

with col1:
    category = st.selectbox("Category", categories)
with col2:
    region = st.selectbox("Region", regions)
with col3:
    year = st.selectbox("Order Year", years)

filtered_df = df.copy()
if category != "All":
    filtered_df = filtered_df[filtered_df["Category"] == category]
if region != "All":
    filtered_df = filtered_df[filtered_df["Region"] == region]
if year != "All":
    filtered_df = filtered_df[filtered_df["Order Year"] == year]

st.markdown("---")

if filtered_df.empty:
    st.warning("No data matches the selected filters. Please adjust your filter selection.")
    st.stop()

# ------------------------------------------------------------------
# Aggregate to product level
# ------------------------------------------------------------------
product_df = (
    filtered_df
    .groupby(
        ["Product ID", "Product Name", "Category"],
        as_index=False
    )
    .agg(
        Sales=("Sales", "sum"),
        Profit=("Profit", "sum"),
        Discount=("Discount", "mean"),
        Orders=("Order ID", "nunique")
    )
)

if len(product_df) < 4:
    st.warning(
        f"Only {len(product_df)} product(s) match the current filters — "
        f"not enough to build a meaningful recommendation ranking. Please widen your filters."
    )
    st.stop()

# ------------------------------------------------------------------
# Rule-based Recommendation Score
# ------------------------------------------------------------------
def normalize(series):
    """Min-max scale a series to 0-1. Flat series -> constant 0.5."""
    lo, hi = series.min(), series.max()
    if hi == lo:
        return pd.Series(0.5, index=series.index)
    return (series - lo) / (hi - lo)


norm_sales = normalize(product_df["Sales"])
norm_profit = normalize(product_df["Profit"])
norm_orders = normalize(product_df["Orders"])
norm_discount = normalize(product_df["Discount"])

raw_score = (
    W_SALES * norm_sales
    + W_PROFIT * norm_profit
    + W_ORDERS * norm_orders
    - W_DISCOUNT * norm_discount
)

product_df["Recommendation Score"] = (normalize(raw_score) * 100).round(2)

score_cutoff = product_df["Recommendation Score"].quantile(SCORE_THRESHOLD_QUANTILE)
product_df["Recommended"] = product_df["Recommendation Score"] >= score_cutoff

order_q75 = product_df["Orders"].quantile(HIGH_DEMAND_QUANTILE)
order_q25 = product_df["Orders"].quantile(LOW_DEMAND_QUANTILE)

product_df["High Demand"] = product_df["Orders"] >= order_q75
product_df["Low Demand"] = product_df["Orders"] <= order_q25

product_df["Status"] = np.where(
    product_df["Recommended"], "✅ Recommended", "❌ Not Recommended"
)

# ------------------------------------------------------------------
# KPIs
# ------------------------------------------------------------------
def format_currency(value):
    """Format large currency values compactly, e.g. $2.30M, $286.4K."""
    abs_value = abs(value)
    if abs_value >= 1_000_000:
        return f"${value / 1_000_000:,.2f}M"
    if abs_value >= 1_000:
        return f"${value / 1_000:,.1f}K"
    return f"${value:,.2f}"


total_products = product_df["Product ID"].nunique()
recommended_products = int(product_df["Recommended"].sum())
high_demand_products = int(product_df["High Demand"].sum())
low_demand_products = int(product_df["Low Demand"].sum())
avg_sales = product_df["Sales"].mean()
avg_profit = product_df["Profit"].mean()

recommended_df = product_df[product_df["Recommended"]]
if not recommended_df.empty:
    best_category = (
        recommended_df.groupby("Category")["Recommendation Score"].mean().idxmax()
    )
else:
    best_category = product_df.groupby("Category")["Recommendation Score"].mean().idxmax()

if recommended_products > 0:
    demand_alignment = (
        product_df.loc[product_df["Recommended"], "High Demand"].sum()
        / recommended_products
        * 100
    )
else:
    demand_alignment = 0.0

st.subheader("📦 Recommendation Overview")

a, b, c, d = st.columns(4)
a.metric("📦 Total Products", f"{total_products:,}")
b.metric("⭐ Recommended Products", f"{recommended_products:,}")
c.metric("🔥 High Demand Products", f"{high_demand_products:,}")
d.metric("📉 Low Demand Products", f"{low_demand_products:,}")

e, f, g, h = st.columns(4)
e.metric("💰 Avg Sales / Product", format_currency(avg_sales))
f.metric("📈 Avg Profit / Product", format_currency(avg_profit))
g.metric("🏆 Best Recommended Category", best_category)
h.metric("🎯 Demand Alignment", f"{demand_alignment:.1f}%")

st.caption(
    "Products in the top 30% by Recommendation Score are marked Recommended. "
    "Demand Alignment is the share of Recommended products that are also High Demand "
    "(top quartile by orders). Orders is part of the score, so this is a consistency "
    "check, not a measure of predictive accuracy."
)

st.markdown("---")

# ------------------------------------------------------------------
# Controls for chart depth
# ------------------------------------------------------------------
top_n = st.slider("Number of products to show in ranked charts", 5, 25, 10)

# ------------------------------------------------------------------
# Top Recommended Products / Product Recommendation Score distribution
# ------------------------------------------------------------------
left, right = st.columns(2)

top_recommended = product_df.sort_values("Recommendation Score", ascending=False).head(top_n)

fig_top_recommended = px.bar(
    top_recommended.sort_values("Recommendation Score"),
    x="Recommendation Score",
    y="Product Name",
    orientation="h",
    color_discrete_sequence=[COLOR_RECOMMENDED],
    text_auto=".1f",
    title="⭐ Top Recommended Products"
)
fig_top_recommended.update_layout(yaxis_title="", xaxis_title="Recommendation Score")

fig_score_distribution = px.histogram(
    product_df,
    x="Recommendation Score",
    nbins=20,
    color_discrete_sequence=[COLOR_PRODUCT],
    title="📈 Product Recommendation Score"
)
fig_score_distribution.add_vline(
    x=score_cutoff, line_dash="dash", line_color=COLOR_HIGH_DEMAND,
    annotation_text="Threshold", annotation_position="top"
)
fig_score_distribution.update_layout(yaxis_title="Products", xaxis_title="Recommendation Score")

with left:
    st.plotly_chart(
        fig_top_recommended,
        use_container_width=True,
        config={"displayModeBar": False},
        key="top_recommended_products"
    )

with right:
    st.plotly_chart(
        fig_score_distribution,
        use_container_width=True,
        config={"displayModeBar": False},
        key="recommendation_score_distribution"
    )

st.markdown("---")

# ------------------------------------------------------------------
# Sales vs Profit Scatter / Recommended Category Distribution
# ------------------------------------------------------------------
left2, right2 = st.columns(2)

fig_scatter = px.scatter(
    product_df,
    x="Sales",
    y="Profit",
    color="Status",
    color_discrete_map={
        "✅ Recommended": COLOR_RECOMMENDED,
        "❌ Not Recommended": COLOR_NOT_RECOMMENDED,
    },
    size="Orders",
    hover_data=["Product Name", "Category", "Recommendation Score"],
    title="💰 Sales vs Profit Scatter"
)

category_dist = (
    product_df[product_df["Recommended"]]
    .groupby("Category", as_index=False)
    .size()
    .rename(columns={"size": "Recommended Products"})
)

fig_category_dist = px.bar(
    category_dist,
    x="Category",
    y="Recommended Products",
    color_discrete_sequence=[COLOR_CUSTOMER],
    text_auto=True,
    title="📊 Recommended Category Distribution"
)
fig_category_dist.update_layout(xaxis_title="", showlegend=False)

with left2:
    st.plotly_chart(
        fig_scatter,
        use_container_width=True,
        config={"displayModeBar": False},
        key="sales_vs_profit_scatter"
    )

with right2:
    st.plotly_chart(
        fig_category_dist,
        use_container_width=True,
        config={"displayModeBar": False},
        key="recommended_category_distribution"
    )

st.markdown("---")

# ------------------------------------------------------------------
# High Demand Products / Low Demand Products
# ------------------------------------------------------------------
left3, right3 = st.columns(2)

high_demand_top = (
    product_df[product_df["High Demand"]]
    .sort_values("Orders", ascending=False)
    .head(top_n)
    .sort_values("Orders")
)

fig_high_demand = px.bar(
    high_demand_top,
    x="Orders",
    y="Product Name",
    orientation="h",
    color_discrete_sequence=[COLOR_HIGH_DEMAND],
    text_auto=True,
    title="🔥 High Demand Products"
)
fig_high_demand.update_layout(yaxis_title="")

low_demand_bottom = (
    product_df[product_df["Low Demand"]]
    .sort_values("Orders", ascending=True)
    .head(top_n)
    .sort_values("Orders", ascending=False)
)

fig_low_demand = px.bar(
    low_demand_bottom,
    x="Orders",
    y="Product Name",
    orientation="h",
    color_discrete_sequence=[COLOR_LOW_DEMAND],
    text_auto=True,
    title="📉 Low Demand Products"
)
fig_low_demand.update_layout(yaxis_title="")

with left3:
    st.plotly_chart(
        fig_high_demand,
        use_container_width=True,
        config={"displayModeBar": False},
        key="high_demand_products"
    )

with right3:
    st.plotly_chart(
        fig_low_demand,
        use_container_width=True,
        config={"displayModeBar": False},
        key="low_demand_products"
    )

st.markdown("---")

# ------------------------------------------------------------------
# Recommended Products Table
# ------------------------------------------------------------------
st.subheader("Recommended Products")

recommended_table = (
    product_df[product_df["Recommended"]]
    .sort_values("Recommendation Score", ascending=False)
    [["Product Name", "Sales", "Profit", "Discount", "Orders", "Recommendation Score"]]
    .copy()
)

recommended_table["Sales"] = recommended_table["Sales"].map("${:,.2f}".format)
recommended_table["Profit"] = recommended_table["Profit"].map("${:,.2f}".format)
recommended_table["Discount"] = recommended_table["Discount"].map("{:.1%}".format)

st.dataframe(recommended_table, use_container_width=True, hide_index=True)

st.markdown("---")

# ------------------------------------------------------------------
# Download CSV
# ------------------------------------------------------------------
export_df = product_df[
    [
        "Product ID", "Product Name", "Category", "Sales", "Profit", "Discount",
        "Orders", "Recommendation Score", "Status", "High Demand", "Low Demand"
    ]
]
csv = export_df.to_csv(index=False).encode("utf-8")

st.download_button(
    "⬇ Download Product Recommendations",
    csv,
    "product_recommendations.csv",
    "text/csv"
)

st.markdown("---")
st.caption("Retail Intelligence Platform | Product Recommendation Dashboard")