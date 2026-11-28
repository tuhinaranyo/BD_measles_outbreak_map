"""District table of the daily dengue report.

Optional detail: the table is published only when all 64 districts and the Dhaka
city line are read and every division's districts add up to the page-1 table.
Anything else raises ValueError and the report is published without districts.
"""
from __future__ import annotations

import re

from ..common import Document, nfd, to_int

# Each division's districts: (id, name as pdfplumber extracts it from the legacy font).
# A new spelling is never guessed; it is reported so that it can be added here.
DISTRICTS = {
    "dhaka": (
        ("dhaka", "ঢাকা"), ("faridpur", "ফরিদপুি"), ("gazipur", "গাজীপুি"), ("gopalganj", "বগাপালগঞ্জ"),
        ("kishoreganj", "রকমািগঞ্জ"), ("madaripur", "াদািীপুি"), ("manikganj", "ারনকগঞ্জ"),
        ("munshiganj", "মুরিরগঞ্জ"), ("narayanganj", "নািায়ণগঞ্জ"), ("narsingdi", "নিরসিংদী"),
        ("rajbari", "িাজোড়ী"), ("shariatpur", "িীয়তপুি"), ("tangail", "টাঙ্গাইল"),
    ),
    "mymensingh": (
        ("mymensingh", "য়নরসিংহ"), ("jamalpur", "জাালপুি"), ("sherpur", "বিপুি"), ("netrokona", "বনত্রমকানা"),
    ),
    "chattogram": (
        ("chattogram", "চট্টগ্রা"), ("coxsbazar", "কক্সোজাি"), ("bandarban", "োন্দিোন"),
        ("rangamati", "িাঙ্গাাটি"), ("khagrachhari", "খাগড়াছরড়"), ("feni", "বফনী"), ("noakhali", "বনায়াখালী"),
        ("cumilla", "কুরল্লা"), ("chandpur", "চাঁদপুি"), ("lakshmipur", "লক্ষীপুি"),
        ("brahmanbaria", "ব্রাহ্মনোরড়য়া"),
    ),
    "khulna": (
        ("khulna", "খুলনা"), ("bagerhat", "োমগিহাট"), ("satkhira", "সাতক্ষীিা"), ("jashore", "যমাি"),
        ("jhenaidah", "রিনাইদহ"), ("magura", "াগুিা"), ("narail", "নড়াইল"), ("kushtia", "কুরিয়া"),
        ("chuadanga", "চুয়ািাঙ্গা"), ("meherpur", "বমহিপুি"),
    ),
    "rajshahi": (
        ("rajshahi", "িাজাহী"), ("chapainawabganj", "চাপাইনোেগঞ্জ"), ("naogaon", "নওগাঁ"), ("natore", "নামটাি"),
        ("joypurhat", "জয়পুিহাট"), ("bogura", "েগুড়া"), ("sirajganj", "রসিাজগঞ্জ"), ("pabna", "পােনা"),
    ),
    "rangpur": (
        ("rangpur", "িিংপুি"), ("lalmonirhat", "লালরনিহাট"), ("kurigram", "কুরড়গ্রা"), ("nilphamari", "নীলফাািী"),
        ("dinajpur", "রদনাজপুি"), ("gaibandha", "গাইোন্ধা"), ("thakurgaon", "ঠাকুিগাঁও"), ("panchagarh", "পঞ্চগড়"),
    ),
    "barishal": (
        ("barishal", "েরিাল"), ("patuakhali", "পটুয়াখালী"), ("bhola", "বভালা"), ("pirojpur", "রপমিাজপুি"),
        ("barguna", "েিগুনা"), ("jhalokati", "িালকাঠি"),
    ),
    "sylhet": (
        ("sylhet", "রসমলট"), ("sunamganj", "সুনাগঞ্জ"), ("habiganj", "হরেগঞ্জ"), ("moulvibazar", "বৌলভীোজাি"),
    ),
}
# Some reports use a second font, where mainly the u vowel comes out as another letter.
OTHER_SPELLINGS = {
    "faridpur": "ফরিদপযি", "gazipur": "গাজীপযি", "madaripur": "াদািীপযি", "munshiganj": "যরিরগঞ্জ",
    "shariatpur": "িীয়তপযি", "jamalpur": "জা ালপযি", "sherpur": "ব িপযি", "chandpur": "চাাঁদপযি",
    "lakshmipur": "লক্ষীপযি", "khulna": "খযলনা", "chuadanga": "চযয়ািাঙ্গা", "meherpur": "ব মহিপযি",
    "naogaon": "নওগাাঁ", "joypurhat": "জয়পযিহাট", "rangpur": "িিংপযি", "dinajpur": "রদনাজপযি",
    "thakurgaon": "ঠাকুিগাাঁও", "patuakhali": "পটযয়াখালী", "pirojpur": "রপমিাজপযি", "sunamganj": "সযনা গঞ্জ",
}
CITY = "dhaka_city"
# Columns of each published row, and where each one sits in the division fields.
COLUMNS = ("admitted_24h", "admitted_total", "deaths_total", "discharged_total", "in_hospital")


def key(name: str) -> str:
    return re.sub(r"[^ঀ-৿]", "", nfd(name))


_IDS = {key(spelling): ident for rows in DISTRICTS.values() for ident, spelling in rows}
_IDS.update({key(spelling): ident for ident, spelling in OTHER_SPELLINGS.items()})


def read(doc: Document, divisions: dict[str, list[int]], fields: tuple[str, ...]) -> dict[str, list[int]]:
    found: dict[str, list[int]] = {}
    unknown: list[str] = []
    for page in doc.rows:
        for table in page:
            for row in table:
                # District pages have 11 columns: division, serial, district, hospital, 7 numbers.
                if len(row) != 11:
                    continue
                numbers = [to_int(c) for c in row[4:]]
                if any(n is None for n in numbers):
                    continue
                name = row[2]
                if name:
                    ident = _IDS.get(key(name))
                    if ident is None:
                        unknown.append(name)
                        continue
                elif not found and key(row[0]).startswith(key("ঢাকা")):
                    ident = CITY  # the first line of the district table
                else:
                    continue  # district, division and country subtotals
                government, private, admitted, *rest = numbers
                if government + private != admitted:
                    raise ValueError(f"{ident}: government plus private is not the total")
                before = found.get(ident, [0] * len(COLUMNS))
                found[ident] = [a + b for a, b in zip(before, [admitted, *rest])]
    if unknown:
        raise ValueError(f"unknown district spelling: {', '.join(sorted(set(unknown)))}")
    wanted = {CITY, *_IDS.values()}
    if set(found) != wanted:
        raise ValueError(f"districts missing: {', '.join(sorted(wanted - set(found))) or 'none'}")
    for division, rows in DISTRICTS.items():
        members = [found[ident] for ident, _ in rows] + ([found[CITY]] if division == "dhaka" else [])
        for column, field in enumerate(COLUMNS):
            summed = sum(m[column] for m in members)
            printed = divisions[division][fields.index(field)]
            if summed != printed:
                raise ValueError(f"{division} {field}: districts add up to {summed}, page 1 says {printed}")
    return found
