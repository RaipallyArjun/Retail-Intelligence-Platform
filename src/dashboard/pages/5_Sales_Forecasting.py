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

st.set_page_config(page_title="Sales Forecasting", page_icon="📉", layout="wide")

# Consistent color theme across the dashboard
COLOR_SALES = "#1f77b4"     # Blue
COLOR_PROFIT = "#2ca02c"    # Green
COLOR_CUSTOMER = "#ff7f0e"  # Orange
COLOR_PRODUCT = "#9467bd"   # Purple
COLOR_FORECAST = "#ff7f0e"  # Orange — reserved for forecasted/predicted values

FORECAST_WINDOW = 3    # months used in the moving average
FORECAST_PERIODS = 12  # months to forecast forward

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
st.title("📉 Sales Forecasting")
st.caption("Project future sales using a moving-average forecast built on historical trends.")

conn = get_connection()
df = pd.read_sql_query("SELECT * FROM Superstore", conn)
conn.close()
st.success("Database Connected Successfully!")

df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")

# ------------------------------------------------------------------
# Filters
# ------------------------------------------------------------------
# Note: Year is intentionally left out of the filters here — the
# forecast needs the full historical time series to build a
# meaningful trend, so only structural filters are offered.
col1, col2, col3 = st.columns(3)
regions = ["All"] + sorted(df["Region"].dropna().unique().tolist())
categories = ["All"] + sorted(df["Category"].dropna().unique().tolist())
segments = ["All"] + sorted(df["Segment"].dropna().unique().tolist())

with col1:
    region = st.selectbox("Region", regions)
with col2:
    category = st.selectbox("Category", categories)
with col3:
    segment = st.selectbox("Segment", segments)

filtered_df = df.copy()
if region != "All":
    filtered_df = filtered_df[filtered_df["Region"] == region]
if category != "All":
    filtered_df = filtered_df[filtered_df["Category"] == category]
if segment != "All":
    filtered_df = filtered_df[filtered_df["Segment"] == segment]

filtered_df = filtered_df.dropna(subset=["Order Date"])

# ------------------------------------------------------------------
# Forecasting helpers
# ------------------------------------------------------------------
def build_monthly_series(data):
    """Aggregate Sales into a chronological monthly time series."""
    monthly = data.assign(Month=data["Order Date"].dt.to_period("M").dt.to_timestamp())
    monthly = monthly.groupby("Month", as_index=False)["Sales"].sum().sort_values("Month")
    return monthly


def moving_average_forecast(values, window=FORECAST_WINDOW, periods=FORECAST_PERIODS):
    """
    Simple moving average forecast: each future value is the mean of
    the trailing `window` values, feeding forward as history runs out.
    """
    series = list(values)
    if not series:
        return [0.0] * periods

    effective_window = min(window, len(series))
    forecast = []
    for _ in range(periods):
        next_val = float(np.mean(series[-effective_window:]))
        forecast.append(next_val)
        series.append(next_val)
    return forecast


monthly_sales = build_monthly_series(filtered_df)

if not monthly_sales.empty:
    last_month = monthly_sales["Month"].max()
    future_dates = pd.date_range(
        start=last_month + pd.DateOffset(months=1),
        periods=FORECAST_PERIODS,
        freq="MS"
    )
    forecast_values = moving_average_forecast(monthly_sales["Sales"].tolist())
else:
    future_dates = pd.date_range(start=pd.Timestamp.today(), periods=FORECAST_PERIODS, freq="MS")
    forecast_values = [0.0] * FORECAST_PERIODS

forecast_df = pd.DataFrame({"Month": future_dates, "Forecast Sales": forecast_values})

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


total_historical_sales = filtered_df["Sales"].sum()
forecast_sales = forecast_df["Forecast Sales"].sum()

trailing_actual_window = monthly_sales["Sales"].tail(FORECAST_PERIODS).sum()
expected_growth = (
    (forecast_sales - trailing_actual_window) / trailing_actual_window * 100
) if trailing_actual_window else 0

avg_monthly_sales = monthly_sales["Sales"].mean() if not monthly_sales.empty else 0

if not forecast_df.empty:
    highest_row = forecast_df.loc[forecast_df["Forecast Sales"].idxmax()]
    lowest_row = forecast_df.loc[forecast_df["Forecast Sales"].idxmin()]
    highest_forecast_month = highest_row["Month"].strftime("%b %Y")
    lowest_forecast_month = lowest_row["Month"].strftime("%b %Y")
else:
    highest_forecast_month = "N/A"
    lowest_forecast_month = "N/A"

if not forecast_df.empty:
    forecast_period_label = (
        f"{forecast_df['Month'].min().strftime('%b %Y')} – "
        f"{forecast_df['Month'].max().strftime('%b %Y')}"
    )
else:
    forecast_period_label = "Next 12 Months"

growth_indicator = "🟢" if expected_growth >= 0 else "🔴"

st.subheader("📉 Forecast Overview")
a, b, c, d = st.columns(4)
a.metric("📈 Total Historical Sales", format_currency(total_historical_sales))
b.metric("🔮 Forecast Sales", format_currency(forecast_sales))
c.metric("📊 Expected Growth", f"{growth_indicator} {expected_growth:+.2f}%")
d.metric("📅 Forecast Period", forecast_period_label)

e, f, g, h = st.columns(4)
e.metric("💰 Average Monthly Sales", format_currency(avg_monthly_sales))
f.metric("📈 Highest Forecast Month", highest_forecast_month)
g.metric("📉 Lowest Forecast Month", lowest_forecast_month)
h.metric("🎯 Forecast Accuracy", "Coming Soon")

st.info(
    f"**Forecast Summary:** Based on the last {FORECAST_WINDOW} months, total forecasted "
    f"sales for the next 12 months are **{format_currency(forecast_sales)}**, representing "
    f"an expected growth of **{growth_indicator} {expected_growth:+.2f}%** over the previous "
    f"12 months."
)

st.markdown("---")

# ------------------------------------------------------------------
# Historical vs Forecast Sales Trend
# ------------------------------------------------------------------
st.subheader("Historical vs Forecast Sales Trend")

# Prepend the last historical point to the forecast series so the two
# lines connect visually instead of leaving a gap.
if not monthly_sales.empty:
    connector = monthly_sales.iloc[[-1]][["Month", "Sales"]].rename(
        columns={"Sales": "Forecast Sales"}
    )
    forecast_line_df = pd.concat([connector, forecast_df], ignore_index=True)
else:
    forecast_line_df = forecast_df

fig_combined = go.Figure()

fig_combined.add_trace(go.Scatter(
    x=monthly_sales["Month"],
    y=monthly_sales["Sales"],
    mode="lines+markers",
    name="Historical Sales",
    line=dict(color=COLOR_SALES, width=3),
    marker=dict(size=6)
))

fig_combined.add_trace(go.Scatter(
    x=forecast_line_df["Month"],
    y=forecast_line_df["Forecast Sales"],
    mode="lines+markers",
    name="Forecast Sales",
    line=dict(color=COLOR_FORECAST, width=3, dash="dash"),
    marker=dict(size=6)
))

fig_combined.update_layout(
    xaxis_title="Month",
    yaxis_title="Sales",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=10, r=10, t=30, b=10)
)

st.plotly_chart(
    fig_combined,
    use_container_width=True,
    config={"displayModeBar": False},
    key="historical_vs_forecast_trend"
)

st.markdown("---")

# ------------------------------------------------------------------
# Monthly Forecast / Forecast by Category
# ------------------------------------------------------------------
left, right = st.columns(2)

monthly_forecast_display = forecast_df.copy()
monthly_forecast_display["Month Label"] = monthly_forecast_display["Month"].dt.strftime("%b %Y")

fig_monthly_forecast = px.bar(
    monthly_forecast_display,
    x="Month Label",
    y="Forecast Sales",
    color_discrete_sequence=[COLOR_FORECAST],
    text_auto=".2s",
    title="Monthly Forecast"
)
fig_monthly_forecast.update_layout(
    xaxis_title="Month",
    showlegend=False
)

category_forecast_rows = []
categories_for_forecast = (
    [category] if category != "All" else sorted(df["Category"].dropna().unique().tolist())
)

for cat in categories_for_forecast:
    if category == "All":
        cat_df = filtered_df[filtered_df["Category"] == cat]
    else:
        cat_df = filtered_df
    cat_monthly = build_monthly_series(cat_df)
    cat_forecast = moving_average_forecast(cat_monthly["Sales"].tolist())
    category_forecast_rows.append({
        "Category": cat,
        "Forecast Sales": float(np.sum(cat_forecast))
    })

category_forecast_df = pd.DataFrame(category_forecast_rows)

fig_category_forecast = px.bar(
    category_forecast_df,
    x="Category",
    y="Forecast Sales",
    color_discrete_sequence=[COLOR_PRODUCT],
    text_auto=".2s",
    title="Forecast by Category"
)
fig_category_forecast.update_layout(showlegend=False)

with left:
    st.plotly_chart(
        fig_monthly_forecast,
        use_container_width=True,
        config={"displayModeBar": False},
        key="monthly_forecast"
    )

with right:
    st.plotly_chart(
        fig_category_forecast,
        use_container_width=True,
        config={"displayModeBar": False},
        key="forecast_by_category"
    )

st.markdown("---")

# ------------------------------------------------------------------
# Forecast Table / Download CSV
# ------------------------------------------------------------------
st.subheader("Forecast Table")

forecast_table = forecast_df.copy()
forecast_table["Month"] = forecast_table["Month"].dt.strftime("%b %Y")

csv = forecast_table.to_csv(index=False).encode("utf-8")

forecast_table["Forecast Sales"] = (
    forecast_table["Forecast Sales"]
    .round(2)
    .map("${:,.2f}".format)
)

st.dataframe(forecast_table, use_container_width=True, hide_index=True)

st.download_button("⬇ Download Forecast Data", csv, "sales_forecast.csv", "text/csv")

st.markdown("---")
st.caption("Retail Intelligence Platform | Sales Forecasting Dashboard")