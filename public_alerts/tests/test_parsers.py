"""python -m unittest discover -s public_alerts/tests -t ."""
import copy
import json
import unittest
from pathlib import Path

from public_alerts.common import Document, Held, classify_division, parse_listing, to_int
from public_alerts.sources import dengue, measles

FIXTURES = Path(__file__).parent / "fixtures"


def load(name: str) -> Document:
    raw = json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
    return Document(raw["texts"], raw["tables"])


def edit(doc: Document, page: int, first_cell_contains: str, change) -> Document:
    """Return a copy with ``change`` applied to the first matching table row."""
    out = copy.deepcopy(doc)
    for table in out.tables[page]:
        for row in table:
            if row and first_cell_contains in row[0]:
                change(table, row)
                return out
    raise AssertionError(f"row not found: {first_cell_contains}")


class Measles(unittest.TestCase):
    def setUp(self):
        self.doc = load("measles-2026-11-26")

    def test_official_report(self):
        result = measles.parse(self.doc, "2026-11-26")
        total = dict(zip(measles.FIELDS, result["total"]))
        self.assertEqual(total["suspected_24h"], 1007)
        self.assertEqual(total["confirmed_total"], 26476)
        self.assertEqual(result["divisions"]["mymensingh"][0], 56)

    def test_missing_division_is_held(self):
        broken = edit(self.doc, 1, "মনস", lambda table, row: table.remove(row))
        with self.assertRaises(Held):
            measles.parse(broken, "2026-11-26")

    def test_changed_number_is_held(self):
        broken = edit(self.doc, 1, "ঢাকা", lambda table, row: row.__setitem__(1, "333"))
        with self.assertRaisesRegex(Held, "division sum"):
            measles.parse(broken, "2026-11-26")

    def test_total_must_match_page_one(self):
        broken = edit(self.doc, 1, "ঢাকা", lambda table, row: row.__setitem__(1, "333"))
        broken = edit(broken, 1, "সমাট", lambda table, row: row.__setitem__(1, "1008"))
        with self.assertRaisesRegex(Held, "page 1"):
            measles.parse(broken, "2026-11-26")

    def test_wrong_date_is_held(self):
        with self.assertRaisesRegex(Held, "date inside"):
            measles.parse(self.doc, "2026-11-27")


class Dengue(unittest.TestCase):
    def setUp(self):
        self.doc = load("dengue-2026-11-25")

    def test_official_report(self):
        result = dengue.parse(self.doc, "2026-11-25")
        self.assertEqual(result["total"], [1152, 2, 177137, 526, 171750, 4861])
        self.assertEqual(result["divisions"]["sylhet"], [5, 0, 1140, 4, 1096, 40])
        self.assertEqual(result["notes"], [])

    def test_wrong_date_is_held(self):
        with self.assertRaisesRegex(Held, "date inside"):
            dengue.parse(self.doc, "2026-11-26")

    def test_countrywide_total_is_required(self):
        broken = Document(self.doc.texts[:1], self.doc.tables[:1])
        with self.assertRaisesRegex(Held, "countrywide"):
            dengue.parse(broken, "2026-11-25")


class Helpers(unittest.TestCase):
    def test_division_names_as_extracted(self):
        seen = {
            "dhaka": ["ঢাকা", "ঢোকো র্র্ভোগ"],
            "mymensingh": ["ময়মননসংহ", "ময়মনসিিংহ", "ময়মনসসিংহ", "ময়মনর্সিংহ র্র্ভোগ", "য় নরসিংহ রর্ভাগ"],
            "chattogram": ["চট্টগ্রাম", "র্ট্টগ্রাম", "চট্টগ্রোম র্র্ভোগ"],
            "khulna": ["খুলনা", "খুেনা", "খযলনো র্র্ভোগ"],
            "rajshahi": ["রাজশাহী", "োজশোহী র্র্ভোগ"],
            "rangpur": ["রংপুর", "িংপয র্র্ভোগ"],
            "barishal": ["বরিশাল", "িনরশাল", "বসরশাে", "বন শাে", "র্র্ শোল র্র্ভোগ"],
            "sylhet": ["সিলেট", "নসন্দলট", "নসন্দেট", "সসন্দেট", "সসভলট", "র্সমলট র্র্ভোগ"],
            "total": ["মোট", "সমাট", "যমাট", "ের্েরমাট:", "সর্মি াট :"],
        }
        for key, names in seen.items():
            for name in names:
                self.assertEqual(classify_division(name), key, name)

    def test_numbers_are_strict(self):
        self.assertEqual(to_int("২,৬১,৫৩৫"), 261535)
        self.assertIsNone(to_int("96%"))
        self.assertIsNone(to_int("15-03-2026"))

    def test_listing(self):
        html = ('<table><tr><td>১</td><td>ডেঙ্গু প্রেস রিলিজ (২৫/১১/২০২৬)</td><td>'
                '<a href="https://objectstorage.ap-dcc-gazipur-1.oraclecloud15.com/a.pdf">x</a>'
                '<a href="/pages/miscellaneous-infos/b">দেখুন</a></td></tr></table>')
        [row] = parse_listing(html, dengue.KEYWORDS)
        self.assertEqual(row.date, "2026-11-25")
        self.assertTrue(row.pdf_url.endswith("a.pdf"))
        self.assertEqual(row.page_url, "https://dghs.gov.bd/pages/miscellaneous-infos/b")


if __name__ == "__main__":
    unittest.main()
