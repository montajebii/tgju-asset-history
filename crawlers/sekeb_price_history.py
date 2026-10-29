"""
سکه بهار آزادی (sekeb) price history crawler for tgju.org.

Thin wrapper around the shared module tgju_price_history.py.
Run from the repository root:  python3 crawlers/sekeb_price_history.py
The CSV lands in data/ (optional override:  python3 crawlers/sekeb_price_history.py <path>)
"""

from tgju_price_history import update_history

SYMBOL = "sekeb"
CSV_FILENAME = "data/sekeb_price_history.csv"

if __name__ == "__main__":
    import sys

    update_history(SYMBOL, sys.argv[1] if len(sys.argv) > 1 else CSV_FILENAME)
