"""DGHS daily dengue report (hospital admissions).

Page 1 prints the division table. The last page prints a countrywide total built
from the hospital-by-hospital list. A report is accepted only when the 8
divisions add up to the page-1 total AND that total is repeated on the last page
AND the date inside the PDF is the date it was listed under.
"""
from __future__ import annotations

import re
from datetime import date

from ..common import Document, Held, ascii_digits, check_sums, division_table, to_int, trailing_ints
from . import dengue_districts

ID = "dengue"
PARSER_VERSION = 3
KEEP_DISTRICTS = 14
LISTING_URL = (
    "https://dghs.gov.bd/pages/miscellaneous-infos"
    "?filters=%7B%22miscellaneous_info_type%22%3A%226a9cf0471fa8cd87d1f50227%22%7D"
)
KEYWORDS = ("ডেঙ্গু", "ডেংগু")
# Reports before this date use a different English-language layout that is not read yet.
START_DATE = "2026-10-26"

FIELDS = ("admitted_24h", "deaths_24h", "admitted_total", "deaths_total", "discharged_total", "in_hospital")


def _check_date(doc: Document, listed: str) -> None:
    wanted = date.fromisoformat(listed)
    stamps = re.findall(r"(?<!\d)(\d{1,2})\s*[-/.]\s*(\d{1,2})\s*[-/.]\s*(\d{4}|\d{2})(?!\d)",
                        ascii_digits(doc.texts[0]))
    # The first date that is not the "since 01-01" marker is the report date.
    for d, m, y in stamps:
        day, month, year = int(d), int(m), int(y)
        year += 2000 if year < 100 else 0
        if (day, month) == (1, 1) and wanted.timetuple().tm_yday != 1:
            continue
        if (day, month, year) != (wanted.day, wanted.month, wanted.year):
            raise Held(f"date inside the PDF ({day}-{month}-{year}) is not the listed date {listed}")
        return
    raise Held("no report date found on page 1")


def _check_countrywide(doc: Document, total: list[int]) -> None:
    t = dict(zip(FIELDS, total))
    tail = [t[f] for f in ("admitted_24h", "admitted_total", "deaths_total", "discharged_total", "in_hospital")]
    rows: list[list[int]] = []
    for index in range(1, len(doc.texts)):
        rows += [trailing_ints(line) for line in doc.texts[index].split("\n")]
        rows += [[n for n in (to_int(c) for c in cells) if n is not None]
                 for table in doc.tables[index] for cells in table]
    if not any(row[-5:] == tail for row in rows if len(row) >= 5):
        raise Held("countrywide total on the later pages does not match page 1")


def parse(doc: Document, listed: str) -> dict:
    _check_date(doc, listed)
    divisions, total = division_table(doc, len(FIELDS), pages=(0,))
    check_sums(divisions, total, FIELDS)
    _check_countrywide(doc, total)
    t = dict(zip(FIELDS, total))
    notes = []
    if t["admitted_total"] != t["discharged_total"] + t["deaths_total"] + t["in_hospital"]:
        notes.append("totals_do_not_balance")
    result = {"total": total, "divisions": divisions, "notes": notes}
    try:
        result["districts"] = dengue_districts.read(doc, divisions, FIELDS)
    except ValueError as exc:  # the division numbers are still good
        print(f"::warning title=dengue districts::{listed}: {exc}", flush=True)
    return result
