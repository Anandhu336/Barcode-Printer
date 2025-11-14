#!/usr/bin/env python
# coding: utf-8

# In[2]:


# app.py - Multi-page launcher + original styling (keeps your CSS/HTML)
import streamlit as st
import base64
import os
from pathlib import Path

# ---------- Page config ----------
st.set_page_config(page_title="Warehouse Management System", layout="wide", initial_sidebar_state="collapsed")

# ---------- Background Image (repo-relative) ----------
REL_IMAGE_PATHS = [
    "Background.jpg",
    "assets/Background.jpg",
    "static/Background.jpg",
    "assets/images/Background.jpg"
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

# ---------- Helper: open a page in new tab ----------
def open_page_in_new_tab(page_slug: str, label: str = "Open"):
    """
    Renders an HTML button that opens a relative path (./<page_slug>) in a new browser tab.
    page_slug should be the filename without .py, e.g. '1_Label_Printing' for pages/1_Label_Printing.py
    """
    url = f"./{page_slug}"
    html = f"""
    <div style="display:flex; gap:8px; align-items:center; justify-content:center;">
      <button onclick="window.open('{url}', '_blank')" style="
        background: linear-gradient(90deg,#ffc857,#ff6f61);
        color:#081826; border:none; padding:10px 14px; border-radius:12px;
        font-weight:800; cursor:pointer; box-shadow:0 8px 24px rgba(0,0,0,0.28);
      ">{label}</button>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# ---------- CSS & UI (kept from your original) ----------
bg_image_css = (f', url("data:image/jpeg;base64,{image_base64}")' if image_base64 else '')

st.markdown(f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(135deg, rgba(8,18,30,0.78), rgba(25,34,45,0.78)){bg_image_css};
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
""", unsafe_allow_html=True)

# ---------- Navbar ----------
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

# ---------- Module Info (tile metadata) ----------
# NOTE: slugs are page filenames (without .py) that must exist in pages/
modules = [
    ("🏷️", "Label Printing", "Generate and print product barcodes easily", "1_Label_Printing"),
    ("📊", "Live Stock Dashboard", "Monitor real-time warehouse inventory", "2_Stock_Dashboard"),
    ("🚀", "Stock Update & Sync", "Update stock levels across systems", "3_Stock_Update"),
    ("🧾", "Daily Report Generator", "View and export daily performance reports", "4_Daily_Report"),
    ("🤖", "AI Sales Forecast", "Predict demand and optimise inventory", "5_AI_Forecast"),
]

# ---------- Helper to create tile HTML ----------
def tile_html(emoji, title, desc, key):
    return f"""
    <div class="tile" id="{key}">
        <div class="tile-emoji">{emoji}</div>
        <div class="tile-title">{title}</div>
        <div class="tile-desc">{desc}</div>
    </div>
    """

# ---------- Render Layout ----------
st.markdown('<div class="content-wrap">', unsafe_allow_html=True)

# Top row (3 tiles)
cols1 = st.columns([1, 1, 1], gap="large")
for i, col in enumerate(cols1):
    emoji, title, desc, slug = modules[i]
    with col:
        st.markdown(tile_html(emoji, title, desc, f"tile_{i}"), unsafe_allow_html=True)
        st.write("")  # spacing
        page_path = Path("pages") / f"{slug}.py"
        if page_path.exists():
            open_page_in_new_tab(slug, label=f"Launch {title}")
        else:
            # fallback: if original file exists in repo root with old name, show a notice and a button to import in-session
            alt_filename = f"{title.lower().replace(' ', '_')}.py"
            root_alt = Path(alt_filename)
            if root_alt.exists():
                st.markdown(f"<div style='color:#ffd6a5;font-weight:700;margin-top:6px;'>Found {root_alt.name} in repo root. Consider moving it to pages/{slug}.py for proper multi-page behaviour.</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='margin-top:6px;'>Open in current tab:</div>", unsafe_allow_html=True)
                # provide an in-session import button as last-resort (works but not cross-tab)
                if st.button(f"Open {title} in current tab", key=f"open_current_{i}"):
                    try:
                        # dynamic import from repo root (not recommended for production)
                        import importlib.util, traceback
                        p = root_alt.resolve()
                        spec = importlib.util.spec_from_file_location(p.stem, str(p))
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                    except Exception as e:
                        st.error(f"Failed to load {root_alt.name}: {e}")
                        st.text(traceback.format_exc())
            else:
                st.markdown(f"<div style='color:#ffb4b4;font-weight:700;margin-top:6px;'>Page missing: pages/{slug}.py</div>", unsafe_allow_html=True)

# Spacer between rows
st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)

# Bottom row (2 tiles)
cols2 = st.columns([1, 0.6, 1], gap="large")

# Left
with cols2[0]:
    emoji, title, desc, slug = modules[3]
    st.markdown(tile_html(emoji, title, desc, "tile_3"), unsafe_allow_html=True)
    st.write("")
    page_path = Path("pages") / f"{slug}.py"
    if page_path.exists():
        open_page_in_new_tab(slug, label=f"Launch {title}")
    else:
        alt_filename = f"{title.lower().replace(' ', '_')}.py"
        root_alt = Path(alt_filename)
        if root_alt.exists():
            st.markdown(f"<div style='color:#ffd6a5;font-weight:700;margin-top:6px;'>Found {root_alt.name} in repo root. Consider moving it to pages/{slug}.py</div>", unsafe_allow_html=True)
            if st.button(f"Open {title} in current tab", key="open_current_3"):
                try:
                    import importlib.util, traceback
                    p = root_alt.resolve()
                    spec = importlib.util.spec_from_file_location(p.stem, str(p))
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                except Exception as e:
                    st.error(f"Failed to load {root_alt.name}: {e}")
                    st.text(traceback.format_exc())
        else:
            st.markdown(f"<div style='color:#ffb4b4;font-weight:700;margin-top:6px;'>Page missing: pages/{slug}.py</div>", unsafe_allow_html=True)

# Spacer (empty middle column)
with cols2[1]:
    st.write("")

# Right
with cols2[2]:
    emoji, title, desc, slug = modules[4]
    st.markdown(tile_html(emoji, title, desc, "tile_4"), unsafe_allow_html=True)
    st.write("")
    page_path = Path("pages") / f"{slug}.py"
    if page_path.exists():
        open_page_in_new_tab(slug, label=f"Launch {title}")
    else:
        alt_filename = f"{title.lower().replace(' ', '_')}.py"
        root_alt = Path(alt_filename)
        if root_alt.exists():
            st.markdown(f"<div style='color:#ffd6a5;font-weight:700;margin-top:6px;'>Found {root_alt.name} in repo root. Consider moving it to pages/{slug}.py</div>", unsafe_allow_html=True)
            if st.button(f"Open {title} in current tab", key="open_current_4"):
                try:
                    import importlib.util, traceback
                    p = root_alt.resolve()
                    spec = importlib.util.spec_from_file_location(p.stem, str(p))
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                except Exception as e:
                    st.error(f"Failed to load {root_alt.name}: {e}")
                    st.text(traceback.format_exc())
        else:
            st.markdown(f"<div style='color:#ffb4b4;font-weight:700;margin-top:6px;'>Page missing: pages/{slug}.py</div>", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ---------- Footer ----------
st.markdown("""
    <div style='text-align:center; color:#cbd5e1; font-size:14px; font-weight:600; margin-top:28px;'>
        © 2025 Warehouse Management System | Designed for Real-Time Operations 🚚
    </div>
""", unsafe_allow_html=True)


# In[ ]:




