#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# label_generator.py
import os
import uuid
import re
import textwrap
from typing import Optional
from PIL import Image, ImageDraw, ImageFont

# Prefer treepoem (vector) then python-barcode (raster). If neither exists, we draw a placeholder barcode.
_barcode_backend = None
try:
    import treepoem  # type: ignore
    _barcode_backend = "treepoem"
except Exception:
    try:
        # Note: python-barcode is optional; we import when needed later to avoid silent import errors on module load
        from barcode import Code128  # type: ignore
        from barcode.writer import ImageWriter  # type: ignore
        _barcode_backend = "pybarcode"
    except Exception:
        _barcode_backend = None

FINAL_LABEL_DIR = "labels/final_labels"
os.makedirs(FINAL_LABEL_DIR, exist_ok=True)


def _load_ttf_candidate(size: int):
    """Try some common TTFs, fallback to PIL default."""
    candidates = [
        "DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "DejaVuSans.ttf",
        "/Library/Fonts/Arial.ttf",
        "Arial.ttf",
    ]
    for c in candidates:
        try:
            return ImageFont.truetype(c, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _font_text_width(font: ImageFont.FreeTypeFont, text: str) -> int:
    """
    Return pixel width for text using modern Pillow APIs.
    Fallback with reasonable defaults if needed.
    """
    try:
        bbox = font.getbbox(text)
        return bbox[2] - bbox[0]
    except Exception:
        # older/foreign fonts might not implement getbbox; try getlength, finally estimate
        if hasattr(font, "getlength"):
            try:
                return int(font.getlength(text))
            except Exception:
                pass
        # fallback estimate
        return max(6, int(font.size * len(text) * 0.5))


def _render_barcode_image(code_value: str, target_w: int, target_h: int) -> Optional[Image.Image]:
    """
    Return a PIL image for the barcode sized to fit within (target_w, target_h).
    Uses treepoem or python-barcode when available. Returns None on failure.
    """
    if _barcode_backend == "treepoem":
        try:
            img = treepoem.generate_barcode(barcode_type="code128", data=str(code_value or " "))
            img = img.convert("RGB")
            bw, bh = img.size
            # scale to fit
            scale = min(target_w / bw, target_h / bh)
            new_w = max(1, int(bw * scale))
            new_h = max(1, int(bh * scale))
            return img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        except Exception:
            return None

    if _barcode_backend == "pybarcode":
        try:
            # construct a temporary file using python-barcode writer
            from barcode import Code128  # type: ignore
            from barcode.writer import ImageWriter  # type: ignore
            temp_path = os.path.join(FINAL_LABEL_DIR, f"tmp_bar_{uuid.uuid4().hex[:6]}.png")
            code = Code128(str(code_value or " "), writer=ImageWriter())
            with open(temp_path, "wb") as fh:
                code.write(fh, options={"module_width": 0.2, "module_height": 12.0, "font_size": 0})
            img = Image.open(temp_path).convert("RGB")
            try:
                os.remove(temp_path)
            except Exception:
                pass
            bw, bh = img.size
            scale = min(target_w / bw, target_h / bh)
            new_w = max(1, int(bw * scale))
            new_h = max(1, int(bh * scale))
            return img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        except Exception:
            return None
    return None


def create_label_image(row,
                       idx: Optional[str] = None,
                       label_cm: float = 10.0,
                       dpi: int = 300,
                       out_dir: str = FINAL_LABEL_DIR) -> str:
    """
    Create a square label PNG sized label_cm x label_cm at the given dpi.
    Layout:
      - Product name (top, wrapped, smaller)
      - Flavour (center, large, auto-wrap and auto-scale)
      - Strength (under flavour)
      - Barcode (bottom center) with SKU text under barcode
    Returns output file path.
    """
    # --- pixel size calculation (cm -> inches -> px) ---
    inches = label_cm / 2.54
    px_size = max(200, int(inches * dpi))
    px_w = px_h = px_size

    # --- canvas ---
    img = Image.new("RGB", (px_w, px_h), "white")
    draw = ImageDraw.Draw(img)

    # --- read row fields safely ---
    raw_product = str(row.get("Product", "") or "").strip()
    raw_sku = str(row.get("Sku", "") or "").strip()

    # try to extract bracketed flavour/strength: "Name [Flavor / 20mg]"
    flavour = ""
    strength = ""
    m = re.search(r"\[(.*?)\]$", raw_product)
    if m:
        inside = m.group(1)
        raw_product = raw_product[:m.start()].strip()
        parts = re.split(r"[/\-|;]", inside)
        if len(parts) >= 1:
            flavour = parts[0].strip()
        if len(parts) >= 2:
            strength = parts[1].strip()

    # fallback explicit columns
    if not flavour and "Flavour" in row:
        flavour = str(row.get("Flavour") or "")
    if not strength and "Strength" in row:
        strength = str(row.get("Strength") or "")

    # --- fonts scaled by label size ---
    # choose base sizes; will be adjusted for long text
    product_font = _load_ttf_candidate(max(12, int(px_h * 0.06)))
    flavour_font = _load_ttf_candidate(max(28, int(px_h * 0.16)))
    strength_font = _load_ttf_candidate(max(14, int(px_h * 0.09)))
    sku_font = _load_ttf_candidate(max(12, int(px_h * 0.06)))

    # --- top area: product name (wrapped to width) ---
    padding_h = int(px_h * 0.04)
    current_y = padding_h
    max_text_w = int(px_w * 0.9)
    # estimate characters per line using font width
    avg_char_w = max(6, _font_text_width(product_font, "a"))
    wrap_chars = max(10, int(max_text_w / avg_char_w))
    prod_lines = textwrap.wrap(raw_product, width=wrap_chars)
    for line in prod_lines:
        bbox = draw.textbbox((0, 0), line, font=product_font)
        w = bbox[2] - bbox[0]; h = bbox[3] - bbox[1]
        draw.text(((px_w - w) / 2, current_y), line, fill="black", font=product_font)
        current_y += h + int(px_h * 0.008)

    # add a gap before the flavour block
    current_y += int(px_h * 0.04)

    # --- centre area: flavour (big) with auto-wrapping and downscaling if too long ---
    flavour_text = (flavour or "").strip()
    if flavour_text:
        # try to fit flavour in up to 2 lines by reducing font if needed
        max_flavour_width = int(px_w * 0.9)
        # start with configured flavour_font size and reduce if text too wide
        # compute single-line width; if too long, attempt wrap to 2 lines; if still too tall, reduce font
        def _flavour_lines_for_font(font):
            avg_w = max(6, _font_text_width(font, "A"))
            approx_wrap_chars = max(4, int(max_flavour_width / avg_w))
            return textwrap.wrap(flavour_text, width=approx_wrap_chars)

        flavour_candidate = flavour_font
        lines = _flavour_lines_for_font(flavour_candidate)
        # if more than 2 lines, reduce font iteratively
        attempts = 0
        while (len(lines) > 2 or any(_font_text_width(flavour_candidate, l) > max_flavour_width for l in lines)) and attempts < 10:
            # shrink font by ~12%
            new_size = max(10, int(getattr(flavour_candidate, "size", int(px_h * 0.16)) * 0.88))
            flavour_candidate = _load_ttf_candidate(new_size)
            lines = _flavour_lines_for_font(flavour_candidate)
            attempts += 1

        # draw the lines
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=flavour_candidate)
            w = bbox[2] - bbox[0]; h = bbox[3] - bbox[1]
            draw.text(((px_w - w) / 2, current_y), line, fill="black", font=flavour_candidate)
            current_y += h + int(px_h * 0.008)
        # set flavour_font to candidate for potential later use (not strictly necessary)
        flavour_font = flavour_candidate

    # --- strength under flavour ---
    strength_text = (strength or "").strip()
    if strength_text:
        bbox = draw.textbbox((0, 0), strength_text, font=strength_font)
        w = bbox[2] - bbox[0]; h = bbox[3] - bbox[1]
        draw.text(((px_w - w) / 2, current_y), strength_text, fill="black", font=strength_font)
        current_y += h + int(px_h * 0.02)

    # --- barcode zone near bottom ---
    barcode_zone_h = int(px_h * 0.22)
    barcode_max_w = int(px_w * 0.8)
    barcode_max_h = int(barcode_zone_h * 0.7)
    barcode_y = px_h - barcode_zone_h - int(px_h * 0.02)

    # attempt to render barcode image with available backend
    barcode_img = _render_barcode_image(raw_sku or " ", barcode_max_w, barcode_max_h)

    if barcode_img is None:
        # draw placeholder barcode box and algorithmic bars for testing/printing reliability
        bx = (px_w - barcode_max_w) // 2
        by = barcode_y
        draw.rectangle([bx, by, bx + barcode_max_w, by + barcode_max_h], outline="black", width=max(1, int(px_h * 0.006)))
        bars = 42
        bar_w = max(2, barcode_max_w // (bars * 2))
        gap = max(1, (barcode_max_w - bars * bar_w) // (bars + 1))
        x = bx + gap
        for j in range(bars):
            draw.rectangle([x, by + int(barcode_max_h * 0.05),
                            x + bar_w, by + int(barcode_max_h * 0.95)], fill="black")
            x += bar_w + gap
    else:
        bw, bh = barcode_img.size
        # center the barcode image in the barcode zone
        bx = (px_w - bw) // 2
        by = barcode_y + (barcode_max_h - bh) // 2
        img.paste(barcode_img, (bx, by))

    # --- SKU text under barcode ---
    sku_text = raw_sku or f"SKU-{uuid.uuid4().hex[:6].upper()}"
    bbox = draw.textbbox((0, 0), sku_text, font=sku_font)
    sw = bbox[2] - bbox[0]; sh = bbox[3] - bbox[1]
    sku_y = px_h - sh - int(px_h * 0.02)
    draw.text(((px_w - sw) / 2, sku_y), sku_text, fill="black", font=sku_font)

    # --- save file with DPI set ---
    os.makedirs(out_dir, exist_ok=True)
    filename = f"label_{(idx or uuid.uuid4().hex[:6])}.png"
    out_path = os.path.join(out_dir, filename)
    # Save with dpi metadata so preview/printers know physical size
    try:
        img.save(out_path, dpi=(dpi, dpi))
    except Exception:
        img.save(out_path)
    return out_path

