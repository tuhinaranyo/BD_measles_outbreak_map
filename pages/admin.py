from __future__ import annotations

import base64
import os
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

from measles_dashboard.config import DB_PATH, DIVISIONS
from measles_dashboard.db import init_db
from measles_dashboard.extractor import extract_pdf_to_db
from measles_dashboard.scraper import collect_and_download_reports
from measles_dashboard.ui import inject_style


st.set_page_config(page_title="DGHS Measles Admin", layout="wide")
inject_style()


def get_admin_password() -> str | None:
    try:
        password = st.secrets.get("ADMIN_PASSWORD")
        if password:
            return str(password)
    except Exception:
        pass
    return os.getenv("ADMIN_PASSWORD")


def require_admin_login() -> None:
    password = get_admin_password()
    if not password:
        st.error("Admin is not configured yet. Add ADMIN_PASSWORD in Streamlit Cloud secrets.")
        st.stop()

    if st.session_state.get("admin_authenticated"):
        return

    st.title("Admin")
    st.caption("Protected workspace for reviewing PDFs and correcting dashboard data.")
    entered = st.text_input("Admin password", type="password")
    if st.button("Enter admin", type="primary", use_container_width=True):
        if entered == password:
            st.session_state["admin_authenticated"] = True
            st.rerun()
        else:
            st.error("Wrong password.")
    st.stop()


require_admin_login()


@st.cache_data(ttl=120)
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        stats = pd.read_sql_query("SELECT * FROM division_daily_stats", conn, parse_dates=["report_date"])
        reports = pd.read_sql_query("SELECT * FROM reports ORDER BY report_date DESC", conn)
    if not stats.empty:
        stats["report_date"] = pd.to_datetime(stats["report_date"], errors="coerce")
        stats = stats.dropna(subset=["report_date"])
    return stats, reports


def save_manual_stats(report_date: str, edited: pd.DataFrame) -> None:
    numeric_columns = [
        "suspected_24h",
        "suspected_deaths_24h",
        "confirmed_24h",
        "confirmed_deaths_24h",
        "admitted_24h",
        "discharged_24h",
        "suspected_total",
        "suspected_deaths_total",
        "confirmed_total",
        "confirmed_deaths_total",
        "admitted_total",
        "discharged_total",
    ]
    rows = edited.copy()
    rows["report_date"] = report_date
    for column in numeric_columns:
        rows[column] = pd.to_numeric(rows[column], errors="coerce").fillna(0).astype(int)

    with sqlite3.connect(DB_PATH) as conn:
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
            rows[["report_date", "division", *numeric_columns]].to_dict("records"),
        )
        conn.execute(
            """
            UPDATE reports
            SET status = 'extracted',
                validation_message = 'Manually reviewed/edited in admin.',
                extracted_at = CURRENT_TIMESTAMP
            WHERE report_date = ?
            """,
            (report_date,),
        )


@st.cache_data(show_spinner=False)
def render_pdf_page(pdf_path: str, page_number: int) -> bytes:
    import io

    import pypdfium2 as pdfium

    document = pdfium.PdfDocument(pdf_path)
    page_index = max(0, min(page_number - 1, len(document) - 1))
    page = document[page_index]
    bitmap = page.render(scale=1.7)
    image = bitmap.to_pil()
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def pdf_page_count(pdf_path: Path) -> int:
    import pypdfium2 as pdfium

    return len(pdfium.PdfDocument(str(pdf_path)))


stats, reports = load_data()

st.title("Admin")
st.caption("Pick a report date, check its PDF, edit the division table, then save.")
st.markdown("[Dashboard](/)")

if st.button("Check for new DGHS PDFs", type="primary", use_container_width=True):
    progress = st.progress(0, text="Opening DGHS press release list...")
    with st.spinner("Checking DGHS and processing report PDFs..."):
        downloaded_paths = collect_and_download_reports(max_pages=6)
        total = max(len(downloaded_paths), 1)
        for index, pdf_path in enumerate(downloaded_paths, start=1):
            progress.progress(index / total, text=f"Extracting {pdf_path.name}")
            extract_pdf_to_db(pdf_path)
    progress.progress(1.0, text=f"Done. Processed {len(downloaded_paths)} PDF file(s).")
    load_data.clear()
    st.success("Update complete. Reloading admin data.")
    st.rerun()

if reports.empty:
    st.info("No reports found yet. Use the button above to check DGHS.")
else:
    status_counts = reports["status"].value_counts().to_dict()
    st.markdown(
        f"""
        <div class="update-strip">
            <span>Total reports: <b>{len(reports)}</b></span>
            <span>Ready: <b>{status_counts.get('extracted', 0)}</b></span>
            <span>Need review: <b>{status_counts.get('needs_review', 0)}</b></span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    report_options = reports["report_date"].astype(str).sort_values(ascending=False).tolist()
    selected_report_date = st.selectbox("Choose day to review", report_options)
    selected_report = reports[reports["report_date"].astype(str) == selected_report_date].iloc[0]

    status = selected_report["status"]
    message = selected_report.get("validation_message") or "No validation note."
    pdf_path = Path(str(selected_report.get("pdf_path") or ""))
    if status == "extracted":
        st.success(f"{selected_report_date} is currently included in the public dashboard. {message}")
    else:
        st.warning(f"{selected_report_date} needs review before public use. {message}")

    editable_columns = [
        "division",
        "suspected_24h",
        "suspected_deaths_24h",
        "confirmed_24h",
        "confirmed_deaths_24h",
        "admitted_24h",
        "discharged_24h",
        "suspected_total",
        "suspected_deaths_total",
        "confirmed_total",
        "confirmed_deaths_total",
        "admitted_total",
        "discharged_total",
    ]
    existing_rows = stats[stats["report_date"].dt.strftime("%Y-%m-%d") == selected_report_date]
    if existing_rows.empty:
        editor_source = pd.DataFrame({"division": DIVISIONS})
        for column in editable_columns:
            if column != "division":
                editor_source[column] = 0
    else:
        editor_source = existing_rows[editable_columns].copy()

    editor_source["division"] = pd.Categorical(editor_source["division"], categories=DIVISIONS, ordered=True)
    editor_source = editor_source.sort_values("division").reset_index(drop=True)

    pdf_col, data_col = st.columns([1, 1], gap="large")
    with pdf_col:
        st.subheader("PDF")
        if pdf_path.exists():
            page_total = pdf_page_count(pdf_path)
            default_page = min(2, page_total)
            page_number = st.number_input("PDF page", min_value=1, max_value=page_total, value=default_page, step=1)
            st.image(render_pdf_page(str(pdf_path), int(page_number)), use_container_width=True)
            with st.expander("Open raw PDF viewer"):
                encoded_pdf = base64.b64encode(pdf_path.read_bytes()).decode("ascii")
                st.markdown(
                    f'<iframe src="data:application/pdf;base64,{encoded_pdf}" width="100%" height="760"></iframe>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("No local PDF file found for this date.")

    with data_col:
        st.subheader("Extracted data")
        st.caption("Compare with the PDF. Edit any wrong number, then save.")
        edited_rows = st.data_editor(
            editor_source,
            use_container_width=True,
            hide_index=True,
            num_rows="fixed",
            disabled=["division"],
            height=620,
        )
        save_clicked = st.button("Save corrected data to database", type="primary", use_container_width=True)

    if save_clicked:
        save_manual_stats(selected_report_date, edited_rows)
        load_data.clear()
        st.success(f"Saved manual data for {selected_report_date}.")
        st.rerun()

    with st.expander("Show all report statuses"):
        st.dataframe(
            reports[["report_date", "title", "status", "validation_message"]],
            use_container_width=True,
            hide_index=True,
        )
