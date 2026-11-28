"""Shared helpers for every alert source.

The rule for the whole package: a number is published only when the official
report proves it twice. Anything that cannot be proven is "held", never guessed.
"""
from __future__ import annotations

import io
import re
import time
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from html import unescape
from urllib.parse import quote, urljoin, urlsplit, urlunsplit

import pdfplumber
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://dghs.gov.bd"
ALLOWED_HOSTS = {"dghs.gov.bd", "objectstorage.ap-dcc-gazipur-1.oraclecloud15.com"}
USER_AGENT = "public-health-alert-fetcher/1.0"
MAX_BYTES = 15 * 1024 * 1024

# Fixed order used in every published file.
DIVISIONS = ("dhaka", "mymensingh", "chattogram", "khulna", "rajshahi", "rangpur", "barishal", "sylhet")

_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
_NUMBER = re.compile(r"\d[\d,٬]*")


class Held(Exception):
    """The report exists but its numbers could not be verified."""


@dataclass
class Listed:
    date: str
    title: str
    page_url: str
    pdf_url: str | None


@dataclass
class Document:
    texts: list[str]  # one string per page
    tables: list[list[list[list[str]]]]  # page -> table -> row -> non-empty cells
    rows: list[list[list[list[str]]]] = field(default_factory=list)  # the same, empty cells kept


def nfd(value: str) -> str:
    return unicodedata.normalize("NFD", value or "")


def ascii_digits(value: str) -> str:
    return (value or "").translate(_DIGITS)


def to_int(cell: str) -> int | None:
    """Strict: the whole cell must be one number. A footnote star after it is allowed."""
    text = ascii_digits(cell).strip().rstrip("*").rstrip()
    if not _NUMBER.fullmatch(text):
        return None
    return int(text.replace(",", "").replace("٬", ""))


def trailing_ints(line: str) -> list[int]:
    """The run of numbers at the end of a text line."""
    out: list[int] = []
    for token in reversed(line.split()):
        number = to_int(token)
        if number is None:
            break
        out.append(number)
    return out[::-1]


# The PDFs use a legacy font, so extracted Bangla names come out misspelled in
# several ways. These rules look for the letters that survive in every variant.
# The caller must still require all 8 divisions exactly once.
def classify_division(name: str) -> str | None:
    # Drop the word "division" (বিভাগ); it contains letters used to tell names apart.
    words = [w for w in nfd(name).split() if not ("ভ" in w and "গ" in w)]
    s = re.sub(r"[^ঀ-৿]", "", "".join(words))
    if not s:
        return None

    def has(*parts: str) -> bool:
        return any(nfd(p) in s for p in parts)

    if has("মাট", "মোট", "মোে", "মাে", "াট"):
        return "total"
    if has("ময়ম", "য়মন", "িংহ", "সংহ"):
        return "mymensingh"
    if has("ঢাক", "ঢোক"):
        return "dhaka"
    if has("জশ"):
        return "rajshahi"
    if has("গ") and has("ট"):
        return "chattogram"
    if has("খ"):
        return "khulna"
    if has("পু", "পয") or (has("ং") and has("প")):
        return "rangpur"
    if has("শ"):
        return "barishal"
    if has("ট") and has("ল", "ন্দ"):
        return "sylhet"
    return None


def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "bn,en;q=0.8"})
    retry = Retry(total=3, backoff_factor=2, status_forcelist=(429, 500, 502, 503, 504))
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def _encode(url: str) -> str:
    p = urlsplit(url)
    return urlunsplit((p.scheme, p.netloc, quote(p.path, safe="/%:@"), quote(p.query, safe="=&%:@/?+"), ""))


def fetch(session: requests.Session, url: str, *, timeout: int = 90) -> bytes:
    """GET an official URL. Certificate checks stay on; other hosts are refused."""
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.hostname not in ALLOWED_HOSTS:
        raise Held(f"unexpected host in link: {parts.scheme}://{parts.hostname}")
    response = session.get(_encode(url), timeout=timeout, stream=True)
    response.raise_for_status()
    if urlsplit(response.url).hostname not in ALLOWED_HOSTS:
        raise Held("redirected to an unexpected host")
    body = bytearray()
    for chunk in response.iter_content(65536):
        body.extend(chunk)
        if len(body) > MAX_BYTES:
            raise Held("file is larger than expected")
    time.sleep(0.4)  # be gentle with the government server
    return bytes(body)


def parse_listing(html: str, keywords: tuple[str, ...]) -> list[Listed]:
    """Rows of a DGHS list page whose title names the topic and a date."""
    out: list[Listed] = []
    for row in re.findall(r"<tr\b.*?</tr>", html, flags=re.I | re.S):
        text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", unescape(row))).strip()
        if not any(nfd(k) in nfd(text) for k in keywords):
            continue
        match = re.search(r"(\d{1,2})\s*[/.\-]\s*(\d{1,2})\s*[/.\-]\s*(20\d{2})", ascii_digits(text))
        if not match:
            continue
        day, month, year = map(int, match.groups())
        try:
            iso = date(year, month, day).isoformat()
        except ValueError:
            continue
        hrefs = [urljoin(BASE_URL, unescape(h)) for h in re.findall(r'href=["\']([^"\']+)["\']', row)]
        pdf = next((h for h in hrefs if urlsplit(h).path.lower().endswith(".pdf")), None)
        page = next((h for h in hrefs if h != pdf), None)
        if not (pdf or page):
            continue
        out.append(Listed(date=iso, title=text[:160], page_url=page or pdf, pdf_url=pdf))
    return out


def pdf_link_on_page(html: str) -> str | None:
    links = [unescape(h) for h in re.findall(r'href=["\']([^"\']+\.pdf(?:\?[^"\']*)?)["\']', html, flags=re.I)]
    stored = [h for h in links if "objectstorage" in h and "/office-dghs/" in h]
    return urljoin(BASE_URL, stored[-1]) if stored else None


def read_pdf(data: bytes) -> Document:
    if not data.startswith(b"%PDF"):
        raise Held("downloaded file is not a PDF")
    texts: list[str] = []
    tables: list[list[list[list[str]]]] = []
    rows: list[list[list[list[str]]]] = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages[:12]:
            texts.append(page.extract_text(x_tolerance=1, y_tolerance=3) or "")
            raw = [[[(c or "").strip() for c in row] for row in table] for table in page.extract_tables() or []]
            rows.append(raw)
            tables.append([[[c for c in row if c] for row in table] for table in raw])
    if not texts:
        raise Held("PDF has no pages")
    return Document(texts, tables, rows)


def division_table(doc: Document, width: int, pages: tuple[int, ...]) -> tuple[dict[str, list[int]], list[int]]:
    """Find the table holding all 8 divisions and the total row, ``width`` numbers each."""
    for index in pages:
        if index >= len(doc.tables):
            continue
        for table in doc.tables[index]:
            found: dict[str, list[int]] = {}
            duplicate = False
            for cells in table:
                numbers = [n for n in (to_int(c) for c in cells) if n is not None]
                names = [c for c in cells if to_int(c) is None]
                if len(numbers) < width or len(numbers) > width + 1 or not names:
                    continue
                key = classify_division(" ".join(names))
                if not key:
                    continue
                duplicate = duplicate or key in found
                found[key] = numbers[-width:]  # drops a leading serial number
            if all(k in found for k in (*DIVISIONS, "total")):
                if duplicate:
                    raise Held("a division appears twice in the table")
                total = found.pop("total")
                return found, total
    raise Held("could not read all 8 divisions and the total row")


def check_sums(divisions: dict[str, list[int]], total: list[int], fields: tuple[str, ...]) -> None:
    for i, field in enumerate(fields):
        summed = sum(divisions[d][i] for d in DIVISIONS)
        if summed != total[i]:
            raise Held(f"division sum does not match the total row for {field}: {summed} != {total[i]}")
