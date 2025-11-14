#!/usr/bin/env python
# coding: utf-8

# In[2]:


# label_generator.py
"""
Label generator: flavour uses a single consistent bold font size across labels.
"""
import os
import re
import uuid
import textwrap
from typing import Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

# Prefer treepoem (vector) then python-barcode (raster).
_barcode_backend = None
try:
    import treepoem  # type: ignore
    _barcode_backend = "treepoem"
except Exception:
    try:
        from barcode import Code128  # type: ignore
        from barcode.writer import ImageWriter  # type: ignore
        _barcode_backend = "pybarcode"
    except Exception:
        _barcode_backend = None

FINAL_LABEL_DIR = "labels/final_labels"
os.makedirs(FINAL_LABEL_DIR, exist_ok=True)


def extract_from_product_field(product: str) -> Tuple[str, Optional[str], Optional[str]]:
    p = str(product or "").strip()
    m = re.search(r"\[(.*?)\]\s*$", p)
    if not m:
        return p, None, None
    inside = m.group(1)
    parts = [s.strip() for s in re.split(r"[/\|\-;]", inside) if s.strip()]
    flavour = parts[0] if len(parts) >= 1 else None
    strength = parts[1] if len(parts) >= 2 else None
    cleaned = p[:m.start()].strip()
    return cleaned, flavour, strength


def _load_ttf_candidate(size: int) -> ImageFont.FreeTypeFont:
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


def _load_bold_ttf(size: int) -> ImageFont.FreeTypeFont:
    bold_candidates = [
        "DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "/Library/Fonts/Arialbd.ttf",
        "Arial Bold.ttf",
        "Arialbd.ttf",
    ]
    for c in bold_candidates:
        try:
            return ImageFont.truetype(c, size)
        except Exception:
            continue
    return _load_ttf_candidate(size)


def _font_text_width(font: ImageFont.FreeTypeFont, text: str) -> int:
    try:
        bbox = font.getbbox(text)
        return bbox[2] - bbox[0]
    except Exception:
        if hasattr(font, "getlength"):
            try:
                return int(font.getlength(text))
            except Exception:
                pass
        return max(6, int(getattr(font, "size", 10) * len(text) * 0.5))


def _render_barcode_image(code_value: str, target_w: int, target_h: int) -> Optional[Image.Image]:
    if _barcode_backend == "treepoem":
        try:
            img = treepoem.generate_barcode(barcode_type="code128", data=str(code_value or " "))
            img = img.convert("RGB")
            bw, bh = img.size
            scale = min(target_w / bw, target_h / bh)
            new_w = max(1, int(bw * scale))
            new_h = max(1, int(bh * scale))
            return img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        except Exception:
            return None

    if _barcode_backend == "pybarcode":
        try:
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


def create_label_image(
    row,
    idx: Optional[str] = None,
    label_cm: float = 10.0,
    dpi: int = 300,
    out_dir: str = FINAL_LABEL_DIR,
    return_image: bool = False
):
    """
    Create a square label PNG sized label_cm x label_cm at the given dpi.
    Flavour will use a single uniform bold size across all lines; it only shrinks
    (uniformly) when necessary to fit into two lines.
    """
    inches = label_cm / 2.54
    px_size = max(200, int(inches * dpi))
    px_w = px_h = px_size

    img = Image.new("RGB", (px_w, px_h), "white")
    draw = ImageDraw.Draw(img)

    raw_product = str(row.get("Product", "") or "").strip()
    raw_sku = str(row.get("Sku", "") or "").strip()

    cleaned, ext_flavour, ext_strength = extract_from_product_field(raw_product)
    if cleaned:
        raw_product = cleaned

    # prefer explicit columns
    flavour = None
    strength = None
    if "Flavour" in row and str(row.get("Flavour") or "").strip():
        flavour = str(row.get("Flavour")).strip()
    elif ext_flavour:
        flavour = ext_flavour

    if "Strength" in row and str(row.get("Strength") or "").strip():
        strength = str(row.get("Strength")).strip()
    elif ext_strength:
        strength = ext_strength

    flavour = (flavour or "").strip()
    strength = (strength or "").strip()

    # fonts
    product_font = _load_ttf_candidate(max(12, int(px_h * 0.06)))

    # --- IMPORTANT: fixed starting flavour size (consistent across labels) ---
    # choose a sensible proportion (tweak 0.12 if you want slightly larger/smaller)
    initial_flavour_size = max(22, int(px_h * 0.12))
    flavour_font = _load_bold_ttf(initial_flavour_size)

    strength_font = _load_ttf_candidate(max(14, int(px_h * 0.09)))
    sku_font = _load_ttf_candidate(max(12, int(px_h * 0.06)))

    # product block
    padding_h = int(px_h * 0.04)
    current_y = padding_h
    max_text_w = int(px_w * 0.9)
    avg_char_w = max(6, _font_text_width(product_font, "a"))
    wrap_chars = max(10, int(max_text_w / avg_char_w))
    prod_lines = textwrap.wrap(raw_product, width=wrap_chars) if raw_product else []
    longest_line_w = 0
    for line in prod_lines:
        bbox = draw.textbbox((0, 0), line, font=product_font)
        w = bbox[2] - bbox[0]; h = bbox[3] - bbox[1]
        draw.text(((px_w - w) / 2, current_y), line, fill="black", font=product_font)
        longest_line_w = max(longest_line_w, w)
        current_y += h + int(px_h * 0.008)

    if prod_lines:
        underline_y = current_y + 1
        u_thickness = max(1, int(px_h * 0.005))
        draw.line(((px_w - longest_line_w) / 2, underline_y, (px_w + longest_line_w) / 2, underline_y),
                  fill="black", width=u_thickness)
        current_y = underline_y + int(px_h * 0.03)
    else:
        current_y += int(px_h * 0.02)

    # ---------- Flavour: uniform font size across lines ----------
    flavour_text = flavour
    if flavour_text:
        max_flavour_w = int(px_w * 0.9)

        def _lines_for_font(font):
            avg_w = max(6, _font_text_width(font, "A"))
            approx_wrap_chars = max(4, int(max_flavour_w / avg_w))
            return textwrap.wrap(flavour_text, width=approx_wrap_chars)

        flavour_candidate = flavour_font
        lines = _lines_for_font(flavour_candidate)

        # If it doesn't fit within 2 lines, reduce size uniformly until it fits or we hit min size.
        if len(lines) > 2 or any(_font_text_width(flavour_candidate, l) > max_flavour_w for l in lines):
            attempts = 0
            min_size = 10
            while (len(lines) > 2 or any(_font_text_width(flavour_candidate, l) > max_flavour_w for l in lines)) and attempts < 14:
                new_size = max(min_size, int(getattr(flavour_candidate, "size", initial_flavour_size) * 0.88))
                if new_size == getattr(flavour_candidate, "size", initial_flavour_size):
                    break
                flavour_candidate = _load_bold_ttf(new_size)
                lines = _lines_for_font(flavour_candidate)
                attempts += 1

            # last resort collapse to 2 lines (balanced) but keep uniform flavour_candidate size
            if len(lines) > 2:
                words = flavour_text.split()
                mid = max(1, len(words) // 2)
                lines = [" ".join(words[:mid]), " ".join(words[mid:])]

        # draw using the final uniform flavour_candidate
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=flavour_candidate)
            w = bbox[2] - bbox[0]; h = bbox[3] - bbox[1]
            draw.text(((px_w - w) / 2, current_y), line, fill="black", font=flavour_candidate)
            current_y += h + int(px_h * 0.008)

        current_y += int(px_h * 0.01)

    # strength
    if strength:
        bbox = draw.textbbox((0, 0), strength, font=strength_font)
        w = bbox[2] - bbox[0]; h = bbox[3] - bbox[1]
        draw.text(((px_w - w) / 2, current_y), strength, fill="black", font=strength_font)
        current_y += h + int(px_h * 0.02)

    # barcode zone
    barcode_zone_h = int(px_h * 0.22)
    barcode_max_w = int(px_w * 0.8)
    barcode_max_h = int(barcode_zone_h * 0.7)
    barcode_y = px_h - barcode_zone_h - int(px_h * 0.02)

    barcode_img = _render_barcode_image(raw_sku or " ", barcode_max_w, barcode_max_h)

    if barcode_img is None:
        bx = (px_w - barcode_max_w) // 2
        by = barcode_y
        draw.rectangle([bx, by, bx + barcode_max_w, by + barcode_max_h], outline="black",
                       width=max(1, int(px_h * 0.006)))
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
        bx = (px_w - bw) // 2
        by = barcode_y + (barcode_max_h - bh) // 2
        img.paste(barcode_img, (bx, by))

    # sku text
    sku_text = raw_sku or f"SKU-{uuid.uuid4().hex[:6].upper()}"
    bbox = draw.textbbox((0, 0), sku_text, font=sku_font)
    sw = bbox[2] - bbox[0]; sh = bbox[3] - bbox[1]
    sku_y = px_h - sh - int(px_h * 0.02)
    draw.text(((px_w - sw) / 2, sku_y), sku_text, fill="black", font=sku_font)

    # save
    os.makedirs(out_dir, exist_ok=True)
    filename = f"label_{(idx or uuid.uuid4().hex[:6])}.png"
    out_path = os.path.join(out_dir, filename)
    try:
        img.save(out_path, dpi=(dpi, dpi))
    except Exception:
        img.save(out_path)

    if return_image:
        return img
    return out_path


# In[ ]:




