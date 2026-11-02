"""Settings loaded from the .env file in the repo root."""
import os
from pathlib import Path

from dotenv import load_dotenv

# This file is MathReady/backend/app/config.py, so the repo root is two folders up.
REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env", override=True)

META_API_KEY = os.getenv("META_API_KEY", "")
META_BASE_URL = os.getenv("META_BASE_URL", "https://api.meta.ai/v1")
META_MODEL = os.getenv("META_MODEL", "muse-spark-1.3")
META_SAM_MODEL = os.getenv("META_SAM_MODEL", "sam-3.1")

# Uploaded PDFs, page images and figure crops are saved here (git-ignored via data/).
DATA_DIR = REPO_ROOT / "data" / "docs"
DATA_DIR.mkdir(parents=True, exist_ok=True)

MAX_PAGES = 30

# The frontend's address, so the browser is allowed to call this API.
FRONTEND_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]