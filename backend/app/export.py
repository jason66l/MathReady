"""Builds one self-contained, accessible HTML file from a reviewed document."""
import base64
import html

from . import store
from .pipeline import render_inline

CSS = """body{font-family:system-ui,-apple-system,sans-serif;max-width:46rem;margin:2rem auto;padding:0 1rem;line-height:1.6;color:#111}
img{max-width:100%;height:auto}figure{margin:1.5rem 0}
math[display=block]{margin:1rem 0;font-size:1.15em}
table{border-collapse:collapse;margin:1rem 0}th,td{border:1px solid #999;padding:.35rem .7rem;text-align:center}
caption{font-weight:600;margin-bottom:.4rem}summary{cursor:pointer}"""


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
    long_desc = html.escape(block.get("alt_long", ""))
    caption = (
        f"<figcaption><details><summary>Full description</summary><p>{long_desc}</p></details></figcaption>"
        if long_desc else ""
    )
    return f'<figure><img src="{src}" alt="{alt}">{caption}</figure>'


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
        f"<body>\n<main>\n<h1>{title}</h1>\n{body}\n</main>\n</body>\n</html>\n"
    )


def pending_review(doc: dict) -> int:
    """How many blocks still need a human to check them."""
    return sum(1 for p in doc["pages"] for b in p["blocks"] if b.get("status") == "needs_review")