"""
MathReady step 1: can Muse Spark read a math page into structured LaTeX?

Setup:
  pip install openai pymupdf latex2mathml
  export META_API_KEY=...            # from the hackathon dashboard
  export META_MODEL=...              # exact Muse Spark model ID from Meta's API docs
  export META_BASE_URL=https://api.meta.ai/v1   # confirm in Meta's docs

Run:
  python test_meta.py lecture.pdf 1      # PDF path, page number (1-based)
"""
from dotenv import load_dotenv
load_dotenv()

import base64, json, os, sys

import fitz  # PyMuPDF
from latex2mathml.converter import convert
from openai import OpenAI

PROMPT = """You are converting a page of STEM course material into structured data.
Return ONLY JSON: {"blocks": [...]} in reading order. Each block is one of:
  {"type":"heading","level":1-3,"text":"..."}
  {"type":"paragraph","text":"..."}   (inline math written as \\( ... \\))
  {"type":"equation","latex":"...","display":true}
  {"type":"figure","bbox":[x0,y0,x1,y1],"caption_guess":"..."}  (pixel coords)
Add "confidence": 0-1 to every equation. Transcribe math exactly; do not solve or simplify."""


def page_png(pdf_path: str, page_no: int) -> bytes:
    doc = fitz.open(pdf_path)
    return doc[page_no - 1].get_pixmap(dpi=200).tobytes("png")


def main():
    pdf_path, page_no = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1
    img_b64 = base64.b64encode(page_png(pdf_path, page_no)).decode()

    client = OpenAI(
        api_key=os.environ["META_API_KEY"],
        base_url=os.environ.get("META_BASE_URL", "https://api.meta.ai/v1"),
    )
    resp = client.chat.completions.create(
        model=os.environ["META_MODEL"],
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
            ],
        }],
    )
    raw = resp.choices[0].message.content
    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
    blocks = json.loads(raw)["blocks"]

    ok = bad = 0
    for b in blocks:
        if b["type"] == "equation":
            try:
                convert(b["latex"])
                ok += 1
                print(f"[OK  {b.get('confidence', '?')}] {b['latex']}")
            except Exception as e:
                bad += 1
                print(f"[BAD] {b['latex']}  ({e})")
        else:
            print(f"[{b['type']}] {str(b.get('text') or b.get('caption_guess', ''))[:80]}")

    print(f"\nEquations: {ok} converted, {bad} failed. Usage: {resp.usage}")
    os.makedirs("out", exist_ok=True)
    with open(f"out/page{page_no}.json", "w") as f:
        json.dump(blocks, f, indent=2)


if __name__ == "__main__":
    main()
