#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# file_handler.py
import os
import pandas as pd
from pdf_converter import convert_pdf_to_csv

UPLOAD_DIR = os.path.join(os.getcwd(), "data", "po_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def read_po_file(uploaded_file):
    """
    Accepts a Streamlit UploadedFile object.
    Returns (DataFrame, saved_path) or (None, path) on failure.
    """
    fname = uploaded_file.name
    save_path = os.path.join(UPLOAD_DIR, fname)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    if fname.lower().endswith(".csv"):
        df = pd.read_csv(save_path)
    elif fname.lower().endswith(".pdf"):
        csv_path = convert_pdf_to_csv(save_path)
        if not csv_path or not os.path.exists(csv_path):
            return None, save_path
        df = pd.read_csv(csv_path)
        save_path = csv_path
    else:
        df = pd.read_excel(save_path)

    # normalize column names (keep original names where possible)
    df.columns = [c.strip() for c in df.columns]
    return df, save_path

