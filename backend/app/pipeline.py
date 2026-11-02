"""PDF -> page images -> Muse Spark blocks -> MathML + figure alt text."""
import html
import io
import re
import traceback

import pymupdf
from latex2mathml.converter import convert
from PIL import Image

from . import meta_client, sam, store
from .config import MAX_PAGES

REVIEW_THRESHOLD = 0.9          # equations below this confidence get flagged
INLINE_MATH = re.compile(r"\\\((.+?)\\\)")   # matches \( ... \)


def to_mathml(latex: str, display: bool = True) -> str:
    return convert(latex, display="block" if display else "inline")


def render_inline(text: str) -> str:
    """Text with \\( ... \\) math -> safe HTML with inline MathML."""
    out, last = [], 0
    for m in INLINE_MATH.finditer(text or ""):
        out.append(html.escape(text[last:m.start()]))
        try:
            out.append(to_mathml(m.group(1), display=False))
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
    """Crop the figure from the page, segment it, and draft alt text."""
    img = Image.open(io.BytesIO(page_png))
    x0, y0, x1, y1 = [int(v) for v in block.get("bbox") or [0, 0, img.width, img.height]]
    pad = int(0.03 * max(img.width, img.height))  # about 50px at 200 dpi
    crop = img.crop((max(0, x0 - pad), max(0, y0 - pad), min(img.width, x1 + pad), min(img.height, y1 + pad)))
    buf = io.BytesIO()
    crop.save(buf, "PNG")
    crop_png = buf.getvalue()
    (folder / "figures" / f"{block['id']}.png").write_bytes(crop_png)
    block["image"] = f"figures/{block['id']}.png"

    regions = sam.segment(crop_png)
    block["segments"] = regions
    try:
        alt = meta_client.describe_figure(crop_png, context, [r.get("label", "") for r in regions])
        block["alt_short"] = alt.get("alt_short", "")
        block["alt_long"] = alt.get("alt_long", "")
        block["error"] = None
    except Exception as e:
        block["alt_short"] = block.get("caption_guess", "")
        block["alt_long"] = ""
        block["error"] = f"Alt text could not be drafted: {e}"
    block["status"] = "needs_review"  # a human always approves figure descriptions