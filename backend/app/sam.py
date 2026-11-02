"""SAM 3.1 segmentation: find named parts of a figure and return their boxes."""
import base64
import re

from . import config
from .meta_client import client

# Each object SAM finds appears as:  <id><|box;x1=..;y1=..;x2=..;y2=..;w=..;h=..|>
BOX = re.compile(r"(\d+)<\|box;([^|]*)\|>")
MIN_SIZE = 0.03  # ignore boxes smaller than 3% of the image (e.g. tiny vector arrows over letters)


def _parse_boxes(text: str) -> list[dict]:
    boxes = []
    for _obj_id, fields in BOX.findall(text):
        v = dict(part.split("=", 1) for part in fields.split(";") if "=" in part)
        try:
            boxes.append({k: float(v[k]) for k in ("x1", "y1", "x2", "y2", "w", "h")})
        except (KeyError, ValueError):
            continue  # skip a malformed record instead of failing
    return boxes


def find(png: bytes, label: str) -> list[list[float]]:
    """Find every instance of `label` in the image.

    Returns boxes as [left, top, right, bottom] in fractions of the image (0-1),
    so the frontend can position them at any display size.
    """
    data_url = "data:image/png;base64," + base64.b64encode(png).decode()
    raw = ""
    with client().responses.stream(
        model=config.META_SAM_MODEL,
        input=[{
            "type": "message",
            "role": "user",
            "content": [
                {"type": "input_text", "text": label},
                {"type": "input_image", "image_url": data_url},
            ],
        }],
    ) as stream:
        for event in stream:
            if event.type == "response.output_text.delta":
                raw += event.delta

    results = []
    for b in _parse_boxes(raw):
        width = (b["x2"] - b["x1"]) / b["w"]
        height = (b["y2"] - b["y1"]) / b["h"]
        if width < MIN_SIZE or height < MIN_SIZE:
            continue  # too small to be a real part
        results.append([
            round(b["x1"] / b["w"], 4),
            round(b["y1"] / b["h"], 4),
            round(b["x2"] / b["w"], 4),
            round(b["y2"] / b["h"], 4),
        ])
    return results