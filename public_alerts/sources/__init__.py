"""To add an alert: write a module with ID, PARSER_VERSION, LISTING_URL, KEYWORDS,
START_DATE, FIELDS and parse(doc, listed_date), then list it here."""
from . import dengue, measles

SOURCES = (measles, dengue)
