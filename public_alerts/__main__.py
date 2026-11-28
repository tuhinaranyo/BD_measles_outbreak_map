"""Fetch new official reports and update one JSON file per alert.

    python -m public_alerts --out DATA_DIR [--only measles] [--pages 2]

Existing verified data is never deleted when a fetch fails; only the status
block changes, so the website can say that the data is stale and why.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from .common import Held, build_session, fetch, parse_listing, pdf_link_on_page, read_pdf
from .sources import SOURCES

SCHEMA = 1
# The newest reports are re-checked for a replaced file on every run.
RECHECK_NEWEST = 3


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load(path: Path, source) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"schema": SCHEMA, "alert": source.ID, "status": {}, "reports": [], "held": []}


def save(path: Path, data: dict) -> None:
    # One report per line keeps git diffs readable.
    def dumps(value) -> str:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))

    parts = []
    for key, value in data.items():
        if key in ("reports", "held"):
            body = ",\n".join(dumps(item) for item in value)
            parts.append(f'"{key}":[\n{body}\n]' if value else f'"{key}":[]')
        else:
            parts.append(f'"{key}":{dumps(value)}')
    tmp = path.with_suffix(".tmp")
    tmp.write_text("{\n" + ",\n".join(parts) + "\n}\n", encoding="utf-8")
    tmp.replace(path)


def mark_revisions(reports: list[dict], fields: tuple[str, ...]) -> None:
    """Running totals should only grow. When the official figure falls noticeably, say so."""
    running = [i for i, name in enumerate(fields) if name.endswith("_total")]
    previous = None
    for report in reports:
        notes = [n for n in report.get("notes", []) if n != "total_fell"]
        if previous:
            pairs = [(report["total"], previous["total"])]
            pairs += [(report["divisions"][d], previous["divisions"][d]) for d in report["divisions"]]
            if any(old[i] - new[i] > max(20, old[i] // 100) for new, old in pairs for i in running):
                notes.append("total_fell")
        report["notes"] = notes
        previous = report


def list_reports(session, source, pages: int, log) -> list:
    """Newest first. Stops early once the list reaches START_DATE."""
    found: dict[str, object] = {}
    sep = "&" if urlsplit(source.LISTING_URL).query else "?"
    for page in range(1, pages + 1):
        url = source.LISTING_URL if page == 1 else f"{source.LISTING_URL}{sep}page={page}"
        try:
            rows = parse_listing(fetch(session, url).decode("utf-8", "replace"), source.KEYWORDS)
        except Exception as exc:
            if page == 1:
                raise
            log(f"list page {page} failed: {exc}")
            continue
        if not rows:
            if page == 1:
                raise Held("the official list page shows no reports; its layout may have changed")
            break
        for row in rows:
            if row.date >= source.START_DATE:
                # The first row seen for a date wins (the list is newest first).
                found.setdefault(row.date, row)
        if min(r.date for r in rows) < source.START_DATE:
            break
    return sorted(found.values(), key=lambda r: r.date, reverse=True)


def update(session, source, out: Path, pages: int) -> bool:
    log = lambda message: print(f"[{source.ID}] {message}", flush=True)
    path = out / f"{source.ID}.json"
    data = load(path, source)
    data["schema"] = SCHEMA
    data["fields"] = list(source.FIELDS)
    data["source_url"] = source.LISTING_URL
    reports = {r["date"]: r for r in data["reports"]}
    held = {r["date"]: r for r in data["held"]}
    status = data["status"]
    status["checked_at"] = now_utc()

    try:
        listed = list_reports(session, source, pages, log)
    except Exception as exc:
        status.update(ok=False, error=f"{type(exc).__name__}: {exc}"[:300])
        save(path, data)
        log(f"FAILED to read the official list: {exc}")
        return False

    errors = 0
    for position, item in enumerate(listed):
        known = reports.get(item.date) or held.get(item.date)
        current = (
            known is not None
            and known.get("page_url") == item.page_url
            and known.get("parser") == source.PARSER_VERSION
            and (item.pdf_url is None or known.get("pdf_url") == item.pdf_url)
        )
        # Lists that link straight to the PDF reveal a replaced file by its URL.
        if current and (item.pdf_url is not None or position >= RECHECK_NEWEST):
            continue

        pdf_url = item.pdf_url
        try:
            if pdf_url is None:
                pdf_url = pdf_link_on_page(fetch(session, item.page_url).decode("utf-8", "replace"))
                if pdf_url is None:
                    raise Held("no PDF attached to the report page")
            if current and known.get("pdf_url") == pdf_url:
                continue
            result = source.parse(read_pdf(fetch(session, pdf_url)), item.date)
        except Held as exc:
            held[item.date] = {
                "date": item.date, "pdf_url": pdf_url, "page_url": item.page_url,
                "reason": str(exc), "parser": source.PARSER_VERSION,
            }
            # A replaced file that fails the checks must not leave old numbers in place.
            reports.pop(item.date, None)
            log(f"{item.date} held: {exc}")
        except Exception as exc:  # network or unexpected PDF trouble: retry next run
            errors += 1
            log(f"{item.date} error: {type(exc).__name__}: {exc}")
        else:
            reports[item.date] = {
                "date": item.date, "pdf_url": pdf_url, "page_url": item.page_url,
                "parser": source.PARSER_VERSION, "fetched_at": now_utc(), **result,
            }
            held.pop(item.date, None)
            log(f"{item.date} verified")

    data["reports"] = [reports[k] for k in sorted(reports)]
    mark_revisions(data["reports"], source.FIELDS)
    # District detail is large, so only the newest reports keep it.
    keep = getattr(source, "KEEP_DISTRICTS", 0)
    if keep:
        for report in data["reports"][:-keep]:
            report.pop("districts", None)
    data["held"] = [held[k] for k in sorted(held)]
    newest = listed[0].date if listed else None
    status.update(
        ok=errors == 0,
        error=None if errors == 0 else f"{errors} report(s) could not be downloaded or read",
        latest_listed=newest,
        latest_verified=max(reports) if reports else None,
    )
    if errors == 0:
        status["last_ok_at"] = status["checked_at"]
    save(path, data)
    log(f"listed {len(listed)}, verified {len(reports)}, held {len(held)}, errors {errors}")
    if newest and newest in held:
        print(f"::warning title={source.ID}::newest report {newest} is held: {held[newest]['reason']}")
    return errors == 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--only", choices=[s.ID for s in SOURCES])
    parser.add_argument("--pages", type=int, default=2, help="list pages to scan (10 reports each)")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    session = build_session()
    ok = True
    for source in SOURCES:
        if args.only and source.ID != args.only:
            continue
        # First run for a source: read the whole history.
        pages = args.pages if (args.out / f"{source.ID}.json").exists() else 40
        ok = update(session, source, args.out, pages) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
