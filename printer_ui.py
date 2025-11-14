#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# app.py
import os
from pathlib import Path
import pandas as pd
import streamlit as st

from file_handler import read_po_file
from calculation import calculate_final_labels
from label_generator import generate_sticker_labels, print_labels_ui, DEFAULT_OUTPUT_DIR

st.set_page_config(page_title="Warehouse Label System", layout="wide")
st.title("🏷️ Warehouse Barcode Label System (Full Flow)")
st.caption("Upload PO (csv/xlsx/pdf), calculate labels, generate images and print.")

UPLOAD_DIR = Path("data/po_uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

uploaded = st.file_uploader("Upload PO file (csv, xlsx, pdf)", type=["csv","xlsx","xls","pdf"])
if uploaded is None:
    st.info("Please upload a file to begin.")
    st.stop()

df, save_path = read_po_file(uploaded)
if df is None or df.empty:
    st.error("File read failed or empty.")
    st.stop()

# Normalize similar to original
df.columns = [c.strip().title().replace(" ", "_") for c in df.columns]
for col in ["Product","Flavour","Count","Outstanding","Receiving","Case_Size","Arm_Id","Sku","Final_Labels"]:
    if col not in df.columns:
        df[col] = None

st.subheader("Raw imported data (first 15 rows)")
st.dataframe(df.head(15), use_container_width=True)

# default case size
st.subheader("Case size (default)")
default_case_size = st.number_input("Default Case Size (used when Case_Size missing)", min_value=1, value=60)
df["Case_Size"] = df["Case_Size"].fillna(default_case_size)

# calculate
calculated = calculate_final_labels(df)
st.subheader("Calculated Final Labels (preview)")
st.dataframe(calculated.head(20), use_container_width=True)

# allow editing
st.subheader("Review & Edit (if needed)")
edited = st.data_editor(calculated, key="editable_table", num_rows="dynamic", use_container_width=True)
final_df = calculate_final_labels(edited)
final_df = final_df.dropna(subset=["Sku"], how="any")
final_df = final_df[final_df["Final_Labels"].notna()]
st.subheader("Final table ready for label generation")
st.dataframe(final_df.head(20), use_container_width=True)

# generate labels
st.subheader("Generate labels (images)")
label_size_mm = st.selectbox("Label size (mm, square)", [40,50,60,70,80], index=2)
if st.button("Generate labels from table"):
    with st.spinner("Generating labels..."):
        labels_df = generate_sticker_labels(final_df, label_size_mm=int(label_size_mm), output_dir=str(DEFAULT_OUTPUT_DIR))
        if labels_df is None or labels_df.empty:
            st.warning("No labels created — check Final_Labels and Sku.")
        else:
            st.success(f"Created {len(labels_df)} label images in {DEFAULT_OUTPUT_DIR/'final_labels'}")
            st.session_state["labels_df"] = labels_df

st.markdown("---")
st.subheader("Print / Preview")
if "labels_df" in st.session_state:
    print_labels_ui(st.session_state["labels_df"], default_preview_count=1)
else:
    files = sorted(Path(DEFAULT_OUTPUT_DIR).glob("final_labels/*.png"))
    if files:
        st.write(f"Found {len(files)} final label images in {DEFAULT_OUTPUT_DIR/'final_labels'}")
        data = [{"Sku": f.stem.split("_")[0] if "_" in f.stem else f.stem, "Product": f.stem, "Label_Path": str(f)} for f in files]
        st.session_state["labels_df"] = pd.DataFrame(data)
        print_labels_ui(st.session_state["labels_df"], default_preview_count=1)
    else:
        st.info("No label images found — generate from CSV/PDF or drop images into labels/stickers/final_labels/")

