# تنظیمات اتصال سرویس‌های آلیسان

راهنمای تهیه سرویس‌ها برای مالک کسب‌وکار: [CLIENT_SERVICE_SETUP.md](../CLIENT_SERVICE_SETUP.md).

قرارداد پیامک بر اساس مستندات رسمی https://api.sms.ir/swagger/v1/swagger.json تنظیم شده است.
ارسال کد ورود و اعلان سفارش از `POST /v1/send/verify` با هدر `x-api-key` و
فیلدهای `mobile`، `templateId` و `parameters` استفاده می‌کند. فقط پاسخ با `status=1`
به معنی پذیرش درخواست است؛ تحویل به گوشی نیاز به آزمون واقعی دارد.

اطلاعات واقعی فقط در فایل خصوصی `.env.production` روی سرور قرار می‌گیرند. نمونه در `.env.production.example` آماده است:

```dotenv
PUBLIC_BASE_URL=https://api.alisan.shop
FRONTEND_URL=https://alisan.shop
NEXT_PUBLIC_SITE_URL=https://alisan.shop
ALLOWED_HOSTS=api.alisan.shop,web
CORS_ALLOWED_ORIGINS=https://alisan.shop,https://www.alisan.shop
CSRF_TRUSTED_ORIGINS=https://alisan.shop,https://www.alisan.shop,https://api.alisan.shop
SMS_PROVIDER=smsir
SMS_API_URL=https://api.sms.ir/v1/send/verify
SMS_API_KEY=replace-with-private-api-key
SMS_TEMPLATE_ID=replace-with-numeric-otp-template-id
SMS_ORDER_TEMPLATE_ID=replace-with-numeric-order-template-id
SMS_OTP_PARAMETER=CODE
SMS_ORDER_PARAMETER=ORDER_REFERENCE
PAYMENT_GATEWAY=zarinpal
ZARINPAL_MERCHANT_ID=replace-with-merchant-id
ZARINPAL_SANDBOX=true
DEVELOPMENT_OTP_CODE=
```

سایر مقادیر فایل نمونه، از جمله کلیدهای مستقل، اطلاعات دیتابیس و اطلاعات عمومی کسب‌وکار نیز باید تکمیل شوند. کلیدهای رمزنگاری دیتابیس موجود را هنگام به‌روزرسانی عوض نکنید.

برای درگاه واقعی پس از تکمیل آزمون‌ها، `ZARINPAL_SANDBOX=false` می‌شود. پیش از انتشار فروش واقعی، `python manage.py production_check --live` باید موفق باشد و یک پیامک و خرید واقعی تحت نظارت مالک آزمایش شوند. فرمان production با مقادیر جایگزین عمداً متوقف می‌شود.

سازگاری حساب واقعی، تأیید الگوها و تحویل به شماره آزمایشی باید پس از دریافت دسترسی بررسی شوند.
