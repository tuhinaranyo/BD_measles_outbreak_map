from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from .config import DB_PATH, ROOT


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
