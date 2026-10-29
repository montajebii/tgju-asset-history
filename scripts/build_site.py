#!/usr/bin/env python3
"""Generate the static dataset site for GitHub Pages.

Writes to --out (default _site):
    index.html      RTL Persian landing page with per-dataset stats
    data/*.csv      the dataset files themselves

The page is intentionally dependency-free static HTML so it works anywhere.
"""

import argparse
import csv
import glob
import html
import os
import shutil
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data")

SYMBOLS = [
    ("dollar_price_history", "price_dollar_rl", "دلار آمریکا", "دلار"),
    ("gold_price_history", "geram18", "طلای ۱۸ عیار", "گرم"),
    ("geram24_price_history", "geram24", "طلای ۲۴ عیار", "گرم"),
    ("sekee_price_history", "sekee", "سکه تمام امامی", "عدد"),
    ("sekeb_price_history", "sekeb", "سکه بهار آزادی", "عدد"),
    ("nim_price_history", "nim", "نیم‌سکه", "عدد"),
    ("rob_price_history", "rob", "ربع‌سکه", "عدد"),
    ("gerami_price_history", "gerami", "سکه گرمی", "عدد"),
]


def stats(path):
    rows = 0
    first = last = None
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows += 1
            if first is None:
                first = row["Date"]
            last = row["Date"]
    return rows, first, last


def build(out_dir):
    os.makedirs(os.path.join(out_dir, "data"), exist_ok=True)

    rows_html = []
    total = 0
    for file, sym, name, unit in SYMBOLS:
        src = os.path.join(DATA_DIR, f"{file}.csv")
        if not os.path.exists(src):
            continue
        shutil.copy2(src, os.path.join(out_dir, "data", f"{file}.csv"))
        rows, first, last = stats(src)
        total += rows
        rows_html.append(
            f"<tr><td class='n'>{html.escape(name)}</td>"
            f"<td dir='ltr'>{html.escape(sym)}</td>"
            f"<td dir='ltr'>{rows:,}</td>"
            f"<td dir='ltr'>{first}</td>"
            f"<td dir='ltr'>{last}</td>"
            f"<td>{html.escape(unit)}</td>"
            f"<td><a href='data/{file}.csv'>CSV</a></td></tr>"
        )

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    page = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>tgju-asset-history — دیتاست قیمت ارز و دارایی</title>
<style>
  body {{ font-family: Vazirmatn, Tahoma, sans-serif; background: #FCFAF7;
         color: #1E2321; margin: 0; padding: 40px 16px; }}
  main {{ max-width: 860px; margin: 0 auto; }}
  h1 {{ font-size: 26px; }} .sub {{ color: #6B7370; font-size: 14px; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 24px;
           background: #fff; border-radius: 12px; overflow: hidden;
           box-shadow: 0 1px 4px rgba(0,0,0,.06); }}
  th, td {{ padding: 10px 12px; text-align: right; font-size: 13.5px;
            border-bottom: 1px solid #E5DFD6; }}
  th {{ background: #0F766E; color: #fff; font-weight: 600; }}
  tr:last-child td {{ border-bottom: none; }}
  .n {{ font-weight: 600; }} a {{ color: #0F766E; }}
  .foot {{ margin-top: 24px; font-size: 12px; color: #6B7370; line-height: 1.9; }}
</style>
</head>
<body>
<main>
  <h1>tgju-asset-history</h1>
  <p class="sub">دیتاست آزاد و به‌روزشدنی قیمت ارز و دارایی ایران بر پایه tgju.org —
  {total:,} ردیف در {len(SYMBOLS)} دارایی · آخرین به‌روزرسانی: {now}</p>
  <table>
    <tr><th>دارایی</th><th>نماد tgju</th><th>ردیف</th><th>از تاریخ</th>
        <th>تا تاریخ</th><th>واحد</th><th>دانلود</th></tr>
    {"".join(rows_html)}
  </table>
  <p class="foot">
    ستون‌ها: Date (میلادی) · Persian_Date (شمسی) · Open · Low · High · Close (ریال).
    برای تاریخ‌های تعطیل ردیفی وجود ندارد؛ نزدیک‌ترین روز معاملاتی قبل را مصرف‌کننده
    باید انتخاب کند. منبع: api.tgju.org — کدها در
    <a href="https://github.com/montajebii/tgju-asset-history">گیت‌هاب</a>.
    این داده رسمی نیست و ممکن است شامل خطای منبع باشد.
  </p>
</main>
</body>
</html>
"""
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)
    print(f"site built: {out_dir} ({total:,} rows across {len(SYMBOLS)} datasets)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="_site")
    args = parser.parse_args()
    build(args.out)
