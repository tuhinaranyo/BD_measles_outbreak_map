from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from measles_dashboard.config import DB_PATH, RAW_PDF_DIR


def _portable_pdf_path(report_date: str, pdf_path: str | None) -> str | None:
    """Store only a repo-relative filename — never an absolute local path."""
    if not pdf_path:
        return None
    name = Path(pdf_path).name
    if name.endswith(".pdf"):
        return f"data/raw_pdfs/{name}"
    return f"data/raw_pdfs/{report_date}.pdf"


def main() -> None:
    output_path = Path("data/seed_data.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        reports = [
            dict(row)
            for row in conn.execute(
                """
                SELECT report_date, title, page_url, pdf_url, pdf_path, status,
                       validation_message, downloaded_at, extracted_at
                FROM reports
                WHERE status = 'extracted'
                ORDER BY report_date
                """
            )
        ]
        stats = [
            dict(row)
            for row in conn.execute(
                """
                SELECT *
                FROM division_daily_stats
                WHERE report_date IN (
                    SELECT report_date FROM reports WHERE status = 'extracted'
                )
                ORDER BY report_date, division
                """
            )
        ]

    for report in reports:
        report["pdf_path"] = _portable_pdf_path(
            str(report["report_date"]),
            report.get("pdf_path"),
        )

    output_path.write_text(
        json.dumps({"reports": reports, "division_daily_stats": stats}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Exported {len(reports)} reports and {len(stats)} division rows to {output_path}")


if __name__ == "__main__":
    main()
