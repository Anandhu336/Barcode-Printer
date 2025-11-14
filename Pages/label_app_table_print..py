#!/usr/bin/env python
# coding: utf-8

# In[19]:


#!/usr/bin/env python3
# label_app_table_print.py
import streamlit as st
import pandas as pd
import io
import os
import math
import hashlib
import uuid
import re

from file_handler import read_po_file                 # your existing parser
from label_generator import create_label_image        # your label rendering function
from calc_labels import clean_rows                    # optional reuse

# --- Constants / folders ---
FINAL_LABEL_DIR = "labels/final_labels"
os.makedirs(FINAL_LABEL_DIR, exist_ok=True)

# --- Helpers ---
def parse_product_fields(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure Product, Flavour, Strength columns exist.
    Extract Flavour/Strength when Product contains '[Flavour / 20mg]'.
    """
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]
    for col in ["Sku", "Product", "Outstanding", "Case_Size", "Flavour", "Strength"]:
        if col not in df.columns:
            df[col] = pd.NA

    def extract(p):
        p = str(p or "")
        flavour = ""
        strength = ""
        m = re.search(r"\[(.*?)\]\s*$", p)
        if m:
            inside = m.group(1)
            # remove bracketed part from product
            p_clean = p[:m.start()].strip()
            parts = re.split(r"[/\-\|;]", inside)
            if len(parts) >= 1:
                flavour = parts[0].strip()
            if len(parts) >= 2:
                strength = parts[1].strip()
            return p_clean, flavour, strength
        return p, "", ""
    parsed = df.apply(lambda row: extract(row.get("Product","")), axis=1, result_type="expand")
    parsed.columns = ["_prod_clean", "_flavour_ex", "_strength_ex"]
    df["_prod_clean"] = parsed["_prod_clean"]
    df["_flavour_ex"] = parsed["_flavour_ex"]
    df["_strength_ex"] = parsed["_strength_ex"]

    # Fill final columns using fallback order: bracketed extract -> explicit column -> existing
    df["Product"] = df["_prod_clean"].where(df["_prod_clean"].notna() & (df["_prod_clean"] != ""), df["Product"])
    df["Flavour"] = df["_flavour_ex"].where(df["_flavour_ex"].notna() & (df["_flavour_ex"] != ""),
                                           df["Flavour"])
    df["Strength"] = df["_strength_ex"].where(df["_strength_ex"].notna() & (df["_strength_ex"] != ""),
                                             df["Strength"])
    # Clean up temp columns
    df = df.drop(columns=["_prod_clean","_flavour_ex","_strength_ex"])
    return df

def to_numeric_safe(s):
    try:
        v = pd.to_numeric(s, errors="coerce")
        return v
    except Exception:
        return s

def compute_final_labels(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Outstanding"] = pd.to_numeric(df.get("Outstanding", 0), errors="coerce").fillna(0)
    df["Case_Size"] = pd.to_numeric(df.get("Case_Size", math.nan), errors="coerce")
    def calc(row):
        cs = row.get("Case_Size")
        out = row.get("Outstanding", 0)
        if pd.notna(cs) and cs > 0 and out > 0:
            return int(math.ceil(out / cs))
        return 0
    df["Final_Labels"] = df.apply(calc, axis=1)
    return df

def df_hash(df: pd.DataFrame) -> str:
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return hashlib.md5(buf.getvalue().encode("utf-8")).hexdigest()

# --- Streamlit UI ---
st.set_page_config(page_title="Table -> Label Printer", layout="wide")
st.title("📋 → 🏷️ Build Table & Print Labels")

uploaded = st.file_uploader("Upload PO (CSV / XLSX / PDF)", type=["csv", "xlsx", "pdf"])
if not uploaded:
    st.info("Upload PO file (CSV/XLSX/PDF) to continue.")
    st.stop()

# read file using your existing helper
raw_df, path = read_po_file(uploaded)
if raw_df is None or raw_df.empty:
    st.error("Could not parse uploaded file. Check file format.")
    st.stop()

# clean and parse product/flavour/strength
raw_df = raw_df.copy()
raw_df = parse_product_fields(raw_df)
raw_df = clean_rows(raw_df)           # optional: drop empty rows
# ensure columns exist
for c in ["Sku","Product","Flavour","Strength","Outstanding","Case_Size"]:
    if c not in raw_df.columns:
        raw_df[c] = pd.NA

# Build the printable table with only desired columns
print_table = raw_df[["Sku","Product","Flavour","Strength","Outstanding","Case_Size"]].copy()

# convert numeric columns
print_table["Outstanding"] = pd.to_numeric(print_table["Outstanding"].astype(str).str.replace(",",""), errors="coerce").fillna(0)
print_table["Case_Size"] = pd.to_numeric(print_table["Case_Size"], errors="coerce")  # keep NaN where missing

# Initialize session state for editor table
if "print_table" not in st.session_state:
    # if Case_Size missing, we leave NaN; user can use default to fill/overwrite
    st.session_state["print_table"] = print_table
    st.session_state["table_hash"] = df_hash(print_table)

st.subheader("1) Review extracted table (edit Case_Size individually or overwrite all below)")
st.caption("Columns: Sku, Product, Flavour, Strength, Outstanding, Case_Size, Final_Labels")

# Default case-size control and overwrite option
col1, col2, col3 = st.columns([2,2,6])
with col1:
    default_cs = st.number_input("Default Case Size (used for overwrite)", min_value=1, value=60, step=1)
with col2:
    apply_all = st.button("Apply Default Case Size to ALL rows (overwrite Case_Size)")
with col3:
    st.write("Tip: edit Case_Size cells directly in the table to set per-row values.")

# If apply_all pressed -> overwrite entire column and recompute
if apply_all:
    df_tmp = st.session_state["print_table"].copy()
    df_tmp["Case_Size"] = int(default_cs)
    df_tmp = compute_final_labels(df_tmp)
    st.session_state["print_table"] = df_tmp
    st.session_state["table_hash"] = df_hash(df_tmp)
    st.success(f"Applied Case_Size = {default_cs} to all rows and recomputed Final_Labels.")

# Show editable table (data_editor)
editor_df = st.session_state["print_table"]
# Add Final_Labels for display
editor_df_display = compute_final_labels(editor_df)
# Use a key that depends on table_hash so the editor refreshes when we change the table in session_state
editor_key = f"print_table_editor_{st.session_state['table_hash']}"
edited = st.data_editor(editor_df_display, key=editor_key, use_container_width=True, num_rows="dynamic")

# Detect edits: compare hash
try:
    buf = io.StringIO()
    edited.to_csv(buf, index=False)
    edited_hash = hashlib.md5(buf.getvalue().encode("utf-8")).hexdigest()
except Exception:
    edited_hash = st.session_state.get("table_hash")

if edited_hash != st.session_state.get("table_hash"):
    # User edited the table: preserve per-row Case_Size but recompute Final_Labels
    updated = edited.copy()
    # Ensure numeric types
    updated["Outstanding"] = pd.to_numeric(updated.get("Outstanding", 0), errors="coerce").fillna(0)
    updated["Case_Size"] = pd.to_numeric(updated.get("Case_Size"), errors="coerce")
    updated = compute_final_labels(updated)
    st.session_state["print_table"] = updated[["Sku","Product","Flavour","Strength","Outstanding","Case_Size","Final_Labels"]]
    st.session_state["table_hash"] = df_hash(st.session_state["print_table"])
    st.experimental_rerun()

# stable view
final_table = st.session_state["print_table"]
st.markdown("**Final printable table:**")
st.dataframe(final_table, use_container_width=True)

# ---------------------------
# 2) Select rows to generate labels from table
# ---------------------------
st.subheader("2) Select rows to generate labels from this table")

# Multi-select by Sku + Product (present unique options)
final_table["__label_key"] = final_table["Sku"].astype(str) + " — " + final_table["Product"].astype(str)
choices = list(final_table["__label_key"].astype(str))
selected = st.multiselect("Choose rows to generate labels for (select none to pick all)", options=choices, default=choices[:5] if len(choices)>0 else [])

if not selected:
    to_generate = final_table.copy()
else:
    to_generate = final_table[final_table["__label_key"].isin(selected)].copy()

# Confirm final labels counts and optionally override per-row print count
to_generate["Planned_Labels"] = to_generate["Final_Labels"].fillna(0).astype(int)
st.write("You can change 'Planned_Labels' to print a different number (e.g. for test).")
to_generate_edit = st.data_editor(to_generate[["Sku","Product","Flavour","Strength","Outstanding","Case_Size","Planned_Labels"]],
                                  num_rows="dynamic", key=f"plan_editor_{st.session_state['table_hash']}", use_container_width=True)

# Prepare final generation df
gen_df = to_generate_edit.copy()
gen_df["Planned_Labels"] = pd.to_numeric(gen_df.get("Planned_Labels",0), errors="coerce").fillna(0).astype(int)

# Generate labels button
if st.button("🎨 Generate & Preview Labels from table selection"):
    all_paths = []
    with st.spinner("Generating label images from selection..."):
        for ridx, r in gen_df.iterrows():
            # find original row data to pass other fields (SKU etc)
            sku = str(r.get("Sku",""))
            # get matching row from final_table to preserve original Product/Flavour/Strength/Case_Size/Outstanding
            row_match = final_table[final_table["Sku"].astype(str)==sku]
            if row_match.shape[0] >= 1:
                row = row_match.iloc[0].to_dict()
            else:
                row = r.to_dict()
            n = int(r.get("Planned_Labels", 0) or 0)
            for i in range(n):
                try:
                    # call external label generator (your module)
                    path = create_label_image(row, idx=f"{sku}_{i}", label_cm=10.0, dpi=300)
                    all_paths.append(path)
                except Exception as e:
                    st.error(f"Failed to create label for SKU={sku}: {e}")
    if not all_paths:
        st.warning("No labels created.")
    else:
        st.success(f"Created {len(all_paths)} label images.")
        # Save into session_state and show previews
        st.session_state["generated_labels"] = all_paths
        # Show first 12 previews
        preview = all_paths[:12]
        st.markdown("### Previews")
        cols = st.columns(min(4,len(preview)))
        for c,p in zip(cols, preview):
            try:
                c.image(p, use_container_width=True, caption=os.path.basename(p))
            except Exception:
                c.write(os.path.basename(p))

# If generated labels exist show list and option to open externally
if st.session_state.get("generated_labels"):
    st.markdown("### Generated labels (recent)")
    for p in st.session_state["generated_labels"][:50]:
        st.write(p)

    if st.button("Open first generated label externally"):
        try:
            import subprocess, sys
            fp = st.session_state["generated_labels"][0]
            if sys.platform.startswith("darwin"):
                subprocess.run(["open", "-a", "Preview", fp])
            elif sys.platform.startswith("linux"):
                subprocess.Popen(["xdg-open", fp])
            else:
                os.startfile(fp)
            st.success("Opened preview in external viewer.")
        except Exception as e:
            st.error(f"Cannot open preview: {e}")

st.write("----")
st.write("After you confirm labels, use your printing UI (or the print_file helper) to send images to the label printer.")


# In[ ]:




