from __future__ import annotations

import argparse
from pathlib import Path

from measles_dashboard.config import DATA_DIR, RAW_PDF_DIR
from measles_dashboard.db import init_db
from measles_dashboard.extractor import extract_pdf_to_db
from measles_dashboard.scraper import collect_and_download_new_reports, collect_and_download_reports


def main() -> None:
    parser = argparse.ArgumentParser(description="Download and extract DGHS measles reports.")
    parser.add_argument("--local-only", action="store_true", help="Only extract PDFs already in data/raw_pdfs.")
    parser.add_argument("--new-only", action="store_true", help="Only download/extract reports that are not already extracted.")
    parser.add_argument("--max-pages", type=int, default=12, help="Maximum listing pages to scan.")
    parser.add_argument("--limit", type=int, default=None, help="Stop after this many reports.")
    args = parser.parse_args()

    DATA_DIR.mkdir(exist_ok=True)
    RAW_PDF_DIR.mkdir(parents=True, exist_ok=True)
    init_db()

    if args.local_only:
        pdfs = sorted(RAW_PDF_DIR.glob("*.pdf"))
        if args.limit:
            pdfs = pdfs[: args.limit]
    elif args.new_only:
        pdfs, skipped = collect_and_download_new_reports(max_pages=args.max_pages, limit=args.limit)
        print(f"Skipped {skipped} already-extracted report(s).")
    else:
        collect_and_download_reports(max_pages=args.max_pages, limit=args.limit)
        pdfs = sorted(RAW_PDF_DIR.glob("*.pdf"))
        if args.limit:
            pdfs = pdfs[: args.limit]

    for pdf_path in pdfs:
        extract_pdf_to_db(pdf_path)

    print(f"Done. Checked {len(pdfs)} PDF file(s).")


if __name__ == "__main__":
    main()
