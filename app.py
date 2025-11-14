#!/usr/bin/env python
# coding: utf-8

# In[2]:


# app.py  - Multi-page launcher (opens pages in new tabs)
import streamlit as st
import os
from pathlib import Path

# ---------- Page config ----------
st.set_page_config(page_title="Warehouse Management System", layout="wide", initial_sidebar_state="collapsed")

# ---------- Helper: open a page in new tab (JS) ----------
def open_page_in_new_tab(page_slug: str, label: str = "Open"):
    """
    Renders a small HTML button that opens a relative path (page_slug) in a new browser tab.
    page_slug should be the filename without .py, e.g. '1_Label_Printing' for pages/1_Label_Printing.py
    """
    # Use a safe relative URL (./<slug>) so it works both locally and on Streamlit Cloud
    url = f"./{page_slug}"
    html = f"""
    <div style="display:flex; gap:8px; align-items:center;">
      <button onclick="window.open('{url}', '_blank')" style="
        background:#0366d6; color:white; border:none; padding:10px 14px; border-radius:8px;
        font-weight:700; cursor:pointer;
      ">{label}</button>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# ---------- Background / Styling (minimal) ----------
st.markdown(
    """
    <style>
      .content-wrap{{
        padding: 18px 36px 48px 36px;
        max-width: 1400px;
        margin: 0 auto;
      }}
      .tile {{
        width: 100%;
        height: 300px;
        border-radius: 20px;
        padding: 22px;
        background: linear-gradient(145deg, rgba(26,40,62,0.6), rgba(12,20,32,0.45));
        color: #eef6ff;
        display:flex;
        flex-direction:column;
        justify-content:center;
        align-items:center;
        text-align:center;
      }}
      .tile-title {{ font-size:20px; font-weight:800; margin-bottom:6px; }}
      .tile-desc {{ font-size:14px; color:#d0d9e6; max-width:300px; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Navbar ----------
st.markdown(
    """
    <div style="max-width:1400px;margin:0 auto;padding:12px 36px;">
      <div style="display:flex;justify-content:space-between;align-items:center;background:rgba(10,16,25,0.7);padding:12px 18px;border-radius:12px;">
        <div style="display:flex;align-items:center;gap:12px;">
          <img src="https://cdn-icons-png.flaticon.com/512/679/679922.png" width="42" style="border-radius:8px;">
          <div style="font-weight:800;font-size:20px;color:#f5f9ff">Warehouse Management System</div>
        </div>
        <div style="display:flex;gap:14px;align-items:center;">
          <div style="background:rgba(255,255,255,0.04);padding:6px 10px;border-radius:10px;display:flex;gap:8px;align-items:center;">
            <img src="https://randomuser.me/api/portraits/men/32.jpg" width="34" style="border-radius:50%;">
            <div style="font-weight:600;color:#e6eef8">Anandh</div>
          </div>
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='content-wrap'>", unsafe_allow_html=True)

# ---------- Define pages (filename without .py is the page slug) ----------
# Make sure these files exist in pages/ (for example pages/1_Label_Printing.py)
pages = [
    ("🏷️", "Label Printing", "Generate and print product barcodes easily", "1_Label_Printing"),
    ("📊", "Live Stock Dashboard", "Monitor real-time warehouse inventory", "2_Stock_Dashboard"),
    ("🚀", "Stock Update & Sync", "Update stock levels across systems", "3_Stock_Update"),
    ("🧾", "Daily Report Generator", "View and export daily performance reports", "4_Daily_Report"),
    ("🤖", "AI Sales Forecast", "Predict demand and optimise inventory", "5_AI_Forecast"),
]

# ---------- Render tiles in two rows ----------
cols1 = st.columns([1,1,1], gap="large")
for i, col in enumerate(cols1):
    if i >= len(pages): break
    emoji, title, desc, slug = pages[i]
    with col:
        st.markdown(f"<div class='tile'><div style='font-size:44px'>{emoji}</div><div class='tile-title'>{title}</div><div class='tile-desc'>{desc}</div></div>", unsafe_allow_html=True)
        st.write("")  # small gap
        # show the open-in-new-tab button (JS opens relative url ./<slug>)
        # but first check file exists in pages/
        page_path = Path("pages") / f"{slug}.py"
        if page_path.exists():
            open_page_in_new_tab(slug, label=f"Launch {title}")
        else:
            st.markdown(f"<div style='color:#ffb4b4;font-weight:700;margin-top:6px;'>Page not found: pages/{slug}.py</div>", unsafe_allow_html=True)

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

cols2 = st.columns([1,0.6,1], gap="large")
# left (4th)
if len(pages) > 3:
    with cols2[0]:
        emoji, title, desc, slug = pages[3]
        st.markdown(f"<div class='tile'><div style='font-size:44px'>{emoji}</div><div class='tile-title'>{title}</div><div class='tile-desc'>{desc}</div></div>", unsafe_allow_html=True)
        st.write("")
        page_path = Path("pages") / f"{slug}.py"
        if page_path.exists():
            open_page_in_new_tab(slug, label=f"Launch {title}")
        else:
            st.markdown(f"<div style='color:#ffb4b4;font-weight:700;margin-top:6px;'>Page not found: pages/{slug}.py</div>", unsafe_allow_html=True)

# spacer middle
with cols2[1]:
    st.write("")

# right (5th)
if len(pages) > 4:
    with cols2[2]:
        emoji, title, desc, slug = pages[4]
        st.markdown(f"<div class='tile'><div style='font-size:44px'>{emoji}</div><div class='tile-title'>{title}</div><div class='tile-desc'>{desc}</div></div>", unsafe_allow_html=True)
        st.write("")
        page_path = Path("pages") / f"{slug}.py"
        if page_path.exists():
            open_page_in_new_tab(slug, label=f"Launch {title}")
        else:
            st.markdown(f"<div style='color:#ffb4b4;font-weight:700;margin-top:6px;'>Page not found: pages/{slug}.py</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ---------- Footer ----------
st.markdown("""
    <div style='text-align:center; color:#cbd5e1; font-size:14px; font-weight:600; margin-top:28px;'>
        © 2025 Warehouse Management System | Designed for Real-Time Operations 🚚
    </div>
""", unsafe_allow_html=True)


# In[ ]:




