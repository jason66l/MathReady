"""Builds one self-contained, accessible HTML file from a reviewed document."""
import base64
import html

from . import store
from .pipeline import render_inline

CSS = """body{font-family:system-ui,-apple-system,sans-serif;max-width:46rem;margin:2rem auto;padding:0 1rem;line-height:1.6;color:#111}
img{max-width:100%;height:auto}figure{margin:1.5rem 0}
math[display=block]{margin:1rem 0;font-size:1.15em}
table{border-collapse:collapse;margin:1rem 0}th,td{border:1px solid #999;padding:.35rem .7rem;text-align:center}
caption{font-weight:600;margin-bottom:.4rem}summary{cursor:pointer}
.stage{position:relative;display:inline-block;max-width:100%}.stage img{display:block}
.part{position:absolute;border:2px solid transparent;border-radius:4px;pointer-events:none}
.part.on{border:3px solid #e11d48;background:rgba(225,29,72,.12)}
.parts{margin:.5rem 0 0;padding-left:1.4rem}
.parts button{all:unset;cursor:pointer;padding:.2rem .3rem;border-radius:4px}
.parts button:focus-visible,.parts button:hover{outline:3px solid #2357d9;background:#eef2fd}"""

# Highlights a figure part on the image when its list item is focused or hovered.
SCRIPT = """document.querySelectorAll('[data-part]').forEach(function(btn){
  var box=document.getElementById(btn.dataset.part);
  function on(){box.classList.add('on')} function off(){box.classList.remove('on')}
  btn.addEventListener('focus',on);btn.addEventListener('blur',off);
  btn.addEventListener('mouseenter',on);btn.addEventListener('mouseleave',off);
});"""


def _table(block: dict) -> str:
    caption = f"<caption>{render_inline(block['caption'])}</caption>" if block.get("caption") else ""
    head = "".join(f'<th scope="col">{render_inline(h)}</th>' for h in block.get("headers", []))
    body = "".join(
        "<tr>" + "".join(f"<td>{render_inline(str(c))}</td>" for c in row) + "</tr>"
        for row in block.get("rows", [])
    )
    return f"<table>{caption}<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def _figure(doc_id: str, block: dict) -> str:
    # Embed the image directly in the HTML so the file works on its own.
    src = ""
    if block.get("image"):
        path = store.doc_dir(doc_id) / block["image"]
        if path.exists():
            src = "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()
    alt = html.escape(block.get("alt_short", ""), quote=True)

    # Outlined boxes over the image (visual only) + a focusable list of parts.
    boxes, items = "", ""
    for i, part in enumerate(block.get("parts") or []):
        box = part.get("box") or [0, 0, 0, 0]
        box_id = f"{block['id']}-part{i + 1}"
        boxes += (
            f'<span class="part" id="{box_id}" aria-hidden="true" style="left:{box[0] * 100:.1f}%;'
            f'top:{box[1] * 100:.1f}%;width:{(box[2] - box[0]) * 100:.1f}%;height:{(box[3] - box[1]) * 100:.1f}%"></span>'
        )
        label = html.escape(part.get("label", f"Part {i + 1}"))
        desc = html.escape(part.get("description", ""))
        items += f'<li><button type="button" data-part="{box_id}"><strong>{label}:</strong> {desc}</button></li>'

    explore = ""
    if items:
        explore = (
            f'<h3 class="explore-heading" id="{block["id"]}-explore">Explore this diagram</h3>'
            f'<ol class="parts" aria-labelledby="{block["id"]}-explore">{items}</ol>'
        )

    long_desc = html.escape(block.get("alt_long", ""))
    details = (
        f"<details><summary>Full description</summary><p>{long_desc}</p></details>" if long_desc else ""
    )
    caption = f"<figcaption>{explore}{details}</figcaption>" if (explore or details) else ""
    return f'<figure><div class="stage"><img src="{src}" alt="{alt}">{boxes}</div>{caption}</figure>'


def build_html(doc: dict) -> str:
    parts = []
    for page in doc["pages"]:
        for block in page["blocks"]:
            kind = block.get("type")
            if kind == "heading":
                level = min(max(int(block.get("level", 1)), 1), 3) + 1  # h1 is the document title
                parts.append(f"<h{level}>{render_inline(block.get('text', ''))}</h{level}>")
            elif kind == "paragraph":
                parts.append(f"<p>{render_inline(block.get('text', ''))}</p>")
            elif kind == "equation":
                parts.append(block.get("mathml", ""))
            elif kind == "table":
                parts.append(_table(block))
            elif kind == "figure":
                parts.append(_figure(doc["doc_id"], block))

    title = html.escape(doc.get("title", "Course document"))
    body = "\n".join(parts)
    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{title}</title>\n<style>{CSS}</style>\n</head>\n"
        f"<body>\n<main>\n<h1>{title}</h1>\n{body}\n</main>\n<script>{SCRIPT}</script>\n</body>\n</html>\n"
    )


def pending_review(doc: dict) -> int:
    """How many blocks still need a human to check them."""
    return sum(1 for p in doc["pages"] for b in p["blocks"] if b.get("status") == "needs_review")