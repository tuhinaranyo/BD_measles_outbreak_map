# DGHS Measles Dashboard

A Streamlit dashboard for collecting DGHS Bangla measles press-release PDFs, extracting division-level measles data, validating the extraction, and showing public-friendly trends.

Project name: `dghs-measles-dashboard`

## Features

- Downloads DGHS measles press-release PDFs.
- Extracts division-wise suspected, confirmed, death, admission, and discharge numbers.
- Validates extracted tables before showing them publicly.
- Hides unsafe reports from the public dashboard until reviewed.
- Provides an admin page for PDF review and manual data correction.
- Supports daily scheduled updates on Windows.

## Pages

- Public dashboard: `http://localhost:8501/`
- Admin page: `http://localhost:8501/admin`

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
```

## Download and Extract Reports

```powershell
.\.venv\Scripts\python update_data.py
```

This downloads measles PDFs from:

https://dghs.gov.bd/pages/press-releases/

PDFs are stored in `data/raw_pdfs`, extracted text/debug files in `data/extracted_text`, and the SQLite database in `data/measles.db`.

## Run The App

```powershell
.\.venv\Scripts\streamlit run app.py
```

## Admin

Open:

```text
http://localhost:8501/admin
```

There you can:

- Check DGHS for new PDFs and extract them.
- Preview a saved PDF by date.
- Manually edit division data for a report date.
- Mark a corrected report as reviewed so it appears in the dashboard.

## Daily Update

For Windows Task Scheduler, create a daily task that runs:

```powershell
powershell.exe -ExecutionPolicy Bypass -File "C:\Users\Tuhin\Documents\Codex\2026-05-16\files-mentioned-by-the-user-a359ad71\run_daily_update.ps1"
```

Good timing is evening Bangladesh time, after DGHS usually posts the day’s file. The updater is safe to run repeatedly; already-downloaded PDFs are checked and skipped unless missing.

## Import a PDF Manually

Put any DGHS measles PDF in `data/raw_pdfs`, then run:

```powershell
.\.venv\Scripts\python update_data.py --local-only
```

The extractor validates every report against the `মোট` row when possible. If a PDF layout changes or text extraction fails, the report is marked for review instead of silently showing wrong numbers.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Admin guide](docs/ADMIN_GUIDE.md)
