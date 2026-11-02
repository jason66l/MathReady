"""
SAM 3.1 go/no-go test: does it find the parts of a diagram?

Run from the repo root:
  python backend/scripts/test_sam.py data/docs/<doc_id>/figures/p1b5.png "arrow"
"""
import base64
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image, ImageDraw

load_dotenv(override=True)

# Each object SAM finds appears as:  <id><|box;x1=..;y1=..;x2=..;y2=..;w=..;h=..|>
BOX = re.compile(r"(\d+)<\|box;([^|]*)\|>")


def parse_boxes(text: str) -> list[dict]:
    boxes = []
    for obj_id, fields in BOX.findall(text):
        values = dict(part.split("=", 1) for part in fields.split(";") if "=" in part)
        boxes.append({"id": int(obj_id), **{k: float(v) for k, v in values.items()}})
    return boxes


def main():
    image_path, label = sys.argv[1], sys.argv[2]
    png = Path(image_path).read_bytes()
    data_url = "data:image/png;base64," + base64.b64encode(png).decode()

    client = OpenAI(
        api_key=os.environ["META_API_KEY"],
        base_url=os.environ.get("META_BASE_URL", "https://api.meta.ai/v1"),
    )

    raw = ""
    with client.responses.stream(
        model=os.environ.get("META_SAM_MODEL", "sam-3.1"),
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

    print("RAW OUTPUT (first 600 chars):")
    print(raw[:600] or "(empty: SAM found nothing)")

    boxes = parse_boxes(raw)
    print(f"\nFound {len(boxes)} object(s) for '{label}':")
    for b in boxes:
        print(f"  id {b['id']}: x1={b.get('x1')} y1={b.get('y1')} x2={b.get('x2')} y2={b.get('y2')}  "
              f"(frame {b.get('w')}x{b.get('h')})")

    # Draw the boxes so you can check them by eye.
    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    for b in boxes:
        # If SAM's frame size differs from the image, scale the box to match.
        sx = img.width / b.get("w", img.width)
        sy = img.height / b.get("h", img.height)
        draw.rectangle(
            [b["x1"] * sx, b["y1"] * sy, b["x2"] * sx, b["y2"] * sy], outline=(255, 0, 255), width=4
        )
    os.makedirs("out", exist_ok=True)
    out_path = f"out/sam_{label.replace(' ', '_')}.png"
    img.save(out_path)
    print(f"\nSaved {out_path}: open it to check the boxes.")


if __name__ == "__main__":
    main()