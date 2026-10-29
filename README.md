# tgju-asset-history

دیتاست آزاد و به‌روزشدنیِ قیمت **ارز و دارایی در ایران** بر پایه داده‌های
[tgju.org](https://www.tgju.org) — شامل دلار، طلای ۱۸ و ۲۴ عیار و پنج نوع سکه،
با تاریخچه روزانه از ۱۳۸۹ تا امروز و کراولر خودکار شبانه.

**English (short):** a free, nightly-updated dataset of Iranian asset prices
(USD/IRR, 18k/24k gold, five coin types) crawled from tgju.org, shipped as
clean CSVs plus the crawler engine. Download from
[GitHub Pages](https://montajebii.github.io/tgju-asset-history/) or
[Releases](https://github.com/montajebii/tgju-asset-history/releases).

## فایل‌های دیتاست

همه فایل‌ها در [`data/`](data/) با یک قالب یکسان ذخیره می‌شوند و همین فایل‌ها
روی [Pages](https://montajebii.github.io/tgju-asset-history/) هم در دسترس‌اند:

| فایل | دارایی | نماد tgju | واحد قیمت |
|---|---|---|---|
| [dollar_price_history.csv](data/dollar_price_history.csv) | دلار آمریکا | `price_dollar_rl` | ریال / دلار |
| [gold_price_history.csv](data/gold_price_history.csv) | طلای ۱۸ عیار | `geram18` | ریال / گرم |
| [geram24_price_history.csv](data/geram24_price_history.csv) | طلای ۲۴ عیار | `geram24` | ریال / گرم |
| [sekee_price_history.csv](data/sekee_price_history.csv) | سکه تمام امامی | `sekee` | ریال / عدد |
| [sekeb_price_history.csv](data/sekeb_price_history.csv) | سکه بهار آزادی | `sekeb` | ریال / عدد |
| [nim_price_history.csv](data/nim_price_history.csv) | نیم‌سکه | `nim` | ریال / عدد |
| [rob_price_history.csv](data/rob_price_history.csv) | ربع‌سکه | `rob` | ریال / عدد |
| [gerami_price_history.csv](data/gerami_price_history.csv) | سکه گرمی | `gerami` | ریال / عدد |

### قالب داده

هر فایل یک CSV ساده با سربرگ ثابت است:

| ستون | توضیح |
|---|---|
| `Date` | تاریخ میلادی، قالب `YYYY/MM/DD` |
| `Persian_Date` | تاریخ شمسی، قالب `YYYY/MM/DD` |
| `Open` | اولین قیمت ثبت‌شدهٔ آن روز (ریال) |
| `Low` | کمترین قیمت آن روز (ریال) |
| `High` | بیشترین قیمت آن روز (ریال) |
| `Close` | آخرین قیمت ثبت‌شدهٔ آن روز (ریال) |

```python
import pandas as pd

df = pd.read_csv(
    "https://montajebii.github.io/tgju-asset-history/data/gold_price_history.csv"
)
df["Date"] = pd.to_datetime(df["Date"])
df = df.set_index("Date")
```

نکته‌های مهم هنگام مصرف داده:

- برای روزهای تعطیل (پنجشنبه/جمعه و تعطیلات رسمی) ردیفی وجود ندارد؛ اگر به
  قیمتِ یک تاریخ خاص نیاز دارید، نزدیک‌ترین روز معاملاتی **قبل** از آن را ملاک
  بگیرید.
- داده از منبع عمومی tgju.org می‌آید و رسمی نیست؛ ممکن است شامل خطا یا شکاف
  باشد. ابزارهای اعتبارسنجی در `tools/` ناسازگاری‌های OHLC را پیدا و تعمیر
  می‌کنند.
- قیمت‌ها همیشه به **ریال** است؛ تبدیل به تومان بر عهده مصرف‌کننده است (÷۱۰).

## به‌روزرسانی دیتاست

### خودکار (GitHub Actions)

هر شب ساعت ۲۲:۰۰ به وقت تهران، ورک‌فلو
[Update dataset](.github/workflows/update.yml) هر هشت کراولر را اجرا می‌کند،
خروجی را اعتبارسنجی می‌کند و در صورت تغییر، کامیت و push می‌کند (کامیت‌ها با
`github-actions[bot]`). سپس ورک‌فلو Pages سایت و لینک‌های CSV را تازه می‌کند.
تگ `v*` بزنید تا zip دیتاست به‌صورت
[Release](https://github.com/montajebii/tgju-asset-history/releases) منتشر شود.

### دستی (سیستم خودتان)

```bash
# از ریشه ریپو؛ هر کراولر یک نماد را کامل fetch و با داده موجود merge می‌کند
python3 crawlers/dollar_price_history.py
python3 crawlers/gold_price_history.py
# ... بقیه نمادها

# اعتبارسنجی و در صورت نیاز تعمیر OHLC
python3 tools/validate_csvs.py
python3 tools/fix_ohlc.py --dry-run
```

## موتور کراولر

همه کراولرها روی یک موتور مشترک سوارند
([`crawlers/tgju_price_history.py`](crawlers/tgju_price_history.py)):

- منبع، همان API سروری است که جدول آرشیو tgju.org استفاده می‌کند:
  `https://api.tgju.org/v1/market/indicator/summary-table-data/<symbol>`
  — کل تاریخچه در یک درخواست HTTP برمی‌گردد؛ نه Selenium، نه درایور مرورگر.
- ادغام بر اساس تاریخ با اولویت داده تازه‌تر، مرتب‌سازی صعودی و گزارش
  اعتبارسنجی (تعداد ردیف، بازه، تکراری، روزهای غایب).
- retry با تاخیر، رد شدن امن ردیف‌های ناقص، و قابلیت تغییر نماد با یک خط
  (`SYMBOL`) — پس افزودن هر نماد دیگر tgju فقط یک فایل پوش نیازمند است.

نمادهای جدید را در `crawlers/` به همان شکل wrapperها اضافه کنید و ردیفشان را
به جدول README و `scripts/build_site.py` بیفزایید.

## پروژه‌های ساخته‌شده روی این داده

- [**مُنتَلا (Montala)**](https://github.com/montajebii/montala) — محاسبه سود و
  زیان فرضی سرمایه‌گذاری و ارزش‌گذاری سبد دارایی در یک تاریخ (کاربرد مهریه)؛
  Flutter برای اندروید، ویندوز، لینوکس و وب.

اگر شما هم استفاده‌ای کردید، خوشحال می‌شوم لینکش را برایم بفرستید تا اینجا
اضافه شود.

## اعتبار و منبع

ایده و دیتاست اولیهٔ دلار از پروژه
[Dollar_Rial_Price_Dataset](https://github.com/M-Taghizadeh/Dollar_Rial_Price_Dataset)
اثر [Mohammad Taghizadeh](https://github.com/M-Taghizadeh) الهام گرفته شده است؛
با تشکر از او. منبع قیمت‌ها [tgju.org](https://www.tgju.org) است.

## لایسنس

[MIT](LICENSE) — آزادانه استفاده، تغییر و بازنشر کنید. داده‌های قیمت صرفاً
کاربرد اطلاعاتی دارند و توصیه سرمایه‌گذاری نیستند.
