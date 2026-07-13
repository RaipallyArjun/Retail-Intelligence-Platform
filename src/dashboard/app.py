import streamlit as st

st.set_page_config(
    page_title="Retail Intelligence Platform",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Retail Intelligence Platform")

st.markdown("""
# Welcome!

This is the **Retail Intelligence Platform**.

Use the navigation panel on the left to explore:

- 🏠 Executive Dashboard
- 📈 Sales Analysis
- 👥 Customer Analysis
- 📦 Product Analysis
- 📉 Sales Forecasting
- 🎯 Customer Segmentation
- 💡 Product Recommendation
""")

st.divider()

col1,col2,col3,col4=st.columns(4)

col1.metric("Sales","2.30M")
col2.metric("Profit","286.40K")
col3.metric("Orders","5K")
col4.metric("Customers","793")

st.divider()

st.info("Select a page from the sidebar.")