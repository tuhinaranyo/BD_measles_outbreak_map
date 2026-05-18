from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from measles_dashboard.config import DB_PATH


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

    output_path.write_text(
        json.dumps({"reports": reports, "division_daily_stats": stats}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Exported {len(reports)} reports and {len(stats)} division rows to {output_path}")


if __name__ == "__main__":
    main()
