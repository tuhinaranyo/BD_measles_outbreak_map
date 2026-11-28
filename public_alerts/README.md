# Public alert data

Verified data for <https://www.tuhinhasan.com/alerts/>, built from reports published by the
Directorate General of Health Services (DGHS), Bangladesh. Not an official government service.

| Alert | Official list | Accepted when |
|---|---|---|
| measles | dghs.gov.bd/pages/press-releases/ (from 2026-05-14) | divisions = total row = page-1 national figures, and the date and 24-hour period inside the PDF match |
| dengue | dghs.gov.bd miscellaneous-infos list (from 2026-10-26) | divisions = page-1 total, repeated on the last page, and the date inside the PDF matches |

A report that fails any check is listed under `held` with the reason. Nothing is estimated,
filled in or carried over from another day.

## Run

```bash
pip install -r public_alerts/requirements.txt
python -m unittest discover -s public_alerts/tests -t .
python -m public_alerts --out ../alerts-data --pages 2
```

`.github/workflows/public-alerts.yml` runs this on a schedule and commits the result to the
`alerts-data` branch. Certificate checks are always on.

## Data file

`<alert>.json`: `fields` names the numbers; each report has `date`, `pdf_url`, `page_url`,
`total` and `divisions` (arrays in `fields` order). `status` records the last check.

## Add an alert

Write `sources/<id>.py` (copy `dengue.py`), add it to `sources/__init__.py`, add a fixture
and a test. If the data is not "national total plus 8 divisions", extend the website too.

## If a parser changes

Raise `PARSER_VERSION` in that source and run the workflow with a larger `pages` value, so
older reports are read again.
