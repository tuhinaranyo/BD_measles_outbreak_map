from __future__ import annotations

import argparse
import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from measles_dashboard.config import DATA_DIR, DB_PATH, RAW_PDF_DIR
from measles_dashboard.db import init_db
from measles_dashboard.extractor import extract_pdf_to_db
from measles_dashboard.scraper import (
    collect_and_download_new_reports,
    collect_and_download_reports,
    ensure_report_pdf,
)

UPDATE_LOG_PATH = DATA_DIR / "last_update.json"


def _reports_to_retry() -> list[Path]:
    """Return PDF paths for reports that previously failed extraction."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT report_date, pdf_url, pdf_path
            FROM reports
            WHERE status IN ('needs_review', 'downloaded', 'pdf_not_found')
            ORDER BY report_date DESC
            """
        ).fetchall()
    paths: list[Path] = []
    for row in rows:
        local = ensure_report_pdf(
            str(row["report_date"]),
            pdf_url=row["pdf_url"],
            pdf_path=row["pdf_path"],
        )
        if local:
            paths.append(local)
    return paths


def _write_run_log(*, source: str, processed: int, errors: list[str], extra: dict | None = None) -> None:
    """Heartbeat file. Always committed by the workflow so the schedule stays
    alive past 60 days of inactivity and so failures are visible in git history.
    """
    UPDATE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        latest = conn.execute(
            "SELECT MAX(report_date) AS latest FROM reports WHERE status = 'extracted'"
        ).fetchone()
        status_counts = {
            row["status"]: row["n"]
            for row in conn.execute("SELECT status, COUNT(*) AS n FROM reports GROUP BY status").fetchall()
        }
    payload: dict = {
        "ran_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source,
        "processed_pdfs": processed,
        "errors": errors[:25],
        "latest_extracted": latest["latest"] if latest else None,
        "status_counts": status_counts,
    }
    if extra:
        payload.update(extra)
    UPDATE_LOG_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Download and extract DGHS measles reports.")
    parser.add_argument("--local-only", action="store_true", help="Only extract PDFs already in data/raw_pdfs.")
    parser.add_argument("--new-only", action="store_true", help="Only download/extract dates we have not yet extracted.")
    parser.add_argument("--retry-failed", action="store_true", help="Also re-extract PDFs in needs_review/downloaded state.")
    parser.add_argument("--max-pages", type=int, default=12, help="Maximum listing pages to scan.")
    parser.add_argument("--limit", type=int, default=None, help="Stop after this many reports.")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    DATA_DIR.mkdir(exist_ok=True)
    RAW_PDF_DIR.mkdir(parents=True, exist_ok=True)
    init_db()

    errors: list[str] = []
    pdfs: list[Path] = []
    source_label = "local-only" if args.local_only else ("new-only" if args.new_only else "full-refresh")

    try:
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
    except Exception as exc:
        errors.append(f"scrape: {type(exc).__name__}: {exc}")
        logging.exception("Scrape phase failed")

    if args.retry_failed:
        retry_paths = _reports_to_retry()
        added = [p for p in retry_paths if p not in pdfs]
        if added:
            print(f"Also retrying {len(added)} previously-failed PDF(s).")
        pdfs = sorted(set(pdfs) | set(retry_paths))

    for pdf_path in pdfs:
        try:
            extract_pdf_to_db(pdf_path)
        except Exception as exc:
            err = f"{pdf_path.name}: {type(exc).__name__}: {exc}"
            errors.append(err)
            logging.exception("Extract failed for %s", pdf_path)

    _write_run_log(source=source_label, processed=len(pdfs), errors=errors)

    print(f"Done. Checked {len(pdfs)} PDF file(s); {len(errors)} error(s).")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
