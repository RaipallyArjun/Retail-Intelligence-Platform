import streamlit as st
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from database.db_connection import get_connection

st.set_page_config(page_title="Customer Analysis", page_icon="👥", layout="wide")

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
st.title("👥 Customer Analysis")
st.caption("Understand customer behavior, retention and value across regions and segments.")

conn = get_connection()
df = pd.read_sql_query("SELECT * FROM Superstore", conn)
conn.close()
st.success("Database Connected Successfully!")

# ------------------------------------------------------------------
# Filters
# ------------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
regions = ["All"] + sorted(df["Region"].dropna().unique().tolist())
segments = ["All"] + sorted(df["Segment"].dropna().unique().tolist())
customers = ["All"] + sorted(df["Customer Name"].dropna().unique().tolist())
years = ["All"] + sorted(df["Order Year"].dropna().astype(int).unique().tolist())

with col1:
    region = st.selectbox("Region", regions)
with col2:
    segment = st.selectbox("Segment", segments)
with col3:
    customer = st.selectbox("Customer", customers)
with col4:
    year = st.selectbox("Order Year", years)

filtered_df = df.copy()
if region != "All":
    filtered_df = filtered_df[filtered_df["Region"] == region]
if segment != "All":
    filtered_df = filtered_df[filtered_df["Segment"] == segment]
if customer != "All":
    filtered_df = filtered_df[filtered_df["Customer Name"] == customer]
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


total_customers = filtered_df["Customer ID"].nunique()

repeat_customers = (
    filtered_df.groupby("Customer ID")["Order ID"]
    .nunique()
    .gt(1)
    .sum()
)

new_customers = total_customers - repeat_customers

avg_sales_customer = (
    filtered_df["Sales"].sum() / total_customers
) if total_customers else 0

avg_orders_customer = (
    filtered_df["Order ID"].nunique() / total_customers
) if total_customers else 0

avg_profit_customer = (
    filtered_df["Profit"].sum() / total_customers
) if total_customers else 0

avg_discount = filtered_df["Discount"].mean()

# Retention rate — share of customers with more than one order
retention_rate = (
    repeat_customers / total_customers * 100
) if total_customers else 0

st.subheader("👥 Customer Performance Overview")
a, b, c, d = st.columns(4)
a.metric("👥 Total Customers", f"{total_customers:,}")
b.metric("🔁 Repeat Customers", f"{repeat_customers:,}")
c.metric("🆕 New Customers", f"{new_customers:,}")
d.metric("💰 Avg Sales per Customer", format_currency(avg_sales_customer))

e, f, g, h = st.columns(4)
e.metric("📦 Avg Orders per Customer", f"{avg_orders_customer:.2f}")
f.metric("💵 Avg Profit per Customer", format_currency(avg_profit_customer))
g.metric("📊 Avg Discount", f"{avg_discount:.2%}")
h.metric("🔁 Retention Rate", f"{retention_rate:.2f}%")

st.markdown("---")

# ------------------------------------------------------------------
# Customer Growth Trend / Customer Distribution
# ------------------------------------------------------------------
left, right = st.columns(2)

growth_trend = (
    filtered_df.groupby("Order Year", as_index=False)["Customer ID"]
    .nunique()
    .rename(columns={"Customer ID": "Customers"})
)

fig_growth = px.line(
    growth_trend,
    x="Order Year",
    y="Customers",
    markers=True,
    title="Customer Growth Trend"
)
fig_growth.update_traces(
    line=dict(width=4, color=COLOR_CUSTOMER),
    marker=dict(size=9, color=COLOR_CUSTOMER),
    fill="tozeroy"
)

customers_by_region = (
    filtered_df.groupby("Region", as_index=False)["Customer ID"]
    .nunique()
    .rename(columns={"Customer ID": "Customers"})
)

fig_distribution = px.bar(
    customers_by_region,
    x="Customers",
    y="Region",
    orientation="h",
    color="Region",
    text_auto=True,
    title="Customer Distribution by Region"
)
fig_distribution.update_layout(showlegend=False)

with left:
    st.plotly_chart(
        fig_growth,
        use_container_width=True,
        config={"displayModeBar": False},
        key="customer_growth_trend"
    )

with right:
    st.plotly_chart(
        fig_distribution,
        use_container_width=True,
        config={"displayModeBar": False},
        key="customer_distribution"
    )

st.markdown("---")

# ------------------------------------------------------------------
# Top 10 Customers / Sales by Customer Segment
# ------------------------------------------------------------------
left, right = st.columns(2)

top_customers = (
    filtered_df
    .groupby("Customer Name", as_index=False)["Sales"]
    .sum()
    .sort_values("Sales", ascending=False)
    .head(10)
)

fig_top_customers = px.bar(
    top_customers,
    x="Sales",
    y="Customer Name",
    orientation="h",
    title="Top 10 Customers",
    color="Sales",
    color_continuous_scale="Oranges",
    text_auto=".2s"
)

fig_top_customers.update_layout(
    height=420,
    margin=dict(l=180, r=20, t=50, b=20),
    yaxis=dict(tickfont=dict(size=10)),
    coloraxis_showscale=False
)

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
    title="Sales by Customer Segment",
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

with left:
    st.plotly_chart(
        fig_top_customers,
        use_container_width=True,
        config={"displayModeBar": False},
        key="top_customers"
    )

with right:
    st.plotly_chart(
        fig_segment,
        use_container_width=True,
        config={"displayModeBar": False},
        key="sales_by_segment"
    )

st.markdown("---")

# ------------------------------------------------------------------
# Top 10 Customer States / Customer Profit Distribution
# ------------------------------------------------------------------
left, right = st.columns(2)

top_states = (
    filtered_df
    .groupby("State", as_index=False)["Customer ID"]
    .nunique()
    .rename(columns={"Customer ID": "Customers"})
    .sort_values("Customers", ascending=False)
    .head(10)
)

top_states = top_states.sort_values("Customers", ascending=True)

fig_top_states = px.bar(
    top_states,
    x="Customers",
    y="State",
    orientation="h",
    color="Customers",
    color_continuous_scale="Oranges",
    text_auto=True,
    title="Top 10 Customer States"
)
fig_top_states.update_layout(showlegend=False, coloraxis_showscale=False)

profit_per_customer = (
    filtered_df.groupby("Customer ID", as_index=False)["Profit"]
    .sum()
)

fig_profit_dist = px.histogram(
    profit_per_customer,
    x="Profit",
    nbins=40,
    title="Customer Profit Distribution",
    color_discrete_sequence=[COLOR_PROFIT]
)
fig_profit_dist.update_layout(
    xaxis_title="Profit",
    yaxis_title="Frequency",
    showlegend=False
)

with left:
    st.plotly_chart(
        fig_top_states,
        use_container_width=True,
        config={"displayModeBar": False},
        key="top_customer_states"
    )

with right:
    st.plotly_chart(
        fig_profit_dist,
        use_container_width=True,
        config={"displayModeBar": False},
        key="customer_profit_distribution"
    )

st.markdown("---")

# ------------------------------------------------------------------
# Customer Details Table / Download CSV
# ------------------------------------------------------------------
st.subheader("Customer Details")

customer_table = (
    filtered_df
    .groupby(["Customer ID", "Customer Name"], as_index=False)
    .agg(
        Region=("Region", "first"),
        Segment=("Segment", "first"),
        Sales=("Sales", "sum"),
        Profit=("Profit", "sum"),
        Orders=("Order ID", "nunique")
    )
    .sort_values("Sales", ascending=False)
)

csv = customer_table.to_csv(index=False).encode("utf-8")

customer_table["Sales"] = customer_table["Sales"].map("${:,.2f}".format)
customer_table["Profit"] = customer_table["Profit"].map("${:,.2f}".format)

st.dataframe(customer_table, use_container_width=True, hide_index=True)

st.download_button("⬇ Download Customer Data", csv, "customer_analysis.csv", "text/csv")

st.markdown("---")
st.caption("Retail Intelligence Platform | Customer Analysis Dashboard")