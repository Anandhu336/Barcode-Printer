#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# pdf_converter.py
import pdfplumber
import pandas as pd
import os
import streamlit as st
import re

def clean_header(headers):
    headers = [str(h).strip() if h else "" for h in headers]
    seen = {}
    new = []
    for h in headers:
        if h == "":
            h = "Extra"
        if h in seen:
            seen[h] += 1
            new.append(f"{h}_{seen[h]}")
        else:
            seen[h] = 1
            new.append(h)
    return new

def ensure_unique_columns(columns):
    seen = {}
    unique = []
    for c in columns:
        if c in seen:
            seen[c] += 1
            unique.append(f"{c}_{seen[c]}")
        else:
            seen[c] = 1
            unique.append(c)
    return unique

def read_pdf_with_plumber(pdf_path):
    all_tables = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                tables = page.extract_tables()
                if not tables:
                    continue
                for t in tables:
                    if not t:
                        continue
                    df = pd.DataFrame(t)
                    header_row = None
                    for j, row in df.iterrows():
                        if any(str(x).strip() for x in row):
                            header_row = j
                            break
                    if header_row is not None:
                        headers = clean_header(df.iloc[header_row].tolist())
                        df = df.iloc[header_row + 1 :].reset_index(drop=True)
                        df.columns = headers
                    else:
                        df.columns = [f"Col_{x}" for x in range(len(df.columns))]
                    df.columns = ensure_unique_columns(df.columns)
                    df["Page"] = i
                    all_tables.append(df)
    except Exception as e:
        st.error(f"PDF read error: {e}")
        return pd.DataFrame()

    if not all_tables:
        return pd.DataFrame()
    try:
        df = pd.concat(all_tables, ignore_index=True)
    except Exception as e:
        st.error(f"PDF merge error: {e}")
        return pd.DataFrame()
    return df

def standardize_columns(df):
    rename_map = {
        "code": "Sku", "sku": "Sku", "product code": "Sku", "item code": "Sku",
        "description": "Product", "product": "Product", "product description": "Product",
        "cost price": "Cost_Price", "barcode": "Barcode", "location": "Location",
        "outstanding": "Outstanding", "qty": "Outstanding", "quantity": "Outstanding",
        "case size": "Case_Size", "case_size": "Case_Size"
    }
    clean_cols = []
    for c in df.columns:
        cname = str(c).strip().lower()
        mapped = cname
        for k, v in rename_map.items():
            if k in cname:
                mapped = v
                break
        clean_cols.append(mapped)
    df.columns = clean_cols
    return df

def convert_pdf_to_csv(pdf_path):
    """
    Reads PDF, extracts tables, standardizes, saves CSV in same dir with suffix _extracted.csv
    """
    df = read_pdf_with_plumber(pdf_path)
    if df.empty:
        return None
    df = standardize_columns(df)
    df.columns = ensure_unique_columns(df.columns)
    # keep relevant cols if present
    keep_cols = ["Sku","Product","Cost_Price","Barcode","Location","Outstanding","Case_Size"]
    df = df[[c for c in df.columns if c in keep_cols]]
    if "Outstanding" in df.columns:
        df["Outstanding"] = df["Outstanding"].astype(str).str.replace(",","")
        df["Outstanding"] = df["Outstanding"].str.extract(r"(\d+)", expand=False)
        df["Outstanding"] = pd.to_numeric(df["Outstanding"], errors="coerce")
    df = df.dropna(how="all")
    df = df.reset_index(drop=True)
    csv_path = os.path.splitext(pdf_path)[0] + "_extracted.csv"
    df.to_csv(csv_path, index=False)
    return csv_path

