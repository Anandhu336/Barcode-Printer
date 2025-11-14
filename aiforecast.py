#!/usr/bin/env python
# coding: utf-8

# In[2]:


# ai_sales_forecast.py
import streamlit as st
import pandas as pd
import plotly.express as px
import os
from prophet import Prophet

st.set_page_config(page_title="🤖 AI Sales Forecast", layout="wide")
st.title("📈 AI Forecast – Vape Sales Movement Trends")
st.caption("Forecasts next 7 days of sales and identifies fast, stable, or slow-moving products.")

# ---------- Load Sales Data ----------
# Use your actual data directory
DATA_DIR = "/Users/anandhu/Downloads/Barcode Printer/data/sales_reports"

if not os.path.exists(DATA_DIR):
    st.error(f"❌ The folder '{DATA_DIR}' does not exist.")
    st.stop()

csv_files = [os.path.join(DATA_DIR, f) for f in os.listdir(DATA_DIR) if f.endswith(".csv")]

if not csv_files:
    st.error("⚠️ No sales data found. Please make sure there are CSV files in the folder.")
    st.stop()

# Combine all CSVs into one dataframe
df_list = []
for f in csv_files:
    try:
        # Extract date from filename like 'sales_2025-10-25.csv'
        date_str = os.path.basename(f)
        date_match = None
        for pattern in [r"sales_(\d{4}-\d{2}-\d{2})", r"(\d{4}-\d{2}-\d{2})"]:
            import re
            m = re.search(pattern, date_str)
            if m:
                date_match = m.group(1)
                break

        if not date_match:
            st.warning(f"⚠️ Skipping file without date pattern: {f}")
            continue

        df = pd.read_csv(f)
        df["Date"] = pd.to_datetime(date_match)
        df_list.append(df)

    except Exception as e:
        st.warning(f"⚠️ Error reading {f}: {e}")

if not df_list:
    st.error("⚠️ No valid sales files loaded.")
    st.stop()

data = pd.concat(df_list, ignore_index=True)

# ---------- Clean Data ----------
if "Product" not in data.columns or "Sales_Units" not in data.columns:
    st.error("❌ Missing required columns: 'Product' and 'Sales_Units'.")
    st.stop()

data["Sales_Units"] = pd.to_numeric(data["Sales_Units"], errors="coerce").fillna(0)
data = data.dropna(subset=["Product"])
daily_sales = data.groupby(["Date", "Product"], as_index=False)["Sales_Units"].sum()

# ---------- Show Recent Data ----------
st.markdown("### 🧾 Recent Sales Data (Last 10 Days)")
st.dataframe(daily_sales.sort_values("Date").tail(10))

# ---------- Product Selection ----------
products = sorted(daily_sales["Product"].unique())
selected_product = st.selectbox("Select a product to forecast", products)

prod_data = daily_sales[daily_sales["Product"] == selected_product][["Date", "Sales_Units"]]
prod_data = prod_data.rename(columns={"Date": "ds", "Sales_Units": "y"})

if len(prod_data) < 5:
    st.warning("⚠️ Not enough data points to forecast reliably.")
    st.stop()

# ---------- Prophet Forecast ----------
m = Prophet(weekly_seasonality=True, daily_seasonality=False, seasonality_mode="additive")
m.fit(prod_data)
future = m.make_future_dataframe(periods=7)
forecast = m.predict(future)

# ---------- Rolling Average Adjustment ----------
forecast_plot = forecast[["ds", "yhat"]].merge(prod_data, on="ds", how="left")
forecast_plot["Adj_Forecast"] = (
    0.7 * forecast_plot["yhat"]
    + 0.3 * forecast_plot["y"].rolling(window=3, min_periods=1).mean().fillna(method="bfill")
)

# ---------- Visualization ----------
fig = px.line(
    forecast_plot,
    x="ds",
    y=["y", "Adj_Forecast"],
    labels={"ds": "Date", "value": "Sales Units"},
    title=f"📊 Forecasted Sales Trend – {selected_product}",
)
fig.update_layout(template="plotly_white", legend_title="Series")
st.plotly_chart(fig, use_container_width=True)

# ---------- Trend Classification ----------
last_actual = forecast_plot["y"].dropna().iloc[-1]
next_forecast = forecast_plot["Adj_Forecast"].iloc[-1]

trend = (
    "⚡ Fast Moving" if next_forecast > last_actual * 1.1
    else "🐢 Slow Moving" if next_forecast < last_actual * 0.9
    else "➖ Stable"
)
st.metric(label="Forecasted Product Trend", value=trend)

# ---------- Multi-Product Trend Summary ----------
st.markdown("### 📈 Fastest & Slowest Moving Products")

summary = (
    daily_sales.groupby("Product", as_index=False)["Sales_Units"].mean()
    .sort_values("Sales_Units", ascending=False)
)
summary["Movement"] = [
    "⚡ Fast" if i < len(summary) * 0.3 else "🐢 Slow" if i > len(summary) * 0.7 else "➖ Stable"
    for i in range(len(summary))
]

st.dataframe(summary)

st.markdown("---")
st.caption("AI Forecast v1.0 | Prophet + Rolling Average | Based on daily sales data")


# In[ ]:




