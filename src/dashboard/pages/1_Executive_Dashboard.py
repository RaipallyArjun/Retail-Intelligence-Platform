import streamlit as st
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path

# ==========================
# Project Path
# ==========================

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from database.db_connection import get_connection
from database.us_states import STATE_CODES

# ==========================
# Page Configuration
# ==========================

st.set_page_config(
    page_title="Executive Dashboard",
    page_icon="🏠",
    layout="wide"
)

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

st.title("🏠 Executive Dashboard")
st.markdown("---")

# ==========================
# Load Data
# ==========================

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

st.markdown("---")

# ==========================
# Filters
# ==========================

col1, col2, col3, col4 = st.columns(4)

regions = ["All"] + sorted(df["Region"].dropna().unique().tolist())
categories = ["All"] + sorted(df["Category"].dropna().unique().tolist())
segments = ["All"] + sorted(df["Segment"].dropna().unique().tolist())
years = ["All"] + sorted(df["Order Year"].dropna().astype(int).unique().tolist())

with col1:
    region = st.selectbox("Region", regions)

with col2:
    category = st.selectbox("Category", categories)

with col3:
    segment = st.selectbox("Segment", segments)

with col4:
    year = st.selectbox("Order Year", years)

# ==========================
# Apply Filters
# ==========================

filtered_df = df.copy()

if region != "All":
    filtered_df = filtered_df[filtered_df["Region"] == region]

if category != "All":
    filtered_df = filtered_df[filtered_df["Category"] == category]

if segment != "All":
    filtered_df = filtered_df[filtered_df["Segment"] == segment]

if year != "All":
    filtered_df = filtered_df[filtered_df["Order Year"] == year]

st.markdown("---")

# ==========================
# KPI Calculations
# ==========================

total_sales = filtered_df["Sales"].sum()

total_profit = filtered_df["Profit"].sum()

total_orders = filtered_df["Order ID"].nunique()

total_customers = filtered_df["Customer ID"].nunique()

profit_margin = (
    total_profit / total_sales * 100
    if total_sales != 0 else 0
)

avg_discount = filtered_df["Discount"].mean()

avg_order_value = (
    total_sales / total_orders
    if total_orders != 0 else 0
)

avg_profit_order = (
    total_profit / total_orders
    if total_orders != 0 else 0
)

st.markdown("## 📊 Key Performance Indicators")

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.markdown(f"""
    <div style="background:#f8f9fa;padding:20px;border-left:6px solid #1f77b4;
    border-radius:10px;box-shadow:0px 2px 8px rgba(0,0,0,0.15);">
        <h5>💰 Total Sales</h5>
        <h2>${total_sales:,.0f}</h2>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
    <div style="background:#f8f9fa;padding:20px;border-left:6px solid green;
    border-radius:10px;box-shadow:0px 2px 8px rgba(0,0,0,0.15);">
        <h5>📈 Total Profit</h5>
        <h2>${total_profit:,.0f}</h2>
    </div>
    """, unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""
    <div style="background:#f8f9fa;padding:20px;border-left:6px solid orange;
    border-radius:10px;box-shadow:0px 2px 8px rgba(0,0,0,0.15);">
        <h5>🛒 Total Orders</h5>
        <h2>{total_orders:,}</h2>
    </div>
    """, unsafe_allow_html=True)

with kpi4:
    st.markdown(f"""
    <div style="background:#f8f9fa;padding:20px;border-left:6px solid purple;
    border-radius:10px;box-shadow:0px 2px 8px rgba(0,0,0,0.15);">
        <h5>👥 Total Customers</h5>
        <h2>{total_customers:,}</h2>
    </div>
    """, unsafe_allow_html=True)

st.write("")

kpi5, kpi6, kpi7, kpi8 = st.columns(4)

kpi5.metric("📊 Profit Margin", f"{profit_margin:.2f}%")
kpi6.metric("🏷 Avg Discount", f"{avg_discount:.2%}")
kpi7.metric("💵 Avg Order Value", f"${avg_order_value:,.2f}")
kpi8.metric("📦 Avg Profit / Order", f"${avg_profit_order:,.2f}")

st.markdown("---")

left, right = st.columns(2)

# Sales by Category
sales_category = (
    filtered_df.groupby("Category")["Sales"]
    .sum()
    .reset_index()
)

fig_category = px.bar(
    sales_category,
    x="Sales",
    y="Category",
    orientation="h",
    color="Category",
    text_auto=".2s",
    title="Sales by Category"
)

fig_category.update_layout(
    showlegend=False,
    height=360,
    margin=dict(l=10, r=10, t=50, b=10)
)

# Profit by Region
profit_region = (
    filtered_df.groupby("Region")["Profit"]
    .sum()
    .reset_index()
)

fig_region = px.bar(
    profit_region,
    x="Region",
    y="Profit",
    color="Region",
    text_auto=".2s",
    title="Profit by Region"
)

fig_region.update_layout(
    showlegend=False,
    height=360,
    margin=dict(l=10, r=10, t=50, b=10)
)

with left:
    st.plotly_chart(
        fig_category,
        use_container_width=True,
        config={"displayModeBar": False}
    )

with right:
    st.plotly_chart(
        fig_region,
        use_container_width=True,
        config={"displayModeBar": False}
    )

st.markdown("---")

# ==========================
# Sales by State (map)
# ==========================

st.subheader("Sales by State")

state_sales = (
    filtered_df.groupby("State", as_index=False)["Sales"]
    .sum()
)

# Plotly's "USA-states" mode needs two-letter codes, not full names.
state_sales["State Code"] = state_sales["State"].map(STATE_CODES)

fig_map = px.choropleth(
    state_sales,
    locations="State Code",
    locationmode="USA-states",
    color="Sales",
    scope="usa",
    color_continuous_scale="Blues",
    hover_name="State"
)

fig_map.update_layout(
    height=420,
    margin=dict(l=10, r=10, t=50, b=10)
)

fig_map.update_geos(
    showlakes=True,
    lakecolor="white"
)

st.plotly_chart(
    fig_map,
    use_container_width=True,
    config={"displayModeBar": False}
)

# ==================================================
# Sales Trend & Top 10 Products
# ==================================================

st.markdown("---")

left, right = st.columns(2)

# Sales Trend
trend = (
    filtered_df
    .groupby("Order Year", as_index=False)["Sales"]
    .sum()
)

fig_trend = px.line(
    trend,
    x="Order Year",
    y="Sales",
    title="Sales Trend",
    markers=True
)

fig_trend.update_layout(
    height=360,
    margin=dict(l=10, r=10, t=50, b=10)
)

fig_trend.update_traces(
    line=dict(width=4),
    marker=dict(size=10)
)

# Top 10 Products
top_products = (
    filtered_df
    .groupby("Product Name", as_index=False)["Sales"]
    .sum()
    .sort_values("Sales", ascending=False)
    .head(10)
)

fig_products = px.bar(
    top_products,
    x="Sales",
    y="Product Name",
    orientation="h",
    title="Top 10 Products by Sales",
    text_auto=".2s",
    color="Sales",
    color_continuous_scale="Blues"
)

fig_products.update_layout(
    height=420,
    margin=dict(l=250, r=20, t=50, b=20),
    yaxis=dict(
        categoryorder="total ascending",
        tickfont=dict(size=11)
    ),
    coloraxis_showscale=False
)

fig_products.update_yaxes(
    tickfont=dict(size=10)
)

with left:
    st.plotly_chart(
        fig_trend,
        use_container_width=True,
        config={"displayModeBar": False}
    )

with right:
    st.plotly_chart(
        fig_products,
        use_container_width=True,
        config={"displayModeBar": False}
    )

# ==================================================
# Profit by Sub-Category & Sales by Segment
# ==================================================

st.markdown("---")

left, right = st.columns(2)

# Profit by Sub-Category
subcategory = (
    filtered_df
    .groupby("Sub-Category", as_index=False)["Profit"]
    .sum()
    .sort_values("Profit", ascending=False)
    .head(10)
)

fig_subcategory = px.bar(
    subcategory,
    x="Profit",
    y="Sub-Category",
    orientation="h",
    title="Profit by Sub-Category",
    text_auto=".2s",
    color="Profit",
    color_continuous_scale="Greens"
)

fig_subcategory.update_layout(
    height=360,
    margin=dict(l=10, r=10, t=50, b=10),
    yaxis={"categoryorder": "total ascending"},
    coloraxis_showscale=False
)

# Sales by Segment
segment_sales = (
    filtered_df
    .groupby("Segment", as_index=False)["Sales"]
    .sum()
)

fig_segment = px.pie(
    segment_sales,
    values="Sales",
    names="Segment",
    title="Sales by Segment",
    hole=0.60,
    color_discrete_sequence=[
        "#1565C0",
        "#64B5F6",
        "#90CAF9"
    ]
)

fig_segment.update_layout(
    height=360,
    margin=dict(l=10, r=10, t=50, b=10)
)

fig_segment.update_traces(
    textposition="inside",
    textinfo="percent",
    textfont_size=14
)

with left:
    st.plotly_chart(
        fig_subcategory,
        use_container_width=True,
        config={"displayModeBar": False}
    )

with right:
    st.plotly_chart(
        fig_segment,
        use_container_width=True,
        config={"displayModeBar": False}
    )