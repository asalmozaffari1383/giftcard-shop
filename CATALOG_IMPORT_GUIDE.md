# راهنمای ورود محصولات دیجیتال

## وضعیت فعلی

محصولات عمومی هفت منبع زیر در «صف بررسی محصولات» پنل مدیریت ذخیره می‌شوند:

- کیف پول من
- موبوگیفت
- Accsell
- AccountPlus
- آی‌پینز
- نخل مارکت (فقط گیفت‌کارت و کد دیجیتال)
- یانگ سنتر (فقط دسته گیفت‌کارت)

داده رقبا مستقیماً به محصول قابل فروش تبدیل نمی‌شود. ابتدا مدیر باید عنوان، قیمت فروش، ریجن، مبلغ، روش تحویل و موجودی واقعی فروشگاه را بررسی کند.

## مسیر پنل مدیریت

1. وارد `http://localhost:8000/admin/` شوید.
2. بخش `Integrations` را باز کنید.
3. وارد `Catalog candidates` شوید.
4. موارد موردنظر را انتخاب و ابتدا «تأیید موارد انتخاب‌شده» را اجرا کنید.
5. سپس «ساخت محصول غیرفعال از موارد انتخاب‌شده» را اجرا کنید.
6. محصول ساخته‌شده را در کاتالوگ باز کنید، قیمت و تنوع را اصلاح کنید و در پایان فعال کنید.

## ورود تکی

در صفحه صف بررسی روی «افزودن» بزنید و مشخصات یک محصول را ثبت کنید.

## ورود گروهی JSON یا CSV

در صفحه صف بررسی روی «ورود JSON / CSV» بزنید. نمونه آماده در فایل زیر قرار دارد:

`data/catalog-import/products.example.json`

ستون‌های الزامی:

- `title`
- `source_url`

ستون‌های اختیاری:

- `external_id`
- `sku`
- `price`
- `old_price`
- `currency`
- `availability`
- `image_url`

مقادیر معتبر `availability` عبارت‌اند از `IN_STOCK`، `OUT_OF_STOCK` و `UNKNOWN`.

## ورود با دستور

```bash
docker compose exec web python manage.py import_catalog_file /path/products.json --source mobogift
```

## همگام‌سازی منابع

همه منابع:

```bash
docker compose exec web python manage.py sync_catalog_sources
```

یک منبع خاص:

```bash
docker compose exec web python manage.py sync_catalog_sources --source accsell
```

همگام‌سازی شبکه‌ای باید مطابق robots.txt، شرایط استفاده سایت منبع و محدودیت نرخ درخواست انجام شود. توضیحات و تصاویر رقبا بدون مجوز برای انتشار عمومی کپی نشوند.

## پرامپت قابل استفاده در آینده

```text
فهرست محصولات دیجیتال منبع جدید را به سیستم Catalog Import پروژه giftcard-shop اضافه کن.
ابتدا robots.txt و روش عمومی مجاز منبع را بررسی کن. فقط عنوان، URL، SKU، قیمت عمومی،
وضعیت موجودی و URL تصویر را به CatalogCandidate وارد کن. توضیحات و تصاویر را کپی یا منتشر نکن.
برای منبع Adapter مستقل و idempotent بساز، محصولات تکراری را با normalized_title شناسایی کن،
همه موارد را در وضعیت PENDING نگه دار و تست‌های sync، upsert و publish غیرفعال را اجرا کن.
```
