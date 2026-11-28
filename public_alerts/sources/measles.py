"""DGHS daily measles press release.

Page 1 prints national figures, page 2 prints the division table. A report is
accepted only when the 8 divisions add up to the total row AND the total row
equals the national figures on page 1 AND the date inside the PDF is the date it
was listed under.
"""
from __future__ import annotations

import re
from datetime import date, timedelta

from ..common import Document, Held, ascii_digits, check_sums, division_table, nfd, to_int, trailing_ints

ID = "measles"
PARSER_VERSION = 2
LISTING_URL = "https://dghs.gov.bd/pages/press-releases/"
KEYWORDS = ("হাম",)
# Earlier releases used a different table layout.
START_DATE = "2026-05-14"

FIELDS = (
    "suspected_24h", "suspected_deaths_24h", "confirmed_24h", "confirmed_deaths_24h",
    "admitted_24h", "discharged_24h",
    "suspected_total", "suspected_deaths_total", "confirmed_total", "confirmed_deaths_total",
    "admitted_total", "discharged_total",
)

# Month names as the legacy font extracts them.
_MONTHS = {
    1: ("জানু",), 2: ("ফেব্রু", "সফব্রু"), 3: ("মার্চ", "মার্"), 4: ("এপ্রি", "এরপ্র", "এনপ্র"),
    5: ("মে", "সম", "যম"), 6: ("জুন", "জুি"), 7: ("জুলা", "জুো"), 8: ("আগ",),
    9: ("সেপ্ট", "সসপ্ট", "যসন্দপ্ট"), 10: ("অক্ট",), 11: ("নভে", "নন্দভ", "িন্দভ"), 12: ("ডিস", "রিস", "নিস"),
}


def _month_of(word: str) -> int | None:
    word = nfd(word)
    for month, variants in _MONTHS.items():
        if any(word.startswith(nfd(v)) for v in variants):
            return month
    return None


def _check_date(doc: Document, listed: str) -> None:
    wanted = date.fromisoformat(listed)
    lines = ascii_digits(doc.texts[0]).split("\n")

    header = None
    for line in lines[:16]:
        # "26 নভেম্বর ২০২৬", also written "18অক্টোবর 2026" or "1লা সেপ্টেম্বর 2026".
        header = re.match(r"^\s*(\d{1,2})(?:লা|ই|রা|ঠা)?\s*([ঀ-৿]+)\s+(20\d{2})\s*$", line)
        if header:
            break
    if not header:
        raise Held("no report date found at the top of the PDF")
    day, word, year = int(header.group(1)), header.group(2), int(header.group(3))
    month = _month_of(word)
    if (day, year) != (wanted.day, wanted.year) or (month and month != wanted.month):
        raise Held(f"date inside the PDF ({day} {word} {year}) is not the listed date {listed}")

    if not month:
        stamps = re.findall(r"(?<!\d)(\d{1,2})[-/.](\d{1,2})[-/.](20\d{2})", ascii_digits("\n".join(doc.texts)))
        if (wanted.day, wanted.month, wanted.year) not in {tuple(map(int, s)) for s in stamps}:
            raise Held("month inside the PDF could not be confirmed")

    period = next((line for line in lines if "8:00" in line), "")
    days = [int(d) for d in re.findall(r"(?<![\d:])(\d{1,2})(?:লা|ই|রা|ঠা)?\s*(?!টা)[ঀ-৿]", period)]
    before = wanted - timedelta(days=1)
    if days[:2] != [before.day, wanted.day]:
        raise Held("the 24-hour period printed in the PDF does not match the date")


def _check_page_one(doc: Document, total: list[int]) -> None:
    t = dict(zip(FIELDS, total))
    national = [t[f] for f in ("suspected_24h", "suspected_total", "confirmed_24h",
                               "confirmed_total", "admitted_total", "discharged_total")]
    deaths = [t[f] for f in ("suspected_deaths_24h", "suspected_deaths_total",
                             "confirmed_deaths_24h", "confirmed_deaths_total")]
    rows = [[to_int(c) for c in cells] for table in doc.tables[0] for cells in table]
    rows = [[n for n in row if n is not None] for row in rows]
    rows += [trailing_ints(line) for line in doc.texts[0].split("\n")]

    if national not in rows:
        raise Held("national figures on page 1 do not match the division table")
    if not any(row[-4:] == deaths for row in rows if len(row) >= 4):
        raise Held("death figures on page 1 do not match the division table")


def parse(doc: Document, listed: str) -> dict:
    _check_date(doc, listed)
    divisions, total = division_table(doc, len(FIELDS), pages=(1, 2, 0))
    check_sums(divisions, total, FIELDS)
    _check_page_one(doc, total)
    # DGHS marks corrected or late-reported figures with a star and explains it under the table.
    starred = any(re.search(r"[0-9০-৯]\s?\*", text) for text in doc.texts[:2])
    return {"total": total, "divisions": divisions, "notes": ["source_footnote"] if starred else []}
