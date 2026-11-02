"""MathReady API. Run from backend/:  uvicorn app.main:app --reload --port 8000"""
import copy
import uuid

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import export, pipeline, store
from .config import DATA_DIR, FRONTEND_ORIGINS

app = FastAPI(title="MathReady API")

# Let the frontend (port 5173) call this server (port 8000).
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve page images and figure crops, e.g. /files/<doc_id>/pages/1.png
app.mount("/files", StaticFiles(directory=DATA_DIR), name="files")


def get_doc(doc_id: str) -> dict:
    try:
        return store.load(doc_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")


def with_urls(doc: dict) -> dict:
    """Copy of the doc with image paths turned into URLs the browser can load."""
    out = copy.deepcopy(doc)
    base = f"/files/{doc['doc_id']}/"
    for page in out["pages"]:
        page["image"] = base + page["image"]
        for block in page["blocks"]:
            if block.get("image"):
                block["image"] = base + block["image"]
    return out


@app.post("/api/documents")
async def upload(background: BackgroundTasks, file: UploadFile = File(...), title: str = Form("")):
    """Receive a PDF, return its new id right away, and process it in the background."""
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF")
    pdf_bytes = await file.read()

    doc_id = uuid.uuid4().hex[:12]
    doc = {
        "doc_id": doc_id,
        "title": title.strip() or (file.filename or "Document").rsplit(".", 1)[0],
        "state": "processing",
        "progress": "Starting",
        "pages": [],
    }
    store.save(doc)
    background.add_task(pipeline.process, doc_id, pdf_bytes)
    return {"doc_id": doc_id}


@app.get("/api/documents/{doc_id}")
def read_document(doc_id: str):
    """The whole document: state, progress, pages and blocks."""
    return with_urls(get_doc(doc_id))


class BlockEdit(BaseModel):
    """Fields the review screen can change. Anything left out stays the same."""
    text: str | None = None
    latex: str | None = None
    alt_short: str | None = None
    alt_long: str | None = None
    approve: bool = False


@app.patch("/api/documents/{doc_id}/blocks/{block_id}")
def edit_block(doc_id: str, block_id: str, edit: BlockEdit):
    """Save an edit and/or approve a block. Returns the updated block."""
    doc = get_doc(doc_id)
    try:
        block = store.find_block(doc, block_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Block not found")

    changes = edit.model_dump(exclude_none=True, exclude={"approve"})
    previous_status = block.get("status")
    block.update(changes)
    if changes and block["type"] != "figure":
        pipeline.finalize_block(block)  # regenerate MathML / inline HTML from the edit
        if block["status"] != "needs_review" or previous_status == "approved":
            block["status"] = previous_status if previous_status != "approved" else block["status"]

    if edit.approve and not block.get("error"):
        block["status"] = "approved"

    store.save(doc)
    base = f"/files/{doc_id}/"
    result = dict(block)
    if result.get("image"):
        result["image"] = base + result["image"]
    return result


@app.get("/api/documents/{doc_id}/export")
def export_document(doc_id: str):
    """Download the accessible HTML. Blocked until every flagged item is reviewed."""
    doc = get_doc(doc_id)
    remaining = export.pending_review(doc)
    if remaining:
        raise HTTPException(status_code=409, detail=f"{remaining} items still need review")
    filename = "".join(c if c.isalnum() else "-" for c in doc["title"]).strip("-") or "document"
    return Response(
        export.build_html(doc),
        media_type="text/html",
        headers={"Content-Disposition": f'attachment; filename="{filename}.html"'},
    )