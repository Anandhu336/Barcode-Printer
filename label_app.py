#!/usr/bin/env python
# coding: utf-8

# In[ ]:


#!/usr/bin/env python3
# label_app.py — Streamlit Label Printing and Preview System (with robust normalization)

import streamlit as st
import pandas as pd
import os
import uuid
import io
import hashlib
import subprocess
import sys
import time
import re
from math import ceil
from typing import Optional

from file_handler import read_po_file
from calc_labels import apply_default_case_size, compute_final_labels, clean_rows
from label_generator import create_label_image  # external generator expected (must accept idx, label_cm, dpi)

# --- Folders ---
BARCODE_DIR = "labels/barcodes"
FINAL_LABEL_DIR = "labels/final_labels"
os.makedirs(BARCODE_DIR, exist_ok=True)
os.makedirs(FINAL_LABEL_DIR, exist_ok=True)

# --- Utilities ---
def safe_rerun():
    try:
        if hasattr(st, "experimental_rerun"):
            st.experimental_rerun()
            return
        if hasattr(st, "rerun"):
            st.rerun()
            return
    except Exception:
        pass
    st.info("UI updated. If you don't see changes, interact (edit a cell or click a button).")

def df_hash(df: pd.DataFrame) -> str:
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return hashlib.md5(buf.getvalue().encode("utf-8")).hexdigest()

def _is_missing_val(x) -> bool:
    # Safe missing check for pd.NA, None, "", "None", etc.
    if x is None:
        return True
    if pd.isna(x):
        return True
    s = str(x).strip()
    return s == "" or s.lower() in ("none", "nan", "na")

# === Normalizer / extractor ===
def extract_from_product_field(product_text: str):
    """
    If product_text ends with "[flavour / strength]" or similar,
    returns (clean_product, flavour, strength). Always returns strings.
    """
    if not isinstance(product_text, str):
        return (str(product_text or ""), "", "")
    s = product_text.strip()
    if s == "":
        return ("", "", "")
    m = re.search(r"\[([^\]]+)\]\s*$", s)
    if not m:
        return (s, "", "")
    inside = m.group(1).strip()
    cleaned = s[:m.start()].strip()
    parts = re.split(r"\s*[/\-\|;]\s*", inside)
    flavour = parts[0].strip() if len(parts) >= 1 else ""
    strength = parts[1].strip() if len(parts) >= 2 else ""
    return (cleaned, flavour, strength)

def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Defensive normalization:
      - ensures Product/Flavour/Strength exist,
      - extracts bracketed flavour/strength from Product if present,
      - only fills Flavour/Strength when empty,
      - returns a copy.
    """
    d = df.copy().reset_index(drop=True)

    # ensure columns exist
    for c in ("Sku", "Product", "Flavour", "Strength", "Outstanding", "Case_Size"):
        if c not in d.columns:
            d[c] = pd.NA

    # Work with strings safely for extraction
    # Temporarily fill with empty strings to avoid pd.NA boolean issues
    d[["Product", "Flavour", "Strength"]] = d[["Product", "Flavour", "Strength"]].fillna("")

    for i, row in d.iterrows():
        prod_raw = str(row.get("Product") or "").strip()
        cur_flavour = str(row.get("Flavour") or "").strip()
        cur_strength = str(row.get("Strength") or "").strip()

        cleaned_prod, ext_flavour, ext_strength = extract_from_product_field(prod_raw)

        # if bracketed info existed, cleaned_prod differs from prod_raw
        if cleaned_prod and cleaned_prod != prod_raw:
            d.at[i, "Product"] = cleaned_prod

        if (cur_flavour == "" or cur_flavour is None) and ext_flavour:
            d.at[i, "Flavour"] = ext_flavour
        if (cur_strength == "" or cur_strength is None) and ext_strength:
            d.at[i, "Strength"] = ext_strength

    # convert empty strings back to pd.NA for Flavour/Strength (keep Product as string)
    for c in ("Flavour", "Strength"):
        d[c] = d[c].replace("", pd.NA)

    return d

# ---------------------------
# Data helpers for UI flows
# ---------------------------
def overwrite_case_size_all(df_in: pd.DataFrame, case_size_value: int) -> pd.DataFrame:
    d = df_in.copy()
    d["Case_Size"] = case_size_value
    d["Outstanding"] = pd.to_numeric(d.get("Outstanding", 0), errors="coerce").fillna(0)
    d = clean_rows(d)
    d = compute_final_labels(d)
    return d

def normalize_preserve_case_and_recompute(df_in: pd.DataFrame, default_cs: int) -> pd.DataFrame:
    d = df_in.copy()
    d["Outstanding"] = pd.to_numeric(d.get("Outstanding", 0), errors="coerce").fillna(0)
    if "Case_Size" in d.columns:
        d["Case_Size"] = pd.to_numeric(d["Case_Size"], errors="coerce").fillna(default_cs)
    else:
        d["Case_Size"] = default_cs
    d = clean_rows(d)
    d = compute_final_labels(d)
    return d

def list_final_label_files():
    files = []
    if os.path.isdir(FINAL_LABEL_DIR):
        for fname in sorted(os.listdir(FINAL_LABEL_DIR)):
            if fname.lower().endswith((".png", ".jpg", ".jpeg")):
                files.append(os.path.join(FINAL_LABEL_DIR, fname))
    return files

def open_preview(path):
    try:
        if sys.platform.startswith("darwin"):
            subprocess.Popen(["qlmanage", "-p", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif sys.platform.startswith("linux"):
            subprocess.Popen(["xdg-open", path])
        else:
            os.startfile(path)
        return True
    except Exception:
        return False

# ---------------------------
# Streamlit UI
# ---------------------------
st.set_page_config(page_title="Label Printing", layout="wide")
st.title("🏷️ Label Printing and Preview System")

# --- Upload ---
uploaded = st.file_uploader("Upload Purchase Order (CSV / XLSX / PDF)", type=["csv", "xlsx", "pdf"])
if not uploaded:
    st.info("Upload a purchase order file to continue.")
    st.stop()

df, path = read_po_file(uploaded)
if df is None or df.empty:
    st.error("Could not parse uploaded file. Check file format.")
    st.stop()

# sanitize column names and ensure expected columns exist
df.columns = [c.strip() for c in df.columns]
for col in ["Sku", "Product", "Location", "Outstanding", "Case_Size", "Flavour", "Strength"]:
    if col not in df.columns:
        df[col] = pd.NA

# run initial clean_rows (removes fully empty rows, trims strings, etc.)
df = clean_rows(df)

# IMPORTANT: normalize/extract flavour & strength here (before computing defaults)
df = normalize_df(df)

# DEBUG: optional toggle to inspect normalization results
if st.checkbox("Show normalized Product/Flavour/Strength (debug)", value=False):
    st.dataframe(df[["Sku", "Product", "Flavour", "Strength", "Outstanding", "Case_Size"]].head(50), use_container_width=True)

# --- Review & edit table ---
st.subheader("✏️ Review, edit and finalise labels")
st.caption("Change Default Case Size = overwrite all Case_Size. Editing the table recalculates Final_Labels.")

default_cs = st.number_input("Default Case Size (apply to ALL rows if changed)", min_value=1, value=60, step=1, key="default_case_input")

# --- Initialize session state safely ---
if "editor_df" not in st.session_state:
    base = apply_default_case_size(df.copy(), default_cs)
    base = clean_rows(base)
    base = compute_final_labels(base)
    st.session_state["editor_df"] = base

if "editor_hash" not in st.session_state:
    buf = io.StringIO()
    st.session_state["editor_df"].to_csv(buf, index=False)
    st.session_state["editor_hash"] = hashlib.md5(buf.getvalue().encode("utf-8")).hexdigest()

st.session_state.setdefault("last_default_cs", default_cs)
st.session_state.setdefault("generated_labels", [])
st.session_state.setdefault("label_names", {})
st.session_state.setdefault("print_statuses", {})
st.session_state.setdefault("selected_labels", [])

# If default case size changed -> overwrite all case sizes & recompute
if default_cs != st.session_state.get("last_default_cs", None):
    tmp = overwrite_case_size_all(st.session_state["editor_df"], default_cs)
    st.session_state["editor_df"] = tmp
    buf = io.StringIO()
    tmp.to_csv(buf, index=False)
    st.session_state["editor_hash"] = hashlib.md5(buf.getvalue().encode("utf-8")).hexdigest()
    st.session_state["last_default_cs"] = default_cs
    st.success(f"Applied Default Case Size = {default_cs} to all rows and recalculated Final_Labels.")
    safe_rerun()

# Editable table (key includes hash to force rebuild when df changes)
editor_df = st.session_state["editor_df"]
editor_key = f"editor_{st.session_state['editor_hash']}"
edited = st.data_editor(editor_df, num_rows="dynamic", use_container_width=True, key=editor_key)

# detect edits via hash and recompute
try:
    buf2 = io.StringIO()
    edited.to_csv(buf2, index=False)
    edited_hash = hashlib.md5(buf2.getvalue().encode("utf-8")).hexdigest()
except Exception:
    edited_hash = st.session_state.get("editor_hash", "")

if edited_hash != st.session_state.get("editor_hash", ""):
    # apply numeric coercion, preserve user-entered case sizes, fill missing with default_cs, recompute labels
    updated = normalize_preserve_case_and_recompute(edited.copy(), default_cs)
    st.session_state["editor_df"] = updated
    buf3 = io.StringIO()
    updated.to_csv(buf3, index=False)
    st.session_state["editor_hash"] = hashlib.md5(buf3.getvalue().encode("utf-8")).hexdigest()
    st.success("Table edited — Final_Labels recalculated.")
    safe_rerun()

# Final preview of the computed table
final_df = st.session_state["editor_df"]
st.success("✅ Current final labels calculated from the table below.")
st.markdown("**Final Labels Preview**")
st.dataframe(final_df, use_container_width=True)

# -------------------------
# Generate Labels button
# -------------------------
st.subheader("🎨 Generate Labels")
if st.button("Generate Label Images"):
    # clear previous images
    for d in (BARCODE_DIR, FINAL_LABEL_DIR):
        if os.path.isdir(d):
            for f in os.listdir(d):
                try:
                    os.remove(os.path.join(d, f))
                except Exception:
                    pass

    all_labels = []
    with st.spinner("Generating label images..."):
        for idx, row in final_df.iterrows():
            try:
                n = int(row.get("Final_Labels", 0) or 0)
            except Exception:
                n = 0
            for i in range(n):
                try:
                    # create_label_image should return a path
                    label_path = create_label_image(row, idx=f"{idx}_{i}", label_cm=10.0, dpi=300)
                    if isinstance(label_path, str) and os.path.exists(label_path):
                        all_labels.append(label_path)
                except Exception as e:
                    # do not crash whole process; log and continue
                    st.warning(f"Label creation failed for row {idx} #{i}: {e}")

    if not all_labels:
        st.warning("⚠️ No labels generated.")
    else:
        st.session_state["generated_labels"] = all_labels
        st.session_state["label_names"] = {p: f"Label {i+1}" for i, p in enumerate(all_labels)}
        for p in all_labels:
            st.session_state["print_statuses"].setdefault(p, "Ready" if os.path.exists(p) else "Missing")
        st.success(f"✅ {len(all_labels)} labels created successfully.")
        safe_rerun()

# Quick previews
gen = st.session_state.get("generated_labels", [])
if gen:
    st.markdown("### 🖼️ Sample Previews")
    preview = gen[:6]
    cols = st.columns(len(preview))
    for c, p in zip(cols, preview):
        try:
            c.image(p, use_container_width=True, caption=os.path.basename(p))
        except Exception:
            c.write(os.path.basename(p))

# -------------------------
# Print & preview management (compact)
# -------------------------
st.subheader("🖨️ Preview & Print Management")

def list_printers():
    try:
        if sys.platform.startswith("darwin") or sys.platform.startswith("linux"):
            out = subprocess.check_output(["lpstat", "-p"], stderr=subprocess.DEVNULL).decode("utf-8")
            return [line.split()[1] for line in out.splitlines() if line.startswith("printer")]
    except Exception:
        return []
    return []

available_printers = list_printers()
printer_choice = None
if available_printers:
    printer_choice = st.selectbox("Select Printer (optional)", options=[None] + available_printers, format_func=lambda x: x or "Default Printer")

def get_label_source_list():
    gen = st.session_state.get("generated_labels", [])
    return gen or list_final_label_files()

source_files = get_label_source_list()
for p in source_files:
    st.session_state["print_statuses"].setdefault(p, "Ready" if os.path.exists(p) else "Missing")

# Search, paging
st.markdown("### Labels List (Search, Filter, Paginate)")
q = st.text_input("Search labels", value="", placeholder="Type to filter", key="search_q")
status_filter = st.selectbox("Show status", ["All", "Ready", "Printed", "Dialog shown", "Failed", "Missing"], index=0)
page_size = st.number_input("Items per page", min_value=5, max_value=50, value=10, step=5)

def matches(p, qstr):
    name = os.path.basename(p)
    return (qstr.strip() == "") or (qstr.lower() in name.lower())

filtered = [p for p in source_files if matches(p, q)]
if status_filter != "All":
    filtered = [p for p in filtered if st.session_state["print_statuses"].get(p, "Missing") == status_filter]

total = len(filtered)
total_pages = max(1, ceil(total / page_size))
page = st.number_input("Page", min_value=1, max_value=total_pages, value=1)
start = (page - 1) * page_size
page_items = filtered[start:start + page_size]

col1, col2, col3, col4 = st.columns([2,1,1,1])
with col1:
    if st.button("Select All on Page"):
        sel = set(st.session_state.get("selected_labels", []))
        sel.update(page_items)
        st.session_state["selected_labels"] = list(sel)
    if st.button("Clear Selection"):
        st.session_state["selected_labels"] = []
with col2:
    if st.button("Preview Selected"):
        sel = st.session_state.get("selected_labels", []).copy()
        if not sel:
            st.warning("No labels selected.")
        else:
            opened = 0
            for p in sel:
                if open_preview(p):
                    opened += 1
            st.success(f"Opened {opened} preview(s).")
with col3:
    if st.button("Print Selected"):
        sel = st.session_state.get("selected_labels", []).copy()
        if not sel:
            st.warning("No labels selected.")
        else:
            for p in sel:
                try:
                    if sys.platform.startswith("darwin"):
                        subprocess.run(["osascript", "-e", f'tell application "Preview" to open POSIX file "{os.path.abspath(p)}"'], check=False)
                        time.sleep(0.6)
                        subprocess.run(["osascript", "-e", 'tell application "Preview" to print front document with print dialog'], check=False)
                        st.session_state["print_statuses"][p] = "Dialog shown"
                    else:
                        subprocess.run(["lp", p], check=False)
                        st.session_state["print_statuses"][p] = "Printed"
                except Exception as e:
                    st.error(f"Printing failed for {os.path.basename(p)}: {e}")
                    st.session_state["print_statuses"][p] = f"Failed: {e}"
            safe_rerun()
with col4:
    st.write(f"Showing {start+1}–{min(start+page_size,total)} of {total}")

st.markdown("---")

for i, p in enumerate(page_items, start=1):
    cols = st.columns([4,1,1,1])
    cb = cols[0].checkbox(f"{st.session_state.get('label_names', {}).get(p, os.path.basename(p))}", value=p in st.session_state["selected_labels"], key=f"cb_{start+i}")
    if cb:
        if p not in st.session_state["selected_labels"]:
            st.session_state["selected_labels"].append(p)
    else:
        if p in st.session_state["selected_labels"]:
            st.session_state["selected_labels"].remove(p)

    if cols[1].button("Preview", key=f"pv_{start+i}"):
        open_preview(p)
    if cols[2].button("Print", key=f"pr_{start+i}"):
        try:
            if sys.platform.startswith("darwin"):
                subprocess.run(["osascript", "-e", f'tell application "Preview" to open POSIX file "{os.path.abspath(p)}"'], check=False)
                time.sleep(0.6)
                subprocess.run(["osascript", "-e", 'tell application "Preview" to print front document with print dialog'], check=False)
                st.session_state["print_statuses"][p] = "Dialog shown"
            else:
                subprocess.run(["lp", p], check=False)
                st.session_state["print_statuses"][p] = "Printed"
            safe_rerun()
        except Exception as e:
            st.error(f"Print failed: {e}")
            st.session_state["print_statuses"][p] = f"Failed: {e}"

    status = st.session_state["print_statuses"].get(p, "Missing")
    cols[3].write(status)

st.markdown("---")
st.caption("End of label management system.")

