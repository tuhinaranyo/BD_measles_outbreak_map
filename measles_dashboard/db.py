from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from .config import DB_PATH, DIVISIONS, ROOT

SEED_PATH = ROOT / "data" / "seed_data.json"


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_date TEXT UNIQUE,
                title TEXT,
                page_url TEXT,
                pdf_url TEXT,
                pdf_path TEXT,
                status TEXT NOT NULL DEFAULT 'new',
                validation_message TEXT,
                downloaded_at TEXT DEFAULT CURRENT_TIMESTAMP,
                extracted_at TEXT
            );

            CREATE TABLE IF NOT EXISTS division_daily_stats (
                report_date TEXT NOT NULL,
                division TEXT NOT NULL,
                suspected_24h INTEGER,
                suspected_deaths_24h INTEGER,
                confirmed_24h INTEGER,
                confirmed_deaths_24h INTEGER,
                admitted_24h INTEGER,
                discharged_24h INTEGER,
                suspected_total INTEGER,
                suspected_deaths_total INTEGER,
                confirmed_total INTEGER,
                confirmed_deaths_total INTEGER,
                admitted_total INTEGER,
                discharged_total INTEGER,
                PRIMARY KEY (report_date, division)
            );

            CREATE TABLE IF NOT EXISTS extraction_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_date TEXT,
                pdf_path TEXT,
                note TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
    seed_if_empty()
    sync_seed_extracted()


def seed_if_empty() -> None:
    if not SEED_PATH.exists():
        return
    with connect() as conn:
        stats_count = conn.execute("SELECT COUNT(*) FROM division_daily_stats").fetchone()[0]
        reports_count = conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
        if stats_count or reports_count:
            return

        seed = json.loads(SEED_PATH.read_text(encoding="utf-8"))
        reports = seed.get("reports", [])
        stats = seed.get("division_daily_stats", [])

        conn.executemany(
            """
            INSERT OR REPLACE INTO reports (
                report_date, title, page_url, pdf_url, pdf_path, status,
                validation_message, downloaded_at, extracted_at
            )
            VALUES (
                :report_date, :title, :page_url, :pdf_url, :pdf_path, :status,
                :validation_message, :downloaded_at, :extracted_at
            )
            """,
            reports,
        )
        conn.executemany(
            """
            INSERT OR REPLACE INTO division_daily_stats (
                report_date, division,
                suspected_24h, suspected_deaths_24h, confirmed_24h, confirmed_deaths_24h,
                admitted_24h, discharged_24h,
                suspected_total, suspected_deaths_total, confirmed_total, confirmed_deaths_total,
                admitted_total, discharged_total
            )
            VALUES (
                :report_date, :division,
                :suspected_24h, :suspected_deaths_24h, :confirmed_24h, :confirmed_deaths_24h,
                :admitted_24h, :discharged_24h,
                :suspected_total, :suspected_deaths_total, :confirmed_total, :confirmed_deaths_total,
                :admitted_total, :discharged_total
            )
            """,
            stats,
        )


def sync_seed_extracted() -> None:
    """Refresh DB rows from seed_data.json when local extraction failed.

    Streamlit Cloud admin can leave ``needs_review`` rows in the ephemeral
    SQLite file (e.g. before an extractor fix was deployed). Seed data is
    the authoritative public dataset — overwrite any non-extracted row for
    dates that seed already validated.
    """
    if not SEED_PATH.exists():
        return

    seed = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    reports = [r for r in seed.get("reports", []) if r.get("status") == "extracted"]
    if not reports:
        return

    stats = seed.get("division_daily_stats", [])
    stats_by_date: dict[str, list[dict]] = {}
    for row in stats:
        stats_by_date.setdefault(str(row["report_date"]), []).append(row)

    with connect() as conn:
        for report in reports:
            report_date = str(report["report_date"])
            existing = conn.execute(
                "SELECT status FROM reports WHERE report_date = ?",
                (report_date,),
            ).fetchone()
            if existing and str(existing["status"]) == "extracted":
                continue

            day_stats = stats_by_date.get(report_date, [])
            if len({row["division"] for row in day_stats}) < len(DIVISIONS):
                continue

            conn.execute("DELETE FROM division_daily_stats WHERE report_date = ?", (report_date,))
            conn.executemany(
                """
                INSERT OR REPLACE INTO division_daily_stats (
                    report_date, division,
                    suspected_24h, suspected_deaths_24h, confirmed_24h, confirmed_deaths_24h,
                    admitted_24h, discharged_24h,
                    suspected_total, suspected_deaths_total, confirmed_total, confirmed_deaths_total,
                    admitted_total, discharged_total
                )
                VALUES (
                    :report_date, :division,
                    :suspected_24h, :suspected_deaths_24h, :confirmed_24h, :confirmed_deaths_24h,
                    :admitted_24h, :discharged_24h,
                    :suspected_total, :suspected_deaths_total, :confirmed_total, :confirmed_deaths_total,
                    :admitted_total, :discharged_total
                )
                """,
                day_stats,
            )
            conn.execute(
                """
                INSERT INTO reports (
                    report_date, title, page_url, pdf_url, pdf_path, status,
                    validation_message, downloaded_at, extracted_at
                )
                VALUES (
                    :report_date, :title, :page_url, :pdf_url, :pdf_path, :status,
                    :validation_message, :downloaded_at, :extracted_at
                )
                ON CONFLICT(report_date) DO UPDATE SET
                    title = excluded.title,
                    page_url = excluded.page_url,
                    pdf_url = COALESCE(excluded.pdf_url, reports.pdf_url),
                    pdf_path = excluded.pdf_path,
                    status = excluded.status,
                    validation_message = excluded.validation_message,
                    extracted_at = excluded.extracted_at
                """,
                report,
            )


def report_status(report_date: str | None) -> str | None:
    if not report_date:
        return None
    with connect() as conn:
        row = conn.execute("SELECT status FROM reports WHERE report_date = ?", (report_date,)).fetchone()
    return str(row["status"]) if row else None


def latest_report_date() -> str | None:
    with connect() as conn:
        row = conn.execute("SELECT MAX(report_date) AS latest FROM reports").fetchone()
    return str(row["latest"]) if row and row["latest"] else None


def report_exists(report_date: str | None) -> bool:
    return report_status(report_date) is not None


def report_is_extracted(report_date: str | None) -> bool:
    return report_status(report_date) == "extracted"


def upsert_report(
    *,
    report_date: str | None,
    title: str,
    page_url: str,
    pdf_url: str | None,
    pdf_path: Path | None,
    status: str = "downloaded",
    validation_message: str | None = None,
) -> None:
    key_date = report_date or Path(pdf_path or page_url).stem
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO reports (report_date, title, page_url, pdf_url, pdf_path, status, validation_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(report_date) DO UPDATE SET
                title=excluded.title,
                page_url=excluded.page_url,
                pdf_url=COALESCE(excluded.pdf_url, reports.pdf_url),
                pdf_path=COALESCE(excluded.pdf_path, reports.pdf_path),
                status=excluded.status,
                validation_message=excluded.validation_message
            """,
            (key_date, title, page_url, pdf_url, str(pdf_path) if pdf_path else None, status, validation_message),
        )


def save_stats(report_date: str, rows: Iterable[dict], status: str, message: str | None) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM division_daily_stats WHERE report_date = ?", (report_date,))
        conn.executemany(
            """
            INSERT INTO division_daily_stats (
                report_date, division,
                suspected_24h, suspected_deaths_24h, confirmed_24h, confirmed_deaths_24h,
                admitted_24h, discharged_24h,
                suspected_total, suspected_deaths_total, confirmed_total, confirmed_deaths_total,
                admitted_total, discharged_total
            )
            VALUES (
                :report_date, :division,
                :suspected_24h, :suspected_deaths_24h, :confirmed_24h, :confirmed_deaths_24h,
                :admitted_24h, :discharged_24h,
                :suspected_total, :suspected_deaths_total, :confirmed_total, :confirmed_deaths_total,
                :admitted_total, :discharged_total
            )
            """,
            rows,
        )
        conn.execute(
            """
            UPDATE reports
            SET status = ?, validation_message = ?, extracted_at = CURRENT_TIMESTAMP
            WHERE report_date = ?
            """,
            (status, message, report_date),
        )


def add_note(report_date: str | None, pdf_path: Path, note: str) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO extraction_notes (report_date, pdf_path, note) VALUES (?, ?, ?)",
            (report_date, str(pdf_path), note),
        )
