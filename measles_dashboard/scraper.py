from __future__ import annotations

import re
import ssl
from dataclasses import dataclass
from html import unescape
from pathlib import Path
from urllib.parse import quote, urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from .bangla import parse_bn_date, slug_date
from .config import BASE_URL, PRESS_RELEASE_URL, RAW_PDF_DIR
from .db import latest_report_date, report_exists, upsert_report


@dataclass
class ReportLink:
    title: str
    report_date: str | None
    page_url: str


def fetch_text(url: str) -> str:
    req = Request(to_uri(url), headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urlopen(req, timeout=30) as response:
            return response.read().decode("utf-8", "ignore")
    except Exception:
        context = ssl._create_unverified_context()
        with urlopen(req, timeout=30, context=context) as response:
            return response.read().decode("utf-8", "ignore")


def fetch_bytes(url: str) -> bytes:
    req = Request(to_uri(url), headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urlopen(req, timeout=60) as response:
            return response.read()
    except Exception:
        context = ssl._create_unverified_context()
        with urlopen(req, timeout=60, context=context) as response:
            return response.read()


def to_uri(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit(
        (
            parts.scheme,
            parts.netloc.encode("idna").decode("ascii"),
            quote(parts.path, safe="/%:@"),
            quote(parts.query, safe="=&%:@/?"),
            quote(parts.fragment, safe="%:@/?"),
        )
    )


def strip_tags(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", unescape(html))).strip()


def discover_report_links(max_pages: int = 6) -> list[ReportLink]:
    reports: list[ReportLink] = []
    seen: set[str] = set()

    for page in range(1, max_pages + 1):
        url = PRESS_RELEASE_URL if page == 1 else f"{PRESS_RELEASE_URL}?page={page}"
        html = fetch_text(url)
        for row in re.findall(r"<tr\b.*?</tr>", html, flags=re.I | re.S):
            if "হাম" not in row or "প্রেস" not in row:
                continue
            href_match = re.search(r'href=["\']([^"\']*/pages/press-releases/[^"\']+)["\']', row, re.I)
            if not href_match:
                continue
            page_url = urljoin(BASE_URL, href_match.group(1))
            if page_url in seen:
                continue
            seen.add(page_url)
            text = strip_tags(row)
            date_value = parse_bn_date(text)
            title_match = re.search(r"(হাম\s+প্রেস\s+রিলিজ\s*\([^)]+\))", text)
            title = title_match.group(1) if title_match else text
            reports.append(
                ReportLink(
                    title=title,
                    report_date=slug_date(date_value) if date_value else None,
                    page_url=page_url,
                )
            )
    return reports


def find_pdf_url(page_url: str) -> str | None:
    html = fetch_text(page_url)
    candidates = re.findall(r'href=["\']([^"\']+\.pdf(?:\?[^"\']*)?)["\']', html, flags=re.I)
    if not candidates:
        return None

    object_storage = [url for url in candidates if "objectstorage" in url]
    chosen = object_storage[-1] if object_storage else candidates[-1]
    return urljoin(BASE_URL, chosen)


def download_report(report: ReportLink) -> Path | None:
    pdf_url = find_pdf_url(report.page_url)
    if not pdf_url:
        upsert_report(
            report_date=report.report_date,
            title=report.title,
            page_url=report.page_url,
            pdf_url=None,
            pdf_path=None,
            status="pdf_not_found",
            validation_message="No PDF link found on report page.",
        )
        return None

    RAW_PDF_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{report.report_date or Path(report.page_url).name}.pdf"
    pdf_path = RAW_PDF_DIR / filename
    if not pdf_path.exists() or pdf_path.stat().st_size == 0:
        pdf_path.write_bytes(fetch_bytes(pdf_url))

    upsert_report(
        report_date=report.report_date,
        title=report.title,
        page_url=report.page_url,
        pdf_url=pdf_url,
        pdf_path=pdf_path,
        status="downloaded",
    )
    return pdf_path


def collect_and_download_reports(max_pages: int = 6, limit: int | None = None) -> list[Path]:
    reports = discover_report_links(max_pages=max_pages)
    if limit:
        reports = reports[:limit]

    paths: list[Path] = []
    for report in reports:
        path = download_report(report)
        if path:
            paths.append(path)
            print(f"Downloaded/checked {report.report_date or report.title}")
    return paths


def collect_and_download_new_reports(max_pages: int = 6, limit: int | None = None) -> tuple[list[Path], int]:
    reports = discover_report_links(max_pages=max_pages)
    if limit:
        reports = reports[:limit]

    paths: list[Path] = []
    skipped = 0
    latest_known = latest_report_date()
    for report in reports:
        if report_exists(report.report_date):
            skipped += 1
            continue
        if latest_known and report.report_date and report.report_date <= latest_known:
            skipped += 1
            continue
        path = download_report(report)
        if path:
            paths.append(path)
            print(f"Downloaded/checked {report.report_date or report.title}")
    return paths, skipped
