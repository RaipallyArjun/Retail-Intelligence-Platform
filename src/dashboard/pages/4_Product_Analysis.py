import streamlit as st
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from database.db_connection import get_connection

st.set_page_config(page_title="Product Analysis", page_icon="📦", layout="wide")

# Consistent color theme across the dashboard
COLOR_SALES = "#1f77b4"     # Blue
COLOR_PROFIT = "#2ca02c"    # Green
COLOR_CUSTOMER = "#ff7f0e"  # Orange
COLOR_PRODUCT = "#9467bd"   # Purple

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
st.title("📦 Product Analysis")
st.caption("Explore product performance, profitability and discounting across categories.")

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
subcategories = ["All"] + sorted(df["Sub-Category"].dropna().unique().tolist())
years = ["All"] + sorted(df["Order Year"].dropna().astype(int).unique().tolist())

with col1:
    region = st.selectbox("Region", regions)
with col2:
    category = st.selectbox("Category", categories)
with col3:
    subcategory = st.selectbox("Sub-Category", subcategories)
with col4:
    year = st.selectbox("Order Year", years)

filtered_df = df.copy()
if region != "All":
    filtered_df = filtered_df[filtered_df["Region"] == region]
if category != "All":
    filtered_df = filtered_df[filtered_df["Category"] == category]
if subcategory != "All":
    filtered_df = filtered_df[filtered_df["Sub-Category"] == subcategory]
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


# Count products by Product ID (the true unique key); a few IDs share more than one name.
total_products = filtered_df["Product ID"].nunique()
total_sales = filtered_df["Sales"].sum()
total_profit = filtered_df["Profit"].sum()
avg_discount = filtered_df["Discount"].mean()

avg_product_sales = (
    total_sales / total_products
) if total_products else 0

avg_product_profit = (
    total_profit / total_products
) if total_products else 0

if total_products:
    best_product = (
        filtered_df.groupby("Product Name")["Sales"]
        .sum()
        .idxmax()
    )
else:
    best_product = "N/A"

loss_products = (
    filtered_df.groupby("Product ID")["Profit"]
    .sum()
    .lt(0)
    .sum()
)

st.subheader("📦 Product Performance Overview")
a, b, c, d = st.columns(4)
a.metric("📦 Total Products", f"{total_products:,}")
b.metric("💰 Total Sales", format_currency(total_sales))
c.metric("📈 Total Profit", format_currency(total_profit))
d.metric("🏷 Avg Discount", f"{avg_discount:.2%}")

e, f, g, h = st.columns(4)
e.metric("💵 Avg Product Sales", format_currency(avg_product_sales))
f.metric("📊 Avg Product Profit", format_currency(avg_product_profit))
g.metric("⭐ Best Selling Product", best_product)
h.metric("📉 Loss Making Products", f"{loss_products:,}")

st.markdown("---")

# ------------------------------------------------------------------
# Sales by Category / Profit by Category
# ------------------------------------------------------------------
left, right = st.columns(2)

sales_category = (
    filtered_df
    .groupby("Category", as_index=False)["Sales"]
    .sum()
    .sort_values("Sales", ascending=True)
)

fig_sales_category = px.bar(
    sales_category,
    x="Sales",
    y="Category",
    orientation="h",
    color_discrete_sequence=[COLOR_SALES],
    text_auto=".2s",
    title="Sales by Category"
)
fig_sales_category.update_layout(showlegend=False)

profit_category = (
    filtered_df
    .groupby("Category", as_index=False)["Profit"]
    .sum()
    .sort_values("Profit", ascending=True)
)

fig_profit_category = px.bar(
    profit_category,
    x="Profit",
    y="Category",
    orientation="h",
    color_discrete_sequence=[COLOR_PROFIT],
    text_auto=".2s",
    title="Profit by Category"
)
fig_profit_category.update_layout(showlegend=False)

with left:
    st.plotly_chart(
        fig_sales_category,
        use_container_width=True,
        config={"displayModeBar": False},
        key="sales_by_category"
    )

with right:
    st.plotly_chart(
        fig_profit_category,
        use_container_width=True,
        config={"displayModeBar": False},
        key="profit_by_category"
    )

st.markdown("---")

# ------------------------------------------------------------------
# Top 10 Products / Top 10 Sub-Categories
# ------------------------------------------------------------------
left, right = st.columns(2)

top_products = (
    filtered_df
    .groupby("Product Name", as_index=False)["Sales"]
    .sum()
    .sort_values("Sales", ascending=False)
    .head(10)
    .sort_values("Sales", ascending=True)
)

fig_top_products = px.bar(
    top_products,
    x="Sales",
    y="Product Name",
    orientation="h",
    title="Top 10 Products",
    color="Sales",
    color_continuous_scale="Purples",
    text_auto=".2s"
)

fig_top_products.update_layout(
    height=420,
    margin=dict(l=260, r=20, t=50, b=20),
    yaxis=dict(tickfont=dict(size=10)),
    coloraxis_showscale=False
)

top_subcategories = (
    filtered_df
    .groupby("Sub-Category", as_index=False)["Sales"]
    .sum()
    .sort_values("Sales", ascending=False)
    .head(10)
    .sort_values("Sales", ascending=True)
)

fig_top_subcategories = px.bar(
    top_subcategories,
    x="Sales",
    y="Sub-Category",
    orientation="h",
    title="Top 10 Sub-Categories",
    color="Sales",
    color_continuous_scale="Purples",
    text_auto=".2s"
)

fig_top_subcategories.update_layout(
    height=420,
    margin=dict(l=150, r=20, t=50, b=20),
    yaxis=dict(tickfont=dict(size=10)),
    coloraxis_showscale=False
)

with left:
    st.plotly_chart(
        fig_top_products,
        use_container_width=True,
        config={"displayModeBar": False},
        key="top_products"
    )

with right:
    st.plotly_chart(
        fig_top_subcategories,
        use_container_width=True,
        config={"displayModeBar": False},
        key="top_subcategories"
    )

st.markdown("---")

# ------------------------------------------------------------------
# Sales by Sub-Category (Treemap) / Discount Analysis
# ------------------------------------------------------------------
left, right = st.columns(2)

sales_subcategory = (
    filtered_df
    .groupby(["Category", "Sub-Category"], as_index=False)["Sales"]
    .sum()
)

fig_treemap = px.treemap(
    sales_subcategory,
    path=["Category", "Sub-Category"],
    values="Sales",
    color="Sales",
    color_continuous_scale="Purples",
    title="Sales by Sub-Category"
)
fig_treemap.update_layout(
    margin=dict(l=10, r=10, t=50, b=10),
    coloraxis_showscale=False
)
fig_treemap.update_traces(
    textinfo="label+value"
)

fig_discount = px.histogram(
    filtered_df,
    x="Discount",
    nbins=30,
    title="Discount Analysis",
    color_discrete_sequence=[COLOR_PRODUCT]
)
fig_discount.update_layout(
    xaxis=dict(title="Discount", tickformat=".0%"),
    yaxis_title="Frequency",
    showlegend=False
)

with left:
    st.plotly_chart(
        fig_treemap,
        use_container_width=True,
        config={"displayModeBar": False},
        key="sales_by_subcategory_treemap"
    )

with right:
    st.plotly_chart(
        fig_discount,
        use_container_width=True,
        config={"displayModeBar": False},
        key="discount_analysis"
    )

st.markdown("---")

# ------------------------------------------------------------------
# Top 10 Loss-Making Products
# ------------------------------------------------------------------
st.subheader("Top 10 Loss-Making Products")

loss_table = (
    filtered_df
    .groupby("Product Name", as_index=False)["Profit"]
    .sum()
    .sort_values("Profit")
    .head(10)
)

fig_loss_products = px.bar(
    loss_table,
    x="Profit",
    y="Product Name",
    orientation="h",
    title="Top 10 Loss-Making Products",
    color="Profit",
    color_continuous_scale="Reds_r",
    text_auto=".2s"
)
fig_loss_products.update_layout(
    height=420,
    margin=dict(l=260, r=20, t=50, b=20),
    yaxis=dict(tickfont=dict(size=10)),
    coloraxis_showscale=False,
    showlegend=False
)

st.plotly_chart(
    fig_loss_products,
    use_container_width=True,
    config={"displayModeBar": False},
    key="top_loss_products"
)

st.markdown("---")

# ------------------------------------------------------------------
# Product Details Table / Download CSV
# ------------------------------------------------------------------
st.subheader("Product Details")

product_table = (
    filtered_df
    .groupby("Product Name", as_index=False)
    .agg(
        Category=("Category", "first"),
        **{"Sub-Category": ("Sub-Category", "first")},
        Sales=("Sales", "sum"),
        Profit=("Profit", "sum"),
        Discount=("Discount", "mean"),
        Orders=("Order ID", "nunique")
    )
    .sort_values("Sales", ascending=False)
)

csv = product_table.to_csv(index=False).encode("utf-8")

product_table["Sales"] = product_table["Sales"].map("${:,.2f}".format)
product_table["Profit"] = product_table["Profit"].map("${:,.2f}".format)
product_table["Discount"] = (
    product_table["Discount"]
    .round(4)
    .map("{:.2%}".format)
)

st.dataframe(product_table, use_container_width=True, hide_index=True)

st.download_button("⬇ Download Product Data", csv, "product_analysis.csv", "text/csv")

st.markdown("---")
st.caption("Retail Intelligence Platform | Product Analysis Dashboard")