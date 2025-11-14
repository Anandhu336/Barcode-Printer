#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# stock_dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import os
import datetime as dt
from thefuzz import fuzz

# --- Page Config ---
st.set_page_config(page_title="Warehouse Stock Dashboard", layout="wide")

st.title("📊 Warehouse Live Stock Dashboard")
st.caption("Visualize and analyze real-time stock levels across all aisles and locations.")

# --- Load or Upload Data ---
DATA_PATH = "data/warehouse_stock.csv"
os.makedirs("data", exist_ok=True)

st.sidebar.header("📂 Data Source")

if not os.path.exists(DATA_PATH):
    st.warning("No stock database found. Please upload one to start.")
    stock_file = st.sidebar.file_uploader("Upload stock data (CSV)", type=["csv"])
    if stock_file:
        df = pd.read_csv(stock_file)
        df.to_csv(DATA_PATH, index=False)
        st.success("✅ Stock data uploaded and saved.")
    else:
        st.stop()
else:
    df = pd.read_csv(DATA_PATH)

# --- Data Cleaning ---
df.columns = [c.strip().title().replace(" ", "_") for c in df.columns]
if "Outstanding" not in df.columns:
    st.error("Missing 'Outstanding' column in your data.")
    st.stop()

df["Outstanding"] = pd.to_numeric(df["Outstanding"], errors="coerce").fillna(0)
df = df.dropna(subset=["Product", "Location"]).reset_index(drop=True)

# --- Sidebar Filters ---
st.sidebar.header("🔍 Filters")

aisles = sorted(df["Aisle"].dropna().unique()) if "Aisle" in df.columns else []
selected_aisle = st.sidebar.selectbox("Select Aisle", ["All"] + aisles)

status_list = ["Received", "In Transit", "Out of Stock"]
if "Status" not in df.columns:
    df["Status"] = "Received"

selected_status = st.sidebar.multiselect("Filter by Stock Status", status_list, default=status_list)
search_query = st.sidebar.text_input("Search Product / SKU / Location")

# --- Filter Logic ---
filtered_df = df.copy()
if selected_aisle != "All":
    filtered_df = filtered_df[filtered_df["Aisle"] == selected_aisle]
if selected_status:
    filtered_df = filtered_df[filtered_df["Status"].isin(selected_status)]

# --- Smart Fuzzy Search ---
def fuzzy_match(row_text, query):
    """Return True if query roughly matches text (case-insensitive, typo-tolerant, any word order)."""
    if not isinstance(row_text, str) or not isinstance(query, str):
        return False
    row_text = row_text.lower()
    query = query.lower()

    # Word-based loose matching
    query_words = query.split()
    if all(word in row_text for word in query_words):
        return True

    # Fuzzy ratio for typos or partial matches
    return fuzz.token_set_ratio(row_text, query) >= 70


if search_query.strip():
    searchable_cols = ["Product", "Location"]
    if "Sku" in filtered_df.columns:
        searchable_cols.append("Sku")

    mask = filtered_df.apply(
        lambda row: any(fuzzy_match(str(row[col]), search_query) for col in searchable_cols),
        axis=1
    )

    filtered_df = filtered_df[mask]

if filtered_df.empty:
    st.info("No matching records found for the selected filters.")
    st.stop()

# --- Low Stock Alerts ---
st.sidebar.header("⚠️ Stock Alert Settings")
low_stock_threshold = st.sidebar.number_input("Low Stock Threshold", min_value=1, value=100, step=10)
filtered_df["Alert"] = filtered_df["Outstanding"].apply(
    lambda x: "🔴 LOW" if x < low_stock_threshold else
              "🟡 Medium" if x < low_stock_threshold * 1.5 else
              "🟢 OK"
)

# --- Metrics ---
st.markdown("### 📈 Stock Summary Overview")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Stock", int(filtered_df["Outstanding"].sum()))
col2.metric("Unique Products", filtered_df["Product"].nunique())
col3.metric("Active Locations", filtered_df["Location"].nunique())
col4.metric("Low Stock Items", (filtered_df['Alert'] == "🔴 LOW").sum())

# --- Visualization 1: Stock per Location ---
st.markdown("### 🏭 Stock by Location")

fig = px.bar(
    filtered_df,
    x="Location",
    y="Outstanding",
    color="Alert",
    text="Outstanding",
    hover_data={
        "Product": True,
        "Status": True,
        "Alert": True,
        "Outstanding": True
    },
    color_discrete_map={
        "🔴 LOW": "red",
        "🟡 Medium": "orange",
        "🟢 OK": "green"
    },
    title=f"Stock Distribution {'(All Aisles)' if selected_aisle == 'All' else f'in Aisle {selected_aisle}'}"
)

fig.update_traces(
    textposition="outside",
    hovertemplate=(
        "<b>📍 Location:</b> %{x}<br>"
        "<b>🧾 Product:</b> %{customdata[0]}<br>"
        "<b>🚚 Status:</b> %{customdata[1]}<br>"
        "<b>📦 Stock:</b> %{y} units<br>"
        "<b>⚠️ Alert:</b> %{customdata[2]}<extra></extra>"
    )
)

# --- 🖤 Hover Fix for Readability ---
fig.update_layout(
    hoverlabel=dict(
        bgcolor="rgba(50, 50, 50, 0.9)",   # dark hover background
        font_color="white",
        font_size=13,
        font_family="Arial"
    ),
    height=600,
    xaxis_title="Location",
    yaxis_title="Outstanding Units",
    template="plotly_white",
    title_x=0.3
)

st.plotly_chart(fig, use_container_width=True)

# --- Visualization 2: Top 10 Products ---
# --- Visualization 2: Top 10 Products ---
st.markdown("##overstock product by  Quantity")

top10 = filtered_df.nlargest(10, "Outstanding")

fig_top = px.bar(
    top10,
    x="Product",
    y="Outstanding",
    color="Outstanding",
    text="Outstanding",
    color_continuous_scale="Blues",
    title="Top 10 Products by Quantity"
)

fig_top.update_traces(textposition="outside")

# ✅ Keep product names straight and readable
fig_top.update_layout(
    xaxis=dict(
        tickangle=0,  # 0 = straight labels
        tickfont=dict(size=12),
        automargin=True
    ),
    yaxis_title="Outstanding Units",
    xaxis_title="Product",
    hoverlabel=dict(
        bgcolor="rgba(50, 50, 50, 0.9)",
        font_color="white",
        font_size=13,
        font_family="Arial"
    ),
    height=500,
    template="plotly_white"
)

st.plotly_chart(fig_top, use_container_width=True)

# --- Visualization 3: Stock Trend (if Date column exists) ---
if "Date" in filtered_df.columns:
    st.markdown("### ⏳ Stock Trend Over Time")
    trend_df = filtered_df.groupby("Date")["Outstanding"].sum().reset_index()
    fig_trend = px.line(trend_df, x="Date", y="Outstanding", title="Stock Trend Over Time", markers=True)
    st.plotly_chart(fig_trend, use_container_width=True)

# --- Detailed Data Table ---
with st.expander("📋 View Detailed Stock Data"):
    st.dataframe(filtered_df, use_container_width=True)

# --- Export Button ---
csv_export = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button("💾 Download Filtered Data (CSV)", csv_export, "filtered_stock.csv", "text/csv")

st.markdown("---")
st.caption("Warehouse Dashboard v2.1 | Smart fuzzy search, alerts, and live analytics.")

