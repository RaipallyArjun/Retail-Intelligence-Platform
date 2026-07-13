import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from database.db_connection import get_connection

st.set_page_config(page_title="Customer Segmentation", page_icon="👥", layout="wide")

# Consistent color theme across the dashboard
COLOR_SALES = "#1f77b4"     # Blue
COLOR_PROFIT = "#2ca02c"    # Green
COLOR_CUSTOMER = "#ff7f0e"  # Orange
COLOR_PRODUCT = "#9467bd"   # Purple

# Cluster / segment colors
COLOR_LOW_VALUE = "#d62728"      # Red
COLOR_REGULAR = "#ff7f0e"        # Orange
COLOR_HIGH_VALUE = "#2ca02c"     # Green

N_CLUSTERS = 3

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
st.title("👥 Customer Segmentation")
st.caption("Group customers into value-based segments using K-Means clustering on Sales, Profit, and Orders.")

conn = get_connection()
df = pd.read_sql_query("SELECT * FROM Superstore", conn)
conn.close()
st.success("Database Connected Successfully!")

df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")

# ------------------------------------------------------------------
# Filters
# ------------------------------------------------------------------
col1, col2, col3 = st.columns(3)

regions = ["All"] + sorted(df["Region"].dropna().unique())
segments = ["All"] + sorted(df["Segment"].dropna().unique())
years = ["All"] + sorted(df["Order Year"].dropna().astype(int).unique())

with col1:
    region = st.selectbox("Region", regions)
with col2:
    segment = st.selectbox("Segment", segments)
with col3:
    year = st.selectbox("Order Year", years)

filtered_df = df.copy()
if region != "All":
    filtered_df = filtered_df[filtered_df["Region"] == region]
if segment != "All":
    filtered_df = filtered_df[filtered_df["Segment"] == segment]
if year != "All":
    filtered_df = filtered_df[filtered_df["Order Year"] == year]

st.markdown("---")

if filtered_df.empty:
    st.warning("No data matches the selected filters. Please adjust your filter selection.")
    st.stop()

# ------------------------------------------------------------------
# Aggregate to customer level
# ------------------------------------------------------------------
customer_df = (
    filtered_df
    .groupby(
        ["Customer ID", "Customer Name"],
        as_index=False
    )
    .agg(
        Sales=("Sales", "sum"),
        Profit=("Profit", "sum"),
        Orders=("Order ID", "nunique")
    )
)

if len(customer_df) < N_CLUSTERS:
    st.warning(
        f"Only {len(customer_df)} customer(s) match the current filters — "
        f"not enough to form {N_CLUSTERS} clusters. Please widen your filters."
    )
    st.stop()

# ------------------------------------------------------------------
# K-Means clustering
# ------------------------------------------------------------------
features = customer_df[["Sales", "Profit", "Orders"]]

scaler = StandardScaler()
scaled_features = scaler.fit_transform(features)

kmeans = KMeans(
    n_clusters=N_CLUSTERS,
    random_state=42,
    n_init=10
)
customer_df["Cluster"] = kmeans.fit_predict(scaled_features)

# Rank clusters by average sales -> Low Value / Regular / High Value
cluster_rank = (
    customer_df.groupby("Cluster")["Sales"]
    .mean()
    .sort_values()
    .index.tolist()
)

segment_labels = {
    cluster_rank[0]: "🔴 Low Value",
    cluster_rank[1]: "🟠 Regular",
    cluster_rank[2]: "🟢 High Value",
}
segment_colors = {
    "🔴 Low Value": COLOR_LOW_VALUE,
    "🟠 Regular": COLOR_REGULAR,
    "🟢 High Value": COLOR_HIGH_VALUE,
}

customer_df["Segment"] = customer_df["Cluster"].map(segment_labels)

best_cluster = cluster_rank[-1]
worst_cluster = cluster_rank[0]

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


total_customers = customer_df["Customer ID"].nunique()
total_clusters = N_CLUSTERS
high_value_count = (customer_df["Cluster"] == best_cluster).sum()
low_value_count = (customer_df["Cluster"] == worst_cluster).sum()
avg_sales = customer_df["Sales"].mean()
avg_profit = customer_df["Profit"].mean()
avg_orders = customer_df["Orders"].mean()
best_cluster_label = segment_labels[best_cluster]

st.subheader("👥 Segmentation Overview")

a, b, c, d = st.columns(4)
a.metric("👥 Total Customers", f"{total_customers:,}")
b.metric("🎯 Total Clusters", f"{total_clusters}")
c.metric("⭐ High Value Customers", f"{high_value_count:,}")
d.metric("📉 Low Value Customers", f"{low_value_count:,}")

e, f, g, h = st.columns(4)
e.metric("💰 Avg Sales / Customer", format_currency(avg_sales))
f.metric("📈 Avg Profit / Customer", format_currency(avg_profit))
g.metric("📦 Avg Orders / Customer", f"{avg_orders:,.2f}")
h.metric("🏆 Best Cluster", best_cluster_label)

st.markdown("---")

# ------------------------------------------------------------------
# Customer Segments (pie) / Cluster Distribution (bar)
# ------------------------------------------------------------------
left, right = st.columns(2)

seg_counts = customer_df["Segment"].value_counts().reset_index()
seg_counts.columns = ["Segment", "Customers"]

fig_segments = px.pie(
    seg_counts,
    names="Segment",
    values="Customers",
    color="Segment",
    color_discrete_map=segment_colors,
    hole=0.45,
    title="Customer Segments"
)
fig_segments.update_traces(textinfo="percent+label")

dist_df = customer_df.groupby("Cluster", as_index=False).size().rename(columns={"size": "Customers"})
dist_df["Cluster Label"] = dist_df["Cluster"].map(segment_labels)

fig_distribution = px.bar(
    dist_df,
    x="Cluster Label",
    y="Customers",
    color_discrete_sequence=[COLOR_CUSTOMER],
    text_auto=True,
    title="Cluster Distribution"
)
fig_distribution.update_layout(xaxis_title="", showlegend=False)

with left:
    st.plotly_chart(
        fig_segments,
        use_container_width=True,
        config={"displayModeBar": False},
        key="customer_segments_pie"
    )

with right:
    st.plotly_chart(
        fig_distribution,
        use_container_width=True,
        config={"displayModeBar": False},
        key="cluster_distribution_bar"
    )

st.markdown("---")

# ------------------------------------------------------------------
# Cluster Scatter Plot / Sales by Segment
# ------------------------------------------------------------------
left2, right2 = st.columns(2)

fig_scatter = px.scatter(
    customer_df,
    x="Sales",
    y="Profit",
    color="Segment",
    color_discrete_map=segment_colors,
    size="Orders",
    hover_data=["Customer ID", "Customer Name", "Orders"],
    title="Cluster Scatter Plot"
)

sales_by_segment = (
    customer_df.groupby("Segment", as_index=False)["Sales"].sum().sort_values("Sales")
)

fig_sales_segment = px.bar(
    sales_by_segment,
    x="Sales",
    y="Segment",
    orientation="h",
    color="Segment",
    color_discrete_map=segment_colors,
    text_auto=".2s",
    title="Sales by Segment"
)
fig_sales_segment.update_layout(yaxis_title="", showlegend=False)

with left2:
    st.plotly_chart(
        fig_scatter,
        use_container_width=True,
        config={"displayModeBar": False},
        key="cluster_scatter_plot"
    )

with right2:
    st.plotly_chart(
        fig_sales_segment,
        use_container_width=True,
        config={"displayModeBar": False},
        key="sales_by_segment_bar"
    )

st.markdown("---")

# ------------------------------------------------------------------
# Profit by Segment
# ------------------------------------------------------------------
st.subheader("Profit by Segment")

profit_by_segment = (
    customer_df.groupby("Segment", as_index=False)["Profit"].sum().sort_values("Profit")
)

fig_profit_segment = px.bar(
    profit_by_segment,
    x="Profit",
    y="Segment",
    orientation="h",
    color="Segment",
    color_discrete_map=segment_colors,
    text_auto=".2s"
)
fig_profit_segment.update_layout(yaxis_title="", showlegend=False, height=320)

st.plotly_chart(
    fig_profit_segment,
    use_container_width=True,
    config={"displayModeBar": False},
    key="profit_by_segment_bar"
)

st.markdown("---")

# ------------------------------------------------------------------
# Cluster Summary
# ------------------------------------------------------------------
st.subheader("Cluster Summary")

cluster_summary = (
    customer_df
    .groupby("Segment", as_index=False)
    .agg(
        Customers=("Customer ID", "count"),
        Sales=("Sales", "sum"),
        Profit=("Profit", "sum"),
        Orders=("Orders", "sum")
    )
)

st.dataframe(
    cluster_summary,
    use_container_width=True,
    hide_index=True
)

st.markdown("---")

# ------------------------------------------------------------------
# Top Customers by Cluster
# ------------------------------------------------------------------
st.subheader("Top Customers by Cluster")

top_n = st.slider("Show top N customers per cluster", 3, 20, 5)

top_customers = (
    customer_df
    .sort_values("Sales", ascending=False)
    .groupby("Cluster", group_keys=False)
    .head(top_n)
    .sort_values(["Cluster", "Sales"], ascending=[True, False])
)

top_customers_display = top_customers[
    ["Customer ID", "Customer Name", "Segment", "Sales", "Profit", "Orders"]
].copy()

top_customers_display["Sales"] = top_customers_display["Sales"].map("${:,.2f}".format)
top_customers_display["Profit"] = top_customers_display["Profit"].map("${:,.2f}".format)

st.dataframe(top_customers_display, use_container_width=True, hide_index=True)

st.markdown("---")

# ------------------------------------------------------------------
# Download CSV
# ------------------------------------------------------------------
export_df = customer_df[
    ["Customer ID", "Customer Name", "Cluster", "Segment", "Sales", "Profit", "Orders"]
]
csv = export_df.to_csv(index=False).encode("utf-8")

st.download_button(
    "⬇ Download Customer Segmentation",
    csv,
    "customer_segmentation.csv",
    "text/csv"
)

st.markdown("---")
st.caption("Retail Intelligence Platform | Customer Segmentation Dashboard")