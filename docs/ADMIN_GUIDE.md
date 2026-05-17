# Admin Guide

Open the admin page:

```text
http://localhost:8501/admin
```

## Check For New PDFs

Click **Check for new DGHS PDFs**.

The app will:

1. open the DGHS press-release listing,
2. find measles reports,
3. download missing PDFs,
4. extract available data,
5. update the SQLite database.

## Review A Report

1. Choose a date from **Choose day to review**.
2. The PDF appears on the left.
3. The extracted data appears on the right.
4. Compare the numbers against the PDF.
5. Edit any wrong number.
6. Click **Save corrected data to database**.

Saving marks the selected date as manually reviewed and includes it in the public dashboard.

## Local Data

Generated files are intentionally not committed to GitHub:

- `data/raw_pdfs/*.pdf`
- `data/extracted_text/*.txt`
- `data/measles.db`

Run `python update_data.py` after setup to rebuild local data.
