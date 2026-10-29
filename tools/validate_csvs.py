#!/usr/bin/env python3
"""Validate every *_price_history.csv dataset in data/.

Checks, per file:
  * header is exactly Date,Persian_Date,Open,Low,High,Close
  * Date parses as YYYY/MM/DD (hard)
  * prices are integers (hard)
  * dates strictly ascend and are unique (hard)
  * High >= max(Open, Close) and Low <= min(Open, Close) (soft, reported)

Hard errors (bad header, duplicate/unordered/unparsable dates, unparsable
prices) make the script exit 1. Soft OHLC inconsistencies are only reported,
with line numbers, so tools/fix_ohlc.py can repair them.

Usage:
    python3 tools/validate_csvs.py [file ...]

With no arguments every *_price_history.csv in data/ is checked.
"""

import csv
import glob
import os
import sys
from datetime import datetime

EXPECTED_HEADER = ["Date", "Persian_Date", "Open", "Low", "High", "Close"]
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def default_files():
    """All *_price_history.csv in the repo root, sorted by name."""
    return sorted(glob.glob(os.path.join(REPO_ROOT, "data", "*_price_history.csv")))


def validate_file(path):
    """Return (hard_errors, soft_errors) as lists of (line, message)."""
    hard = []
    soft = []

    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return [(1, "file is empty")], []

        if header != EXPECTED_HEADER:
            hard.append((1, f"bad header {header!r}, expected {EXPECTED_HEADER!r}"))

        seen = {}
        previous_date = None
        previous_lineno = None
        rows = 0

        for lineno, raw in enumerate(reader, start=2):
            if not raw or all(not cell.strip() for cell in raw):
                continue  # tolerate blank lines
            rows += 1

            if len(raw) != len(EXPECTED_HEADER):
                hard.append(
                    (lineno, f"expected {len(EXPECTED_HEADER)} columns, got {len(raw)}")
                )
                continue

            date_raw, _persian, *prices = [cell.strip() for cell in raw]

            try:
                current_date = datetime.strptime(date_raw, "%Y/%m/%d")
            except ValueError:
                hard.append((lineno, f"unparsable Date {date_raw!r}"))
                current_date = None

            parsed_prices = {}
            prices_ok = True
            for name, value in zip(EXPECTED_HEADER[2:], prices):
                try:
                    parsed_prices[name] = int(value)
                except ValueError:
                    hard.append((lineno, f"unparsable {name} {value!r}"))
                    prices_ok = False

            if current_date is not None:
                if date_raw in seen:
                    hard.append(
                        (lineno, f"duplicate Date {date_raw} (first at line {seen[date_raw]})")
                    )
                else:
                    seen[date_raw] = lineno
                if previous_date is not None and current_date <= previous_date:
                    hard.append(
                        (lineno, f"Date {date_raw} not after line {previous_lineno} date")
                    )
                previous_date = current_date
                previous_lineno = lineno

            if prices_ok:
                o = parsed_prices["Open"]
                l = parsed_prices["Low"]
                h = parsed_prices["High"]
                c = parsed_prices["Close"]
                if h < max(o, c):
                    soft.append((lineno, f"High {h} < max(Open {o}, Close {c})"))
                if l > min(o, c):
                    soft.append((lineno, f"Low {l} > min(Open {o}, Close {c})"))
                if h < l:
                    soft.append((lineno, f"High {h} < Low {l}"))

        print(f"{os.path.basename(path)}: {rows} data rows")

    return hard, soft


def main(argv):
    paths = argv[1:] or default_files()
    if not paths:
        print("No *_price_history.csv files found; nothing to validate.")
        return 0

    total_hard = 0
    total_soft = 0

    for path in paths:
        hard, soft = validate_file(path)
        total_hard += len(hard)
        total_soft += len(soft)
        for lineno, message in hard:
            print(f"  HARD {os.path.basename(path)}:{lineno}: {message}")
        for lineno, message in soft:
            print(f"  SOFT {os.path.basename(path)}:{lineno}: {message}")

    print(f"\nTotals: {total_hard} hard error(s), {total_soft} OHLC inconsistency(ies)")

    if total_soft:
        print("OHLC inconsistencies are reported only; run tools/fix_ohlc.py to repair.")

    return 1 if total_hard else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
