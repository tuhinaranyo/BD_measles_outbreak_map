from __future__ import annotations

import re
import unicodedata
from datetime import date
from pathlib import Path

from .bangla import bn_to_int, normalize_text, parse_bn_date
from .config import DIVISIONS as _RAW_DIVISIONS, TEXT_DIR
from .db import add_note, save_stats, upsert_report


def _canon(value: str) -> str:
    """
    Decompose Bengali letters to a single canonical form for *matching*.

    Bangla 'য়'/'ড়'/'ঢ়' are Unicode composition exclusions: NFC leaves
    precomposed (U+09DF) and decomposed (U+09AF U+09BC) variants distinct
    even though they render identically. NFD always decomposes, so equality
    checks via NFD are stable. Stored / returned names stay in whatever form
    the caller passed in (so the DB stays consistent with seed_data.json).
    """
    return unicodedata.normalize("NFD", value or "")


# Public canonical lists stay in their source (NFC) form so the database
# layer and seed_data.json keep using identical strings for joins/groupbys.
DIVISIONS: list[str] = list(_RAW_DIVISIONS)

FIELDS = [
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

_RAW_DIVISION_ALIASES = {
    "চট্রগ্রাম": "চট্টগ্রাম",
    "র্ট্টগ্রাম": "চট্টগ্রাম",
    "রট্টগ্রাম": "চট্টগ্রাম",
    "চট্টগ্রাম": "চট্টগ্রাম",
    "ঢাকা": "ঢাকা",
    "রাজশাহী": "রাজশাহী",
    "বরিশাল": "বরিশাল",
    "িনরশাল": "বরিশাল",
    "বনরশাল": "বরিশাল",
    "বনিশাল": "বরিশাল",
    "বনরশাে": "বরিশাল",
    "বনশাে": "বরিশাল",
    "বনশাল": "বরিশাল",
    "বন শাে": "বরিশাল",
    # Glyph variant first seen 2026-05-25 onwards (র→স, ল→ে).
    "বসিশাে": "বরিশাল",
    "বসিশাল": "বরিশাল",
    "বসরশাে": "বরিশাল",
    "বসরশাল": "বরিশাল",
    "সিলেট": "সিলেট",
    "নসন্দলট": "সিলেট",
    "নসন্দেট": "সিলেট",
    "নসন্দে্": "সিলেট",
    "ময়মনসিংহ": "ময়মনসিংহ",
    "ময়মননসিংহ": "ময়মনসিংহ",
    "ময়মননসংহ": "ময়মনসিংহ",
    "ময়মনচসংহ": "ময়মনসিংহ",
    "খুলনা": "খুলনা",
    "খুেনা": "খুলনা",
    "রংপুর": "রংপুর",
}

# NFD form → exact DIVISIONS member, so alias resolution always returns the
# canonical byte sequence stored in DIVISIONS / seed_data.json regardless of
# how the alias value was typed in the source file.
_NFD_TO_DIVISION: dict[str, str] = {_canon(d): d for d in DIVISIONS}


def _alias_value_to_division(value: str) -> str:
    return _NFD_TO_DIVISION.get(_canon(value), value)


DIVISION_ALIASES: dict[str, str] = {
    k: _alias_value_to_division(v) for k, v in _RAW_DIVISION_ALIASES.items()
}

# Internal NFD-canonical mirror used only for matching. Keys are NFD-decomposed,
# values are the canonical member from DIVISIONS (exact byte identity).
_ALIAS_LOOKUP_NFD: dict[str, str] = {
    _canon(k): _alias_value_to_division(v) for k, v in DIVISION_ALIASES.items()
}
_DIVISIONS_NFD: list[str] = list(_NFD_TO_DIVISION.keys())

# Strings DGHS PDFs use for the row-aggregate "Total" (মোট) row.
TOTAL_TOKENS: tuple[str, ...] = ("মোট", "সমাট", "যমাট", "মোে", "সমাে")
_TOTAL_TOKENS_NFD: tuple[str, ...] = tuple(_canon(t) for t in TOTAL_TOKENS)


def safe_print(message: str) -> None:
    print(message.encode("ascii", "backslashreplace").decode("ascii"))


def extract_text_pages(pdf_path: Path) -> list[str]:
    try:
        import pdfplumber
    except ImportError as exc:
        raise RuntimeError("pdfplumber is not installed. Run pip install -r requirements.txt.") from exc

    pages: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text(x_tolerance=1, y_tolerance=3) or "")
    return pages


def extract_tables(pdf_path: Path) -> list[list[list[str | None]]]:
    try:
        import pdfplumber
    except ImportError:
        return []

    tables: list[list[list[str | None]]] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables.extend(page.extract_tables() or [])
    return tables


def guess_report_date(pdf_path: Path, pages: list[str]) -> str:
    match = re.search(r"(20\d{2})[-_]?(\d{2})[-_]?(\d{2})", pdf_path.stem)
    if match:
        return date(int(match.group(1)), int(match.group(2)), int(match.group(3))).isoformat()

    for candidate in [pdf_path.stem, *pages[:2]]:
        parsed = parse_bn_date(candidate)
        if parsed:
            return parsed.isoformat()
    return pdf_path.stem


def normalize_division(value: str) -> str | None:
    """Map a noisy division-name string back to its canonical Bangla name.

    Matching is done in NFD form so that `ম + য + ়` (decomposed) and
    `ম + য়` (precomposed) both reach the same alias. The returned canonical
    name is in its original NFC form so the DB column stays consistent with
    historical seed_data.
    """
    text = _canon(normalize_text(value))
    text = re.sub(r"[^\u0980-\u09ff]", "", text)
    if not text:
        return None
    direct = _ALIAS_LOOKUP_NFD.get(text)
    if direct is not None:
        return direct
    for alias_nfd, division in _ALIAS_LOOKUP_NFD.items():
        if alias_nfd and alias_nfd in text:
            return division
    return None


def row_to_numbers(cells: list[str | None]) -> list[int]:
    values: list[int] = []
    for cell in cells:
        number = bn_to_int(cell)
        if number is not None:
            values.append(number)
    return values


def _is_total_token(text: str) -> bool:
    """True when ``text`` (already NFD-canonical, Bengali letters only)
    starts with any of the known 'Total' (মোট) glyph variants.
    """
    if not text:
        return False
    return any(text.startswith(token) for token in _TOTAL_TOKENS_NFD)


def parse_table_rows_from_pdf_tables(tables: list[list[list[str | None]]], report_date: str) -> tuple[list[dict], dict | None]:
    for table in tables:
        candidates: list[tuple[list[int], str | None, bool]] = []
        for raw_row in table:
            text_cells = [normalize_text(c or "") for c in raw_row]
            joined_nfd = _canon(" ".join(text_cells))
            joined_bn_only_nfd = re.sub(r"[^\u0980-\u09ff]", "", joined_nfd)
            division = None
            for cell in text_cells:
                division = normalize_division(cell)
                if division:
                    break

            numbers = row_to_numbers(text_cells)
            if len(numbers) < len(FIELDS):
                continue
            is_total = _is_total_token(joined_bn_only_nfd) or any(
                token in joined_nfd for token in _TOTAL_TOKENS_NFD
            )
            if not division and not is_total:
                continue
            candidates.append((numbers[-len(FIELDS) :], division, is_total))

        if len(candidates) < len(DIVISIONS):
            continue

        rows: list[dict] = []
        total_row: dict | None = None
        division_index = 0
        used_divisions: set[str] = set()
        for numbers, division, is_total in candidates:
            if is_total or division_index >= len(DIVISIONS):
                row_division = "মোট"
            else:
                if division and division not in used_divisions:
                    row_division = division
                else:
                    while division_index < len(DIVISIONS) and DIVISIONS[division_index] in used_divisions:
                        division_index += 1
                    row_division = DIVISIONS[division_index] if division_index < len(DIVISIONS) else "মোট"
                if row_division != "মোট":
                    used_divisions.add(row_division)
                division_index += 1

            parsed = {"report_date": report_date, "division": row_division}
            parsed.update(dict(zip(FIELDS, numbers)))

            if row_division != "মোট":
                rows.append(parsed)
            else:
                total_row = parsed

        if len(rows) >= len(DIVISIONS):
            return rows[: len(DIVISIONS)], total_row

    return [], None


def parse_rows_from_text(text: str, report_date: str) -> tuple[list[dict], dict | None]:
    """Fallback parser used when pdfplumber's table detector misses the grid.

    Uses ``normalize_division`` so glyph-mangled division names (e.g.
    ``বসিশাে`` for ``বরিশাল``) still resolve via ``DIVISION_ALIASES``.
    """
    rows: list[dict] = []
    total_row: dict | None = None
    lines = [normalize_text(line) for line in text.splitlines()]

    for line in lines:
        if not line:
            continue
        line_nfd = _canon(line)

        # 1) Canonical division match in NFD space (form-agnostic).
        division: str | None = None
        for canonical_nfc, canonical_nfd in zip(DIVISIONS, _DIVISIONS_NFD):
            if canonical_nfd in line_nfd:
                division = canonical_nfc
                break
        # 2) Alias-based fallback (handles mis-rendered glyphs).
        if division is None:
            guess = normalize_division(line)
            if guess in DIVISIONS:
                division = guess

        # 3) Total-row detection across known glyph variants.
        bangla_only_nfd = re.sub(r"[^\u0980-\u09ff]", "", line_nfd)
        is_total = (not division) and _is_total_token(bangla_only_nfd)

        if not division and not is_total:
            continue

        numbers = re.findall(r"[-০-৯0-9,٬]+", line)
        values = [bn_to_int(n) for n in numbers]
        values = [v for v in values if v is not None]
        if len(values) < len(FIELDS):
            continue
        values = values[-len(FIELDS) :]
        parsed = {"report_date": report_date, "division": division or "মোট"}
        parsed.update(dict(zip(FIELDS, values)))

        if division:
            rows.append(parsed)
        else:
            total_row = parsed

    return rows, total_row


def validate_rows(rows: list[dict], total_row: dict | None) -> tuple[str, str]:
    found = {row["division"] for row in rows}
    missing = [division for division in DIVISIONS if division not in found]
    messages: list[str] = []
    status = "extracted"

    if missing:
        status = "needs_review"
        messages.append("Missing division rows: " + ", ".join(missing))

    if total_row and rows:
        for field in FIELDS:
            total = sum((row.get(field) or 0) for row in rows)
            expected = total_row.get(field)
            if expected is not None and total != expected:
                status = "needs_review"
                messages.append(f"Total mismatch for {field}: rows={total}, total_row={expected}")
                break
    elif rows:
        status = "needs_review"
        messages.append("No মোট row found for validation.")
    else:
        status = "needs_review"
        messages.append("No division table rows extracted.")

    suspicious_death_rows = [
        row["division"]
        for row in rows
        if (row.get("suspected_deaths_24h") or 0) > 25 or (row.get("confirmed_deaths_24h") or 0) > 25
    ]
    if suspicious_death_rows:
        status = "needs_review"
        messages.append(
            "Implausible 24h death values; possible shifted PDF columns: "
            + ", ".join(suspicious_death_rows)
        )

    return status, "; ".join(messages) if messages else "Validated against মোট row."


def ensure_report_record(pdf_path: Path, report_date: str) -> None:
    upsert_report(
        report_date=report_date,
        title=f"Local PDF {pdf_path.name}",
        page_url="manual-import",
        pdf_url=None,
        pdf_path=pdf_path,
        status="downloaded",
    )


def extract_pdf_to_db(pdf_path: Path) -> None:
    try:
        pages = extract_text_pages(pdf_path)
        report_date = guess_report_date(pdf_path, pages)
        ensure_report_record(pdf_path, report_date)

        TEXT_DIR.mkdir(parents=True, exist_ok=True)
        text_path = TEXT_DIR / f"{report_date}.txt"
        text_path.write_text("\n\n--- PAGE BREAK ---\n\n".join(pages), encoding="utf-8")

        rows, total_row = parse_table_rows_from_pdf_tables(extract_tables(pdf_path), report_date)
        if len(rows) < 8:
            rows, total_row = parse_rows_from_text("\n".join(pages), report_date)

        status, message = validate_rows(rows, total_row)
        save_stats(report_date, rows, status, message)
        safe_print(f"{pdf_path.name}: {status} - {message}")
    except Exception as exc:
        fallback_date = pdf_path.stem
        ensure_report_record(pdf_path, fallback_date)
        add_note(fallback_date, pdf_path, str(exc))
        save_stats(fallback_date, [], "needs_review", str(exc))
        safe_print(f"{pdf_path.name}: needs_review - {exc}")
