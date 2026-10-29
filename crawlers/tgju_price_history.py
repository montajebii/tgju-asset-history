"""
Shared tgju.org price-history crawler engine.

Fetches the full daily OHLC history of a symbol from the same server-side
endpoint the tgju.org archive table uses, then merges it with the existing CSV
(dedupe by date, newest value wins) and writes it back sorted ascending.

Usage:
    python tgju_price_history.py [symbol] [csv_filename]

Defaults to geram18/gold_price_history.csv. Asset scripts in this project are
thin wrappers that call update_history() with their own symbol and filename.
"""

import csv
import os
import sys
import time
from datetime import datetime, timedelta

import requests

REQUEST_TIMEOUT = 60
MAX_ATTEMPTS = 3
RETRY_DELAY = 5  # seconds between attempts
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    )
}
FIELDNAMES = ["Date", "Persian_Date", "Open", "Low", "High", "Close"]


# ------------------ HELPERS ------------------
def parse_price(raw):
    """Convert a price string like '1,000,000' to a number, or None if invalid."""
    raw = raw.replace(",", "").strip()
    if not raw or raw == "-":
        return None
    try:
        return int(raw)
    except ValueError:
        try:
            return float(raw)
        except ValueError:
            return None


def parse_date(raw):
    """Parse a 'YYYY/MM/DD' string to datetime, or None if invalid."""
    try:
        return datetime.strptime(raw.strip(), "%Y/%m/%d")
    except (ValueError, AttributeError):
        return None


def read_existing_data(filename):
    """Return list of dicts from CSV, or empty list if file missing.

    Malformed rows are skipped instead of crashing the update.
    """
    data = []
    if not os.path.exists(filename):
        return data
    with open(filename, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                data.append(
                    {
                        "Date": row["Date"].strip(),
                        "Persian_Date": row["Persian_Date"].strip(),
                        "Open": int(row["Open"]),
                        "Low": int(row["Low"]),
                        "High": int(row["High"]),
                        "Close": int(row["Close"]),
                    }
                )
            except (KeyError, TypeError, ValueError):
                continue
    return data


def fetch_history(symbol):
    """Fetch the full price history for symbol from the tgju.org API."""
    api_url = (
        "https://api.tgju.org/v1/market/indicator/summary-table-data/"
        f"{symbol}?lang=fa&order_dir=asc"
    )
    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = requests.get(api_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            payload = response.json()
            rows = payload.get("data")
            if rows is None:
                raise ValueError(f"unexpected API payload: {str(payload)[:200]}")
            return rows
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            print(f"Attempt {attempt}/{MAX_ATTEMPTS} failed: {exc}")
            if attempt < MAX_ATTEMPTS:
                time.sleep(RETRY_DELAY)
    raise RuntimeError(f"Failed to fetch data for '{symbol}': {last_error}")


def sanitize_ohlc(open_price, low_price, high_price, close_price):
    """Force an OHLC tuple to satisfy Low <= min(O,C) and High >= max(O,C)."""
    candles = (open_price, low_price, high_price, close_price)
    return open_price, min(candles), max(candles), close_price


def parse_api_rows(raw_rows):
    """Convert raw API rows to our record dicts, skipping incomplete rows."""
    records = []
    for row in raw_rows:
        try:
            # Columns: open, low, high, close, change, change%, gregorian, persian
            gregorian = row[6].strip()
            persian = row[7].strip()
            open_price = parse_price(row[0])
            low_price = parse_price(row[1])
            high_price = parse_price(row[2])
            close_price = parse_price(row[3])
        except (IndexError, AttributeError):
            continue
        if not gregorian or not persian:
            continue
        if None in (open_price, low_price, high_price, close_price):
            continue
        if parse_date(gregorian) is None:
            continue
        # The API itself occasionally returns self-inconsistent OHLC
        # (High < Low, or Close outside [Low, High]). Clamp here so the
        # dataset written to disk is always internally consistent and a
        # re-fetch cannot reintroduce the defect.
        open_price, low_price, high_price, close_price = sanitize_ohlc(
            open_price, low_price, high_price, close_price
        )
        records.append(
            {
                "Date": gregorian,
                "Persian_Date": persian,
                "Open": open_price,
                "Low": low_price,
                "High": high_price,
                "Close": close_price,
            }
        )
    return records


# ------------------ MAIN ------------------
def update_history(symbol, csv_filename):
    """Fetch, merge and save the full price history for one symbol."""
    existing_data = read_existing_data(csv_filename)
    print(f"Existing records in {csv_filename}: {len(existing_data)}")
    if existing_data:
        last_date = max(parse_date(row["Date"]) for row in existing_data)
        print(f'Last date in CSV: {last_date.strftime("%Y/%m/%d")}')

    print(f"Fetching full history for symbol '{symbol}' from tgju.org API...")
    raw_rows = fetch_history(symbol)
    print(f"API returned {len(raw_rows)} raw rows.")

    new_records = parse_api_rows(raw_rows)
    print(f"Parsed {len(new_records)} valid records from API.")

    # Merge: API rows overwrite same-date rows so corrections propagate,
    # rows only present in the CSV are preserved.
    merged = {row["Date"]: row for row in existing_data}
    fresh_dates = sum(1 for row in new_records if row["Date"] not in merged)
    merged.update({row["Date"]: row for row in new_records})

    merged = sorted(merged.values(), key=lambda row: parse_date(row["Date"]))

    with open(csv_filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(merged)

    print(f"New dates added: {fresh_dates}")
    print(f"After merging and dedup: {len(merged)} records.")
    print(f"CSV updated: {csv_filename}")

    # ------------------ VALIDATION REPORT ------------------
    print("\n--- VALIDATION REPORT ---")
    dates = [parse_date(row["Date"]) for row in merged]
    is_sorted = all(dates[i] <= dates[i + 1] for i in range(len(dates) - 1))
    print(f"Data sorted by date (ascending): {is_sorted}")
    duplicates = len(merged) - len(set(row["Date"] for row in merged))
    print(f"Duplicate rows found: {duplicates}")
    print(f"Total records in CSV: {len(merged)}")
    print(f'Date range: {merged[0]["Date"]} to {merged[-1]["Date"]}')

    date_set = set(dates)
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    missing = []
    current = dates[0]
    while current <= today - timedelta(days=1):
        if current not in date_set:
            missing.append(current.strftime("%Y/%m/%d"))
        current += timedelta(days=1)
    # Weekends (Thu/Fri) and official holidays are expected gaps.
    print(
        f"Missing calendar days within range: {len(missing)} "
        "(weekends/holidays expected)"
    )
    if missing:
        print(f"First few: {missing[:5]}")
    print("Validation complete.")


if __name__ == "__main__":
    symbol = sys.argv[1] if len(sys.argv) > 1 else "geram18"
    csv_filename = (
        sys.argv[2] if len(sys.argv) > 2 else f"{symbol}_price_history.csv"
    )
    update_history(symbol, csv_filename)
