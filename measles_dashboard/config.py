from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_PDF_DIR = DATA_DIR / "raw_pdfs"
TEXT_DIR = DATA_DIR / "extracted_text"
DB_PATH = DATA_DIR / "measles.db"

PRESS_RELEASE_URL = "https://dghs.gov.bd/pages/press-releases/"
BASE_URL = "https://dghs.gov.bd"

DIVISIONS = [
    "ঢাকা",
    "রাজশাহী",
    "চট্টগ্রাম",
    "বরিশাল",
    "সিলেট",
    "ময়মনসিংহ",
    "খুলনা",
    "রংপুর",
]
