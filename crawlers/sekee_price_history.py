"""
سکه تمام امامی (sekee) price history crawler for tgju.org.

Thin wrapper around the shared module tgju_price_history.py.
Run from the repository root:  python3 crawlers/sekee_price_history.py
The CSV lands in data/ (optional override:  python3 crawlers/sekee_price_history.py <path>)
"""

from tgju_price_history import update_history

SYMBOL = "sekee"
CSV_FILENAME = "data/sekee_price_history.csv"

if __name__ == "__main__":
    import sys

    update_history(SYMBOL, sys.argv[1] if len(sys.argv) > 1 else CSV_FILENAME)
