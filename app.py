#!/usr/bin/env python
# coding: utf-8

# In[2]:


# app.py - Main entry for Warehouse Management System
# Replace your existing app.py with this file.

import streamlit as st
import base64
import os
from pathlib import Path
import importlib.util
import traceback

# ---------------- Page config ----------------
st.set_page_config(page_title="Warehouse Management System", layout="wide", initial_sidebar_state="collapsed")

# ---------------- Background image (repo-relative) ----------------
# Put Background.jpg in repo root or assets/ or static/ and commit it.
REL_IMAGE_PATHS = [
    "Background.jpg",
    "assets/Background.jpg",
    "static/Background.jpg",
]

def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception:
        return ""

image_base64 = ""
for p in REL_IMAGE_PATHS:
    if os.path.exists(p):
        image_base64 = get_base64_image(p)
        break

# ---------------- Robust module launcher (works on Streamlit Cloud) ----------------
def launch_module(filename: str, message: str = ""):
    """
    Import/execute a local module by filename without spawning a new Streamlit process.
    Looks for the file in repo root, pages/, and apps/ directories.
    Shows friendly Streamlit errors and full traceback in an expander.
    """
    base = Path(__file__).resolve().parent

    # candidate locations to look for the file (repo root, pages, apps)
    candidates = [
        base / filename,
        base / "pages" / filename,
        base / "apps" / filename,
    ]

    found = None
    for p in candidates:
        if p.exists():
            found = p
            break

    if found is None:
        st.error("❌ Module not found. Tried these locations:")
        for p in candidates:
            st.write(f"- {p}")
        return

    try:
        # Inform the user
        if message:
            st.info(message)

        # Import and execute the module by file path
        spec = importlib.util.spec_from_file_location(found.stem, str(found))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        st.success(f"✅ {found.name} launched successfully in this session.")
    except Exception as e:
        st.error(f"⚠️ Failed to import {found.name}: {e}")
        with st.expander("Full traceback (for debugging)"):
            st.text(traceback.format_exc())

# ---------------- CSS & UI Design ----------------
bg_style = f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(135deg, rgba(8,18,30,0.78), rgba(25,34,45,0.78)){ (', url("data:image/jpeg;base64,' + image_base64 + '")') if image_base64 else '' };
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        color: #e6eef8;
    }}

    /* Navbar */
    .navbar {{
        display:flex;
        align-items:center;
        justify-content:space-between;
        background: rgba(20,28,40,0.78);
        padding: 14px 26px;
        border-radius: 14px;
        margin-bottom: 24px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.45);
        backdrop-filter: blur(8px);
    }}
    .navbar .left {{ display:flex; align-items:center; gap:12px; }}
    .navbar img.logo {{ width:44px; height:44px; border-radius:10px; }}
    .navbar h1 {{ font-size:22px; margin:0; font-weight:800; color:#f1f5f9; }}
    .profile {{
        display:flex; align-items:center; gap:10px;
        background: rgba(255,255,255,0.06);
        padding:6px 10px; border-radius:12px;
        backdrop-filter: blur(6px);
    }}
    .profile img {{ width:34px; height:34px; border-radius:50%; object-fit:cover; }}

    .content-wrap {{
        padding: 12px 36px 48px 36px;
        max-width: 1400px;
        margin: 0 auto;
    }}

    /* TILE DESIGN */
    .tile {{
        width: 100%;
        height: 320px;
        border-radius: 28px;
        padding: 28px;
        background: linear-gradient(145deg, rgba(26,40,62,0.6), rgba(12,20,32,0.45));
        border: 1px solid rgba(255,255,255,0.1);
        box-shadow: 0 10px 40px rgba(0,0,0,0.45);
        text-align: center;
        transition: all 0.3s ease;
        backdrop-filter: blur(12px);
        cursor: pointer;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }}
    .tile:hover {{
        transform: translateY(-8px) scale(1.03);
        box-shadow: 0 18px 70px rgba(255, 200, 50, 0.25);
        border: 1px solid rgba(255,200,50,0.3);
        background: linear-gradient(145deg, rgba(255,200,50,0.12), rgba(18,30,48,0.6));
    }}
    .tile-emoji {{
        font-size:52px;
        line-height:1;
        margin-bottom:15px;
        text-shadow: 0 2px 8px rgba(0,0,0,0.4);
    }}
    .tile-title {{
        font-size:23px;
        font-weight:900;
        color:#ffffff;
        margin-bottom:8px;
        text-shadow: 0 1px 8px rgba(0,0,0,0.6);
    }}
    .tile-desc {{
        font-size:16px;
        font-weight:500;
        color:#d0d9e6;
        opacity:0.95;
        text-align:center;
        line-height:1.5;
        max-width:280px;
        margin:0 auto;
    }}

    footer, header {{ visibility: hidden; }}
    </style>
"""
st.markdown(bg_style, unsafe_allow_html=True)

# ---------------- Navbar ----------------
st.markdown("""
    <div class="content-wrap">
        <div class="navbar">
            <div class="left">
                <img class="logo" src="https://cdn-icons-png.flaticon.com/512/679/679922.png" alt="logo">
                <h1>Warehouse Management System</h1>
            </div>
            <div class="right" style="display:flex; align-items:center; gap:16px;">
                <div class="profile">
                    <img src="https://randomuser.me/api/portraits/men/32.jpg" alt="profile">
                    <div style="font-weight:600; color:#e6eef8;">Anandh</div>
                </div>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# ---------------- Module Info ----------------
modules = [
    ("🏷️", "Label Printing", "Generate and print product barcodes easily", "label_app.py", "Launching Label Printing Module..."),
    ("📊", "Live Stock Dashboard", "Monitor real-time warehouse inventory", "stock_dashboard.py", "Opening Live Stock Dashboard..."),
    ("🚀", "Stock Update & Sync", "Update stock levels across systems", "stock_update.py", "Opening Stock Update Module..."),
    ("🧾", "Daily Report Generator", "View and export daily performance reports", "daily_report.py", "Generating Daily Report..."),
    ("🤖", "AI Sales Forecast", "Predict demand and optimise inventory", "aiforecast.py", "Launching AI Forecast System..."),
]

# ---------------- Helper to create tiles ----------------
def tile_html(emoji, title, desc, key):
    return f"""
    <div class="tile" id="{key}">
        <div class="tile-emoji">{emoji}</div>
        <div class="tile-title">{title}</div>
        <div class="tile-desc">{desc}</div>
    </div>
    """

# ---------------- Render Layout ----------------
st.markdown('<div class="content-wrap">', unsafe_allow_html=True)

# Top row (3 tiles)
cols1 = st.columns([1, 1, 1], gap="large")
for i, col in enumerate(cols1):
    emoji, title, desc, file, msg = modules[i]
    with col:
        st.markdown(tile_html(emoji, title, desc, f"tile_{i}"), unsafe_allow_html=True)
        if st.button(f"Launch {title}", key=f"btn_{i}", use_container_width=True):
            launch_module(file, msg)

# Spacer between rows
st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)

# Bottom row (2 tiles)
cols2 = st.columns([1, 0.6, 1], gap="large")

# Left
with cols2[0]:
    emoji, title, desc, file, msg = modules[3]
    st.markdown(tile_html(emoji, title, desc, "tile_3"), unsafe_allow_html=True)
    if st.button(f"Launch {title}", key="btn_3", use_container_width=True):
        launch_module(file, msg)

# Spacer (empty middle column)
with cols2[1]:
    st.write("")

# Right
with cols2[2]:
    emoji, title, desc, file, msg = modules[4]
    st.markdown(tile_html(emoji, title, desc, "tile_4"), unsafe_allow_html=True)
    if st.button(f"Launch {title}", key="btn_4", use_container_width=True):
        launch_module(file, msg)

st.markdown('</div>', unsafe_allow_html=True)

# ---------------- Footer ----------------
st.markdown("""
    <div style='text-align:center; color:#cbd5e1; font-size:14px; font-weight:600; margin-top:28px;'>
        © 2025 Warehouse Management System | Designed for Real-Time Operations 🚚
    </div>
""", unsafe_allow_html=True)


# In[ ]:




