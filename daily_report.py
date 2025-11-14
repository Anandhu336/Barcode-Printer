#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# daily_report.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# --- Page Config ---
st.set_page_config(page_title="Daily Delivery Report", layout="wide")

st.title("🧾 Daily Delivery Report")
st.caption("Automatically summarizes today’s product deliveries from uploaded PO sheets.")

# --- File Upload Section ---
st.subheader("📦 Upload Today's PO Sheet")

uploaded_po = st.file_uploader("Upload your delivery PO sheet (CSV, XLSX, or PDF)", type=["csv", "xlsx", "pdf"])

if uploaded_po is None:
    st.info("Please upload a PO file to generate today's delivery report.")
    st.stop()

# --- Read PO Data ---
try:
    if uploaded_po.name.lower().endswith(".csv"):
        df = pd.read_csv(uploaded_po)
    elif uploaded_po.name.lower().endswith(".xlsx"):
        df = pd.read_excel(uploaded_po)
    elif uploaded_po.name.lower().endswith(".pdf"):
        from file_handler import read_po_file
        df, _ = read_po_file(uploaded_po)
    else:
        st.error("Unsupported file format.")
        st.stop()
except Exception as e:
    st.error(f"Error reading PO file: {e}")
    st.stop()

# --- Clean Columns ---
df.columns = [c.strip().title().replace(" ", "_") for c in df.columns]
expected_cols = ["Sku", "Product", "Location", "Outstanding"]

for col in expected_cols:
    if col not in df.columns:
        df[col] = None

df = df.dropna(subset=["Product"])
df["Outstanding"] = pd.to_numeric(df["Outstanding"], errors="coerce").fillna(0)

if df.empty:
    st.warning("No valid delivery data found in this PO sheet.")
    st.stop()

# --- Save for records ---
today = datetime.now().strftime("%Y-%m-%d")
save_dir = "data/delivery_reports"
os.makedirs(save_dir, exist_ok=True)
csv_path = os.path.join(save_dir, f"delivery_report_{today}.csv")
df.to_csv(csv_path, index=False)

# --- Key Metrics ---
st.markdown("## 📊 Delivery Summary")

total_products = len(df)
total_delivered = int(df["Outstanding"].sum())
unique_locations = df["Location"].nunique()

col1, col2, col3 = st.columns(3)
col1.metric("Delivered Products", total_products)
col2.metric("Total Units Delivered", total_delivered)
col3.metric("Locations Updated", unique_locations)

# --- Top Delivered Products ---
st.markdown("### 🚀 Top Delivered Products")
top_delivered = df.sort_values("Outstanding", ascending=False).head(10)

fig1 = px.bar(
    top_delivered,
    x="Outstanding",
    y="Product",
    color="Outstanding",
    text="Outstanding",
    orientation="h",  # Horizontal bars for readability
    title="Top 10 Delivered Products Today",
    color_continuous_scale="teal"
)

fig1.update_traces(textposition="outside")
fig1.update_layout(
    height=500,
    xaxis_title="Units Delivered",
    yaxis_title="Product Name",
    yaxis=dict(autorange="reversed"),  # Top product at top
    margin=dict(l=120, r=20, t=60, b=40),
    title_x=0.3,
    template="plotly_white"
)
st.plotly_chart(fig1, use_container_width=True)

# --- Deliveries by Location ---
if "Location" in df.columns and df["Location"].notna().any():
    st.markdown("### 🏭 Deliveries by Location")

    location_summary = df.groupby("Location", as_index=False)["Outstanding"].sum().sort_values("Outstanding", ascending=True)

    fig2 = px.bar(
        location_summary,
        x="Outstanding",
        y="Location",
        color="Outstanding",
        text="Outstanding",
        orientation="h",  # Horizontal layout for clarity (especially many locations)
        color_continuous_scale="Blues",
        title="Delivered Units per Location"
    )

    fig2.update_traces(textposition="outside")
    fig2.update_layout(
        height=600,
        xaxis_title="Units Delivered",
        yaxis_title="Location",
        margin=dict(l=120, r=20, t=60, b=40),
        title_x=0.3,
        template="plotly_white"
    )
    st.plotly_chart(fig2, use_container_width=True)

# --- Delivery Table ---
st.markdown("### 📋 Delivery Breakdown")
st.dataframe(df[["Product", "Sku", "Location", "Outstanding"]], use_container_width=True)

# --- Download Report ---
st.markdown("### 💾 Export Today's Report")

csv_export = df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="⬇️ Download Daily Delivery Report (CSV)",
    data=csv_export,
    file_name=f"daily_delivery_report_{today}.csv",
    mime="text/csv"
)

st.success(f"✅ Daily report generated for {today}")
st.markdown("---")
st.caption("Daily delivery summary auto-generated from uploaded PO sheet.")

