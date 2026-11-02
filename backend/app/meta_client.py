"""Calls to Muse Spark through the Meta Model API (OpenAI-compatible)."""
import base64
import json

from openai import OpenAI

from . import config

PAGE_PROMPT = r"""You are converting a page of STEM course material into structured data for an accessible web version.
Return ONLY JSON: {"blocks": [...]} in reading order. Each block is one of:
  {"type":"heading","level":1-3,"text":"..."}
  {"type":"paragraph","text":"..."}
  {"type":"equation","latex":"...","display":true,"confidence":0-1}
  {"type":"table","caption":"...","headers":["..."],"rows":[["..."]]}
  {"type":"figure","bbox":[x0,y0,x1,y1],"caption_guess":"..."}
Rules:
- Transcribe math exactly. Do not solve, simplify or reformat it.
- Write inline math inside paragraphs as \( ... \).
- Write units with \text{}, e.g. 2.0\,\text{kg}.
- Equation numbers like (1) are not part of the equation.
- Payoff matrices, data grids and anything with rows and columns are tables, not figures. Table cells may contain \( ... \) math.
- Figure bbox is in pixel coordinates of this image and should tightly cover the figure.
- confidence = how sure you are the LaTeX matches the page exactly."""

ALT_PROMPT = """Write alt text for this figure from a STEM course, for a student using a screen reader.
Context from the page: {context}
{segments}
Return ONLY JSON: {{"alt_short": "one sentence naming what the figure shows",
"alt_long": "a structured description: what it depicts, each labeled part, directions, axes and values a student needs to solve the problem"}}"""

_client = None


def client() -> OpenAI:
    """Create the API client once, then reuse it."""
    global _client
    if _client is None:
        if not config.META_API_KEY:
            raise RuntimeError("META_API_KEY is missing. Add it to the .env file in the repo root.")
        _client = OpenAI(api_key=config.META_API_KEY, base_url=config.META_BASE_URL)
    return _client


def _image_part(png: bytes) -> dict:
    """Package PNG bytes the way the API expects an image."""
    b64 = base64.b64encode(png).decode()
    return {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}


def _parse_json(text: str) -> dict:
    """Pull the JSON object out of the model's reply, even if wrapped in ``` fences."""
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"Model did not return JSON: {text[:200]}")
    return json.loads(text[start:end + 1])


def read_page(png: bytes, text_layer: str = "") -> list[dict]:
    """Page image (+ optional embedded PDF text) -> ordered list of blocks."""
    content = [{"type": "text", "text": PAGE_PROMPT}]
    if text_layer.strip():
        content.append({"type": "text", "text": "Embedded PDF text (may help with spelling):\n" + text_layer[:6000]})
    content.append(_image_part(png))

    resp = client().chat.completions.create(
        model=config.META_MODEL,
        messages=[{"role": "user", "content": content}],
    )
    return _parse_json(resp.choices[0].message.content).get("blocks", [])


def describe_figure(png: bytes, context: str = "", segment_labels: list[str] | None = None) -> dict:
    """Figure crop -> {"alt_short": ..., "alt_long": ...}."""
    segments = ""
    if segment_labels:
        segments = "Parts located by segmentation: " + ", ".join(segment_labels)
    prompt = ALT_PROMPT.format(context=context[:1500] or "(none)", segments=segments)

    resp = client().chat.completions.create(
        model=config.META_MODEL,
        messages=[{"role": "user", "content": [{"type": "text", "text": prompt}, _image_part(png)]}],
    )
    return _parse_json(resp.choices[0].message.content)