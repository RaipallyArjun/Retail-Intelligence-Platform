import streamlit as st
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from database.db_connection import get_connection
from database.us_states import STATE_CODES

st.set_page_config(page_title="Sales Analysis", page_icon="📈", layout="wide")

# Consistent color theme across the dashboard
COLOR_SALES = "#1f77b4"     # Blue
COLOR_PROFIT = "#2ca02c"    # Green
COLOR_CUSTOMER = "#ff7f0e"  # Orange

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
st.title("📈 Sales Analysis")
st.caption("Analyze sales performance across regions, categories, customers and products.")

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

# ------------------------------------------------------------------
# Filters
# ------------------------------------------------------------------
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

filtered_df = df.copy()
if region != "All":
    filtered_df = filtered_df[filtered_df["Region"] == region]
if category != "All":
    filtered_df = filtered_df[filtered_df["Category"] == category]
if segment != "All":
    filtered_df = filtered_df[filtered_df["Segment"] == segment]
if year != "All":
    filtered_df = filtered_df[filtered_df["Order Year"] == year]

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


total_sales = filtered_df["Sales"].sum()
total_profit = filtered_df["Profit"].sum()
total_orders = filtered_df["Order ID"].nunique()
total_customers = filtered_df["Customer ID"].nunique()
profit_margin = (total_profit / total_sales * 100) if total_sales else 0
avg_discount = filtered_df["Discount"].mean()
avg_order_value = (total_sales / total_orders) if total_orders else 0
avg_profit_order = (total_profit / total_orders) if total_orders else 0

st.subheader("📈 Sales Performance Overview")
a, b, c, d = st.columns(4)
a.metric("💰 Total Sales", format_currency(total_sales))
b.metric("📈 Total Profit", format_currency(total_profit))
c.metric("🛒 Total Orders", f"{total_orders:,}")
d.metric("👥 Total Customers", f"{total_customers:,}")

e, f, g, h = st.columns(4)
e.metric("📊 Profit Margin", f"{profit_margin:.2f}%")
f.metric("🏷 Avg Discount", f"{avg_discount:.2%}")
g.metric("💵 Avg Order Value", f"${avg_order_value:,.2f}")
h.metric("📦 Avg Profit / Order", f"${avg_profit_order:,.2f}")

st.markdown("---")

# ------------------------------------------------------------------
# Yearly Sales Trend / Yearly Profit Trend
# ------------------------------------------------------------------
left, right = st.columns(2)

sales = filtered_df.groupby("Order Year", as_index=False)["Sales"].sum()
fig1 = px.line(sales, x="Order Year", y="Sales", markers=True, title="Yearly Sales Trend")
fig1.update_traces(line=dict(width=4, color=COLOR_SALES), marker=dict(size=9, color=COLOR_SALES))

profit = filtered_df.groupby("Order Year", as_index=False)["Profit"].sum()
fig2 = px.line(profit, x="Order Year", y="Profit", markers=True, title="Yearly Profit Trend")
fig2.update_traces(line=dict(width=4, color=COLOR_PROFIT), marker=dict(size=9, color=COLOR_PROFIT))

with left:
    st.plotly_chart(
        fig1,
        use_container_width=True,
        key="sales_trend",
        config={"displayModeBar": False}
    )
with right:
    st.plotly_chart(
        fig2,
        use_container_width=True,
        key="profit_trend",
        config={"displayModeBar": False}
    )

st.markdown("---")

# ------------------------------------------------------------------
# Sales by Region / Profit by Category
# ------------------------------------------------------------------
left, right = st.columns(2)

sales_region = (
    filtered_df
    .groupby("Region", as_index=False)["Sales"]
    .sum()
)

fig_region = px.bar(
    sales_region,
    x="Region",
    y="Sales",
    color_discrete_sequence=[COLOR_SALES],
    text_auto=".2s",
    title="Sales by Region"
)

fig_region.update_layout(
    height=380,
    margin=dict(l=10, r=10, t=50, b=10),
    showlegend=False
)

profit_category = (
    filtered_df
    .groupby("Category", as_index=False)["Profit"]
    .sum()
)

fig_profit_cat = px.bar(
    profit_category,
    x="Category",
    y="Profit",
    color_discrete_sequence=[COLOR_PROFIT],
    text_auto=".2s",
    title="Profit by Category"
)

fig_profit_cat.update_layout(
    height=380,
    margin=dict(l=10, r=10, t=50, b=10),
    showlegend=False
)

with left:
    st.plotly_chart(
        fig_region,
        use_container_width=True,
        config={"displayModeBar": False},
        key="sales_region"
    )

with right:
    st.plotly_chart(
        fig_profit_cat,
        use_container_width=True,
        config={"displayModeBar": False},
        key="profit_category"
    )

st.markdown("---")

# ------------------------------------------------------------------
# Sales by State (Map)
# ------------------------------------------------------------------
st.subheader("Sales by State")

state_sales = (
    filtered_df
    .groupby("State", as_index=False)["Sales"]
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
    height=550,
    margin=dict(l=10, r=10, t=20, b=10)
)

fig_map.update_geos(
    showlakes=True,
    lakecolor="white"
)

st.plotly_chart(
    fig_map,
    use_container_width=True,
    config={"displayModeBar": False},
    key="sales_map"
)

st.markdown("---")

# ------------------------------------------------------------------
# Top 10 Products / Top 10 Customers
# ------------------------------------------------------------------
left, right = st.columns(2)

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
    title="Top 10 Products",
    color="Sales",
    color_continuous_scale="Blues",
    text_auto=".2s"
)

fig_products.update_layout(
    height=420,
    margin=dict(l=260, r=20, t=50, b=20),
    yaxis=dict(tickfont=dict(size=10)),
    coloraxis_showscale=False
)

top_customers = (
    filtered_df
    .groupby("Customer Name", as_index=False)["Sales"]
    .sum()
    .sort_values("Sales", ascending=False)
    .head(10)
)

fig_customers = px.bar(
    top_customers,
    x="Sales",
    y="Customer Name",
    orientation="h",
    title="Top 10 Customers",
    color="Sales",
    color_continuous_scale="Oranges",
    text_auto=".2s"
)

fig_customers.update_layout(
    height=420,
    margin=dict(l=180, r=20, t=50, b=20),
    yaxis=dict(tickfont=dict(size=10)),
    coloraxis_showscale=False
)

with left:
    st.plotly_chart(
        fig_products,
        use_container_width=True,
        config={"displayModeBar": False},
        key="top_products"
    )

with right:
    st.plotly_chart(
        fig_customers,
        use_container_width=True,
        config={"displayModeBar": False},
        key="top_customers"
    )

st.markdown("---")

# ------------------------------------------------------------------
# Sales by Segment / Sales by Ship Mode
# ------------------------------------------------------------------
left, right = st.columns(2)

segment_sales = (
    filtered_df
    .groupby("Segment", as_index=False)["Sales"]
    .sum()
)

fig_segment = px.pie(
    segment_sales,
    values="Sales",
    names="Segment",
    hole=0.6,
    title="Sales by Segment",
    color_discrete_sequence=px.colors.sequential.Blues_r
)

fig_segment.update_traces(
    textinfo="percent+label",
    textposition="inside"
)

fig_segment.update_layout(
    showlegend=True,
    legend_title="Segment"
)

ship_sales = (
    filtered_df
    .groupby("Ship Mode", as_index=False)["Sales"]
    .sum()
)

fig_ship = px.pie(
    ship_sales,
    values="Sales",
    names="Ship Mode",
    hole=0.6,
    title="Sales by Ship Mode",
    color_discrete_sequence=px.colors.sequential.Blues_r
)

fig_ship.update_traces(
    textinfo="percent+label",
    textposition="inside"
)

fig_ship.update_layout(
    showlegend=True,
    legend_title="Ship Mode"
)

with left:
    st.plotly_chart(
        fig_segment,
        use_container_width=True,
        config={"displayModeBar": False},
        key="segment_sales"
    )

with right:
    st.plotly_chart(
        fig_ship,
        use_container_width=True,
        config={"displayModeBar": False},
        key="ship_mode"
    )

st.markdown("---")

# ------------------------------------------------------------------
# Sales Details Table / Download CSV
# ------------------------------------------------------------------
st.subheader("Sales Details")
st.dataframe(filtered_df, use_container_width=True, hide_index=True)

csv = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button("⬇ Download Sales Data", csv, "sales_analysis.csv", "text/csv")

st.markdown("---")
st.caption("Retail Intelligence Platform | Sales Analysis Dashboard")