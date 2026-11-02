"""Tiny file-based storage: each document lives in data/docs/<doc_id>/."""
import json
import threading
from pathlib import Path

from .config import DATA_DIR

# Only one thread writes doc.json at a time (processing runs in the background).
_lock = threading.Lock()


def doc_dir(doc_id: str) -> Path:
    """Folder for one document: its JSON, page images and figure crops."""
    return DATA_DIR / doc_id


def load(doc_id: str) -> dict:
    """Read a document's JSON. Raises FileNotFoundError if it doesn't exist."""
    return json.loads((doc_dir(doc_id) / "doc.json").read_text())


def save(doc: dict) -> None:
    """Write a document's JSON safely."""
    with _lock:
        folder = doc_dir(doc["doc_id"])
        folder.mkdir(parents=True, exist_ok=True)
        tmp = folder / "doc.json.tmp"
        tmp.write_text(json.dumps(doc, indent=2))
        tmp.replace(folder / "doc.json")  # swap in the new file in one step


def find_block(doc: dict, block_id: str) -> dict:
    """Return the block with this id, searching every page."""
    for page in doc["pages"]:
        for block in page["blocks"]:
            if block["id"] == block_id:
                return block
    raise KeyError(block_id)