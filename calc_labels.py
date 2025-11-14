#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# calc_labels.py
import math
import pandas as pd

def apply_default_case_size(df, default_case_size):
    if "Case_Size" not in df.columns:
        df["Case_Size"] = pd.NA
    df["Case_Size"] = pd.to_numeric(df["Case_Size"], errors="coerce")
    if default_case_size and default_case_size > 0:
        df["Case_Size"] = df["Case_Size"].fillna(default_case_size)
    return df

def compute_final_labels(df):
    """
    For every row, compute Final_Labels = ceil(Outstanding / Case_Size)
    If Case_Size missing or zero, leave Final_Labels as None.
    """
    df["Outstanding"] = pd.to_numeric(df["Outstanding"], errors="coerce").fillna(0)
    def calc(row):
        cs = row.get("Case_Size")
        out = row.get("Outstanding", 0)
        if pd.notna(cs) and cs > 0 and out > 0:
            return int(math.ceil(out / cs))
        return 0
    df["Final_Labels"] = df.apply(calc, axis=1)
    return df

def clean_rows(df):
    # drop rows that are all NaN or empty
    df = df.replace(r'^\s*$', pd.NA, regex=True)
    df = df.dropna(how="all")
    # drop rows that have no Product and no Sku
    if "Product" in df.columns and "Sku" in df.columns:
        df = df[ df["Product"].notna() | df["Sku"].notna() ]
    return df.reset_index(drop=True)

