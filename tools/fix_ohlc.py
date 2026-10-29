#!/usr/bin/env python3
"""Repair OHLC inconsistencies in the *_price_history.csv datasets in place.

For every row, clamps
    High = max(Open, Low, Close, High)
    Low  = min(Open, Low, Close, Low)
so the app never reads a candle where High < max(Open, Close) or
Low > min(Open, Close).

A timestamped backup of each modified file is written next to it
(<name>.bak-YYYYMMDD-HHMMSS) before the repaired file replaces the original
via a temp file + os.replace. Unchanged files are not rewritten.

Usage:
    python3 tools/fix_ohlc.py [--dry-run] [file ...]

With no file arguments every *_price_history.csv in data/ is processed.
"""

import csv
import glob
import os
import shutil
import sys
from datetime import datetime

FIELDNAMES = ["Date", "Persian_Date", "Open", "Low", "High", "Close"]
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def default_files():
    """All *_price_history.csv in the repo root, sorted by name."""
    return sorted(glob.glob(os.path.join(REPO_ROOT, "data", "*_price_history.csv")))


def repair_file(path, dry_run=False):
    """Clamp inconsistent rows in path. Returns (rows, changed, unparsable, backup)."""
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != FIELDNAMES:
            print(f"{os.path.basename(path)}: unexpected header, skipped")
            return 0, 0, 0, None

        records = []
        changed = 0
        unparsable = 0
        # Track original line numbers so reports point at the real file.
        for lineno, row in enumerate(reader, start=2):
            try:
                o = int(row["Open"])
                l = int(row["Low"])
                h = int(row["High"])
                c = int(row["Close"])
            except (KeyError, TypeError, ValueError) as exc:
                # Leave the row untouched rather than dropping data; validate_csvs
                # reports it as a hard error for a human to resolve.
                print(f"  KEEP line {lineno} unchanged: {exc}")
                unparsable += 1
                records.append({name: row.get(name, "") for name in FIELDNAMES})
                continue

            new_h = max(o, l, c, h)
            new_l = min(o, l, c, h)
            if (new_h, new_l) != (h, l):
                changed += 1
                print(
                    f"  line {lineno} {row['Date']}: "
                    f"O={o} L={l} H={h} C={c} -> L={new_l} H={new_h}"
                )
                row["Low"] = str(new_l)
                row["High"] = str(new_h)

            records.append(
                {
                    "Date": row["Date"],
                    "Persian_Date": row["Persian_Date"],
                    "Open": str(o),
                    "Low": str(new_l),
                    "High": str(new_h),
                    "Close": str(c),
                }
            )

    backup = None
    if changed and not dry_run:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = f"{path}.bak-{stamp}"
        shutil.copy2(path, backup)

        tmp_path = f"{path}.tmp"
        with open(tmp_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
            writer.writerows(records)
        os.replace(tmp_path, path)

    return len(records), changed, unparsable, backup


def main(argv):
    args = [a for a in argv[1:] if a != "--dry-run"]
    dry_run = "--dry-run" in argv[1:]
    paths = args or default_files()

    if not paths:
        print("No *_price_history.csv files found; nothing to repair.")
        return 0

    total_changed = 0
    for path in paths:
        rows, changed, unparsable, backup = repair_file(path, dry_run=dry_run)
        total_changed += changed
        status = "would repair" if dry_run else "repaired"
        print(
            f"{os.path.basename(path)}: {rows} rows, "
            f"{status} {changed}, unparsable {unparsable}"
        )
        if backup:
            print(f"  backup: {os.path.basename(backup)}")

    print(f"\nTotal rows {'to repair' if dry_run else 'repaired'}: {total_changed}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
