from __future__ import annotations

import re
import unicodedata
from datetime import date

BN_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
EN_TO_BN_DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")

MONTH_WORDS = {
    "জানুয়ারি": 1,
    "ফেব্রুয়ারি": 2,
    "মার্চ": 3,
    "এপ্রিল": 4,
    "মে": 5,
    "জুন": 6,
    "জুলাই": 7,
    "আগস্ট": 8,
    "সেপ্টেম্বর": 9,
    "অক্টোবর": 10,
    "নভেম্বর": 11,
    "ডিসেম্বর": 12,
}


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFC", value or "")
    return re.sub(r"\s+", " ", value).strip()


def bn_to_int(value: str | None) -> int | None:
    if value is None:
        return None
    cleaned = normalize_text(str(value)).translate(BN_DIGITS)
    cleaned = cleaned.replace(",", "").replace("٬", "")
    match = re.search(r"-?\d+", cleaned)
    return int(match.group(0)) if match else None


def parse_bn_date(value: str) -> date | None:
    text = normalize_text(value).translate(BN_DIGITS)
    match = re.search(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", text)
    if match:
        day, month, year = map(int, match.groups())
        return date(year, month, day)

    match = re.search(r"(\d{1,2})\s+([^\s]+)\s+(\d{4})", text)
    if match:
        day = int(match.group(1))
        month = MONTH_WORDS.get(match.group(2))
        year = int(match.group(3))
        if month:
            return date(year, month, day)
    return None


def slug_date(value: date) -> str:
    return value.isoformat()
