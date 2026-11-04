"""PDF -> page images -> Muse Spark blocks -> MathML + figure alt text."""
import html
import io
import re
import traceback

import pymupdf
from latex2mathml.converter import convert
from PIL import Image

from . import meta_client, sam, store
from .speech import latex_to_speech
from .config import MAX_PAGES

REVIEW_THRESHOLD = 0.9          # equations below this confidence get flagged
INLINE_MATH = re.compile(r"\\\((.+?)\\\)")   # matches \( ... \)


def to_mathml(latex: str, display: bool = True) -> str:
    return convert(latex, display="block" if display else "inline")


def render_inline(text: str) -> str:
    """Text with \\( ... \\) math -> safe HTML with inline math.

    Each piece of math becomes: spoken English for screen readers (visually hidden)
    + MathML for sighted readers (hidden from screen readers). That way continuous
    reading flows straight through sentences instead of stopping at every equation.
    """
    out, last = [], 0
    for m in INLINE_MATH.finditer(text or ""):
        out.append(html.escape(text[last:m.start()]))
        latex = m.group(1)
        try:
            mathml = to_mathml(latex, display=False)
            spoken = html.escape(latex_to_speech(latex))
            out.append(f'<span class="visually-hidden">{spoken}</span><span aria-hidden="true">{mathml}</span>')
        except Exception:
            out.append(html.escape(m.group(0)))  # leave broken math as plain text
        last = m.end()
    out.append(html.escape((text or "")[last:]))
    return "".join(out)


def finalize_block(block: dict) -> None:
    """Fill in the HTML/MathML a block needs, and decide if a human must check it."""
    kind = block.get("type")
    block["error"] = None

    if kind == "equation":
        # Spoken version for screen readers, unless a reviewer wrote their own.
        if not block.get("speech_edited"):
            block["speech"] = latex_to_speech(block.get("latex", ""))
        try:
            block["mathml"] = to_mathml(block.get("latex", ""), block.get("display", True))
            low = float(block.get("confidence", 0)) < REVIEW_THRESHOLD
            block["status"] = "needs_review" if low else "draft"
        except Exception as e:  # malformed LaTeX
            block["mathml"] = ""
            block["error"] = f"LaTeX could not be converted: {e}"
            block["status"] = "needs_review"

    elif kind in ("heading", "paragraph"):
        block["html"] = render_inline(block.get("text", ""))
        block.setdefault("status", "draft")

    elif kind == "table":
        block["headers_html"] = [render_inline(h) for h in block.get("headers", [])]
        block["rows_html"] = [[render_inline(str(c)) for c in row] for row in block.get("rows", [])]
        block.setdefault("status", "draft")


def process(doc_id: str, pdf_bytes: bytes) -> None:
    """Runs in the background after upload. Saves progress after every page."""
    doc = store.load(doc_id)
    folder = store.doc_dir(doc_id)
    (folder / "pages").mkdir(exist_ok=True)
    (folder / "figures").mkdir(exist_ok=True)

    try:
        pdf = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        n = min(len(pdf), MAX_PAGES)

        for i in range(n):
            doc["progress"] = f"Reading page {i + 1} of {n}"
            store.save(doc)

            page = pdf[i]
            png = page.get_pixmap(dpi=200).tobytes("png")
            (folder / "pages" / f"{i + 1}.png").write_bytes(png)

            blocks = meta_client.read_page(png, page.get_text())
            last_text = ""  # the paragraph just before a figure, used as context
            for j, block in enumerate(blocks):
                block["id"] = f"p{i + 1}b{j + 1}"
                if block.get("type") == "figure":
                    doc["progress"] = f"Describing a figure on page {i + 1}"
                    store.save(doc)
                    describe_figure(folder, png, block, last_text)
                else:
                    finalize_block(block)
                    last_text = block.get("text", last_text)

            doc["pages"].append({"n": i + 1, "image": f"pages/{i + 1}.png", "blocks": blocks})
            store.save(doc)

        doc["state"] = "ready"
        doc["progress"] = "Done"
    except Exception as e:
        traceback.print_exc()
        doc["state"] = "error"
        doc["progress"] = f"Something went wrong: {e}"
    store.save(doc)


def describe_figure(folder, page_png: bytes, block: dict, context: str) -> None:
    """Crop the figure, find its parts with SAM, and draft alt text + part descriptions."""
    # 1. Crop the figure out of the page (with padding, since the box is approximate).
    img = Image.open(io.BytesIO(page_png))
    x0, y0, x1, y1 = [int(v) for v in block.get("bbox") or [0, 0, img.width, img.height]]
    pad = int(0.03 * max(img.width, img.height))
    crop = img.crop((max(0, x0 - pad), max(0, y0 - pad), min(img.width, x1 + pad), min(img.height, y1 + pad)))
    buf = io.BytesIO()
    crop.save(buf, "PNG")
    crop_png = buf.getvalue()
    (folder / "figures" / f"{block['id']}.png").write_bytes(crop_png)
    block["image"] = f"figures/{block['id']}.png"

    # 2. Muse Spark names the kinds of parts; SAM finds each one.
    regions = []
    try:
        for kind in meta_client.list_part_types(crop_png):
            for box in sam.find(crop_png, kind):
                regions.append({"region": len(regions) + 1, "kind": kind, "box": box})
        regions = regions[:12]  # keep it manageable for the student and the prompt
    except Exception as e:
        print(f"SAM step skipped for {block['id']}: {e}")
        regions = []

    # 3. Muse Spark writes alt text and labels each region.
    try:
        alt = meta_client.describe_figure(crop_png, context, regions)
        block["alt_short"] = alt.get("alt_short", "")
        block["alt_long"] = alt.get("alt_long", "")
        block["error"] = None

        by_number = {r["region"]: r for r in regions}
        parts = []
        for p in alt.get("parts", []):
            try:
                region = by_number.get(int(p.get("region", 0)))
            except (TypeError, ValueError):
                region = None
            if region:
                parts.append({
                    "label": p.get("label", region["kind"]),
                    "description": p.get("description", ""),
                    "kind": region["kind"],
                    "box": region["box"],  # [left, top, right, bottom], 0-1 fractions
                })
        block["parts"] = parts
    except Exception as e:
        block["alt_short"] = block.get("caption_guess", "")
        block["alt_long"] = ""
        block["parts"] = []
        block["error"] = f"Alt text could not be drafted: {e}"

    block["status"] = "needs_review"  # a human always approves figure descriptions