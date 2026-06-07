from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from html import unescape
from pathlib import Path
from urllib.parse import quote, urljoin, urlsplit, urlunsplit

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .bangla import parse_bn_date, slug_date
from .config import BASE_URL, PRESS_RELEASE_URL, RAW_PDF_DIR
from .db import latest_report_date, report_exists, upsert_report

log = logging.getLogger("measles_dashboard.scraper")

# Browser-like headers: needed because some govt CDNs return HTML to bots /
# block default urllib User-Agent. Required headers are User-Agent + Accept-*.
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "bn-BD,bn;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

# Older row filter required both 'হাম' and 'প্রেস' to be present, which broke
# the day DGHS changed wording. Accept any row that mentions measles in any
# of these recognisable forms — the date is then re-verified before download.
MEASLES_TOKENS: tuple[str, ...] = ("হাম", "মিজলস", "এমআর", "measles", "MR")


@dataclass
class ReportLink:
    title: str
    report_date: str | None
    page_url: str


def _build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(BROWSER_HEADERS)
    retry = Retry(
        total=4,
        connect=3,
        read=3,
        backoff_factor=1.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "HEAD"),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


_SESSION = _build_session()
# Flipped to False once we hit the first SSL verification failure so we don't
# repeat the (slow) connect-retry loop for every subsequent URL in the same run.
_VERIFY_TLS = True


def _disable_tls_verification() -> None:
    global _VERIFY_TLS
    if _VERIFY_TLS:
        log.warning("DGHS TLS verification failed once; using verify=False for the rest of the run.")
        try:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        except Exception:
            pass
        _VERIFY_TLS = False


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


def fetch_text(url: str, *, timeout: int = 45) -> str:
    """Fetch HTML/text with retries; fall back to verify=False on SSL errors."""
    safe_url = to_uri(url)
    try:
        response = _SESSION.get(safe_url, timeout=timeout, verify=_VERIFY_TLS)
        response.raise_for_status()
        if response.encoding is None or response.encoding.lower() == "iso-8859-1":
            response.encoding = response.apparent_encoding or "utf-8"
        return response.text
    except requests.exceptions.SSLError:
        _disable_tls_verification()
        response = _SESSION.get(safe_url, timeout=timeout, verify=False)
        response.raise_for_status()
        if response.encoding is None or response.encoding.lower() == "iso-8859-1":
            response.encoding = response.apparent_encoding or "utf-8"
        return response.text


def fetch_bytes(url: str, *, timeout: int = 120) -> bytes:
    safe_url = to_uri(url)
    try:
        response = _SESSION.get(safe_url, timeout=timeout, verify=_VERIFY_TLS)
        response.raise_for_status()
        return response.content
    except requests.exceptions.SSLError:
        _disable_tls_verification()
        response = _SESSION.get(safe_url, timeout=timeout, verify=False)
        response.raise_for_status()
        return response.content


def strip_tags(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", unescape(html))).strip()


def _looks_measles(row_text: str) -> bool:
    return any(token in row_text for token in MEASLES_TOKENS)


def discover_report_links(max_pages: int = 6) -> list[ReportLink]:
    reports: list[ReportLink] = []
    seen: set[str] = set()

    for page in range(1, max_pages + 1):
        url = PRESS_RELEASE_URL if page == 1 else f"{PRESS_RELEASE_URL}?page={page}"
        try:
            html = fetch_text(url)
        except Exception as exc:
            log.warning("Listing page %s fetch failed: %r", url, exc)
            time.sleep(2.0)
            continue

        for row in re.findall(r"<tr\b.*?</tr>", html, flags=re.I | re.S):
            text = strip_tags(row)
            if not _looks_measles(text):
                continue
            href_match = re.search(
                r'href=["\']([^"\']*/pages?/press-releases?/[^"\']+)["\']',
                row,
                re.I,
            )
            if not href_match:
                continue
            page_url = urljoin(BASE_URL, href_match.group(1))
            if page_url in seen:
                continue
            seen.add(page_url)
            date_value = parse_bn_date(text)
            title_match = re.search(r"(হাম\s+প্রেস\s+রিলিজ\s*\([^)]+\))", text)
            title = title_match.group(1) if title_match else text[:200]
            reports.append(
                ReportLink(
                    title=title,
                    report_date=slug_date(date_value) if date_value else None,
                    page_url=page_url,
                )
            )
    log.info("Discovered %d measles report link(s) across %d page(s).", len(reports), max_pages)
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
    try:
        pdf_url = find_pdf_url(report.page_url)
    except Exception as exc:
        log.warning("Could not load detail page for %s: %r", report.page_url, exc)
        upsert_report(
            report_date=report.report_date,
            title=report.title,
            page_url=report.page_url,
            pdf_url=None,
            pdf_path=None,
            status="needs_review",
            validation_message=f"Detail page fetch failed: {exc!r}",
        )
        return None

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
        try:
            pdf_path.write_bytes(fetch_bytes(pdf_url))
        except Exception as exc:
            log.warning("Could not download %s: %r", pdf_url, exc)
            upsert_report(
                report_date=report.report_date,
                title=report.title,
                page_url=report.page_url,
                pdf_url=pdf_url,
                pdf_path=None,
                status="needs_review",
                validation_message=f"PDF download failed: {exc!r}",
            )
            return None

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
    """
    Download only press-release dates that we have not already EXTRACTED.
    Reports that exist but are still in ``needs_review`` / ``pdf_not_found``
    will be re-downloaded (and the caller will re-extract them) — so a fixed
    extractor automatically recovers previously-broken days.
    """
    reports = discover_report_links(max_pages=max_pages)
    if limit:
        reports = reports[:limit]

    paths: list[Path] = []
    skipped = 0
    for report in reports:
        from .db import report_is_extracted

        if report_is_extracted(report.report_date):
            skipped += 1
            continue
        path = download_report(report)
        if path:
            paths.append(path)
            print(f"Downloaded/checked {report.report_date or report.title}")
    return paths, skipped
