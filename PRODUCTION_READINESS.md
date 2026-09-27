# آمادگی مرحله نهایی Production

این پروژه طوری آماده شده که اطلاعات هاست، دامنه، پیامک و درگاه در آخرین مرحله دریافت شوند. تا قبل از آن، مقادیر واقعی نباید داخل Git قرار بگیرند.

## اطلاعاتی که در پایان از کارفرما می‌گیریم

1. دسترسی سرور یا پنل هاست و سیستم‌عامل/منابع سرور
2. دامنه‌های نهایی فرانت و API و دسترسی DNS
3. Merchant ID زرین‌پال و مشخص‌شدن Sandbox یا Live
4. آدرس API، کلید و Template ID سرویس پیامک
5. اطلاعات حقوقی یا متن‌هایی که در صفحه پرداخت و پیامک نمایش داده می‌شوند

## آماده‌سازی فایل محیطی

```bash
cp .env.production.example .env.production
```

مقادیر `replace-with-*` و `example.com` را فقط روی سرور عوض کنید. برای ساخت Secretها:

```bash
python -c 'import secrets; print(secrets.token_urlsafe(64))'
python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```

`INVENTORY_FINGERPRINT_KEY` باید برای همیشه ثابت بماند. هنگام چرخش Fernet، کلید جدید ابتدای `INVENTORY_FERNET_KEYS` قرار می‌گیرد و کلید قبلی تا پایان بازرمزنگاری حذف نمی‌شود.

## اجرای Production

```bash
docker compose --env-file .env.production -f compose.production.yaml config
docker compose --env-file .env.production -f compose.production.yaml build
docker compose --env-file .env.production -f compose.production.yaml up -d
docker compose --env-file .env.production -f compose.production.yaml exec web python manage.py check --deploy
docker compose --env-file .env.production -f compose.production.yaml exec web python manage.py production_check
```

پورت‌های `3000` و `8000` فقط روی `127.0.0.1` باز می‌شوند. Reverse Proxy هاست باید دامنه فروشگاه را به `3000` و دامنه API را به `8000` متصل و HTTPS را اجباری کند.

## ترتیب اتصال سرویس‌های واقعی

1. ابتدا دامنه و HTTPS و سپس `PUBLIC_BASE_URL`، `FRONTEND_URL`، `ALLOWED_HOSTS`، CORS و CSRF تنظیم شوند.
2. اطلاعات پیامک ابتدا با حساب Staging تست شود؛ سپس OTP ثابت خالی بماند و ارسال واقعی بررسی شود.
3. زرین‌پال ابتدا با `ZARINPAL_SANDBOX=true` از ورود تا تحویل کد تست شود.
4. فقط پس از تأیید Callback و Verify، مقدار Sandbox به `false` تغییر کند.
5. Callback معتبر زرین‌پال باید به این الگو برسد: `https://api.example.com/api/v1/payments/callback/<payment-id>/`.
6. درست قبل از انتشار Live، دستور `python manage.py production_check --live` باید بدون خطا تمام شود.

## بکاپ و بازیابی

```bash
bash scripts/backup_postgres.sh
RESTORE_CONFIRM=RESTORE-giftcard_shop bash scripts/restore_postgres.sh backups/postgres_giftcard_shop_DATE.sql.gz
```

بکاپ دیتابیس بدون فایل `.env.production` و کلیدهای رمزنگاری برای بازیابی کدها کافی نیست. نسخه رمزگذاری‌شده Secretها باید جداگانه و خارج از سرور نگهداری شود. Restore ابتدا سرویس‌های وب و Celery را متوقف می‌کند و بدون عبارت تأیید اجرا نمی‌شود.

## کنترل نهایی قبل از انتشار

- `DEBUG=false` و `AUTH_COOKIE_SECURE=true`
- هیچ مقدار `replace-with-*` یا `example.com` باقی نمانده باشد
- PostgreSQL و Redis از اینترنت قابل دسترسی نباشند
- صفحه Admin فقط برای کاربر `is_staff + is_admin + is_verified` یا Superuser قابل استفاده باشد
- `/health/live/` و `/health/ready/` پاسخ ۲۰۰ بدهند
- OTP واقعی به شماره آزمایشی برسد و متن آن اطلاعات حساس اضافی نداشته باشد
- پرداخت Sandbox، Callback، Verify و تحویل کد کامل تست شوند
- تراکنش‌های `RECONCILIATION` قبل از هر Refund با گزارش تسویه درگاه تطبیق داده شوند
- یک بکاپ ساخته و حداقل یک بار Restore آن روی محیط آزمایشی امتحان شود
- حساب‌های Admin دارای رمز قوی و ترجیحاً MFA در لایه هاست/Identity Provider باشند

## رسیدگی به پرداخت تحویل‌نشده

ابتدا فقط گزارش تراکنش را ببینید:

```bash
python manage.py reconcile_payment PAYMENT_UUID
```

پس از تطبیق Reference ID با گزارش تسویه درگاه، اگر خروجی نشان داد تمام موجودی همان سفارش هنوز رزرو است، تحویل دستی کنترل‌شده انجام می‌شود:

```bash
python manage.py reconcile_payment PAYMENT_UUID --fulfill
```

این دستور برای سفارش Failed، تراکنش Refundشده، پرداخت بدون تأیید بانکی، پرداخت تکراری یا رزرو ناقص تحویل انجام نمی‌دهد. در این حالت باید وجه در پنل درگاه مسترد و سپس Refund در سیستم ثبت شود.
