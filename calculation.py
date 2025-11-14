#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# calculation.py
import pandas as pd
import math

def detect_quantity_column(df):
    for cand in ["Receiving", "Outstanding", "Count"]:
        if cand in df.columns:
            return cand
    return None

def calculate_final_labels(df):
    df = df.copy()
    qty_col = detect_quantity_column(df)
    if not qty_col:
        return df

    df[qty_col] = pd.to_numeric(df[qty_col], errors="coerce").fillna(0)
    df["Case_Size"] = pd.to_numeric(df.get("Case_Size", pd.Series()), errors="coerce")

    for idx, row in df.iterrows():
        cs = row.get("Case_Size")
        qty = row.get(qty_col, 0)
        fl = row.get("Final_Labels")
        if pd.notna(fl):
            try:
                df.at[idx, "Final_Labels"] = int(fl)
                continue
            except Exception:
                pass
        if pd.notna(cs) and cs and cs > 0:
            df.at[idx, "Final_Labels"] = int(math.ceil(qty / cs))
        else:
            df.at[idx, "Final_Labels"] = None

    return df

